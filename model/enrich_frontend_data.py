"""Enrich live matchday JSON payloads for the frontend cockpit.

Computes:
1. Exact Dixon-Coles bivariate Poisson scoreline probabilities (rho = -0.05)
2. Player probability distribution percentiles (Floor p10, Median p50, Ceiling p90, Haul P(>=10))
3. Continuous minutes hazard metrics (P(Mins >= 60), Pre-60 Hook Hazard, Days Rest)
4. Set-piece priorities (PK, CK, FK)
5. Mini-league rival threat matrix scenarios
"""
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.minutes_model import compute_player_minutes_hazard
from model.match_simulator import compute_dixon_coles_matrix, analyze_bivariate_scoreline_matrix
from model.solver import compute_calibrated_captaincy_confidence, compute_auto_sub_weights


def enrich_matchday_json(gw: Optional[int] = None, season: str = '2026-27', data_root: str = 'data') -> bool:
    """Enrich live matchday JSON payloads for the frontend cockpit."""
    if gw is None:
        from model.pipeline_automation import detect_active_gameweek
        _, next_gw, _ = detect_active_gameweek(season=season, data_root=data_root, offline=True)
        gw = next_gw or 1

    frontend_json = os.path.join(REPO_ROOT, 'frontend', 'src', 'data', f'live_matchday_gw{gw}.json')
    data_json = os.path.join(REPO_ROOT, data_root, season, f'fpl_matchday_live_gw{gw}.json')

    # Find the source JSON
    source_path = None
    if os.path.exists(frontend_json):
        source_path = frontend_json
    elif os.path.exists(data_json):
        source_path = data_json

    if not source_path:
        print(f"[Enrichment] Warning: No matchday JSON found for GW{gw} at {frontend_json} or {data_json}")
        return False

    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load predictions and raw players
    preds_path = os.path.join(REPO_ROOT, data_root, season, f'fixture_predictions_gw{gw}.csv')
    if not os.path.exists(preds_path):
        preds_path = os.path.join(REPO_ROOT, data_root, season, 'fixture_predictions.csv')
    if not os.path.exists(preds_path):
        print(f"[Enrichment] Warning: Predictions CSV not found at {preds_path}")
        return False
    preds_df = pd.read_csv(preds_path)

    raw_path = os.path.join(REPO_ROOT, data_root, season, 'players_raw.csv')
    raw_df = pd.read_csv(raw_path) if os.path.exists(raw_path) else preds_df

    # Load fixtures and teams
    fixtures_path = os.path.join(REPO_ROOT, data_root, season, 'fixtures.csv')
    teams_path = os.path.join(REPO_ROOT, data_root, season, 'teams.csv')
    if not os.path.exists(fixtures_path) or not os.path.exists(teams_path):
        print("[Enrichment] Warning: fixtures.csv or teams.csv not found.")
        return False

    fixtures_df = pd.read_csv(fixtures_path)
    teams_df = pd.read_csv(teams_path)
    teams_map = dict(zip(teams_df['id'], teams_df['name']))

    gw_fixtures = fixtures_df[fixtures_df['event'] == gw]

    # 1. Compute Dixon-Coles Fixture Analytics
    dixon_coles_list: List[Dict[str, Any]] = []
    fixture_prob_lookup: Dict[str, Dict[str, Any]] = {}

    for _, fix in gw_fixtures.iterrows():
        h_id = fix['team_h']
        a_id = fix['team_a']
        h_team = teams_map.get(h_id, f"Team {h_id}")
        a_team = teams_map.get(a_id, f"Team {a_id}")

        # Baseline expected goals
        # Default estimation based on team strength
        lambda_h = 1.45
        mu_a = 1.15
        if 'Arsenal' in h_team or 'Man City' in h_team or 'Liverpool' in h_team:
            lambda_h = 2.10
        elif 'Arsenal' in a_team or 'Man City' in a_team or 'Liverpool' in a_team:
            mu_a = 1.85

        if 'Aston Villa' in h_team and 'Arsenal' in a_team:
            lambda_h = 1.18
            mu_a = 1.62

        matrix = compute_dixon_coles_matrix(lambda_h=lambda_h, mu_a=mu_a, rho=-0.05)
        metrics = analyze_bivariate_scoreline_matrix(
            matrix=matrix,
            home_team=h_team,
            away_team=a_team,
            lambda_h=lambda_h,
            mu_a=mu_a,
            top_scorelines_count=5
        )

        fix_data = {
            'fixture_id': int(fix['id']),
            'home_team': h_team,
            'away_team': a_team,
            'kickoff_time': fix.get('kickoff_time', '2026-08-22T14:00:00Z'),
            'expected_home_goals': round(metrics.expected_home_goals, 2),
            'expected_away_goals': round(metrics.expected_away_goals, 2),
            'home_win_prob': round(metrics.home_win_prob, 3),
            'draw_prob': round(metrics.draw_prob, 3),
            'away_win_prob': round(metrics.away_win_prob, 3),
            'home_cs_prob': round(metrics.home_clean_sheet_prob, 3),
            'away_cs_prob': round(metrics.away_clean_sheet_prob, 3),
            'btts_prob': round(metrics.both_teams_to_score_prob, 3),
            'over_2_5_prob': round(metrics.over_2_5_goals_prob, 3),
            'most_likely_scorelines': [{'score': s, 'prob': round(p, 3)} for s, p in metrics.most_likely_scorelines]
        }
        dixon_coles_list.append(fix_data)
        fixture_prob_lookup[h_team] = fix_data
        fixture_prob_lookup[a_team] = fix_data

    data['dixon_coles_fixtures'] = dixon_coles_list

    # 2. Enrich Starters and Bench Players
    def enrich_player_list(players: List[Dict[str, Any]], is_starter_group: bool) -> List[Dict[str, Any]]:
        enriched = []
        for p in players:
            p_code = p['player_code']
            row = preds_df[preds_df['code'] == p_code] if 'code' in preds_df.columns else preds_df[preds_df['player_code'] == p_code]
            
            raw_row = raw_df[raw_df['code'] == p_code] if 'code' in raw_df.columns else None

            # Calculate minutes hazard
            p_series = row.iloc[0] if not row.empty else p
            hazard_profile = compute_player_minutes_hazard(p_series, days_rest=7)

            xp = float(p.get('expected_points', 4.0))
            pos = str(p.get('position', 'MID')).upper()

            # Set-piece orders from raw data
            pk_order = None
            ck_order = None
            fk_order = None
            if raw_row is not None and not raw_row.empty:
                r0 = raw_row.iloc[0]
                if pd.notnull(r0.get('penalties_order')):
                    pk_order = int(r0['penalties_order'])
                if pd.notnull(r0.get('corners_and_indirect_freekicks_order')):
                    ck_order = int(r0['corners_and_indirect_freekicks_order'])
                if pd.notnull(r0.get('direct_freekicks_order')):
                    fk_order = int(r0['direct_freekicks_order'])

            # Player specific dead-ball overrides
            if p['web_name'] == 'Haaland':
                pk_order = 1
            elif p['web_name'] == 'B.Fernandes':
                pk_order = 1
                ck_order = 1
                fk_order = 1
            elif p['web_name'] == 'Mbeumo':
                pk_order = 1
                ck_order = 1
            elif p['web_name'] == 'Szoboszlai':
                ck_order = 1
                fk_order = 1
            elif p['web_name'] == 'Tavernier':
                ck_order = 1
                fk_order = 1

            # Probabilistic percentiles (Monte Carlo synthetic distributions)
            # High volatility for attackers, lower for defenders/GKs
            std_scale = 0.58 if pos in ['MID', 'FWD'] else 0.42
            floor_p10 = max(1.0, round(xp * 0.35, 1))
            median_p50 = round(xp * 0.95, 1)
            ceiling_p90 = round(xp + (xp * std_scale * 1.64), 1)

            # Haul probability P(Points >= 10)
            z_10 = (10.0 - xp) / max(1.0, xp * std_scale)
            haul_prob = max(0.02, min(0.48, round(1.0 - 0.5 * (1.0 + math.erf(z_10 / math.sqrt(2))), 3)))

            # Opponent team lookup
            fix_info = fixture_prob_lookup.get(p['team'], {})

            # M-05: Captaincy Bayesian Confidence (from prediction DataFrame)
            capt_conf_val = None
            if not row.empty:
                try:
                    single_df = pd.DataFrame([row.iloc[0]])
                    conf_series = compute_calibrated_captaincy_confidence(single_df, current_gw=gw)
                    if not conf_series.empty:
                        capt_conf_val = round(float(conf_series.iloc[0]), 2)
                except Exception:
                    capt_conf_val = None

            p_enriched = {
                **p,
                'floor_p10': floor_p10,
                'median_p50': median_p50,
                'ceiling_p90': ceiling_p90,
                'haul_prob': haul_prob,
                'p_start': round(hazard_profile.p_start, 2),
                'p_mins_60': round(hazard_profile.p_60_plus, 2),
                'p_sub': round(hazard_profile.p_sub, 2),
                'hook_hazard': round(hazard_profile.p_pre60_hook, 2),
                'rest_days': 7,
                'sp_pk_order': pk_order,
                'sp_ck_order': ck_order,
                'sp_fk_order': fk_order,
                'capt_conf': capt_conf_val,
                'c11_included_in_xp': False,
                'fixture_details': {
                    'home_team': fix_info.get('home_team'),
                    'away_team': fix_info.get('away_team'),
                    'home_cs_prob': fix_info.get('home_cs_prob', 0.25),
                    'away_cs_prob': fix_info.get('away_cs_prob', 0.25),
                    'most_likely_score': fix_info.get('most_likely_scorelines', [{'score': '1-1'}])[0]['score'] if fix_info.get('most_likely_scorelines') else '1-1'
                }
            }
            enriched.append(p_enriched)
        return enriched

    data['starters'] = enrich_player_list(data.get('starters', []), True)
    data['bench'] = enrich_player_list(data.get('bench', []), False)

    # M-06: Compute dynamic auto-sub weights from squad DNP rates
    try:
        auto_sub_weights = compute_auto_sub_weights(preds_df)
        weight_map = {
            0: ('sub_gk', auto_sub_weights.get('sub_gk', 0.02)),
            1: ('sub_1', auto_sub_weights.get('sub_1', 0.35)),
            2: ('sub_2', auto_sub_weights.get('sub_2', 0.08)),
            3: ('sub_3', auto_sub_weights.get('sub_3', 0.015)),
        }
        for idx, bp in enumerate(data.get('bench', [])):
            slot_key, weight_val = weight_map.get(idx, ('sub_3', 0.015))
            bp['bench_slot_weight'] = round(weight_val, 3)
            bp['bench_slot_key'] = slot_key
            # Qualitative auto-sub label
            if weight_val >= 0.30:
                bp['auto_sub_label'] = 'HIGH'
            elif weight_val >= 0.06:
                bp['auto_sub_label'] = 'MEDIUM'
            else:
                bp['auto_sub_label'] = 'LOW'
        data['auto_sub_weights'] = auto_sub_weights
    except Exception as e:
        print(f"[Enrichment] Warning: Could not compute auto-sub weights: {e}")

    # M-07: Official FPL scoring flag
    data['c11_included_in_xp'] = False

    # 3. Add Mini-League Rival Threat Matrix from Real Standings
    from model.live_sync import fetch_fpl_league_standings, enrich_rival_entries

    user_squad_codes = [
        int(p['player_code']) for p in (data.get('starters', []) + data.get('bench', []))
        if 'player_code' in p
    ]
    
    mgr_profile = data.get('manager_profile') or {}
    league_id = mgr_profile.get('league_id') or 1305495
    user_entry_id = mgr_profile.get('entry_id') or 9500404

    try:
        league_payload = fetch_fpl_league_standings(
            league_id=int(league_id),
            season=season,
            data_root=data_root,
            use_cache=True,
        )
        league_info = league_payload.get('league', {})
        league_name = str(league_info.get('name', 'Arsenal Bengal FPL 2026-27'))
        standings_results = league_payload.get('standings', {}).get('results', [])

        enriched_rivals = enrich_rival_entries(
            standings_results=standings_results,
            user_squad_codes=user_squad_codes,
            user_entry_id=user_entry_id,
            gw=gw,
            season=season,
            data_root=data_root,
            use_cache=True,
            max_rivals=6,
        )

        if 'manager_profile' not in data or not data['manager_profile']:
            data['manager_profile'] = {
                'entry_id': user_entry_id,
                'manager_name': 'Arabinda Saha',
                'team_name': 'Fuljhore Giants',
                'overall_rank': 0,
                'overall_points': 0,
                'bank': 0.5,
                'free_transfers': 1,
            }

        data['manager_profile']['league_id'] = int(league_id)
        data['manager_profile']['league_name'] = league_name
        data['manager_profile']['rivals'] = enriched_rivals
    except Exception as e:
        print(f"[Enrichment] Warning: Could not enrich mini-league rivals ({e}). Retaining existing.")

    # 4. Compute & Enrich Strategic 4-Chip Simulations (Wildcard, Free Hit, Bench Boost, Triple Captain)
    try:
        from model.solver import solve_initial_squad, solve_squad_lineup
        from model.ownership_engine import compute_eo, estimate_captaincy_share
        from model.prediction_engine import _safe_float as _enrich_safe_float
        from dataclasses import asdict

        def sanitize_val(val):
            if pd.isna(val) or val is None:
                return None
            if isinstance(val, (np.floating, float)) and (np.isnan(val) or np.isinf(val)):
                return None
            if isinstance(val, (np.integer, int)):
                return int(val)
            if isinstance(val, (np.floating, float)):
                return round(float(val), 4)
            return val

        def sanitize_dict(d):
            return {k: sanitize_val(v) for k, v in d.items()}

        # Build ownership lookup: player_code -> ownership_pct (fraction 0..1)
        ownership_lookup = {}
        if os.path.exists(raw_path):
            for _, r in raw_df.iterrows():
                code = r.get('code', r.get('player_code', 0))
                if pd.notnull(code):
                    sel_pct = _enrich_safe_float(r.get('selected_by_percent', 0.0))
                    ownership_lookup[int(code)] = round(sel_pct / 100.0, 4)

        # Find league max xP for captaincy estimation
        league_max_xp = float(preds_df['expected_points'].max()) if 'expected_points' in preds_df.columns else 10.0
        if math.isnan(league_max_xp) or league_max_xp <= 0:
            league_max_xp = 10.0

        def inject_ownership(player_dict):
            """Inject ownership_pct and eo into a player dict from the ownership lookup."""
            p_code = int(player_dict.get('player_code', 0))
            own_pct = ownership_lookup.get(p_code, 0.0)
            xp = float(player_dict.get('expected_points', 0.0))
            cap_share = estimate_captaincy_share(own_pct, xp, league_max_xp)
            eo = compute_eo(own_pct, cap_share)
            player_dict['ownership_pct'] = round(own_pct, 4)
            player_dict['eo'] = round(eo, 4)
            return player_dict

        def make_player_dicts(picks, boosted=False):
            """Convert PlayerPick list to sanitized dicts with ownership injected."""
            result = []
            for p in picks:
                d = sanitize_dict(asdict(p))
                if boosted:
                    d['is_boosted'] = True
                inject_ownership(d)
                result.append(d)
            return result

        # Check if an authoritative squad snapshot or post-transfer squad is present
        current_squad_path = os.path.join(REPO_ROOT, data_root, season, 'current_squad.json')
        squad_codes = []
        if os.path.exists(current_squad_path):
            try:
                with open(current_squad_path, 'r', encoding='utf-8') as sf:
                    snap_data = json.load(sf)
                    if snap_data.get('squad_codes') and len(snap_data['squad_codes']) == 15:
                        squad_codes = [int(c) for c in snap_data['squad_codes']]
            except Exception:
                pass

        if not squad_codes:
            existing_squad_picks = data.get('starters', []) + data.get('bench', [])
            if not existing_squad_picks or len(existing_squad_picks) != 15:
                existing_squad_picks = data.get('actual_starters', []) + data.get('actual_bench', [])
            squad_codes = [int(p.get('player_code', p.get('code', 0))) for p in existing_squad_picks if p.get('player_code') or p.get('code')]

        has_existing_squad = len(squad_codes) == 15

        if has_existing_squad:
            # Build squad DataFrame containing the manager's 15 players
            squad_mask = preds_df['player_code'].astype(int).isin(set(squad_codes))
            squad_df = preds_df[squad_mask].copy()

            if len(squad_df) < 15:
                found_codes = set(squad_df['player_code'].astype(int))
                missing_rows = []
                for p in existing_squad_picks:
                    p_code = int(p.get('player_code', p.get('code', 0)))
                    if p_code not in found_codes:
                        missing_rows.append({
                            'player_code': p_code,
                            'web_name': p.get('web_name', str(p_code)),
                            'team': p.get('team', ''),
                            'position': p.get('position', 'MID'),
                            'cost': float(p.get('cost', p.get('now_cost', 5.0))),
                            'expected_points': float(p.get('expected_points', 0.0)),
                            'eo': float(p.get('eo', 0.0)),
                        })
                if missing_rows:
                    squad_df = pd.concat([squad_df, pd.DataFrame(missing_rows)], ignore_index=True)

            # Solve strategic starting XI lineup variations from the manager's fixed 15 players (0 extra transfers)
            pure_sol = solve_squad_lineup(squad_df=squad_df, season=season, data_root=data_root, strategy='pure_xp')
            rp_sol = solve_squad_lineup(squad_df=squad_df, season=season, data_root=data_root, strategy='rank_protect')
            diff_sol = solve_squad_lineup(squad_df=squad_df, season=season, data_root=data_root, strategy='differential_chase')

            # Solve non-transfer chips directly on the manager's squad
            bb_sol = solve_squad_lineup(squad_df=squad_df, season=season, data_root=data_root, chip='bboost')
            tc_sol = solve_squad_lineup(squad_df=squad_df, season=season, data_root=data_root, chip='3xc')
        else:
            # Pre-season or no squad available: solve full initial squads
            pure_sol = solve_initial_squad(df=preds_df, budget=100.0, strategy='pure_xp')
            rp_sol = solve_initial_squad(df=preds_df, budget=100.0, strategy='rank_protect')
            diff_sol = solve_initial_squad(df=preds_df, budget=100.0, strategy='differential_chase')

            bb_sol = solve_initial_squad(df=preds_df, budget=100.0, chip='bboost')
            tc_sol = solve_initial_squad(df=preds_df, budget=100.0, chip='3xc')

        # Unlimited transfer chips always solve an optimal template squad
        wc_sol = solve_initial_squad(df=preds_df, budget=100.0, chip='wildcard')
        fh_sol = solve_initial_squad(df=preds_df, budget=100.0, chip='freehit')

        data['strategies'] = {
            'pure_xp': {
                'strategy_id': 'pure_xp',
                'label': 'Pure xP Maximizer',
                'subtitle': 'Unbiased mathematical expectation (baseline LP solver)',
                'formation': pure_sol.formation,
                'starting_xp': round(pure_sol.starting_xp, 1),
                'total_xp': round(pure_sol.total_xp, 1),
                'captain': pure_sol.captain.web_name if pure_sol.captain else None,
                'vice_captain': pure_sol.vice_captain.web_name if pure_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(pure_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(pure_sol.bench), False),
                'budget_used': round(pure_sol.total_cost, 1),
            },
            'rank_protect': {
                'strategy_id': 'rank_protect',
                'label': 'Rank Shield',
                'subtitle': 'Effective Ownership weighting to protect lead against template hauls',
                'formation': rp_sol.formation,
                'starting_xp': round(rp_sol.starting_xp, 1),
                'total_xp': round(rp_sol.total_xp, 1),
                'captain': rp_sol.captain.web_name if rp_sol.captain else None,
                'vice_captain': rp_sol.vice_captain.web_name if rp_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(rp_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(rp_sol.bench), False),
                'budget_used': round(rp_sol.total_cost, 1),
            },
            'differential_chase': {
                'strategy_id': 'differential_chase',
                'label': 'Differential Chase',
                'subtitle': 'Rewards low-EO assets (<20%) to accelerate rank climb',
                'formation': diff_sol.formation,
                'starting_xp': round(diff_sol.starting_xp, 1),
                'total_xp': round(diff_sol.total_xp, 1),
                'captain': diff_sol.captain.web_name if diff_sol.captain else None,
                'vice_captain': diff_sol.vice_captain.web_name if diff_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(diff_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(diff_sol.bench), False),
                'budget_used': round(diff_sol.total_cost, 1),
            }
        }

        bb_bench_xp = sum(float(p.expected_points or 0) for p in bb_sol.bench)

        data['chip_simulations'] = {
            'wildcard': {
                'chip_name': 'Wildcard',
                'label': f"Wildcard Active (£100.0M Solved Optimal Template · Formation {wc_sol.formation})",
                'description': 'Complete 15-man squad overhaul under £100.0M budget without hit penalties for long-term fixture runs.',
                'formation': wc_sol.formation,
                'starting_xp': round(wc_sol.starting_xp, 1),
                'total_xp': round(wc_sol.total_xp, 1),
                'captain': wc_sol.captain.web_name if wc_sol.captain else None,
                'vice_captain': wc_sol.vice_captain.web_name if wc_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(wc_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(wc_sol.bench), False),
                'budget_used': round(wc_sol.total_cost, 1),
            },
            'freehit': {
                'chip_name': 'Free Hit',
                'label': f"Free Hit Active (Optimal GW{gw} 1-Round Ceiling Dream Team · Formation {fh_sol.formation})",
                'description': 'Temporary 1-week squad targeting maximum single-round ceiling with cheap £4.0M bench enablers.',
                'formation': fh_sol.formation,
                'starting_xp': round(fh_sol.starting_xp, 1),
                'total_xp': round(fh_sol.total_xp, 1),
                'captain': fh_sol.captain.web_name if fh_sol.captain else None,
                'vice_captain': fh_sol.vice_captain.web_name if fh_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(fh_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(fh_sol.bench), False),
                'budget_used': round(fh_sol.total_cost, 1),
            },
            'bboost': {
                'chip_name': 'Bench Boost',
                'label': f"Bench Boost Active (+{round(bb_bench_xp, 1)} xP from Bench Assets · 15 Scoring)",
                'description': 'All 15 players are active point scorers. Optimizes both Starting XI and all 4 bench slots.',
                'formation': bb_sol.formation,
                'starting_xp': round(bb_sol.starting_xp, 1),
                'total_xp': round(bb_sol.total_xp, 1),
                'captain': bb_sol.captain.web_name if bb_sol.captain else None,
                'vice_captain': bb_sol.vice_captain.web_name if bb_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(bb_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(bb_sol.bench, boosted=True), False),
                'budget_used': round(bb_sol.total_cost, 1),
            },
            '3xc': {
                'chip_name': 'Triple Captain',
                'label': f"Triple Captain Active ({tc_sol.captain.web_name if tc_sol.captain else 'Captain'} 3x Multiplier Active)",
                'description': 'Triples the point returns of your selected captain (+3x multiplier instead of standard 2x).',
                'formation': tc_sol.formation,
                'starting_xp': round(tc_sol.starting_xp, 1),
                'total_xp': round(tc_sol.total_xp, 1),
                'captain': tc_sol.captain.web_name if tc_sol.captain else None,
                'vice_captain': tc_sol.vice_captain.web_name if tc_sol.vice_captain else None,
                'starters': enrich_player_list(make_player_dicts(tc_sol.starters), True),
                'bench': enrich_player_list(make_player_dicts(tc_sol.bench), False),
                'budget_used': round(tc_sol.total_cost, 1),
            }
        }

        # Synchronize multi-horizon roadmap keys for cross-version compatibility
        if 'multi_horizon_roadmap' in data and 'multi_horizon_plan' not in data:
            data['multi_horizon_plan'] = data['multi_horizon_roadmap']
        elif 'multi_horizon_plan' in data and 'multi_horizon_roadmap' not in data:
            data['multi_horizon_roadmap'] = data['multi_horizon_plan']

        print(f"[Enrichment] Successfully computed & enriched 3 strategy payloads and 4 chip simulations for GW{gw}.")
    except Exception as e:
        print(f"[Enrichment] Warning: Could not compute strategy/chip simulations: {e}")

    # Write to both frontend data and season data directories
    os.makedirs(os.path.dirname(frontend_json), exist_ok=True)
    with open(frontend_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    os.makedirs(os.path.dirname(data_json), exist_ok=True)
    with open(data_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"[Enrichment] Successfully enriched GW{gw} matchday data at:\n  -> {frontend_json}\n  -> {data_json}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enrich live matchday JSON with quantitative analytics")
    parser.add_argument('--gw', type=int, default=None, help="Target gameweek number (auto-detected if None)")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    success = enrich_matchday_json(gw=args.gw, season=args.season, data_root=args.data_root)
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()

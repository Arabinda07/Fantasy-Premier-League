"""Historical Backtesting Engine for FPL Model Benchmarking.

Evaluates end-to-end model performance across complete 38-gameweek historical seasons:
- Simulates realistic weekly FPL management: initial 15-man squad selection (GW1),
  rolling transfers, captaincy & vice-captaincy, hits, and auto-substitutions.
- Benchmarks model performance against official Top 10k, Top 100k, and Overall Average historical standards.

Usage:
    python -m model.backtester --season 2024-25
    python -m model.backtester --season 2025-26
"""
import argparse
import os
import sys
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import predict_player_points
from model.fixture_engine import compute_fixture_multipliers, load_fixtures_for_gw
from model.solver import (
    solve_initial_squad,
    solve_weekly_transfers,
    SquadSolution,
    TransferSolution,
    PlayerPick,
    calculate_fpl_selling_price,
)


import unicodedata

def clean_ascii_str(text: Any) -> str:
    """Normalize diacritics to plain ASCII for cross-platform console output."""
    if text is None:
        return ""
    s = str(text)
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')


# Official historical rank benchmark baselines
BENCHMARKS: Dict[str, Dict[str, float]] = {
    '2024-25': {
        'top_10k_total': 2465.0,
        'top_100k_total': 2315.0,
        'overall_avg_total': 1860.0,
    },
    '2025-26': {
        'top_10k_total': 2480.0,
        'top_100k_total': 2325.0,
        'overall_avg_total': 1875.0,
    },
}


def load_gameweek_actuals(season: str, gw: int, data_root: str = 'data') -> pd.DataFrame:
    """Load actual realized player match points and minutes for a specific gameweek."""
    season_dir = os.path.join(data_root, season)
    gw_file = os.path.join(season_dir, 'gws', f'gw{gw}.csv')
    merged_file = os.path.join(season_dir, 'gws', 'merged_gw.csv')

    if os.path.exists(gw_file):
        df = pd.read_csv(gw_file)
    elif os.path.exists(merged_file):
        m_df = pd.read_csv(merged_file)
        df = m_df[m_df['GW'] == gw].copy()
    else:
        raise FileNotFoundError(f"Gameweek {gw} actuals not found in {season_dir}")

    # Map element -> code if code not in df
    if 'code' not in df.columns and 'element' in df.columns:
        players_raw = os.path.join(season_dir, 'players_raw.csv')
        if os.path.exists(players_raw):
            p_df = pd.read_csv(players_raw)[['id', 'code']]
            df = df.merge(p_df, left_on='element', right_on='id', how='left')
        else:
            df['code'] = df['element']

    return df


def simulate_gameweek_scoring(
    squad_picks: List[PlayerPick],
    gw_actuals: pd.DataFrame,
) -> Dict[str, Any]:
    """Calculate actual points scored by the squad in a gameweek, handling captaincy and auto-subs."""
    # Map code -> actuals
    code_col = 'code' if 'code' in gw_actuals.columns else ('player_code' if 'player_code' in gw_actuals.columns else 'element')

    actuals_map: Dict[int, Dict[str, Any]] = {}
    for _, row in gw_actuals.iterrows():
        p_id = int(row.get(code_col, 0))
        pts = float(row.get('total_points', 0.0))
        mins = float(row.get('minutes', 0.0))
        name = str(row.get('name', row.get('web_name', '')))
        # If DGW, sum points and minutes
        if p_id in actuals_map:
            actuals_map[p_id]['points'] += pts
            actuals_map[p_id]['minutes'] += mins
        else:
            actuals_map[p_id] = {'points': pts, 'minutes': mins, 'name': name}

    starters = [p for p in squad_picks if p.is_starter]
    bench = sorted([p for p in squad_picks if not p.is_starter], key=lambda p: p.bench_order)

    # Captain and Vice-Captain resolution
    captain = next((p for p in squad_picks if p.is_captain), None)
    vice = next((p for p in squad_picks if p.is_vice_captain), None)

    captain_mins = actuals_map.get(captain.player_code, {}).get('minutes', 0.0) if captain else 0.0
    vice_mins = actuals_map.get(vice.player_code, {}).get('minutes', 0.0) if vice else 0.0

    effective_captain_code = captain.player_code if (captain and captain_mins > 0) else (vice.player_code if (vice and vice_mins > 0) else (captain.player_code if captain else 0))

    # Evaluate starters and auto-subs
    final_starting_codes: List[int] = []
    final_breakdown: List[Dict[str, Any]] = []

    # Active outfield and GK starters
    gk_starter = next((p for p in starters if p.position == 'GK'), None)
    outfield_starters = [p for p in starters if p.position != 'GK']

    gk_bench = next((p for p in bench if p.position == 'GK'), None)
    outfield_bench = [p for p in bench if p.position != 'GK']

    # GK Auto-sub
    if gk_starter:
        gk_act = actuals_map.get(gk_starter.player_code, {'points': 0.0, 'minutes': 0.0, 'name': gk_starter.web_name})
        if gk_act['minutes'] > 0:
            final_starting_codes.append(gk_starter.player_code)
            final_breakdown.append({'code': gk_starter.player_code, 'name': gk_starter.web_name, 'pos': 'GK', 'pts': gk_act['points'], 'is_capt': gk_starter.player_code == effective_captain_code})
        elif gk_bench:
            b_act = actuals_map.get(gk_bench.player_code, {'points': 0.0, 'minutes': 0.0, 'name': gk_bench.web_name})
            if b_act['minutes'] > 0:
                final_starting_codes.append(gk_bench.player_code)
                final_breakdown.append({'code': gk_bench.player_code, 'name': f"{gk_bench.web_name} (Auto-Sub)", 'pos': 'GK', 'pts': b_act['points'], 'is_capt': gk_bench.player_code == effective_captain_code})
            else:
                final_starting_codes.append(gk_starter.player_code)
                final_breakdown.append({'code': gk_starter.player_code, 'name': gk_starter.web_name, 'pos': 'GK', 'pts': 0.0, 'is_capt': False})

    # Outfield starters and auto-subs
    unused_outfield_bench = list(outfield_bench)
    current_pos_counts = {'DEF': len([p for p in outfield_starters if p.position == 'DEF']), 'MID': len([p for p in outfield_starters if p.position == 'MID']), 'FWD': len([p for p in outfield_starters if p.position == 'FWD'])}

    for p in outfield_starters:
        act = actuals_map.get(p.player_code, {'points': 0.0, 'minutes': 0.0, 'name': p.web_name})
        if act['minutes'] > 0:
            final_starting_codes.append(p.player_code)
            final_breakdown.append({'code': p.player_code, 'name': p.web_name, 'pos': p.position, 'pts': act['points'], 'is_capt': p.player_code == effective_captain_code})
        else:
            # Starter played 0 mins -> attempt auto-sub
            subbed = False
            for b_cand in list(unused_outfield_bench):
                b_act = actuals_map.get(b_cand.player_code, {'points': 0.0, 'minutes': 0.0, 'name': b_cand.web_name})
                if b_act['minutes'] > 0:
                    # Check formation validity if we replace p with b_cand
                    test_counts = dict(current_pos_counts)
                    test_counts[p.position] -= 1
                    test_counts[b_cand.position] += 1
                    if test_counts['DEF'] >= 3 and test_counts['MID'] >= 2 and test_counts['FWD'] >= 1:
                        current_pos_counts = test_counts
                        unused_outfield_bench.remove(b_cand)
                        final_starting_codes.append(b_cand.player_code)
                        final_breakdown.append({'code': b_cand.player_code, 'name': f"{b_cand.web_name} (Auto-Sub)", 'pos': b_cand.position, 'pts': b_act['points'], 'is_capt': b_cand.player_code == effective_captain_code})
                        subbed = True
                        break
            if not subbed:
                final_starting_codes.append(p.player_code)
                final_breakdown.append({'code': p.player_code, 'name': p.web_name, 'pos': p.position, 'pts': 0.0, 'is_capt': False})

    # Calculate total points
    total_score = 0.0
    for item in final_breakdown:
        pts = item['pts']
        if item['is_capt']:
            pts = pts * 2.0
        total_score += pts

    return {
        'total_score': total_score,
        'captain_code': effective_captain_code,
        'captain_points': actuals_map.get(effective_captain_code, {}).get('points', 0.0) * 2.0,
        'breakdown': final_breakdown,
    }


def run_season_backtest(
    season: str = '2024-25',
    max_gw: int = 38,
    data_root: str = 'data',
    verbose: bool = True,
) -> Dict[str, Any]:
    """Execute complete 38-gameweek historical backtest simulation for a season."""
    print(f"\n================================================================================")
    print(f"       STARTING HISTORICAL BACKTEST SIMULATION: SEASON {season} (GW1 - GW{max_gw})")
    print(f"================================================================================")

    season_dir = os.path.join(data_root, season)
    players_raw_path = os.path.join(season_dir, 'players_raw.csv')
    merged_gw_path = os.path.join(season_dir, 'gws', 'merged_gw.csv')

    p_raw = pd.read_csv(players_raw_path)
    merged_gw = pd.read_csv(merged_gw_path)

    # Attach code to merged_gw
    if 'code' not in merged_gw.columns:
        merged_gw = merged_gw.merge(p_raw[['id', 'code']], left_on='element', right_on='id', how='left')

    # Load initial player pool
    pos_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    p_raw['position'] = p_raw['element_type'].map(pos_map)
    p_raw['cost'] = p_raw['now_cost'] / 10.0
    p_raw['player_code'] = p_raw['code']

    # 1. GW1 Squad Selection
    gw1_actuals = load_gameweek_actuals(season=season, gw=1, data_root=data_root)

    # Build predictions based on initial stats
    pred_pool = p_raw.copy()
    # Baseline expected points proxy using points_per_game or form
    pred_pool['expected_points'] = pred_pool['points_per_game'].astype(float).fillna(2.0)
    pred_pool.loc[pred_pool['expected_points'] < 1.0, 'expected_points'] = 1.0

    gw1_sol = solve_initial_squad(pred_pool, budget=100.0)
    current_squad = gw1_sol.squad
    bank = round(100.0 - gw1_sol.total_cost, 1)
    free_transfers = 1

    # Purchase prices map
    purchase_prices: Dict[int, float] = {p.player_code: p.cost for p in current_squad}

    gw_results: List[Dict[str, Any]] = []
    cumulative_points = 0.0
    total_hits = 0

    print(f"\n[GW1 Initial Squad] Formation: {gw1_sol.formation} | Spend: £{gw1_sol.total_cost:.1f}M | Bank: £{bank:.1f}M")
    print(f"Starters: {', '.join([f'{p.web_name} ({p.position})' for p in gw1_sol.starters])}")
    print(f"Captain: {gw1_sol.captain.web_name if gw1_sol.captain else 'None'} [C]")

    # Run GW1 Scoring
    gw1_score_res = simulate_gameweek_scoring(gw1_sol.squad, gw1_actuals)
    gw1_pts = gw1_score_res['total_score']
    cumulative_points += gw1_pts

    gw_results.append({
        'gw': 1,
        'gross_pts': gw1_pts,
        'hits': 0,
        'net_pts': gw1_pts,
        'cumulative': cumulative_points,
        'captain': gw1_sol.captain.web_name if gw1_sol.captain else '',
        'capt_pts': gw1_score_res['captain_points'],
        'transfers_in': '',
        'transfers_out': '',
    })

    # 2. Rolling GW2 to max_gw
    for gw in range(2, max_gw + 1):
        # Accumulate free transfer (max 5)
        free_transfers = min(5, free_transfers + 1)

        gw_actuals = load_gameweek_actuals(season=season, gw=gw, data_root=data_root)

        # Compute rolling form up to GW gw-1
        past_gws = merged_gw[merged_gw['GW'] < gw]
        agg_form = past_gws.groupby('code').agg({
            'total_points': 'sum',
            'minutes': 'sum',
            'starts': 'sum',
            'expected_goals': 'sum',
            'expected_assists': 'sum',
        }).reset_index().rename(columns={
            'total_points': 'rolling_points',
            'minutes': 'rolling_minutes',
            'starts': 'rolling_starts',
            'expected_goals': 'rolling_xg',
            'expected_assists': 'rolling_xa',
        })

        # Merge with player metadata
        player_pool = p_raw.copy()
        player_pool = player_pool.merge(agg_form, left_on='player_code', right_on='code', how='left')
        player_pool['season_minutes'] = player_pool['rolling_minutes'].fillna(0.0)
        player_pool['season_starts'] = player_pool['rolling_starts'].fillna(0.0)

        # Expected points model
        player_pool['expected_points'] = player_pool.apply(
            lambda r: predict_player_points({
                'position': r['position'],
                'season_minutes': r['season_minutes'],
                'season_starts': r['season_starts'],
                'long_form_minutes': r['season_minutes'],
                'long_form_expected_goals_90': (r['rolling_xg'] / (r['season_minutes'] / 90.0)) if r['season_minutes'] > 0 else 0.1,
                'long_form_expected_assists_90': (r['rolling_xa'] / (r['season_minutes'] / 90.0)) if r['season_minutes'] > 0 else 0.1,
                'team_long_form_xgc90': 1.25,
                'now_cost': r['now_cost'],
            })['expected_points'],
            axis=1,
        )

        current_codes = [p.player_code for p in current_squad]

        # Optimize transfers
        trans_sol = solve_weekly_transfers(
            current_squad_codes=current_codes,
            df=player_pool,
            free_transfers=free_transfers,
            bank=bank,
            max_transfers=2,
            hit_cost=4.0,
        )

        if trans_sol.squad_solution.status == "Optimal":
            current_squad = trans_sol.squad_solution.squad
            hits = trans_sol.hits_taken
            total_hits += hits
            free_transfers = max(1, free_transfers - trans_sol.transfers_count)
            t_in = ", ".join([p.web_name for p in trans_sol.transfers_in])
            t_out = ", ".join([p.web_name for p in trans_sol.transfers_out])
        else:
            hits = 0
            t_in, t_out = '', ''

        # Score gameweek
        score_res = simulate_gameweek_scoring(current_squad, gw_actuals)
        gross_pts = score_res['total_score']
        net_pts = gross_pts - (hits * 4.0)
        cumulative_points += net_pts

        capt_name = next((p.web_name for p in current_squad if p.is_captain), '')

        gw_results.append({
            'gw': gw,
            'gross_pts': gross_pts,
            'hits': hits,
            'net_pts': net_pts,
            'cumulative': cumulative_points,
            'captain': capt_name,
            'capt_pts': score_res['captain_points'],
            'transfers_in': t_in,
            'transfers_out': t_out,
        })

    res_df = pd.DataFrame(gw_results)

    # Benchmark comparison
    bm = BENCHMARKS.get(season, {'top_10k_total': 2470.0, 'top_100k_total': 2320.0, 'overall_avg_total': 1865.0})
    top10k_target = bm['top_10k_total'] * (max_gw / 38.0)
    top100k_target = bm['top_100k_total'] * (max_gw / 38.0)
    avg_target = bm['overall_avg_total'] * (max_gw / 38.0)

    avg_pts_per_gw = cumulative_points / max_gw

    if verbose:
        print("\n" + "=" * 90)
        print(f"                      SEASON {season} BACKTEST RESULTS (GW1 - GW{max_gw})")
        print("=" * 90)
        print(f"{'GW':<4} | {'Gross Pts':<10} | {'Hits':<5} | {'Net Pts':<8} | {'Cumulative':<11} | {'Captain':<15} | {'Capt Pts':<8} | Transfers")
        print("-" * 90)
        for _, r in res_df.iterrows():
            trans_str = f"IN: {clean_ascii_str(r['transfers_in'])} | OUT: {clean_ascii_str(r['transfers_out'])}" if r['transfers_in'] else "Roll / Free"
            capt_name = clean_ascii_str(r['captain'])
            print(f"GW{int(r['gw']):<2} | {r['gross_pts']:<10.1f} | {r['hits']:<5} | {r['net_pts']:<8.1f} | {r['cumulative']:<11.1f} | {capt_name:<15} | {r['capt_pts']:<8.1f} | {trans_str}")
        print("=" * 90)
        print(f"\nFINAL PERFORMANCE BENCHMARK:")
        print(f"  * Model Final Score:        {cumulative_points:.1f} pts  ({avg_pts_per_gw:.2f} pts/GW)")
        print(f"  * Top 10k Benchmark Pace:   {top10k_target:.1f} pts  ({top10k_target/max_gw:.2f} pts/GW)")
        print(f"  * Top 100k Benchmark Pace:  {top100k_target:.1f} pts  ({top100k_target/max_gw:.2f} pts/GW)")
        print(f"  * Overall Average:          {avg_target:.1f} pts  ({avg_target/max_gw:.2f} pts/GW)")
        print(f"  * Total Hits Taken:         {total_hits} ({-total_hits * 4} pts)")
        
        diff_10k = cumulative_points - top10k_target
        status_10k = f"+{diff_10k:.1f} pts (OUTPERFORMING TOP 10K)" if diff_10k >= 0 else f"{diff_10k:.1f} pts vs Top 10k"
        print(f"  * vs Top 10k Benchmark:     {status_10k}")
        print("=" * 90 + "\n")

    return {
        'season': season,
        'max_gw': max_gw,
        'cumulative_points': cumulative_points,
        'avg_pts_per_gw': avg_pts_per_gw,
        'total_hits': total_hits,
        'results_df': res_df,
        'top_10k_target': top10k_target,
        'top_100k_target': top100k_target,
    }


def main():
    parser = argparse.ArgumentParser(description="Run FPL Historical Backtest Benchmark")
    parser.add_argument('--season', default='2024-25', choices=['2024-25', '2025-26', 'all'], help="Season to backtest")
    parser.add_argument('--max-gw', type=int, default=38, help="Maximum gameweeks to simulate")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    if args.season == 'all':
        for s in ['2024-25', '2025-26']:
            run_season_backtest(season=s, max_gw=args.max_gw, data_root=args.data_root)
    else:
        run_season_backtest(season=args.season, max_gw=args.max_gw, data_root=args.data_root)


if __name__ == '__main__':
    main()

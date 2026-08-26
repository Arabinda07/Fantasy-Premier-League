"""Fixture & Form Adjustment Engine for Fantasy Premier League (Phase 3).

Adjusts baseline player scoring expectations based on:
1. Opponent attacking & defensive relative strength ratios compared to league average (~1.35).
2. Home vs. Away conjugate symmetric performance multipliers:
   - Home: +8% attacking output (1.08), -7.4% goals conceded (0.9259).
   - Away: -7.4% attacking output (0.9259), +8% goals conceded (1.08).
3. Short-form (last 6 GWs) vs. Long-form stat blending with sample-size shrinkage (m0_short = 270 mins).
4. Promoted team prior modeling (1.05 xG, 1.80 xGC) for teams lacking historical PL logs.
5. Dynamic Goalkeeper save scaling based on opponent attacking volume.
6. Fixture-scaled Bonus (C6) and Defensive Contribution (C11) adjustments.
7. Fixture scheduling edge cases: Double Gameweeks (sum with rotation dampening) & Blank Gameweeks (0.0 pts).

Usage:
    python -m model.fixture_engine [--season 2026-27] [--gw 1] [--alpha 0.35]
"""
import argparse
import math
import os
import sys
from typing import Dict, Any, List, Tuple, Union, Optional
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import (
    predict_player_points,
    apply_empirical_bayes_shrinkage,
    POSITIONAL_PRIORS,
    DEFAULT_MINS_FILTER,
    _safe_float,
)
from model.build_dataset import load_teams_map, build_dataset


# ---------------------------------------------------------------------------
# Phase 3 Modeling Constants
# ---------------------------------------------------------------------------

DEFAULT_ALPHA: float = 0.35  # Form blending weight for short-form (last 6 GWs)
DEFAULT_SHORT_FORM_M0: float = 450.0  # 5 full matches for short-form sample confidence

# Conjugate symmetric venue factors (1.08 / 0.9259) for exact goal conservation
HOME_ATTACK_FACTOR: float = 1.08
HOME_DEFENSE_FACTOR: float = 0.9259  # 1 / 1.08
AWAY_ATTACK_FACTOR: float = 0.9259
AWAY_DEFENSE_FACTOR: float = 1.08

DEFAULT_LEAGUE_AVG_XG: float = 1.35
DEFAULT_LEAGUE_AVG_XGC: float = 1.35

# Promoted team prior baselines (historically ~1.05 xG, 1.80 xGC in first PL season)
PROMOTED_TEAM_PRIORS: Dict[str, float] = {
    'xg90': 1.05,
    'xgc90': 1.80,
}


# ---------------------------------------------------------------------------
# Form Blending
# ---------------------------------------------------------------------------

def blend_form_rates(
    short_rate: float,
    long_rate: float,
    alpha: float = DEFAULT_ALPHA,
    short_mins: float = 0.0,
    m0_short: float = DEFAULT_SHORT_FORM_M0,
) -> float:
    """Blend short-form (last 6 GWs) and long-form per-90 rates with sample-size shrinkage.

    Prevents noisy low-minute cameos (e.g. 15 mins with 1 goal = 6.0 xG90)
    from heavily polluting player projections.

    Formula:
        alpha_eff = alpha * (short_mins / (short_mins + m0_short))
        blended = alpha_eff * short_rate + (1 - alpha_eff) * long_rate

    Args:
        short_rate: rate per 90 across short-form window.
        long_rate: rate per 90 across long-form window.
        alpha: base weight given to short form (default 0.35).
        short_mins: minutes played in short-form window.
        m0_short: short-form confidence scale in minutes (default 270.0).

    Returns:
        Blended rate per 90 float.
    """
    if short_mins <= 0.0:
        return float(long_rate)

    alpha_base = min(1.0, max(0.0, float(alpha)))
    # Sample-size scaled effective alpha
    alpha_eff = alpha_base * (short_mins / (short_mins + m0_short))
    return (alpha_eff * float(short_rate)) + ((1.0 - alpha_eff) * float(long_rate))


# ---------------------------------------------------------------------------
# League Baseline & Fixture Multipliers
# ---------------------------------------------------------------------------

def compute_team_league_averages(
    team_stats_map: Dict[str, Dict[str, float]],
) -> Tuple[float, float]:
    """Compute league average xG90 and xGC90 across all teams in the active dataset.

    Args:
        team_stats_map: Dict mapping team_name -> {'xg90': float, 'xgc90': float}.

    Returns:
        Tuple of (league_avg_xg, league_avg_xgc). Defaults to (1.35, 1.35) if empty.
    """
    if not team_stats_map:
        return (DEFAULT_LEAGUE_AVG_XG, DEFAULT_LEAGUE_AVG_XGC)

    xg_list = [v['xg90'] for v in team_stats_map.values() if v.get('xg90') is not None and v['xg90'] > 0]
    xgc_list = [v['xgc90'] for v in team_stats_map.values() if v.get('xgc90') is not None and v['xgc90'] > 0]

    avg_xg = sum(xg_list) / len(xg_list) if xg_list else DEFAULT_LEAGUE_AVG_XG
    avg_xgc = sum(xgc_list) / len(xgc_list) if xgc_list else DEFAULT_LEAGUE_AVG_XGC

    return (round(avg_xg, 4), round(avg_xgc, 4))


def compute_fixture_multipliers(
    team_name: str,
    opponent_name: str,
    is_home: bool,
    team_stats_map: Dict[str, Dict[str, float]],
    league_avg_xg: float = DEFAULT_LEAGUE_AVG_XG,
    league_avg_xgc: float = DEFAULT_LEAGUE_AVG_XGC,
) -> Dict[str, float]:
    """Calculate attacking and defensive multipliers for a specific fixture matchup.

    Formulas:
        Venue Attack Factor: 1.08 (Home) or 0.9259 (Away)
        Venue Defense Factor: 0.9259 (Home) or 1.08 (Away)
        Attack Multiplier: (Opponent xGC90 / League Avg xGC) * Venue Attack Factor
        Fixture Conceded xGC: Team xGC90 * (Opponent xG90 / League Avg xG) * Venue Defense Factor

    Args:
        team_name: attacking/defending player's team.
        opponent_name: opponent team.
        is_home: True if player's team is playing at home, False if away.
        team_stats_map: mapping of team names to their blended {'xg90': float, 'xgc90': float}.
        league_avg_xg: baseline league average attacking xG.
        league_avg_xgc: baseline league average defensive xGC.

    Returns:
        Dict with keys: 'attack_mult', 'fixture_xgc90', 'opp_xg90', 'is_home'
    """
    # Safe lookups with fallback to PROMOTED_TEAM_PRIORS if team has no match logs
    team_stats = team_stats_map.get(team_name, PROMOTED_TEAM_PRIORS)
    opp_stats = team_stats_map.get(opponent_name, PROMOTED_TEAM_PRIORS)

    team_xgc90 = _safe_float(team_stats.get('xgc90'), default=PROMOTED_TEAM_PRIORS['xgc90'])
    opp_xg90 = _safe_float(opp_stats.get('xg90'), default=PROMOTED_TEAM_PRIORS['xg90'])
    opp_xgc90 = _safe_float(opp_stats.get('xgc90'), default=PROMOTED_TEAM_PRIORS['xgc90'])

    # Relative ratios
    base_avg_xg = max(0.2, league_avg_xg)
    base_avg_xgc = max(0.2, league_avg_xgc)

    opp_defense_ratio = opp_xgc90 / base_avg_xgc
    opp_attack_ratio = opp_xg90 / base_avg_xg

    # Conjugate venue factors for exact mathematical conservation of goals
    venue_attack = HOME_ATTACK_FACTOR if is_home else AWAY_ATTACK_FACTOR
    venue_defense = HOME_DEFENSE_FACTOR if is_home else AWAY_DEFENSE_FACTOR

    # Combined multipliers
    attack_mult = opp_defense_ratio * venue_attack
    fixture_xgc90 = team_xgc90 * opp_attack_ratio * venue_defense

    return {
        'attack_mult': round(attack_mult, 4),
        'fixture_xgc90': round(max(0.1, fixture_xgc90), 4),
        'opp_xg90': round(opp_xg90, 4),
        'is_home': 1.0 if is_home else 0.0,
    }


# ---------------------------------------------------------------------------
# Fixture Loading & Matching
# ---------------------------------------------------------------------------

def load_fixtures_for_gw(
    season: str,
    gw: int,
    data_root: str = 'data',
) -> List[Dict[str, Any]]:
    """Load and parse fixture schedule for a target gameweek.

    Args:
        season: season string e.g. '2026-27'.
        gw: target gameweek integer (1-38).
        data_root: root data directory.

    Returns:
        List of dicts representing fixtures scheduled in the gameweek.
    """
    fixtures_path = os.path.join(data_root, season, 'fixtures.csv')
    if not os.path.exists(fixtures_path):
        return []

    teams_map = load_teams_map(season, data_root)
    df = pd.read_csv(fixtures_path)

    if 'event' not in df.columns or df.empty:
        return []

    # Filter by target gameweek (handling potential float / string types)
    gw_df = df[df['event'].fillna(-1).astype(float) == float(gw)]
    if gw_df.empty:
        return []

    fixtures = []
    for _, row in gw_df.iterrows():
        team_h_id = row.get('team_h')
        team_a_id = row.get('team_a')

        home_team = teams_map.get(int(team_h_id)) if pd.notnull(team_h_id) else None
        away_team = teams_map.get(int(team_a_id)) if pd.notnull(team_a_id) else None

        if not home_team or not away_team:
            continue

        fixtures.append({
            'fixture_id': int(row.get('id', 0)),
            'code': int(row.get('code', 0)),
            'gw': int(gw),
            'home_team': home_team,
            'away_team': away_team,
            'home_fdr': int(row.get('team_h_difficulty', 3)) if pd.notnull(row.get('team_h_difficulty')) else 3,
            'away_fdr': int(row.get('team_a_difficulty', 3)) if pd.notnull(row.get('team_a_difficulty')) else 3,
            'kickoff_time': str(row.get('kickoff_time', '')),
        })

    return fixtures


# ---------------------------------------------------------------------------
# Player Prediction per Matchup
# ---------------------------------------------------------------------------

def predict_player_fixture(
    player: Union[pd.Series, Dict[str, Any]],
    fixture: Dict[str, Any],
    is_home: bool,
    team_stats_map: Dict[str, Dict[str, float]],
    league_avg_xg: float = DEFAULT_LEAGUE_AVG_XG,
    league_avg_xgc: float = DEFAULT_LEAGUE_AVG_XGC,
    alpha: float = DEFAULT_ALPHA,
    m0: float = DEFAULT_MINS_FILTER,
) -> Dict[str, Any]:
    """Calculate fixture-adjusted expected points for a single player in a single match.

    Args:
        player: row/dict containing player metrics from model_dataset.csv.
        fixture: fixture dict with home_team, away_team, fdr, etc.
        is_home: True if home, False if away.
        team_stats_map: team statistics lookup.
        league_avg_xg: league average attacking xG.
        league_avg_xgc: league average defending xGC.
        alpha: short-form blending weight.
        m0: Empirical Bayes shrinkage minutes filter.

    Returns:
        Dict containing fixture-adjusted expected points, component breakdown,
        and fixture metadata (opponent, venue, FDR, attack multiplier).
    """
    position = str(player.get('position', 'MID')).upper()
    if position not in ('GK', 'DEF', 'MID', 'FWD'):
        position = 'MID'

    team = player.get('team')
    opponent = fixture['away_team'] if is_home else fixture['home_team']
    fdr = fixture['home_fdr'] if is_home else fixture['away_fdr']

    # 1. Form blending across short-form and long-form with sample-size shrinkage
    short_mins = _safe_float(player.get('short_form_minutes'))
    long_mins = _safe_float(player.get('long_form_minutes'))
    season_mins = _safe_float(player.get('season_minutes'))

    raw_xg90 = blend_form_rates(
        _safe_float(player.get('short_form_expected_goals_90')),
        _safe_float(player.get('long_form_expected_goals_90')),
        alpha, short_mins
    )
    raw_xa90 = blend_form_rates(
        _safe_float(player.get('short_form_expected_assists_90')),
        _safe_float(player.get('long_form_expected_assists_90')),
        alpha, short_mins
    )
    raw_dc90 = blend_form_rates(
        _safe_float(player.get('short_form_defensive_contribution_90')),
        _safe_float(player.get('long_form_defensive_contribution_90')),
        alpha, short_mins
    )
    blended_bonus90 = blend_form_rates(
        _safe_float(player.get('short_form_bonus_90')),
        _safe_float(player.get('long_form_bonus_90')),
        alpha, short_mins
    )

    # 2. Empirical Bayes Shrinkage on player baseline rates
    alpha_base = min(1.0, max(0.0, float(alpha)))
    alpha_eff = alpha_base * (short_mins / (short_mins + DEFAULT_SHORT_FORM_M0)) if short_mins > 0 else 0.0
    sample_mins = (alpha_eff * short_mins + (1.0 - alpha_eff) * long_mins) if long_mins > 0 else (season_mins if season_mins > 0 else short_mins)
    priors = POSITIONAL_PRIORS.get(position, POSITIONAL_PRIORS['MID'])

    adj_xg90 = apply_empirical_bayes_shrinkage(raw_xg90, sample_mins, priors['xg90'], m0)
    adj_xa90 = apply_empirical_bayes_shrinkage(raw_xa90, sample_mins, priors['xa90'], m0)
    adj_dc90 = apply_empirical_bayes_shrinkage(raw_dc90, sample_mins, priors['dc90'], m0)

    # 3. Fixture Multipliers
    mults = compute_fixture_multipliers(team, opponent, is_home, team_stats_map, league_avg_xg, league_avg_xgc)
    attack_mult = mults['attack_mult']
    fixture_xgc90 = mults['fixture_xgc90']
    opp_xg90 = mults['opp_xg90']

    # 4. Apply multipliers & dynamic component scaling
    fixture_player = dict(player)
    fixture_player['long_form_expected_goals_90'] = adj_xg90 * attack_mult
    fixture_player['long_form_expected_assists_90'] = adj_xa90 * attack_mult
    fixture_player['team_long_form_xgc90'] = fixture_xgc90

    # GK Save Scaling: facing harder attack increases shot volume and expected saves
    if position == 'GK':
        raw_saves90 = _safe_float(player.get('saves_90', player.get('long_form_saves_90')), default=3.0)
        venue_def = HOME_DEFENSE_FACTOR if is_home else AWAY_DEFENSE_FACTOR
        fixture_saves90 = raw_saves90 * math.pow(opp_xg90 / max(0.2, league_avg_xg), 0.65) * venue_def
        fixture_player['saves_90'] = round(min(7.5, max(0.5, fixture_saves90)), 4)

    # Bonus Scaling (C6): teams scoring more goals capture higher share of BPS
    fixture_bonus90 = blended_bonus90 * min(2.0, max(0.3, math.pow(attack_mult, 0.75)))
    fixture_player['long_form_bonus_90'] = fixture_bonus90

    # Defensive Contribution Scaling (C11): defenders under pressure make more tackles/blocks/clearances
    fixture_dc90 = adj_dc90 * min(1.8, max(0.5, math.pow(opp_xg90 / max(0.2, league_avg_xg), 0.40)))
    fixture_player['long_form_defensive_contribution_90'] = fixture_dc90

    # 5. Run prediction engine (with pre-shrunken rates)
    points_breakdown = predict_player_points(fixture_player, apply_shrinkage=False)

    result = {
        'fixture_opponent': opponent,
        'fixture_venue': 'H' if is_home else 'A',
        'fixture_fdr': fdr,
        'fixture_attack_mult': attack_mult,
        'fixture_xgc90': fixture_xgc90,
        'fixture_xp': points_breakdown['expected_points'],
    }
    result.update(points_breakdown)
    return result


# ---------------------------------------------------------------------------
# Full Gameweek Orchestrator
# ---------------------------------------------------------------------------

def predict_gameweek_fixtures(
    season: str = '2026-27',
    gw: int = 1,
    alpha: float = DEFAULT_ALPHA,
    m0: float = DEFAULT_MINS_FILTER,
    data_root: str = 'data',
    save_csv: bool = True,
    dynamic_dataset: bool = False,
) -> pd.DataFrame:
    """Predict fixture-adjusted expected points for all players in a given gameweek.

    Handles normal 1-game weeks, Double Gameweeks (DGW: sums both fixtures with rotation dampening),
    and Blank Gameweeks (BGW: 0.0 points).

    Args:
        season: season string e.g. '2026-27'.
        gw: target gameweek integer (1 to 38).
        alpha: short-form blending weight (default 0.35).
        m0: Empirical Bayes shrinkage minutes filter (default 500.0).
        data_root: root data directory.
        save_csv: if True, writes output to data/<season>/fixture_predictions.csv.
        dynamic_dataset: if True, dynamically builds rolling dataset as of gameweek gw (strictly prior data).

    Returns:
        pd.DataFrame containing player metadata, fixture details, and predicted xP.
    """
    season_dir = os.path.join(data_root, season)
    dataset_path = os.path.join(season_dir, 'model_dataset.csv')

    if dynamic_dataset or not os.path.exists(dataset_path):
        df = build_dataset(season=season, gw=gw, data_root=data_root)
    else:
        df = pd.read_csv(dataset_path)

    if df.empty:
        print(f"[{season}] Warning: empty player dataset for season {season}")
        return pd.DataFrame()

    # Build blended team stats map
    team_stats_map: Dict[str, Dict[str, float]] = {}
    for team_name in df['team'].dropna().unique():
        team_rows = df[df['team'] == team_name]
        if team_rows.empty:
            continue
        first_row = team_rows.iloc[0]

        t_long_xg = _safe_float(first_row.get('team_long_form_xg90'), DEFAULT_LEAGUE_AVG_XG)
        t_short_xg = _safe_float(first_row.get('team_short_form_xg90'), t_long_xg)
        t_long_xgc = _safe_float(first_row.get('team_long_form_xgc90'), DEFAULT_LEAGUE_AVG_XGC)
        t_short_xgc = _safe_float(first_row.get('team_short_form_xgc90'), t_long_xgc)

        # Use actual team short-form minutes for sample-size weighted blending
        # (F-07 fix: was hardcoded to 1.0, which made short-form contribute ~0.08%)
        team_short_mins = _safe_float(first_row.get('team_short_form_minutes'), default=540.0)
        team_stats_map[team_name] = {
            'xg90': blend_form_rates(t_short_xg, t_long_xg, alpha, team_short_mins),
            'xgc90': blend_form_rates(t_short_xgc, t_long_xgc, alpha, team_short_mins),
        }

    league_avg_xg, league_avg_xgc = compute_team_league_averages(team_stats_map)

    # Load fixtures for target gameweek
    fixtures = load_fixtures_for_gw(season, gw, data_root)
    print(f"[{season}] Gameweek {gw}: found {len(fixtures)} fixtures scheduled.")

    # Organize fixtures by team -> List of (fixture, is_home)
    team_fixtures: Dict[str, List[Tuple[Dict[str, Any], bool]]] = {}
    for f in fixtures:
        h_team = f['home_team']
        a_team = f['away_team']
        team_fixtures.setdefault(h_team, []).append((f, True))
        team_fixtures.setdefault(a_team, []).append((f, False))

    records = []
    for _, player in df.iterrows():
        team = player.get('team')
        scheduled = team_fixtures.get(team, [])

        if len(scheduled) == 0:
            # Blank Gameweek (BGW): 0 fixtures -> 0 points
            rec = {
                'gw': gw,
                'fixture_count': 0,
                'fixture_opponent': 'BLANK',
                'fixture_venue': '-',
                'fixture_fdr': 0,
                'fixture_attack_mult': 0.0,
                'fixture_xgc90': 0.0,
                'expected_points': 0.0,
                'c1_app_1_60': 0.0,
                'c2_app_60_plus': 0.0,
                'c3_saves': 0.0,
                'c4_yellow_cards': 0.0,
                'c5_red_cards': 0.0,
                'c6_bonus': 0.0,
                'c7_assists': 0.0,
                'c8_goals': 0.0,
                'c9_clean_sheets': 0.0,
                'c10_goals_conceded': 0.0,
                'c11_defensive_contributions': 0.0,
                'p_start': 0.0,
                'p_app': 0.0,
                'p_60_plus': 0.0,
            }
        elif len(scheduled) == 1:
            # Standard single match
            fix, is_home = scheduled[0]
            pred = predict_player_fixture(
                player, fix, is_home, team_stats_map, league_avg_xg, league_avg_xgc, alpha, m0
            )
            rec = {
                'gw': gw,
                'fixture_count': 1,
                'fixture_opponent': pred['fixture_opponent'],
                'fixture_venue': pred['fixture_venue'],
                'fixture_fdr': pred['fixture_fdr'],
                'fixture_attack_mult': pred['fixture_attack_mult'],
                'fixture_xgc90': pred['fixture_xgc90'],
                'expected_points': pred['expected_points'],
                'c1_app_1_60': pred['c1_app_1_60'],
                'c2_app_60_plus': pred['c2_app_60_plus'],
                'c3_saves': pred['c3_saves'],
                'c4_yellow_cards': pred['c4_yellow_cards'],
                'c5_red_cards': pred['c5_red_cards'],
                'c6_bonus': pred['c6_bonus'],
                'c7_assists': pred['c7_assists'],
                'c8_goals': pred['c8_goals'],
                'c9_clean_sheets': pred['c9_clean_sheets'],
                'c10_goals_conceded': pred['c10_goals_conceded'],
                'c11_defensive_contributions': pred['c11_defensive_contributions'],
                'p_start': pred['p_start'],
                'p_app': pred['p_app'],
                'p_60_plus': pred['p_60_plus'],
            }
        else:
            # Double Gameweek (DGW): sum expected points and component breakdowns
            total_xp = 0.0
            opponents = []
            venues = []
            fdrs = []
            comp_names = [
                'c1_app_1_60', 'c2_app_60_plus', 'c3_saves', 'c4_yellow_cards', 'c5_red_cards',
                'c6_bonus', 'c7_assists', 'c8_goals', 'c9_clean_sheets', 'c10_goals_conceded',
                'c11_defensive_contributions'
            ]
            comp_totals = {c: 0.0 for c in comp_names}
            total_p_start = 0.0
            total_p_app = 0.0
            total_p_60 = 0.0
            # F-08 fix: collect per-match predictions to avoid variable shadowing
            match_preds: List[Dict[str, Any]] = []

            for match_idx, (fix, is_home) in enumerate(scheduled):
                fixture_player = dict(player)
                # Apply 0.90x rotation/minutes dampening on match 2 for outfield players
                if match_idx > 0 and str(player.get('position', '')).upper() != 'GK':
                    p_start_base = _safe_float(player.get('season_starts', player.get('fbref_starts')))
                    fixture_player['season_starts'] = p_start_base * 0.90

                pred = predict_player_fixture(
                    fixture_player, fix, is_home, team_stats_map, league_avg_xg, league_avg_xgc, alpha, m0
                )
                match_preds.append(pred)
                total_xp += pred['expected_points']
                opponents.append(pred['fixture_opponent'])
                venues.append(pred['fixture_venue'])
                fdrs.append(str(pred['fixture_fdr']))
                for c in comp_names:
                    comp_totals[c] += pred[c]
                total_p_start += pred['p_start']
                total_p_app += pred['p_app']
                total_p_60 += pred['p_60_plus']

            rec = {
                'gw': gw,
                'fixture_count': len(scheduled),
                'fixture_opponent': ', '.join(opponents),
                'fixture_venue': ', '.join(venues),
                'fixture_fdr': '/'.join(fdrs),
                'fixture_attack_mult': round(sum(mp['fixture_attack_mult'] for mp in match_preds) / len(match_preds), 4),
                'fixture_xgc90': round(sum(mp['fixture_xgc90'] for mp in match_preds) / len(match_preds), 4),
                'expected_points': round(total_xp, 4),
                'p_start': round(total_p_start, 4),
                'p_app': round(total_p_app, 4),
                'p_60_plus': round(total_p_60, 4),
            }
            for c in comp_names:
                rec[c] = round(comp_totals[c], 4)

        records.append(rec)

    pred_df = pd.DataFrame(records, index=df.index)
    result_df = pd.concat([df, pred_df], axis=1)

    if save_csv:
        from model.file_utils import atomic_write_csv
        from model.schema_validator import validate_dataframe_schema

        is_valid, errors = validate_dataframe_schema(result_df, 'fixture_predictions')
        if not is_valid:
            print(f"[!] Warning: fixture_predictions schema validation found issues: {errors}")

        out_csv = os.path.join(season_dir, 'fixture_predictions.csv')
        out_gw_csv = os.path.join(season_dir, f'fixture_predictions_gw{gw}.csv')
        atomic_write_csv(out_csv, result_df)
        atomic_write_csv(out_gw_csv, result_df)
        print(f"[{season}] Successfully wrote {len(result_df)} fixture predictions to {out_csv} and {out_gw_csv}")

    return result_df


# ---------------------------------------------------------------------------
# CLI Runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate fixture-adjusted player point predictions")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Target gameweek number (1-38)")
    parser.add_argument('--alpha', type=float, default=DEFAULT_ALPHA, help="Form blending weight for short form (default 0.35)")
    parser.add_argument('--m0', type=float, default=DEFAULT_MINS_FILTER, help="Bayesian shrinkage minutes filter (default 500)")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    predict_gameweek_fixtures(
        season=args.season,
        gw=args.gw,
        alpha=args.alpha,
        m0=args.m0,
        data_root=args.data_root,
        save_csv=True,
    )


if __name__ == '__main__':
    main()

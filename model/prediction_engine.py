"""Point-Prediction Engine for Fantasy Premier League (Phase 2).

Implements the 11-component mathematical expectation model for player gameweek points:
- C1: 1-60 mins appearance (1 pt)
- C2: 60+ mins appearance (1 pt)
- C3: Goalkeeper saves (1 pt per 3 saves)
- C4: Yellow cards (-1 pt, corrected for 2-yellow dismissals)
- C5: Red cards (-3 pts)
- C6: Bonus points
- C7: Expected Assists (3 pts)
- C8: Expected Goals (4/5/6 pts by position)
- C9: Clean Sheets (4 pts GK/DEF, 1 pt MID via Poisson P(GC=0))
- C10: Exact Discrete Expected Penalty for 2+ Goals Conceded (-1 pt per 2 GC above 1)
- C11: Defensive Contributions (1 pt / 10 DC, 2 pts / 15 DC via Poisson)

Remediations Included:
- Empirical Bayes prior shrinkage on small-sample rates (Dowman fix)
- Exact discrete expectation for C10 (replaces binary approximation)
- Starter minutes proration in active_ratio
- Disciplinary yellow card correction (avoids double penalty on red cards)
- Price-based cold-start playing priors for new marquee transfers with 0 PL minutes

Usage:
    python -m model.prediction_engine [--season 2026-27] [--gw 1]
"""
import argparse
import math
import os
import sys
from typing import Dict, Any, List, Tuple, Union, Optional
import pandas as pd

# Add repo root to path if needed
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.build_dataset import build_dataset


# ---------------------------------------------------------------------------
# Scoring Constants (Official FPL Rules)
# ---------------------------------------------------------------------------

GOAL_POINTS: Dict[str, float] = {
    'GK': 6.0,
    'DEF': 6.0,
    'MID': 5.0,
    'FWD': 4.0,
}

ASSIST_POINTS: float = 3.0

CLEAN_SHEET_POINTS: Dict[str, float] = {
    'GK': 4.0,
    'DEF': 4.0,
    'MID': 1.0,
    'FWD': 0.0,
}

SAVES_PER_POINT: float = 3.0
YELLOW_CARD_DEDUCTION: float = -1.0
RED_CARD_DEDUCTION: float = -3.0
OWN_GOAL_DEDUCTION: float = -2.0

# Positional baseline priors for Empirical Bayes shrinkage
POSITIONAL_PRIORS: Dict[str, Dict[str, float]] = {
    'FWD': {'xg90': 0.35, 'xa90': 0.15, 'dc90': 2.0, 'bonus90': 0.60},
    'MID': {'xg90': 0.15, 'xa90': 0.15, 'dc90': 4.0, 'bonus90': 0.50},
    'DEF': {'xg90': 0.05, 'xa90': 0.05, 'dc90': 8.0, 'bonus90': 0.30},
    'GK':  {'xg90': 0.00, 'xa90': 0.00, 'dc90': 1.0, 'bonus90': 0.20},
}

DEFAULT_MINS_FILTER: float = 500.0  # M0 confidence threshold for shrinkage


# ---------------------------------------------------------------------------
# Mathematical Distribution Helpers
# ---------------------------------------------------------------------------

def poisson_pmf(k: int, lambda_param: float) -> float:
    """Calculate Poisson probability P(X = k) = (lambda^k * e^-lambda) / k!."""
    if lambda_param <= 0.0:
        return 1.0 if k == 0 else 0.0
    if k < 0:
        return 0.0
    return (math.pow(lambda_param, k) * math.exp(-lambda_param)) / math.factorial(k)


def poisson_cdf(k: int, lambda_param: float) -> float:
    """Calculate Poisson cumulative distribution P(X <= k)."""
    if lambda_param <= 0.0:
        return 1.0 if k >= 0 else 0.0
    if k < 0:
        return 0.0
    return sum(poisson_pmf(i, lambda_param) for i in range(k + 1))


def poisson_clean_sheet_prob(xgc90: float) -> float:
    """P(Clean Sheet) = P(X = 0) = exp(-lambda)."""
    if xgc90 <= 0.0:
        return 1.0
    return math.exp(-xgc90)


def poisson_two_plus_gc_prob(xgc90: float) -> float:
    """P(Goals Conceded >= 2) = 1 - P(X = 0) - P(X = 1)."""
    if xgc90 <= 0.0:
        return 0.0
    return 1.0 - (math.exp(-xgc90) * (1.0 + xgc90))


def poisson_exact_gc_penalty(xgc90: float, max_goals: int = 10) -> float:
    """Calculate exact discrete expectation for 2+ goals conceded penalty (C10).

    In FPL:
    - 0 or 1 goal conceded -> 0 penalty
    - 2 or 3 goals conceded -> -1 pt
    - 4 or 5 goals conceded -> -2 pts
    - 6 or 7 goals conceded -> -3 pts
    - 8 or 9 goals conceded -> -4 pts
    - 10+ goals conceded -> -5 pts

    Formula:
        E[Penalty] = - sum_{m=1}^{5} m * (P(X = 2m) + P(X = 2m + 1))

    Args:
        xgc90: Expected goals conceded per 90 minutes.
        max_goals: Maximum goals conceded ceiling for summation (default 10).

    Returns:
        Exact expected penalty (a negative float, e.g. -0.264).
    """
    if xgc90 <= 0.0:
        return 0.0

    expected_penalty = 0.0
    for m in range(1, (max_goals // 2) + 1):
        g1 = 2 * m
        g2 = 2 * m + 1
        p_g1 = poisson_pmf(g1, xgc90)
        p_g2 = poisson_pmf(g2, xgc90) if g2 <= max_goals else 0.0
        expected_penalty += float(m) * (p_g1 + p_g2)

    return -1.0 * expected_penalty


def poisson_dc_hit_prob(dc90: float, threshold: int = 10) -> float:
    """P(Defensive Contribution >= threshold) = 1 - Poisson_CDF(threshold - 1)."""
    if dc90 <= 0.0:
        return 0.0
    return 1.0 - poisson_cdf(threshold - 1, dc90)


def apply_empirical_bayes_shrinkage(
    raw_rate: float,
    minutes: float,
    prior: float,
    m0: float = DEFAULT_MINS_FILTER,
) -> float:
    """Shrink a player's raw per-90 rate toward a positional baseline prior.

    Formula:
        rate_adj = (M / (M + M0)) * raw_rate + (M0 / (M + M0)) * prior
    """
    if minutes <= 0.0:
        return prior
    weight_raw = minutes / (minutes + m0)
    weight_prior = m0 / (minutes + m0)
    return (weight_raw * raw_rate) + (weight_prior * prior)


# ---------------------------------------------------------------------------
# Prediction Functions
# ---------------------------------------------------------------------------

def estimate_playing_probabilities(
    starts: float,
    subs: float,
    unused_subs: float,
    total_minutes: float,
    position: str,
    cost: float = 0.0,
    status: str = 'a',
) -> Dict[str, float]:
    """Estimate starting probability, appearance probability, and 60+ mins probability.

    Includes price-based cold-start priors for new transfers with 0 historical PL minutes.

    Args:
        starts: season starts count.
        subs: substitute appearances count.
        unused_subs: unused substitute appearances count.
        total_minutes: total minutes played across window.
        position: player position string ('GK', 'DEF', 'MID', 'FWD').
        cost: player cost in £M (default 0.0).
        status: player availability status (e.g. 'a', 'd', 'i', 's').

    Returns:
        Dict with keys: 'p_start', 'p_sub', 'p_app', 'p_60_plus', 'active_ratio'
    """
    squads_made = starts + subs + unused_subs

    if squads_made > 0:
        p_start = starts / squads_made
        p_sub = subs / squads_made
    elif total_minutes > 0:
        est_starts = min(38.0, total_minutes / 75.0)
        p_start = min(1.0, est_starts / 38.0)
        p_sub = min(0.3, max(0.0, (total_minutes - (starts * 75.0)) / (38.0 * 20.0))) if starts > 0 else 0.0
    else:
        # Cold-start prior for newly transferred / marquee players with 0 historical PL minutes
        norm_status = str(status).lower() if pd.notnull(status) else 'a'
        norm_cost = float(cost) / 10.0 if float(cost) > 25.0 else float(cost)

        if norm_status in ('a', 'available', '') and norm_cost >= 5.5:
            if norm_cost >= 9.0:
                p_start = 0.85
                p_app = 0.90
                mins_per_start = 80.0
            elif norm_cost >= 7.0:
                p_start = 0.70
                p_app = 0.80
                mins_per_start = 75.0
            else:  # 5.5 <= cost < 7.0
                p_start = 0.45
                p_app = 0.60
                mins_per_start = 65.0

            p_sub = max(0.0, p_app - p_start)
            p_60_plus = p_start * (mins_per_start / 90.0)
            active_ratio = (p_start * (mins_per_start / 90.0)) + (p_sub * (20.0 / 90.0))
            return {
                'p_start': round(p_start, 4),
                'p_sub': round(p_sub, 4),
                'p_app': round(p_app, 4),
                'p_60_plus': round(p_60_plus, 4),
                'active_ratio': round(active_ratio, 4),
            }
        else:
            return {
                'p_start': 0.0,
                'p_sub': 0.0,
                'p_app': 0.0,
                'p_60_plus': 0.0,
                'active_ratio': 0.0,
            }

    # Probability of making an appearance (start or sub)
    p_app = min(1.0, p_start + ((1.0 - p_start) * (subs / (subs + unused_subs) if (subs + unused_subs) > 0 else 0.0)))
    if p_app == 0.0 and (starts + subs) > 0:
        p_app = min(1.0, (starts + subs) / max(1.0, squads_made))

    mins_per_start = min(90.0, max(45.0, total_minutes / starts)) if starts > 0 else (90.0 if position == 'GK' else 60.0)

    try:
        from model.minutes_model import calculate_pre60_hook_probability
        p_hook = calculate_pre60_hook_probability(
            avg_starter_mins=mins_per_start,
            is_goalkeeper=(position == 'GK'),
            is_defender=(position == 'DEF'),
        )
        p_60_given_start = 1.0 - p_hook
    except Exception:
        if position == 'GK':
            p_60_given_start = 0.99 if p_start > 0 else 0.0
        else:
            p_60_given_start = min(1.0, max(0.0, (mins_per_start - 30.0) / 45.0))

    p_60_plus = p_start * p_60_given_start
    mins_per_sub = 20.0
    active_ratio = (p_start * (mins_per_start / 90.0)) + (p_sub * (mins_per_sub / 90.0))

    return {
        'p_start': round(p_start, 4),
        'p_sub': round(p_sub, 4),
        'p_app': round(p_app, 4),
        'p_60_plus': round(p_60_plus, 4),
        'active_ratio': round(active_ratio, 4),
    }


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float, handling None, NaN, empty strings, and missing values."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if math.isnan(f) else f
    except (ValueError, TypeError):
        return default


def predict_player_points(
    player: Union[pd.Series, Dict[str, Any]],
    apply_shrinkage: bool = True,
) -> Dict[str, float]:
    """Calculate the 11-component point prediction breakdown for a single player.

    Args:
        player: row/dict containing player metrics from model_dataset.csv.
        apply_shrinkage: if True, applies Empirical Bayes shrinkage to raw rates.

    Returns:
        Dict with keys:
            c1_app_1_60, c2_app_60_plus, c3_saves, c4_yellow_cards, c5_red_cards,
            c6_bonus, c7_assists, c8_goals, c9_clean_sheets, c10_goals_conceded,
            c11_defensive_contributions, expected_points, p_start, p_app, p_60_plus
    """
    position = str(player.get('position', 'MID') if player.get('position') is not None and not (isinstance(player.get('position'), float) and math.isnan(player.get('position'))) else 'MID').upper()
    if position not in ('GK', 'DEF', 'MID', 'FWD'):
        position = 'MID'

    # Extract minutes and participation stats
    total_minutes = _safe_float(player.get('season_minutes', player.get('long_form_minutes')))
    starts = _safe_float(player.get('season_starts', player.get('fbref_starts')))
    subs = _safe_float(player.get('fbref_subs'))
    unused_subs = _safe_float(player.get('fbref_unused_subs'))
    cost = _safe_float(player.get('now_cost', player.get('cost', 0.0)))
    status = str(player.get('status', 'a'))

    # Probabilities
    probs = estimate_playing_probabilities(
        starts=starts,
        subs=subs,
        unused_subs=unused_subs,
        total_minutes=total_minutes,
        position=position,
        cost=cost,
        status=status,
    )
    p_start = probs['p_start']
    p_app = probs['p_app']
    p_60_plus = probs['p_60_plus']
    active_ratio = probs['active_ratio']

    # Inactive player early return
    if p_app <= 0.0 and active_ratio <= 0.0:
        return {
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
            'expected_points': 0.0,
            'p_start': 0.0,
            'p_app': 0.0,
            'p_60_plus': 0.0,
        }

    # Rates per 90
    raw_xg90 = _safe_float(player.get('long_form_expected_goals_90'))
    raw_xa90 = _safe_float(player.get('long_form_expected_assists_90'))
    raw_dc90 = _safe_float(player.get('long_form_defensive_contribution_90'))
    team_xgc90 = _safe_float(player.get('team_long_form_xgc90', player.get('long_form_expected_goals_conceded_90')), default=1.3)
    bonus90 = _safe_float(player.get('long_form_bonus_90'))
    saves90 = _safe_float(player.get('saves_90', player.get('long_form_saves_90')), default=3.0 if position == 'GK' else 0.0)

    # Apply Empirical Bayes shrinkage toward positional priors (Dowman fix)
    if apply_shrinkage:
        priors = POSITIONAL_PRIORS.get(position, POSITIONAL_PRIORS['MID'])
        sample_mins = _safe_float(player.get('long_form_minutes'))
        if sample_mins <= 0.0:
            sample_mins = total_minutes

        xg90 = apply_empirical_bayes_shrinkage(raw_xg90, sample_mins, priors['xg90'])
        xa90 = apply_empirical_bayes_shrinkage(raw_xa90, sample_mins, priors['xa90'])
        dc90 = apply_empirical_bayes_shrinkage(raw_dc90, sample_mins, priors['dc90'])
    else:
        xg90 = raw_xg90
        xa90 = raw_xa90
        dc90 = raw_dc90

    # 1. C1: 1-60 mins appearance (1 pt)
    c1 = 1.0 * p_app

    # 2. C2: 60+ mins appearance (1 pt)
    c2 = 1.0 * p_60_plus

    # 3. C3: Goalkeeper Saves (1 pt per 3 saves)
    c3 = (saves90 / SAVES_PER_POINT) * p_start if position == 'GK' else 0.0

    # 4. C4: Yellow Cards (-1 pt)
    # F-02 fix: removed `- 2.0 * rc90` correction. In FPL, a second yellow that triggers
    # a red gives BOTH -1 (yellow) AND -3 (red). Both penalties are applied.
    yc90 = _safe_float(player.get('yellow_cards_90'), default=0.12)
    rc90 = _safe_float(player.get('red_cards_90'), default=0.01)
    c4 = YELLOW_CARD_DEDUCTION * yc90 * p_app

    # 5. C5: Red Cards (-3 pts)
    c5 = RED_CARD_DEDUCTION * rc90 * p_app

    # 6. C6: Bonus Points (F-16 fix: apply Empirical Bayes shrinkage to bonus90)
    if apply_shrinkage:
        bonus90 = apply_empirical_bayes_shrinkage(
            _safe_float(player.get('long_form_bonus_90')),
            sample_mins if 'sample_mins' in dir() else _safe_float(player.get('long_form_minutes', total_minutes)),
            priors.get('bonus90', 0.40),
        )
    else:
        bonus90 = _safe_float(player.get('long_form_bonus_90'))
    c6 = bonus90 * p_start

    # 7. C7: Assists (3 pts)
    c7 = ASSIST_POINTS * xa90 * active_ratio

    # 8. C8: Goals (4/5/6 pts based on position)
    goal_pts = GOAL_POINTS.get(position, 4.0)
    c8 = goal_pts * xg90 * active_ratio

    # 9. C9: Clean Sheets (4 pts GK/DEF, 1 pt MID)
    cs_pts = CLEAN_SHEET_POINTS.get(position, 0.0)
    p_cs = poisson_clean_sheet_prob(team_xgc90)
    c9 = cs_pts * p_cs * p_60_plus if cs_pts > 0.0 else 0.0

    # 10. C10: Exact Discrete Expected Penalty for 2+ Goals Conceded
    if position in ('GK', 'DEF'):
        penalty_expectation = poisson_exact_gc_penalty(team_xgc90)
        c10 = penalty_expectation * p_60_plus
    else:
        c10 = 0.0

    # 11. C11: Defensive Contributions (1 pt for >=10, 2 pts for >=15)
    # F-01 fix: gated on p_60_plus like C9/C10, since DC points require 60+ mins
    p_dc_10 = poisson_dc_hit_prob(dc90 * active_ratio, threshold=10)
    p_dc_15 = poisson_dc_hit_prob(dc90 * active_ratio, threshold=15)
    c11 = ((1.0 * p_dc_10) + (1.0 * p_dc_15)) * p_60_plus

    # Total Expected Points
    total_expected = c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11

    return {
        'c1_app_1_60': round(c1, 4),
        'c2_app_60_plus': round(c2, 4),
        'c3_saves': round(c3, 4),
        'c4_yellow_cards': round(c4, 4),
        'c5_red_cards': round(c5, 4),
        'c6_bonus': round(c6, 4),
        'c7_assists': round(c7, 4),
        'c8_goals': round(c8, 4),
        'c9_clean_sheets': round(c9, 4),
        'c10_goals_conceded': round(c10, 4),
        'c11_defensive_contributions': round(c11, 4),
        'expected_points': round(total_expected, 4),
        'p_start': round(p_start, 4),
        'p_app': round(p_app, 4),
        'p_60_plus': round(p_60_plus, 4),
    }


def predict_all_players(
    season_or_df: Union[str, pd.DataFrame] = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
    save_csv: bool = True,
    season: Optional[str] = None,
) -> pd.DataFrame:
    """Generate baseline expected point predictions for all players in a season or given DataFrame."""
    if season is not None:
        season_or_df = season

    if isinstance(season_or_df, pd.DataFrame):
        df = season_or_df.copy()
        save_csv = False
    else:
        season_str = str(season_or_df)
        season_dir = os.path.join(data_root, season_str)
        dataset_path = os.path.join(season_dir, 'model_dataset.csv')

        if not os.path.exists(dataset_path):
            print(f"[{season}] model_dataset.csv not found, building dataset first...")
            df = build_dataset(season=season, gw=gw, data_root=data_root)
        else:
            df = pd.read_csv(dataset_path)

        if df.empty:
            print(f"[{season}] Warning: empty player dataset for season {season}")
            return pd.DataFrame()

    predictions = []
    for _, player in df.iterrows():
        pred = predict_player_points(player, apply_shrinkage=True)
        predictions.append(pred)

    pred_df = pd.DataFrame(predictions, index=df.index)
    result_df = pd.concat([df, pred_df], axis=1)

    if save_csv and isinstance(season_or_df, str):
        from model.file_utils import atomic_write_csv
        from model.schema_validator import validate_dataframe_schema

        is_valid, errors = validate_dataframe_schema(result_df, 'predictions')
        if not is_valid:
            print(f"[!] Warning: predictions schema validation found issues: {errors}")

        season_dir = os.path.join(data_root, str(season_or_df))
        out_csv = os.path.join(season_dir, 'predictions.csv')
        atomic_write_csv(out_csv, result_df)
        print(f"[{season_or_df}] Successfully wrote {len(result_df)} predictions to {out_csv}")

    return result_df


# ---------------------------------------------------------------------------
# CLI Runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate FPL player point predictions")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Current gameweek number")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    predict_all_players(season_or_df=args.season, gw=args.gw, data_root=args.data_root, save_csv=True)


if __name__ == '__main__':
    main()

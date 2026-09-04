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
        E[Penalty] = - [ sum_{m=1}^{4} m * (P(X = 2m) + P(X = 2m + 1)) + 5.0 * P(X >= 10) ]

    Args:
        xgc90: Expected goals conceded per 90 minutes.
        max_goals: Maximum goals conceded ceiling for summation (default 10).

    Returns:
        Exact expected penalty (a negative float, e.g. -0.264).
    """
    if xgc90 <= 0.0:
        return 0.0

    expected_penalty = 0.0
    for m in range(1, 5):
        g1 = 2 * m
        g2 = 2 * m + 1
        p_g1 = poisson_pmf(g1, xgc90)
        p_g2 = poisson_pmf(g2, xgc90)
        expected_penalty += float(m) * (p_g1 + p_g2)

    # Top tier absorbs entire upper tail: P(X >= 10) = 1 - sum_{k=0}^9 P(X = k)
    p_under_10 = sum(poisson_pmf(k, xgc90) for k in range(10))
    p_10_plus = max(0.0, 1.0 - p_under_10)
    expected_penalty += 5.0 * p_10_plus

    return -1.0 * expected_penalty


# ---------------------------------------------------------------------------
# Negative Binomial Distribution Helpers (M-01 Overdispersion)
# ---------------------------------------------------------------------------

DEFAULT_DISPERSION_R: float = 6.0


def negative_binomial_pmf(k: int, mu: float, r: float = DEFAULT_DISPERSION_R) -> float:
    """Calculate Negative Binomial probability P(X = k) with mean mu and dispersion r.

    Parameterization:
        p = r / (r + mu)
        P(X = k) = [Gamma(k + r) / (k! * Gamma(r))] * p^r * (1 - p)^k
    When r is very large (r >= 50.0 or r <= 0), falls back to Poisson PMF.
    """
    if mu <= 0.0:
        return 1.0 if k == 0 else 0.0
    if k < 0:
        return 0.0
    if r is None or r <= 0.0 or r >= 50.0:
        return poisson_pmf(k, mu)

    # Use log-gamma to avoid numerical overflow
    log_coef = math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
    p = r / (r + mu)
    log_prob = log_coef + (r * math.log(p)) + (k * math.log(1.0 - p))
    return math.exp(log_prob)


def negative_binomial_clean_sheet_prob(xgc90: float, r: float = DEFAULT_DISPERSION_R) -> float:
    """P(Clean Sheet) = P(X = 0) = (1 + mu/r)^(-r) under Negative Binomial."""
    if xgc90 <= 0.0:
        return 1.0
    if r is None or r <= 0.0 or r >= 50.0:
        return poisson_clean_sheet_prob(xgc90)
    return math.pow(1.0 + (xgc90 / r), -r)


def negative_binomial_exact_gc_penalty(
    xgc90: float,
    r: float = DEFAULT_DISPERSION_R,
    max_goals: int = 10,
) -> float:
    """Calculate exact discrete expectation for 2+ goals conceded penalty (C10) under Negative Binomial.

    In FPL:
    - 0 or 1 goal conceded -> 0 penalty
    - 2 or 3 goals conceded -> -1 pt
    - 4 or 5 goals conceded -> -2 pts
    - 6 or 7 goals conceded -> -3 pts
    - 8 or 9 goals conceded -> -4 pts
    - 10+ goals conceded -> -5 pts

    Formula:
        E[Penalty] = - [ sum_{m=1}^{4} m * (P_NB(X = 2m) + P_NB(X = 2m + 1)) + 5.0 * P_NB(X >= 10) ]
    """
    if xgc90 <= 0.0:
        return 0.0
    if r is None or r <= 0.0 or r >= 50.0:
        return poisson_exact_gc_penalty(xgc90, max_goals=max_goals)

    expected_penalty = 0.0
    for m in range(1, 5):
        g1 = 2 * m
        g2 = 2 * m + 1
        p_g1 = negative_binomial_pmf(g1, xgc90, r=r)
        p_g2 = negative_binomial_pmf(g2, xgc90, r=r)
        expected_penalty += float(m) * (p_g1 + p_g2)

    # Top tier absorbs entire upper tail: P(X >= 10) = 1 - sum_{k=0}^9 P(X = k)
    p_under_10 = sum(negative_binomial_pmf(k, xgc90, r=r) for k in range(10))
    p_10_plus = max(0.0, 1.0 - p_under_10)
    expected_penalty += 5.0 * p_10_plus

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
        raw_p_start = starts / squads_made
        raw_p_sub = subs / squads_made
        if squads_made < 4.0:
            # Shrink toward conservative baseline prior for early-season stability
            # GKs have higher starting stability (0.90), outfield players (0.75)
            start_prior = 0.90 if position == 'GK' else 0.75
            sub_prior = 0.05 if position == 'GK' else 0.15
            m_squads = 3.0
            p_start = (squads_made / (squads_made + m_squads)) * raw_p_start + (m_squads / (squads_made + m_squads)) * start_prior
            p_sub = (squads_made / (squads_made + m_squads)) * raw_p_sub + (m_squads / (squads_made + m_squads)) * sub_prior
        else:
            p_start = raw_p_start
            p_sub = raw_p_sub
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
    min_minutes_pct: Optional[float] = None,
    available_minutes: Optional[float] = None,
    dispersion_r: float = DEFAULT_DISPERSION_R,
    days_rest: int = 7,
    european_teams: Optional[Dict[str, List[str]]] = None,
    include_c11_in_xp: bool = False,
) -> Dict[str, float]:
    """Calculate the 11-component point prediction breakdown for a single player.

    Args:
        player: row/dict containing player metrics from model_dataset.csv.
        apply_shrinkage: if True, applies Empirical Bayes shrinkage to raw rates.
        min_minutes_pct: optional minimum percentage of available minutes (e.g. 0.10 for 10%).
        available_minutes: optional total available team minutes (e.g. gw * 90.0).
        dispersion_r: Negative Binomial dispersion parameter r (default DEFAULT_DISPERSION_R).
        days_rest: days since previous competitive match for European congestion adjustment.
        european_teams: optional dictionary of European competition club rosters.
        include_c11_in_xp: if True, adds C11 (defensive contributions) into expected_points.
            Defaults to False to strictly conform to official Fantasy Premier League scoring.

    Returns:
        Dict with keys:
            c1_app_1_60, c2_app_60_plus, c3_saves, c4_yellow_cards, c5_red_cards,
            c6_bonus, c7_assists, c8_goals, c9_clean_sheets, c10_goals_conceded,
            c11_defensive_contributions, expected_points, p_start, p_sub, p_app,
            p_60_plus, expected_minutes, active_ratio
    """
    position = str(player.get('position', 'MID') if player.get('position') is not None and not (isinstance(player.get('position'), float) and math.isnan(player.get('position'))) else 'MID').upper()
    if position not in ('GK', 'DEF', 'MID', 'FWD'):
        position = 'MID'

    # Extract minutes and participation stats
    total_minutes = _safe_float(player.get('season_minutes', player.get('long_form_minutes')))
    starts = _safe_float(player.get('season_starts', player.get('fbref_starts')))
    cost = _safe_float(player.get('now_cost', player.get('cost', 0.0)))

    # Dynamic minutes filter threshold (zeros out inactive bench fodder below fraction of season)
    if min_minutes_pct is not None and available_minutes is not None and available_minutes > 0:
        threshold_mins = float(min_minutes_pct) * float(available_minutes)
        if total_minutes < threshold_mins and starts == 0.0 and cost < 6.0:
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
                'p_sub': 0.0,
                'p_app': 0.0,
                'p_60_plus': 0.0,
                'expected_minutes': 0.0,
                'active_ratio': 0.0,
            }

    # Canonical Continuous Minutes Survival Hazard Profile (M-02)
    from model.minutes_model import compute_player_minutes_hazard
    minutes_profile = compute_player_minutes_hazard(
        player_row=player,
        days_rest=days_rest,
        european_teams=european_teams,
    )
    p_start = minutes_profile.p_start
    p_sub = minutes_profile.p_sub
    p_app = minutes_profile.p_app
    p_60_plus = minutes_profile.p_60_plus
    active_ratio = minutes_profile.active_ratio
    expected_mins_60_plus = minutes_profile.expected_mins_60_plus

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
            'p_sub': 0.0,
            'p_app': 0.0,
            'p_60_plus': 0.0,
            'expected_minutes': 0.0,
            'active_ratio': 0.0,
        }

    # Rates per 90
    raw_xg90 = _safe_float(player.get('long_form_expected_goals_90'))
    raw_xa90 = _safe_float(player.get('long_form_expected_assists_90'))
    raw_dc90 = _safe_float(player.get('long_form_defensive_contribution_90'))
    team_xgc90 = _safe_float(player.get('team_long_form_xgc90', player.get('long_form_expected_goals_conceded_90')), default=1.3)
    bonus90 = _safe_float(player.get('long_form_bonus_90'))
    saves90 = _safe_float(player.get('saves_90', player.get('long_form_saves_90')), default=3.0 if position == 'GK' else 0.0)

    # Set-piece & Penalty Equity Attribution (First-class decomposition with team frequency)
    pk_equity = 0.0
    if player.get('pk_xg_boost') is not None:
        pk_equity = _safe_float(player.get('pk_xg_boost'), default=0.0)
    elif player.get('is_penalty_taker') is True or _safe_float(player.get('penalties_order')) == 1.0:
        from model.set_pieces import get_team_pk_rate, PK_XG_VALUE
        team_name = player.get('team', '')
        team_pk_rate = get_team_pk_rate(team_name)
        pk_equity = team_pk_rate * PK_XG_VALUE
    elif _safe_float(player.get('penalties_order')) == 2.0:
        from model.set_pieces import get_team_pk_rate, PK_XG_VALUE
        team_name = player.get('team', '')
        team_pk_rate = get_team_pk_rate(team_name)
        pk_equity = team_pk_rate * PK_XG_VALUE * 0.25  # ~25% absent-primary equity

    # Apply Empirical Bayes shrinkage toward positional priors (Dowman fix & M-03 P1 decoupling)
    if apply_shrinkage:
        priors = POSITIONAL_PRIORS.get(position, POSITIONAL_PRIORS['MID'])
        sample_mins = _safe_float(
            player.get('long_form_unweighted_minutes',
            player.get('unweighted_minutes',
            player.get('long_form_minutes')))
        )
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
    yc90 = _safe_float(player.get('yellow_cards_90'), default=0.12)
    rc90 = _safe_float(player.get('red_cards_90'), default=0.01)
    c4 = YELLOW_CARD_DEDUCTION * yc90 * p_app

    # 5. C5: Red Cards (-3 pts)
    c5 = RED_CARD_DEDUCTION * rc90 * p_app

    # 6. C6: Bonus Points (F-16 fix: apply Empirical Bayes shrinkage to bonus90)
    if apply_shrinkage:
        bonus90 = apply_empirical_bayes_shrinkage(
            _safe_float(player.get('long_form_bonus_90')),
            sample_mins if 'sample_mins' in dir() else _safe_float(
                player.get('long_form_unweighted_minutes',
                player.get('unweighted_minutes',
                player.get('long_form_minutes', total_minutes)))
            ),
            priors.get('bonus90', 0.40),
        )
    else:
        bonus90 = _safe_float(player.get('long_form_bonus_90'))
    c6 = bonus90 * p_start

    # 7. C7: Assists (3 pts)
    c7 = ASSIST_POINTS * xa90 * active_ratio

    # 8. C8: Goals (4/5/6 pts based on position, with penalty equity included)
    goal_pts = GOAL_POINTS.get(position, 4.0)
    total_xg90 = xg90 + pk_equity
    c8 = goal_pts * total_xg90 * active_ratio

    # 9. C9: Clean Sheets (4 pts GK/DEF, 1 pt MID)
    cs_pts = CLEAN_SHEET_POINTS.get(position, 0.0)
    # Scale expected goals conceded by pitch exposure conditional on 60+ mins qualification.
    # In FPL, defenders subbed off at 60-75 mins retain clean sheet points if 0 goals were conceded
    # while on pitch (goals conceded post-substitution do not deduct clean sheet points).
    cs_exposure = min(1.0, max(0.667, expected_mins_60_plus / 90.0)) if expected_mins_60_plus > 0 else 1.0
    effective_team_xgc = team_xgc90 * cs_exposure
    p_cs = negative_binomial_clean_sheet_prob(effective_team_xgc, r=dispersion_r)
    c9 = cs_pts * p_cs * p_60_plus if cs_pts > 0.0 else 0.0

    # 10. C10: Exact Discrete Expected Penalty for 2+ Goals Conceded
    if position in ('GK', 'DEF'):
        # In FPL, defenders/GKs lose 1 pt per 2 goals conceded while on the pitch,
        # evaluated separately over starter duration and substitute exposure (un-gated from p_60_plus).
        exp_starter_mins = minutes_profile.avg_starter_mins if minutes_profile.avg_starter_mins > 0 else 90.0
        xgc_starter = team_xgc90 * min(1.0, max(0.1, exp_starter_mins / 90.0))
        penalty_starter = negative_binomial_exact_gc_penalty(xgc_starter, r=dispersion_r)

        xgc_sub = team_xgc90 * (20.0 / 90.0)
        penalty_sub = negative_binomial_exact_gc_penalty(xgc_sub, r=dispersion_r)

        c10 = (penalty_starter * p_start) + (penalty_sub * p_sub)
    else:
        c10 = 0.0

    # 11. C11: Defensive Contributions (1 pt for >=10, 2 pts for >=15)
    # M-02 & M-07 fix: Rate is normalized conditional on playing 60+ minutes (no double-discounting),
    # then gated once on p_60_plus for qualification.
    exposure_60_plus = expected_mins_60_plus / 90.0
    lambda_dc_60 = dc90 * exposure_60_plus
    p_dc_10 = poisson_dc_hit_prob(lambda_dc_60, threshold=10)
    p_dc_15 = poisson_dc_hit_prob(lambda_dc_60, threshold=15)
    c11 = ((1.0 * p_dc_10) + (1.0 * p_dc_15)) * p_60_plus

    # Total Expected Points
    # Under official FPL scoring (include_c11_in_xp=False, default), C11 (defensive contributions)
    # does not award direct fantasy points (C1-C10 only).
    # When include_c11_in_xp=True, C11 is added to total_expected for custom draft leagues.
    if include_c11_in_xp:
        total_expected = c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11
    else:
        total_expected = c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10

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
        'p_sub': round(p_sub, 4),
        'p_app': round(p_app, 4),
        'p_60_plus': round(p_60_plus, 4),
        'expected_minutes': round(minutes_profile.expected_minutes, 2),
        'active_ratio': round(active_ratio, 4),
    }


def predict_all_players(
    season_or_df: Union[str, pd.DataFrame] = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
    save_csv: bool = True,
    season: Optional[str] = None,
    min_minutes_pct: Optional[float] = None,
    available_minutes: Optional[float] = None,
    include_c11_in_xp: bool = False,
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

    avail_mins = available_minutes if available_minutes is not None else float(gw * 90.0)

    predictions = []
    for _, player in df.iterrows():
        pred = predict_player_points(
            player,
            apply_shrinkage=True,
            min_minutes_pct=min_minutes_pct,
            available_minutes=avail_mins,
            include_c11_in_xp=include_c11_in_xp,
        )
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
    parser.add_argument('--include-c11-in-xp', action='store_true', default=False, help="Include C11 (defensive contributions) in expected points (custom league mode)")
    args = parser.parse_args()

    predict_all_players(
        season_or_df=args.season,
        gw=args.gw,
        data_root=args.data_root,
        save_csv=True,
        include_c11_in_xp=args.include_c11_in_xp,
    )


if __name__ == '__main__':
    main()

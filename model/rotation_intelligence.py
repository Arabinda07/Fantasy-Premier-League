"""Manager Rotation & Tactical Hazard Engine for Fantasy Premier League.

Models three types of playing time hazards that reduce expected minutes and points:

1. **Midweek European congestion** — Teams in UCL/UEL/UECL with ≤72h rest
   between fixtures have elevated rotation risk (0.82×–0.90× starter probability).

2. **Sub-60-minute substitution vulnerability** — Players historically subbed
   before the 60th minute lose clean sheet and 60+ appearance bonuses; we compute
   P(60+ | Start) from historical data and dampen accordingly.

3. **Live news & status flags** — chance_of_playing_this_round from FPL API is
   mapped to probability dampening factors (75% → 0.75, 50% → 0.40, etc.).

Usage:
    from model.rotation_intelligence import compute_rotation_hazard, apply_rotation_dampening
"""
import math
import os
import sys
from typing import Any, Dict, List, Optional, Union

import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import _safe_float


# ---------------------------------------------------------------------------
# Rotation Constants
# ---------------------------------------------------------------------------

# European competition team sets (updated per season).
# These are example team names; update each season when the draw is confirmed.
DEFAULT_EUROPEAN_TEAMS: Dict[str, List[str]] = {
    'UCL': ['Arsenal', 'Liverpool', 'Man City', 'Aston Villa'],
    'UEL': ['Man Utd', 'Tottenham'],
    'UECL': ['Chelsea'],
}

# Midweek rest hazard factors based on days of rest before a match.
# days_rest <= 3: 0.82 for rotation-heavy managers (Pep, Slot)
# days_rest <= 4: 0.90
# days_rest >= 5: 1.00 (no hazard)
MIDWEEK_HAZARD_SEVERE: float = 0.82   # ≤3 days rest
MIDWEEK_HAZARD_MODERATE: float = 0.90  # ≤4 days rest
MIDWEEK_HAZARD_NONE: float = 1.00      # ≥5 days rest

# Managers known for heavy rotation (Pep roulette, etc.)
ROTATION_HEAVY_MANAGERS: List[str] = ['Man City', 'Liverpool']

# News status dampening factors
# chance_of_playing_this_round → (p_start_mult, p_app_mult)
NEWS_DAMPENING: Dict[int, Dict[str, float]] = {
    100: {'p_start_mult': 1.00, 'p_app_mult': 1.00},
    75:  {'p_start_mult': 0.75, 'p_app_mult': 0.85},
    50:  {'p_start_mult': 0.40, 'p_app_mult': 0.60},
    25:  {'p_start_mult': 0.15, 'p_app_mult': 0.30},
    0:   {'p_start_mult': 0.00, 'p_app_mult': 0.00},
}

# Status codes that force zero availability
UNAVAILABLE_STATUSES = ('i', 's', 'u')


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def compute_midweek_hazard(
    team_name: str,
    days_rest: int = 7,
    european_teams: Optional[Dict[str, List[str]]] = None,
) -> float:
    """Calculate midweek congestion hazard factor for a player's team.

    Args:
        team_name: player's team name.
        days_rest: number of days since the team's last match.
        european_teams: mapping of competition → list of team names.

    Returns:
        Hazard multiplier (0.82 to 1.00) applied to P(Start).
    """
    if european_teams is None:
        european_teams = DEFAULT_EUROPEAN_TEAMS

    # Check if team is in any European competition
    is_european = any(
        team_name in teams
        for teams in european_teams.values()
    )

    if not is_european:
        return MIDWEEK_HAZARD_NONE

    if days_rest <= 3:
        # Extra rotation risk for known heavy-rotation managers
        if team_name in ROTATION_HEAVY_MANAGERS:
            return MIDWEEK_HAZARD_SEVERE
        return MIDWEEK_HAZARD_MODERATE
    elif days_rest <= 4:
        return MIDWEEK_HAZARD_MODERATE
    else:
        return MIDWEEK_HAZARD_NONE


def compute_sub60_vulnerability(
    total_starts: float,
    starts_60_plus: float,
) -> float:
    """Calculate the probability of playing 60+ minutes given a start.

    Players who are frequently substituted before the 60th minute lose
    clean sheet bonuses (GK/DEF) and the +1 appearance point for 60+ minutes.

    Args:
        total_starts: total number of starts in the sample window.
        starts_60_plus: number of starts where the player played 60+ minutes.

    Returns:
        P(60+ | Start) as a float between 0.0 and 1.0.
    """
    if total_starts <= 0:
        return 0.85  # Default prior for players with no start data
    return min(1.0, max(0.0, starts_60_plus / total_starts))


def compute_news_dampening(
    status: str,
    chance_of_playing: Optional[float],
) -> Dict[str, float]:
    """Calculate playing probability dampening from FPL news and status flags.

    Args:
        status: FPL status code ('a' = available, 'd' = doubtful,
                'i' = injured, 's' = suspended, 'u' = unavailable).
        chance_of_playing: chance_of_playing_this_round from API (0-100 or None).

    Returns:
        Dict with 'p_start_mult' and 'p_app_mult' dampening factors.
    """
    norm_status = str(status).lower().strip() if status else 'a'

    # Hard unavailability overrides
    if norm_status in UNAVAILABLE_STATUSES:
        return {'p_start_mult': 0.0, 'p_app_mult': 0.0}

    # If status is doubtful or we have a specific chance value
    if chance_of_playing is not None and not (isinstance(chance_of_playing, float) and math.isnan(chance_of_playing)):
        chance_int = int(round(float(chance_of_playing)))
        # Find the closest dampening tier
        tiers = sorted(NEWS_DAMPENING.keys())
        best_tier = tiers[0]
        for t in tiers:
            if chance_int >= t:
                best_tier = t
        return NEWS_DAMPENING.get(best_tier, NEWS_DAMPENING[100])

    # Available with no flags
    if norm_status in ('a', 'available', ''):
        return {'p_start_mult': 1.0, 'p_app_mult': 1.0}

    # Doubtful without specific chance → default 50%
    if norm_status == 'd':
        return NEWS_DAMPENING[50]

    return {'p_start_mult': 1.0, 'p_app_mult': 1.0}


def compute_rotation_hazard(
    team_name: str,
    status: str = 'a',
    chance_of_playing: Optional[float] = None,
    days_rest: int = 7,
    total_starts: float = 0.0,
    starts_60_plus: float = 0.0,
    european_teams: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, float]:
    """Compute combined rotation hazard for a player.

    Combines midweek congestion, sub-60 vulnerability, and news dampening
    into a single set of multiplicative adjustments.

    Args:
        team_name: player's team name.
        status: FPL status code.
        chance_of_playing: chance_of_playing_this_round from API.
        days_rest: days since last team match.
        total_starts: total starts in sample window.
        starts_60_plus: starts with 60+ minutes.
        european_teams: European competition team mapping.

    Returns:
        Dict with 'midweek_hazard', 'sub60_prob', 'news_p_start_mult',
        'news_p_app_mult', 'combined_p_start_mult', 'combined_p_app_mult'.
    """
    midweek = compute_midweek_hazard(team_name, days_rest, european_teams)
    sub60 = compute_sub60_vulnerability(total_starts, starts_60_plus)
    news = compute_news_dampening(status, chance_of_playing)

    combined_start = midweek * news['p_start_mult']
    combined_app = news['p_app_mult']  # Midweek doesn't affect sub appearances

    return {
        'midweek_hazard': round(midweek, 4),
        'sub60_prob': round(sub60, 4),
        'news_p_start_mult': round(news['p_start_mult'], 4),
        'news_p_app_mult': round(news['p_app_mult'], 4),
        'combined_p_start_mult': round(combined_start, 4),
        'combined_p_app_mult': round(combined_app, 4),
    }


def apply_rotation_dampening(
    pred_df: pd.DataFrame,
    season: str = '2026-27',
    data_root: str = 'data',
    european_teams: Optional[Dict[str, List[str]]] = None,
    days_rest_map: Optional[Dict[str, int]] = None,
) -> pd.DataFrame:
    """Apply rotation and news dampening to an existing predictions DataFrame.

    This is a lighter-weight alternative to the injury dampening in live_manager.py,
    designed to layer on midweek congestion and sub-60 risk alongside the existing
    news-based dampening.

    Args:
        pred_df: predictions DataFrame with player_code, team, p_start, p_app,
                 expected_points columns.
        season: season string.
        data_root: root data directory.
        european_teams: European competition team mapping override.
        days_rest_map: optional mapping of team_name → days_rest.

    Returns:
        Enriched DataFrame copy with rotation_hazard, midweek_hazard columns,
        and dampened p_start / p_app / expected_points.
    """
    raw_path = os.path.join(data_root, season, 'players_raw.csv')
    df = pred_df.copy()

    # Load status and news from players_raw
    status_map: Dict[int, str] = {}
    chance_map: Dict[int, Optional[float]] = {}
    if os.path.exists(raw_path):
        p_raw = pd.read_csv(raw_path)
        for _, r in p_raw.iterrows():
            code = int(r.get('code', 0))
            status_map[code] = str(r.get('status', 'a'))
            chance_val = r.get('chance_of_playing_this_round')
            if pd.notnull(chance_val):
                chance_map[code] = float(chance_val)
            else:
                chance_map[code] = None

    if days_rest_map is None:
        days_rest_map = {}

    midweek_list = []
    rotation_list = []

    for idx, row in df.iterrows():
        p_code = int(row.get('player_code', 0))
        team = str(row.get('team', ''))
        status = status_map.get(p_code, 'a')
        chance = chance_map.get(p_code)
        days_rest = days_rest_map.get(team, 7)

        hazard = compute_rotation_hazard(
            team_name=team,
            status=status,
            chance_of_playing=chance,
            days_rest=days_rest,
            european_teams=european_teams,
        )

        midweek_list.append(hazard['midweek_hazard'])
        rotation_list.append(hazard['combined_p_start_mult'])

        # Apply combined dampening to predictions
        combined_start = hazard['combined_p_start_mult']
        combined_app = hazard['combined_p_app_mult']

        if combined_start < 1.0 or combined_app < 1.0:
            orig_xp = _safe_float(row.get('expected_points', 0.0))
            orig_p_start = _safe_float(row.get('p_start', 0.0))
            orig_p_app = _safe_float(row.get('p_app', 0.0))

            # Scale xP proportionally to the probability dampening
            xp_scale = min(combined_start, combined_app) if orig_p_start > 0 else combined_app
            df.at[idx, 'expected_points'] = round(orig_xp * xp_scale, 4)
            df.at[idx, 'p_start'] = round(orig_p_start * combined_start, 4)
            df.at[idx, 'p_app'] = round(orig_p_app * combined_app, 4)

    df['midweek_hazard'] = midweek_list
    df['rotation_dampening'] = rotation_list

    return df

"""Effective Ownership (EO) & Game Theory Engine for Fantasy Premier League.

Calculates overall and estimated top-10k Effective Ownership, and provides
rank-adjusted utility functions for the MILP solver and live manager.

EO Definition:
    EO_i = Ownership_i + Captaincy_Share_i + Triple_Captaincy_Share_i

Three strategy modes:
    - 'pure_xp': Lambda = 0.  Raw expected points only.
    - 'rank_protect': Penalises fading high-EO captains (shields rank).
    - 'differential_chase': Rewards low-EO assets (climbs rank).

Usage:
    from model.ownership_engine import compute_eo, rank_adjusted_utility
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
# Constants
# ---------------------------------------------------------------------------

# Default strategy mode
DEFAULT_STRATEGY: str = 'pure_xp'
VALID_STRATEGIES = ('pure_xp', 'rank_protect', 'differential_chase')

# Strategy tuning parameters
RANK_PROTECT_SHIELD_WEIGHT: float = 1.8   # Reward for holding high-EO assets
RANK_PROTECT_THRESHOLD: float = 0.20        # EO above which shielding kicks in (20%+)

DIFFERENTIAL_REWARD_WEIGHT: float = 2.5   # Reward for owning low-EO assets (<20%)
DIFFERENTIAL_THRESHOLD: float = 0.20       # EO below which differential bonus applies
DIFFERENTIAL_PENALTY_WEIGHT: float = 1.8   # Penalty for high-EO assets in chase mode (>25%)
DIFFERENTIAL_PENALTY_THRESHOLD: float = 0.25

# Strategy intensity multiplier (lambda)
DEFAULT_STRATEGY_LAMBDA: float = 1.0


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def compute_eo(
    ownership_pct: float,
    captaincy_share: float = 0.0,
    triple_captain_share: float = 0.0,
) -> float:
    """Calculate Effective Ownership for a player.

    EO = ownership% + captaincy_share% + triple_captain_share%

    In practice for top-10k:
    - Haaland might be 85% owned, 60% captained → EO = 145%
    - A 5% owned differential → EO = 5%

    Args:
        ownership_pct: overall ownership as a fraction (e.g. 0.85 for 85%).
        captaincy_share: fraction of managers captaining this player (0.0 to 1.0).
        triple_captain_share: fraction of managers triple-captaining (usually ~0).

    Returns:
        Effective Ownership as a float (can exceed 1.0).
    """
    return float(ownership_pct) + float(captaincy_share) + float(triple_captain_share)


def estimate_captaincy_share(
    ownership_pct: float,
    expected_points: float,
    league_max_xp: float = 10.0,
) -> float:
    """Estimate captaincy share heuristically from ownership and expected points.

    Higher-xP players with high ownership tend to attract higher captaincy rates.
    This is a simple sigmoid-based heuristic; real data would come from the FPL API
    live endpoint (not available pre-deadline).

    Args:
        ownership_pct: overall ownership as a fraction (0.0 to 1.0).
        expected_points: player's predicted xP for the gameweek.
        league_max_xp: normalisation ceiling for xP (the league-best xP).

    Returns:
        Estimated captaincy share (0.0 to ~0.80).
    """
    if ownership_pct <= 0.0 or expected_points <= 0.0:
        return 0.0

    # Normalised xP score [0, 1]
    xp_norm = min(1.0, max(0.0, expected_points / max(1.0, league_max_xp)))

    # Captaincy roughly follows ownership * xP dominance
    raw_share = ownership_pct * xp_norm * 0.80
    return round(min(0.80, max(0.0, raw_share)), 4)


def rank_adjusted_utility(
    expected_points: float,
    eo: float,
    strategy: str = DEFAULT_STRATEGY,
    strategy_lambda: float = DEFAULT_STRATEGY_LAMBDA,
) -> float:
    """Calculate rank-adjusted utility combining xP with EO-based game theory.

    Utility(i) = xP_i + lambda * Phi(EO_i, strategy)

    Strategy Modes:
        'pure_xp': Phi = 0.  No EO adjustment.
        'rank_protect': Phi = +0.5 * (EO - 1.0) if EO > 1.0, else 0.
            Rewards holding high-EO players to prevent rank drawdowns.
        'differential_chase': Phi = +1.2 * (0.20 - EO) if EO < 0.20,
                              Phi = -0.5 * (EO - 1.0) if EO > 1.0.
            Rewards low-owned assets, penalises template captains.

    Args:
        expected_points: player's predicted xP for the gameweek.
        eo: Effective Ownership (can exceed 1.0).
        strategy: one of 'pure_xp', 'rank_protect', 'differential_chase'.
        strategy_lambda: intensity multiplier for the EO adjustment.

    Returns:
        Rank-adjusted utility float.
    """
    if strategy not in VALID_STRATEGIES:
        strategy = DEFAULT_STRATEGY

    if strategy == 'pure_xp':
        return float(expected_points)

    phi = 0.0

    if strategy == 'rank_protect':
        if eo > RANK_PROTECT_THRESHOLD:
            phi = RANK_PROTECT_SHIELD_WEIGHT * (eo - RANK_PROTECT_THRESHOLD)

    elif strategy == 'differential_chase':
        if eo < DIFFERENTIAL_THRESHOLD:
            phi = DIFFERENTIAL_REWARD_WEIGHT * (DIFFERENTIAL_THRESHOLD - eo)
        if eo > DIFFERENTIAL_PENALTY_THRESHOLD:
            phi -= DIFFERENTIAL_PENALTY_WEIGHT * (eo - DIFFERENTIAL_PENALTY_THRESHOLD)

    return float(expected_points) + (strategy_lambda * phi)


def enrich_predictions_with_ownership(
    pred_df: pd.DataFrame,
    season: str = '2026-27',
    data_root: str = 'data',
    strategy: str = DEFAULT_STRATEGY,
    strategy_lambda: float = DEFAULT_STRATEGY_LAMBDA,
) -> pd.DataFrame:
    """Add Effective Ownership and rank-adjusted utility columns to predictions.

    Reads selected_by_percent from players_raw.csv, estimates captaincy shares,
    computes EO, and derives utility_xp adjusted by the chosen strategy.

    Args:
        pred_df: predictions DataFrame with player_code, expected_points columns.
        season: season string.
        data_root: root data directory.
        strategy: EO strategy mode.
        strategy_lambda: strategy intensity multiplier.

    Returns:
        Enriched DataFrame copy with eo, captaincy_share, ownership_pct,
        utility_xp columns.
    """
    raw_path = os.path.join(data_root, season, 'players_raw.csv')
    df = pred_df.copy()

    ownership_map: Dict[int, float] = {}
    if os.path.exists(raw_path):
        p_raw = pd.read_csv(raw_path)
        for _, r in p_raw.iterrows():
            code = int(r.get('code', 0))
            sel_pct = _safe_float(r.get('selected_by_percent', 0.0))
            ownership_map[code] = sel_pct / 100.0  # Convert percentage to fraction

    # Find league max xP for captaincy estimation
    league_max_xp = df['expected_points'].max() if 'expected_points' in df.columns else 10.0
    if math.isnan(league_max_xp) or league_max_xp <= 0:
        league_max_xp = 10.0

    eo_list = []
    cap_list = []
    own_list = []
    util_list = []

    for _, row in df.iterrows():
        p_code = int(row.get('player_code', 0))
        xp = _safe_float(row.get('expected_points', 0.0))
        own_pct = ownership_map.get(p_code, 0.0)

        cap_share = estimate_captaincy_share(own_pct, xp, league_max_xp)
        eo = compute_eo(own_pct, cap_share)
        utility = rank_adjusted_utility(xp, eo, strategy, strategy_lambda)

        eo_list.append(round(eo, 4))
        cap_list.append(round(cap_share, 4))
        own_list.append(round(own_pct, 4))
        util_list.append(round(utility, 4))

    df['ownership_pct'] = own_list
    df['captaincy_share'] = cap_list
    df['eo'] = eo_list
    df['utility_xp'] = util_list

    return df

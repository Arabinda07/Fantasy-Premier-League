"""Price Change & Team Value Forecaster for Fantasy Premier League.

Tracks net transfer velocity (transfers_in_event − transfers_out_event) from
players_raw.csv and classifies each player's price movement risk into one of
five alert tiers: RISING_LOCK, RISING_ALERT, STABLE, FALLING_ALERT, FALLING_LOCK.

Integrates with the live manager to recommend early transfer execution when a
target is about to rise and a current asset is about to fall.

Usage:
    from model.price_predictor import classify_price_trend, enrich_predictions_with_price_trends
"""
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import _safe_float


# ---------------------------------------------------------------------------
# Price Change Constants
# ---------------------------------------------------------------------------

# Alert tier classifications
RISING_LOCK = 'RISING_LOCK'         # Price rise ≥100% threshold, +£0.1M within 24h
RISING_ALERT = 'RISING_ALERT'       # Price rise ≥75% threshold, imminent
STABLE = 'STABLE'                   # Low transfer momentum
FALLING_ALERT = 'FALLING_ALERT'     # Price fall ≤-75% threshold, imminent
FALLING_LOCK = 'FALLING_LOCK'       # Price fall ≤-100% threshold, -£0.1M within 24h

# FPL price change threshold is roughly based on net transfers relative to
# total managers.  With ~10M+ managers, typical thresholds are ~80k-120k net
# transfers for a price change.  We use a simplified ownership-weighted model.
DEFAULT_TOTAL_MANAGERS: int = 10_000_000
DEFAULT_BASE_THRESHOLD: int = 100_000  # Approximate net transfers needed for ±£0.1M


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def compute_net_transfer_velocity(
    transfers_in_event: int,
    transfers_out_event: int,
) -> int:
    """Calculate net transfer velocity for the current gameweek event.

    Args:
        transfers_in_event: transfers in during the current event.
        transfers_out_event: transfers out during the current event.

    Returns:
        Net transfer velocity (positive = rising demand, negative = falling).
    """
    return int(transfers_in_event) - int(transfers_out_event)


def estimate_price_threshold(
    ownership_pct: float,
    total_managers: int = DEFAULT_TOTAL_MANAGERS,
    base_threshold: int = DEFAULT_BASE_THRESHOLD,
) -> float:
    """Estimate the net transfer threshold for a price change.

    Higher-owned players require more net transfers for a price change (FPL uses
    a dynamic threshold based on ownership).

    Args:
        ownership_pct: ownership percentage as a fraction (0.0 to 1.0).
        total_managers: total number of FPL managers.
        base_threshold: base net transfers needed.

    Returns:
        Estimated net transfer threshold for a ±£0.1M price change.
    """
    # FPL scales the threshold by roughly: base * (1 + ownership * factor)
    # Higher ownership → harder to change price (more managers need to act)
    ownership_factor = 1.0 + (max(0.0, ownership_pct) * 2.0)
    return float(base_threshold) * ownership_factor


def classify_price_trend(
    net_velocity: int,
    threshold: float,
) -> str:
    """Classify a player's price trend into an alert tier.

    Tiers:
        net_velocity ≥ +threshold       → RISING_LOCK
        net_velocity ≥ +0.75*threshold  → RISING_ALERT
        net_velocity ≤ -threshold       → FALLING_LOCK
        net_velocity ≤ -0.75*threshold  → FALLING_ALERT
        Otherwise                       → STABLE

    Args:
        net_velocity: net transfer velocity.
        threshold: estimated price change threshold.

    Returns:
        One of RISING_LOCK, RISING_ALERT, STABLE, FALLING_ALERT, FALLING_LOCK.
    """
    if threshold <= 0:
        return STABLE

    ratio = float(net_velocity) / float(threshold)

    if ratio >= 1.0:
        return RISING_LOCK
    elif ratio >= 0.75:
        return RISING_ALERT
    elif ratio <= -1.0:
        return FALLING_LOCK
    elif ratio <= -0.75:
        return FALLING_ALERT
    else:
        return STABLE


def compute_player_price_trend(
    transfers_in_event: int,
    transfers_out_event: int,
    ownership_pct: float,
    total_managers: int = DEFAULT_TOTAL_MANAGERS,
    base_threshold: int = DEFAULT_BASE_THRESHOLD,
) -> Dict[str, Any]:
    """Full price trend analysis for a single player.

    Args:
        transfers_in_event: transfers in during the current event.
        transfers_out_event: transfers out during the current event.
        ownership_pct: ownership percentage as a fraction (0.0 to 1.0).
        total_managers: total number of FPL managers.
        base_threshold: base net transfers needed.

    Returns:
        Dict with 'net_velocity', 'threshold', 'velocity_ratio', 'trend'.
    """
    net_vel = compute_net_transfer_velocity(transfers_in_event, transfers_out_event)
    threshold = estimate_price_threshold(ownership_pct, total_managers, base_threshold)
    trend = classify_price_trend(net_vel, threshold)
    velocity_ratio = (float(net_vel) / float(threshold)) if threshold > 0 else 0.0

    return {
        'net_velocity': net_vel,
        'threshold': round(threshold, 0),
        'velocity_ratio': round(velocity_ratio, 4),
        'trend': trend,
    }


def enrich_predictions_with_price_trends(
    pred_df: pd.DataFrame,
    season: str = '2026-27',
    data_root: str = 'data',
) -> pd.DataFrame:
    """Add price trend columns to an existing predictions DataFrame.

    Reads transfer event data and ownership from players_raw.csv and computes
    net velocity, trend classification, and velocity ratio for each player.

    Args:
        pred_df: predictions DataFrame with player_code column.
        season: season string.
        data_root: root data directory.

    Returns:
        Enriched DataFrame copy with price_net_velocity, price_trend,
        price_velocity_ratio columns.
    """
    raw_path = os.path.join(data_root, season, 'players_raw.csv')
    df = pred_df.copy()

    transfer_data: Dict[int, Dict[str, Any]] = {}
    if os.path.exists(raw_path):
        p_raw = pd.read_csv(raw_path)
        for _, r in p_raw.iterrows():
            code = int(r.get('code', 0))
            t_in = int(_safe_float(r.get('transfers_in_event', 0)))
            t_out = int(_safe_float(r.get('transfers_out_event', 0)))
            sel_pct = _safe_float(r.get('selected_by_percent', 0.0)) / 100.0
            transfer_data[code] = {
                'transfers_in_event': t_in,
                'transfers_out_event': t_out,
                'ownership_pct': sel_pct,
            }

    velocities = []
    trends = []
    ratios = []

    for _, row in df.iterrows():
        p_code = int(row.get('player_code', 0))
        t_data = transfer_data.get(p_code)

        if t_data:
            result = compute_player_price_trend(
                transfers_in_event=t_data['transfers_in_event'],
                transfers_out_event=t_data['transfers_out_event'],
                ownership_pct=t_data['ownership_pct'],
            )
            velocities.append(result['net_velocity'])
            trends.append(result['trend'])
            ratios.append(result['velocity_ratio'])
        else:
            velocities.append(0)
            trends.append(STABLE)
            ratios.append(0.0)

    df['price_net_velocity'] = velocities
    df['price_trend'] = trends
    df['price_velocity_ratio'] = ratios

    return df

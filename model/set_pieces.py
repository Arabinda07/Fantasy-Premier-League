"""Set-Piece & Penalty Hierarchy Engine for Fantasy Premier League.

Reads official FPL set-piece role indicators (penalties_order, direct_freekicks_order,
corners_and_indirect_freekicks_order) from players_raw.csv and computes baseline
goal/assist equity adjustments for the 11-component prediction engine.

Penalty takers receive additive xG equity (C8) based on team penalty frequency and
conversion rates.  Corner and free-kick delivery specialists receive additive xA
equity (C7) based on team set-piece volume.

Usage:
    from model.set_pieces import compute_set_piece_equity
    equity = compute_set_piece_equity(player_row, team_pk_rate=0.20)
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
# Set-Piece Constants
# ---------------------------------------------------------------------------

# Average Premier League team penalty frequency per 90 minutes of team play.
# PL average ~0.10-0.12 penalties won per match; top teams can reach ~0.20.
DEFAULT_TEAM_PK_RATE_PER_90: float = 0.12

# Calibrated historical penalty win frequencies per 90 minutes of play
TEAM_PK_RATES: Dict[str, float] = {
    # High Box-Touch & Penalty Winning Tier (~7-9 penalties/season)
    'Man City': 0.18,
    'Chelsea': 0.18,
    'Arsenal': 0.16,
    'Liverpool': 0.16,
    'Man Utd': 0.15,
    # Standard Tier (~4-5 penalties/season)
    'Aston Villa': 0.12,
    'Newcastle': 0.12,
    'Spurs': 0.12,
    'Brighton': 0.12,
    'Brentford': 0.12,
    'West Ham': 0.11,
    'Crystal Palace': 0.11,
    'Fulham': 0.11,
    'Bournemouth': 0.10,
    # Low Box-Touch Tier (~2-3 penalties/season)
    'Everton': 0.07,
    'Nott\'m Forest': 0.07,
    'Wolves': 0.07,
    'Leicester': 0.07,
    'Ipswich': 0.06,
    'Southampton': 0.06,
    'Coventry': 0.06,
    'Hull': 0.06,
    'Sunderland': 0.06,
}

def get_team_pk_rate(team_name: Optional[str] = None) -> float:
    """Retrieve calibrated team penalty frequency per 90 minutes."""
    if not team_name:
        return DEFAULT_TEAM_PK_RATE_PER_90
    return TEAM_PK_RATES.get(team_name, DEFAULT_TEAM_PK_RATE_PER_90)

# Penalty conversion rate (league-wide historical average ~78%).
PK_CONVERSION_RATE: float = 0.78

# Expected goals value of a penalty kick (based on post-shot xG models).
PK_XG_VALUE: float = 0.79

# Default corner kicks per 90 for a team (PL average ~5.0-6.0).
DEFAULT_TEAM_CK_PER_90: float = 5.5

# Expected assists per corner delivery (league average ~0.018).
XA_PER_CORNER: float = 0.018

# Expected assists per direct free kick in dangerous areas (league average ~0.020).
XA_PER_DIRECT_FK: float = 0.020

# Default direct free kicks in dangerous areas per 90 (team level).
DEFAULT_TEAM_FK_PER_90: float = 1.2

# Set-piece role column names in players_raw.csv
COL_PK_ORDER = 'penalties_order'
COL_FK_ORDER = 'direct_freekicks_order'
COL_CK_ORDER = 'corners_and_indirect_freekicks_order'


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def load_set_piece_roles(
    season: str = '2026-27',
    data_root: str = 'data',
) -> pd.DataFrame:
    """Load set-piece role assignments from players_raw.csv.

    Args:
        season: season string e.g. '2026-27'.
        data_root: root data directory.

    Returns:
        DataFrame with columns: player_code, web_name, team, position,
        penalties_order, direct_freekicks_order, corners_and_indirect_freekicks_order.
    """
    path = os.path.join(data_root, season, 'players_raw.csv')
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)

    cols_needed = ['code', 'web_name', 'team', 'element_type',
                   COL_PK_ORDER, COL_FK_ORDER, COL_CK_ORDER]
    for c in cols_needed:
        if c not in df.columns:
            df[c] = None

    pos_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    df['position'] = df['element_type'].map(pos_map).fillna('MID')

    return df[['code', 'web_name', 'team', 'position',
               COL_PK_ORDER, COL_FK_ORDER, COL_CK_ORDER]].copy()


def get_team_primary_taker_codes(
    roles_df: pd.DataFrame,
    team_id: int,
) -> Dict[str, Optional[int]]:
    """Identify primary PK, FK, and CK taker player codes for a team.

    Args:
        roles_df: DataFrame from load_set_piece_roles().
        team_id: FPL team integer ID.

    Returns:
        Dict with keys 'pk_primary', 'fk_primary', 'ck_primary' mapping to
        player codes (or None if not assigned).
    """
    team_rows = roles_df[roles_df['team'] == team_id]
    result: Dict[str, Optional[int]] = {
        'pk_primary': None,
        'fk_primary': None,
        'ck_primary': None,
    }

    if team_rows.empty:
        return result

    # Find order-1 takers
    for col, key in [(COL_PK_ORDER, 'pk_primary'),
                     (COL_FK_ORDER, 'fk_primary'),
                     (COL_CK_ORDER, 'ck_primary')]:
        candidates = team_rows[team_rows[col] == 1.0]
        if not candidates.empty:
            result[key] = int(candidates.iloc[0]['code'])

    return result


def compute_set_piece_equity(
    player_code: int,
    position: str,
    pk_order: float,
    fk_order: float,
    ck_order: float,
    p_on_pitch: float = 1.0,
    team_pk_rate: float = DEFAULT_TEAM_PK_RATE_PER_90,
    team_ck_per_90: float = DEFAULT_TEAM_CK_PER_90,
    team_fk_per_90: float = DEFAULT_TEAM_FK_PER_90,
    primary_taker_p_on_pitch: float = 0.90,
) -> Dict[str, float]:
    """Calculate set-piece goal and assist equity for a single player.

    Penalty equity:
        If order == 1: delta_xg_pk = p_on_pitch * team_pk_rate * PK_XG_VALUE
        If order == 2: delta_xg_pk = p_on_pitch * (1 - primary_p) * team_pk_rate * PK_XG_VALUE

    Corner/FK assist equity:
        If order == 1: delta_xa_ck = p_on_pitch * team_ck_per_90 * XA_PER_CORNER
                       delta_xa_fk = p_on_pitch * team_fk_per_90 * XA_PER_DIRECT_FK

    Args:
        player_code: unique FPL player code.
        position: player position string ('GK', 'DEF', 'MID', 'FWD').
        pk_order: penalties_order (1.0 = primary, 2.0 = secondary, NaN = not a taker).
        fk_order: direct_freekicks_order.
        ck_order: corners_and_indirect_freekicks_order.
        p_on_pitch: probability the player is on the pitch (p_app or p_start).
        team_pk_rate: team penalty win rate per 90.
        team_ck_per_90: team corners per 90.
        team_fk_per_90: team direct free kicks in dangerous areas per 90.
        primary_taker_p_on_pitch: estimated probability primary taker is on pitch (for secondary calc).

    Returns:
        Dict with 'delta_xg_pk', 'delta_xa_ck', 'delta_xa_fk',
        'delta_c8_goals', 'delta_c7_assists', 'is_pk_taker', 'is_ck_taker', 'is_fk_taker'.
    """
    delta_xg_pk = 0.0
    delta_xa_ck = 0.0
    delta_xa_fk = 0.0

    # Penalty Goal Equity
    pk_ord = _safe_float(pk_order, default=0.0)
    if pk_ord == 1.0:
        delta_xg_pk = p_on_pitch * team_pk_rate * PK_XG_VALUE
    elif pk_ord == 2.0:
        # Secondary taker: only takes when primary is absent
        delta_xg_pk = p_on_pitch * (1.0 - primary_taker_p_on_pitch) * team_pk_rate * PK_XG_VALUE

    # Corner Assist Equity
    ck_ord = _safe_float(ck_order, default=0.0)
    if ck_ord == 1.0:
        delta_xa_ck = p_on_pitch * team_ck_per_90 * XA_PER_CORNER
    elif ck_ord == 2.0:
        delta_xa_ck = p_on_pitch * (1.0 - primary_taker_p_on_pitch) * team_ck_per_90 * XA_PER_CORNER

    # Direct Free Kick Assist Equity
    fk_ord = _safe_float(fk_order, default=0.0)
    if fk_ord == 1.0:
        delta_xa_fk = p_on_pitch * team_fk_per_90 * XA_PER_DIRECT_FK
    elif fk_ord == 2.0:
        delta_xa_fk = p_on_pitch * (1.0 - primary_taker_p_on_pitch) * team_fk_per_90 * XA_PER_DIRECT_FK

    # Map equity to FPL point components
    goal_pts_map = {'GK': 6.0, 'DEF': 6.0, 'MID': 5.0, 'FWD': 4.0}
    goal_pts = goal_pts_map.get(position.upper(), 4.0)
    assist_pts = 3.0

    delta_c8 = delta_xg_pk * goal_pts * PK_CONVERSION_RATE
    delta_c7 = (delta_xa_ck + delta_xa_fk) * assist_pts

    return {
        'delta_xg_pk': round(delta_xg_pk, 6),
        'delta_xa_ck': round(delta_xa_ck, 6),
        'delta_xa_fk': round(delta_xa_fk, 6),
        'delta_c8_goals': round(delta_c8, 6),
        'delta_c7_assists': round(delta_c7, 6),
        'is_pk_taker': pk_ord in (1.0, 2.0),
        'is_ck_taker': ck_ord in (1.0, 2.0),
        'is_fk_taker': fk_ord in (1.0, 2.0),
    }


def enrich_predictions_with_set_pieces(
    pred_df: pd.DataFrame,
    season: str = '2026-27',
    data_root: str = 'data',
) -> pd.DataFrame:
    """Add set-piece equity columns to an existing predictions DataFrame.

    Enriches the DataFrame with delta_c7_sp, delta_c8_sp, sp_pk_order,
    sp_fk_order, sp_ck_order columns, and adjusts expected_points to include
    set-piece equity.

    Args:
        pred_df: predictions DataFrame with player_code, position, p_start columns.
        season: season string.
        data_root: root data directory.

    Returns:
        Enriched DataFrame copy.
    """
    roles_df = load_set_piece_roles(season=season, data_root=data_root)
    if roles_df.empty:
        df = pred_df.copy()
        df['delta_c7_sp'] = 0.0
        df['delta_c8_sp'] = 0.0
        df['sp_pk_order'] = None
        df['sp_fk_order'] = None
        df['sp_ck_order'] = None
        return df

    # Build lookup by player code
    role_lookup: Dict[int, Dict[str, float]] = {}
    for _, r in roles_df.iterrows():
        code = int(r['code'])
        role_lookup[code] = {
            'pk_order': _safe_float(r[COL_PK_ORDER], 0.0),
            'fk_order': _safe_float(r[COL_FK_ORDER], 0.0),
            'ck_order': _safe_float(r[COL_CK_ORDER], 0.0),
        }

    df = pred_df.copy()
    delta_c7_list = []
    delta_c8_list = []
    pk_orders = []
    fk_orders = []
    ck_orders = []

    for _, row in df.iterrows():
        p_code = int(row.get('player_code', 0))
        position = str(row.get('position', 'MID')).upper()
        p_start = _safe_float(row.get('p_start', 0.0))
        team = str(row.get('team', ''))

        roles = role_lookup.get(p_code, {'pk_order': 0.0, 'fk_order': 0.0, 'ck_order': 0.0})
        team_pk = get_team_pk_rate(team)

        equity = compute_set_piece_equity(
            player_code=p_code,
            position=position,
            pk_order=roles['pk_order'],
            fk_order=roles['fk_order'],
            ck_order=roles['ck_order'],
            p_on_pitch=p_start,
            team_pk_rate=team_pk,
        )

        delta_c7_list.append(equity['delta_c7_assists'])
        delta_c8_list.append(equity['delta_c8_goals'])
        pk_orders.append(roles['pk_order'] if roles['pk_order'] > 0 else None)
        fk_orders.append(roles['fk_order'] if roles['fk_order'] > 0 else None)
        ck_orders.append(roles['ck_order'] if roles['ck_order'] > 0 else None)

    df['delta_c7_sp'] = delta_c7_list
    df['delta_c8_sp'] = delta_c8_list
    df['sp_pk_order'] = pk_orders
    df['sp_fk_order'] = fk_orders
    df['sp_ck_order'] = ck_orders

    # Adjust total expected_points to include set-piece equity
    df['expected_points'] = df['expected_points'] + df['delta_c7_sp'] + df['delta_c8_sp']

    return df

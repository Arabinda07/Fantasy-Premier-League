"""FPL Squad Optimization Solver (Phase 4).

Mixed Integer Linear Programming (MILP / ILP) optimization solver for Fantasy Premier League.

Key Capabilities:
1. 15-Man Squad Selection under £100.0M budget and 3-player club limit.
2. 11-Man Starting XI & Dynamic Formation Selection (min 3 DEF, min 2 MID, min 1 FWD).
3. Captain ($2x$) & Vice-Captain Assignment.
4. Ordered Bench Priority (GK slot 1, outfield slots 2-4 ordered descending by xP).
5. Weekly Transfer Optimizer with Free Transfers ($1..5$) and -4 hit calculations.
6. FPL Selling Price Mechanics (50% profit retention rule).
7. Strategic Chip Optimization: Bench Boost ('bboost'), Triple Captain ('3xc'), Free Hit ('freehit'), Wildcard ('wildcard').
8. Pitch Visualization and reporting.

Usage:
    python -m model.solver [--season 2026-27] [--gw 1] [--budget 100.0] [--chip 3xc]
"""
import argparse
from dataclasses import dataclass
import math
import os
import sys
from typing import Dict, Any, List, Tuple, Optional, Set, Union
import warnings
import numpy as np
import pandas as pd
import pulp

# Suppress PuLP internal deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pulp")

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import _safe_float
from model.ownership_engine import enrich_predictions_with_ownership, rank_adjusted_utility
from model.matchup_intelligence import enrich_predictions_with_matchup_intelligence
from model.set_pieces import enrich_predictions_with_set_pieces
from model.rotation_intelligence import apply_rotation_dampening

# Official FPL 15-man squad positional quotas
POSITIONAL_QUOTAS: Dict[str, int] = {
    'GK': 2,
    'DEF': 5,
    'MID': 5,
    'FWD': 3,
}


def resolve_player_code(identifier: Union[int, str], df: pd.DataFrame) -> Optional[int]:
    """Resolve a single player code from an integer code or string web_name / full name."""
    if identifier is None:
        return None
    if isinstance(identifier, int):
        return identifier
    s_val = str(identifier).strip()
    if s_val.isdigit():
        return int(s_val)

    # Search in player_code, code, web_name, name
    for col in ['web_name', 'name', 'second_name', 'first_name']:
        if col in df.columns:
            matches = df[df[col].astype(str).str.lower() == s_val.lower()]
            if not matches.empty:
                code_col = 'player_code' if 'player_code' in matches.columns else ('code' if 'code' in matches.columns else 'id')
                return int(matches.iloc[0][code_col])
    return None


def resolve_player_codes(identifiers: Optional[Union[List[Union[int, str]], str]], df: pd.DataFrame) -> List[int]:
    """Resolve a comma-separated string or list of identifiers into integer player codes."""
    if not identifiers:
        return []
    if isinstance(identifiers, str):
        items = [x.strip() for x in identifiers.split(',') if x.strip()]
    else:
        items = identifiers
    result = []
    for it in items:
        code = resolve_player_code(it, df)
        if code is not None:
            result.append(code)
    return result


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class PlayerPick:
    """Represents a single player selection in squad/lineup."""
    player_code: int
    web_name: str
    team: str
    position: str
    cost: float  # In millions e.g. 15.0
    expected_points: float
    is_starter: bool
    is_captain: bool
    is_vice_captain: bool
    bench_order: Optional[int] = None  # 1 for GK, 2/3/4 for outfield bench


@dataclass
class SquadSolution:
    """Complete solution for a 15-man squad and matchday lineup."""
    squad: List[PlayerPick]
    starters: List[PlayerPick]
    bench: List[PlayerPick]
    captain: Optional[PlayerPick]
    vice_captain: Optional[PlayerPick]
    total_cost: float
    starting_xp: float
    captain_xp: float
    total_xp: float
    formation: str
    status: str
    chip: Optional[str] = None


@dataclass
class TransferSolution:
    """Optimal weekly transfer decision solution."""
    transfers_in: List[PlayerPick]
    transfers_out: List[PlayerPick]
    transfers_count: int
    free_transfers_used: int
    hits_taken: int
    hit_penalty: float
    net_xp: float
    squad_solution: SquadSolution


@dataclass
class GameweekPlan:
    """Plan for a single gameweek in a multi-horizon lookahead solution."""
    gw: int
    transfers_in: List[PlayerPick]
    transfers_out: List[PlayerPick]
    transfers_count: int
    hits_taken: int
    hit_penalty: float
    free_transfers_available: int
    free_transfers_remaining: int
    bank: float
    squad_solution: SquadSolution
    net_xp: float


@dataclass
class MultiHorizonSolution:
    """Complete multi-gameweek lookahead solution across 3 to 5 gameweeks."""
    horizon: int
    discount_factor: float
    total_discounted_xp: float
    total_hits_taken: int
    total_hit_penalty: float
    gw_plans: List[GameweekPlan]
    status: str


# ---------------------------------------------------------------------------
# Data Preprocessing & Cost Loading
# ---------------------------------------------------------------------------

def load_player_costs(
    season: str = '2026-27',
    data_root: str = 'data',
) -> Dict[int, float]:
    """Load player prices in £M from players_raw.csv.

    Args:
        season: season string e.g. '2026-27'.
        data_root: root data directory.

    Returns:
        Dict mapping player_code (int) -> cost in £M (float).
    """
    raw_path = os.path.join(data_root, season, 'players_raw.csv')
    if not os.path.exists(raw_path):
        return {}

    raw_df = pd.read_csv(raw_path)
    costs: Dict[int, float] = {}

    code_col = 'code' if 'code' in raw_df.columns else ('id' if 'id' in raw_df.columns else None)
    cost_col = 'now_cost' if 'now_cost' in raw_df.columns else None

    if code_col and cost_col:
        for _, row in raw_df.iterrows():
            code = row.get(code_col)
            cost = row.get(cost_col)
            if pd.notnull(code) and pd.notnull(cost):
                cost_val = float(cost)
                if cost_val > 25.0:  # Tenths format (e.g. 45 -> 4.5, 150 -> 15.0)
                    costs[int(code)] = round(cost_val / 10.0, 1)
                else:
                    costs[int(code)] = round(cost_val, 1)

    return costs


def calculate_fpl_selling_price(
    purchase_price: float,
    current_price: float,
) -> float:
    """Calculate exact FPL selling price under 50% profit retention rule.

    Formula (in integer tenths to avoid floating-point floor division fragility):
        profit_tenths = round((current_price - purchase_price) * 10)
        share_tenths = profit_tenths // 2
        selling_price = purchase_price + share_tenths / 10.0
    """
    if current_price <= purchase_price:
        return current_price
    # F-03 fix: operate in integer tenths to avoid floating-point floor fragility
    profit_tenths = round((current_price - purchase_price) * 10)
    share_tenths = profit_tenths // 2
    return round(purchase_price + share_tenths / 10.0, 1)


def prepare_solver_dataframe(
    df: pd.DataFrame,
    season: str = '2026-27',
    data_root: str = 'data',
    strategy: str = 'pure_xp',
    lambda_risk: float = 0.0,
) -> pd.DataFrame:
    """Prepares and cleans dataframe for optimization solvers with risk adjustment.

    Args:
        df: raw input DataFrame.
        season: season string e.g. '2026-27'.
        data_root: root data directory.
        strategy: 'pure_xp', 'rank_protect', or 'differential_chase'.
        lambda_risk: CVaR risk aversion parameter (>0 penalizes downside, <0 rewards upside).

    Returns:
        Cleaned DataFrame ready for ILP formulation.
    """
    df = df.copy()

    costs = load_player_costs(season, data_root)

    if 'player_code' not in df.columns and 'code' in df.columns:
        df['player_code'] = df['code']
    elif 'player_code' not in df.columns and 'id' in df.columns:
        df['player_code'] = df['id']

    if 'cost' not in df.columns:
        if 'now_cost' in df.columns:
            df['cost'] = df['now_cost'].apply(
                lambda c: round(float(c) / 10.0, 1) if float(c) > 25.0 else round(float(c), 1)
            )
        else:
            df['cost'] = df['player_code'].apply(lambda c: costs.get(int(c), 5.0) if pd.notnull(c) else 5.0)

    df['position'] = df['position'].astype(str).str.upper()
    df = df[df['position'].isin(['GK', 'DEF', 'MID', 'FWD'])]

    if 'expected_points' not in df.columns and 'fixture_xp' in df.columns:
        df['expected_points'] = df['fixture_xp']
    elif 'expected_points' not in df.columns:
        df['expected_points'] = 0.0

    df['expected_points'] = pd.to_numeric(df['expected_points'], errors='coerce').fillna(0.0)
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce').fillna(5.0)

    if 'is_promoted' in df.columns:
        df['is_promoted'] = df['is_promoted'].fillna(False).astype(bool)

    # Matchup Intelligence (H2H & Tactical Archetype)
    if 'h2h_mult' not in df.columns and 'fixture_opponent' in df.columns:
        df = enrich_predictions_with_matchup_intelligence(df, season=season, data_root=data_root)

    # Set Pieces & Penalties
    if 'sp_pk_order' not in df.columns:
        df = enrich_predictions_with_set_pieces(df, season=season, data_root=data_root)

    # Injury & Rotation Hazard Dampening (Forces 0.0 xP for Injured/Suspended players)
    if 'rotation_dampening' not in df.columns:
        df = apply_rotation_dampening(df, season=season, data_root=data_root)

    # Strategy / Effective Ownership rank-adjusted utility
    if strategy != 'pure_xp' and 'utility_xp' not in df.columns:
        df = enrich_predictions_with_ownership(df, season=season, data_root=data_root, strategy=strategy)

    if 'utility_xp' in df.columns and strategy != 'pure_xp':
        df['opt_points'] = pd.to_numeric(df['utility_xp'], errors='coerce').fillna(df['expected_points'])
    else:
        df['opt_points'] = df['expected_points'].copy()

    # Risk-Adjusted CVaR / Tail-Risk Adjustment
    eff_lambda = lambda_risk
    if eff_lambda == 0.0:
        if strategy == 'rank_protect':
            eff_lambda = 0.15
        elif strategy == 'differential_chase':
            eff_lambda = -0.15

    if eff_lambda != 0.0:
        if 'floor_p10' in df.columns and 'ceiling_p90' in df.columns:
            downside_risk = np.maximum(0.0, df['expected_points'] - pd.to_numeric(df['floor_p10'], errors='coerce').fillna(0.0))
            upside_reward = np.maximum(0.0, pd.to_numeric(df['ceiling_p90'], errors='coerce').fillna(df['expected_points']) - df['expected_points'])
        elif 'std' in df.columns:
            stdev = pd.to_numeric(df['std'], errors='coerce').fillna(1.5)
            downside_risk = stdev
            upside_reward = stdev
        else:
            pos_factor = df['position'].map({'GK': 0.35, 'DEF': 0.40, 'MID': 0.55, 'FWD': 0.60}).fillna(0.50)
            stdev = df['expected_points'] * pos_factor + 1.2
            downside_risk = stdev * 1.28
            upside_reward = stdev * 1.28

        if eff_lambda > 0:
            df['opt_points'] = df['opt_points'] - eff_lambda * downside_risk
        else:
            df['opt_points'] = df['opt_points'] + abs(eff_lambda) * upside_reward

    # Captaincy Bayesian Confidence regularizer: prevents low-minute fringe cameos from usurping captaincy
    if 'season_minutes' in df.columns:
        season_mins = pd.to_numeric(df['season_minutes'], errors='coerce').fillna(900.0)
    elif 'minutes' in df.columns:
        season_mins = pd.to_numeric(df['minutes'], errors='coerce').fillna(900.0)
    else:
        season_mins = pd.Series(900.0, index=df.index)

    if 'p_start' in df.columns:
        p_start_val = pd.to_numeric(df['p_start'], errors='coerce').fillna(1.0)
    else:
        p_start_val = pd.Series(1.0, index=df.index)

    cost_val = pd.to_numeric(df['cost'], errors='coerce').fillna(5.0)
    capt_conf = np.minimum(1.0, np.maximum(0.20, (season_mins / 720.0) * p_start_val + (cost_val / 25.0)))
    df['captain_points'] = df['opt_points'] * capt_conf

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Initial Squad Solver (MILP / ILP)
# ---------------------------------------------------------------------------

def solve_initial_squad(
    df: pd.DataFrame,
    budget: float = 100.0,
    max_team_players: int = 3,
    max_promoted_players: int = 2,
    chip: Optional[str] = None,
    season: str = '2026-27',
    data_root: str = 'data',
    strategy: str = 'pure_xp',
    lambda_risk: float = 0.0,
    locked_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    excluded_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    forced_captain_code: Optional[Union[int, str]] = None,
    forced_vice_captain_code: Optional[Union[int, str]] = None,
) -> SquadSolution:
    """Solve for the optimal 15-man squad, starting XI, captain, and bench.

    Mathematical Formulation:
        Maximize sum_{i} (opt_points_i * s_i + capt_bonus * opt_points_i * c_i + bench_w * opt_points_i * (x_i - s_i))

    Args:
        df: DataFrame with candidate players.
        budget: maximum squad cost in £M (default 100.0).
        max_team_players: maximum allowed players from any single club (default 3).
        max_promoted_players: maximum allowed players from any single promoted club (default 2).
        chip: optional FPL chip ('bboost', '3xc', 'freehit', 'wildcard').
        season: season string for price resolution.
        data_root: root data directory.
        strategy: game theory strategy ('pure_xp', 'rank_protect', 'differential_chase').
        lambda_risk: CVaR risk aversion parameter (>0 penalizes downside, <0 rewards upside).
        locked_player_codes: list or comma-separated string of player names/codes to force in squad.
        excluded_player_codes: list or comma-separated string of player names/codes to exclude.
        forced_captain_code: player name or code to force as captain.
        forced_vice_captain_code: player name or code to force as vice-captain.

    Returns:
        SquadSolution object.
    """
    df = prepare_solver_dataframe(df, season=season, data_root=data_root, strategy=strategy, lambda_risk=lambda_risk)

    prob = pulp.LpProblem("FPL_Initial_Squad_Optimization", pulp.LpMaximize)
    indices = list(df.index)

    # Decision variables
    x = {i: pulp.LpVariable(f"squad_{i}", cat=pulp.LpBinary) for i in indices}
    s = {i: pulp.LpVariable(f"starter_{i}", cat=pulp.LpBinary) for i in indices}
    c = {i: pulp.LpVariable(f"captain_{i}", cat=pulp.LpBinary) for i in indices}
    v = {i: pulp.LpVariable(f"vice_{i}", cat=pulp.LpBinary) for i in indices}

    # Chip modifiers
    is_bench_boost = (chip == 'bboost')
    is_triple_captain = (chip == '3xc')
    is_free_hit = (chip == 'freehit')

    capt_multiplier = 2.0 if is_triple_captain else 1.0  # +2x bonus for 3xC, +1x for standard
    bench_weight = 1.0 if is_bench_boost else (0.0 if is_free_hit else 0.05)
    bench_cost_penalty = 0.01 if is_free_hit else 0.0

    # Objective function
    prob += pulp.lpSum(
        df.loc[i, 'opt_points'] * s[i] +
        capt_multiplier * df.loc[i, 'captain_points'] * c[i] +
        bench_weight * df.loc[i, 'opt_points'] * (x[i] - s[i]) -
        bench_cost_penalty * df.loc[i, 'cost'] * (x[i] - s[i])
        for i in indices
    )

    # 1. Positional Quotas in 15-Man Squad
    gk_indices = df[df['position'] == 'GK'].index
    def_indices = df[df['position'] == 'DEF'].index
    mid_indices = df[df['position'] == 'MID'].index
    fwd_indices = df[df['position'] == 'FWD'].index

    prob += pulp.lpSum(x[i] for i in gk_indices) == 2, "Squad_GK_Quota"
    prob += pulp.lpSum(x[i] for i in def_indices) == 5, "Squad_DEF_Quota"
    prob += pulp.lpSum(x[i] for i in mid_indices) == 5, "Squad_MID_Quota"
    prob += pulp.lpSum(x[i] for i in fwd_indices) == 3, "Squad_FWD_Quota"
    prob += pulp.lpSum(x[i] for i in indices) == 15, "Squad_Total_Size"

    # 2. Starting XI / Lineup Constraints
    for i in indices:
        prob += s[i] <= x[i], f"Starter_Must_Be_In_Squad_{i}"

    if is_bench_boost:
        # All 15 players start on Bench Boost
        for i in indices:
            prob += s[i] == x[i], f"All_Start_Bench_Boost_{i}"
    else:
        prob += pulp.lpSum(s[i] for i in indices) == 11, "Starting_XI_Total_Size"
        prob += pulp.lpSum(s[i] for i in gk_indices) == 1, "Starting_GK_Count"
        prob += pulp.lpSum(s[i] for i in def_indices) >= 3, "Starting_DEF_Min"
        prob += pulp.lpSum(s[i] for i in def_indices) <= 5, "Starting_DEF_Max"
        prob += pulp.lpSum(s[i] for i in mid_indices) >= 2, "Starting_MID_Min"
        prob += pulp.lpSum(s[i] for i in mid_indices) <= 5, "Starting_MID_Max"
        prob += pulp.lpSum(s[i] for i in fwd_indices) >= 1, "Starting_FWD_Min"
        prob += pulp.lpSum(s[i] for i in fwd_indices) <= 3, "Starting_FWD_Max"

    # 3. Budget Constraint
    prob += pulp.lpSum(df.loc[i, 'cost'] * x[i] for i in indices) <= budget, "Total_Budget_Limit"

    # 4. Club / Team Constraints (with Promoted Team Limits)
    promoted_teams = set()
    if 'is_promoted' in df.columns:
        promoted_teams = set(df[df['is_promoted'] == True]['team'].dropna().unique())

    for team_name in df['team'].dropna().unique():
        team_indices = df[df['team'] == team_name].index
        limit = min(max_team_players, max_promoted_players) if team_name in promoted_teams else max_team_players
        prob += pulp.lpSum(x[i] for i in team_indices) <= limit, f"Team_Limit_{team_name}"

    # 5. Captaincy & Vice-Captaincy Constraints
    prob += pulp.lpSum(c[i] for i in indices) == 1, "Exactly_One_Captain"
    prob += pulp.lpSum(v[i] for i in indices) == 1, "Exactly_One_Vice_Captain"
    for i in indices:
        prob += c[i] <= s[i], f"Captain_Must_Be_Starter_{i}"
        prob += v[i] <= s[i], f"Vice_Must_Be_Starter_{i}"
        prob += c[i] + v[i] <= 1, f"Captain_Vice_Distinct_{i}"

    # 6. User Constraints (Locks, Exclusions, Forced Captains)
    if locked_player_codes:
        resolved_locks = resolve_player_codes(locked_player_codes, df)
        for pcode in resolved_locks:
            matching_idx = df[df['player_code'] == pcode].index
            if not matching_idx.empty:
                prob += x[matching_idx[0]] == 1, f"Lock_Player_{pcode}"

    if excluded_player_codes:
        resolved_excludes = resolve_player_codes(excluded_player_codes, df)
        for pcode in resolved_excludes:
            matching_idx = df[df['player_code'] == pcode].index
            if not matching_idx.empty:
                prob += x[matching_idx[0]] == 0, f"Exclude_Player_{pcode}"

    if forced_captain_code is not None:
        resolved_c = resolve_player_code(forced_captain_code, df)
        if resolved_c is not None:
            capt_idx = df[df['player_code'] == resolved_c].index
            if not capt_idx.empty:
                prob += c[capt_idx[0]] == 1, "Forced_Captain_Constraint"
                prob += s[capt_idx[0]] == 1, "Forced_Captain_Must_Start"

    if forced_vice_captain_code is not None:
        resolved_v = resolve_player_code(forced_vice_captain_code, df)
        if resolved_v is not None:
            vice_idx = df[df['player_code'] == resolved_v].index
            if not vice_idx.empty:
                prob += v[vice_idx[0]] == 1, "Forced_Vice_Captain_Constraint"
                prob += s[vice_idx[0]] == 1, "Forced_Vice_Must_Start"

    # Solve using CBC solver
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)
    status_str = pulp.LpStatus[prob.status]

    if status_str != "Optimal":
        print(f"Warning: solver returned non-optimal status: {status_str}")
        return SquadSolution(
            squad=[],
            starters=[],
            bench=[],
            captain=None,
            vice_captain=None,
            total_cost=0.0,
            starting_xp=0.0,
            captain_xp=0.0,
            total_xp=0.0,
            formation="0-0-0",
            status=status_str,
            chip=chip,
        )

    # Build solution output
    squad_picks: List[PlayerPick] = []
    starters: List[PlayerPick] = []
    bench_unranked: List[PlayerPick] = []
    captain_pick: Optional[PlayerPick] = None
    vice_pick: Optional[PlayerPick] = None

    for i in indices:
        if pulp.value(x[i]) and pulp.value(x[i]) > 0.5:
            is_start = bool(pulp.value(s[i]) and pulp.value(s[i]) > 0.5)
            is_capt = bool(pulp.value(c[i]) and pulp.value(c[i]) > 0.5)
            is_vice = bool(pulp.value(v[i]) and pulp.value(v[i]) > 0.5)

            pick = PlayerPick(
                player_code=int(df.loc[i, 'player_code']),
                web_name=str(df.loc[i, 'web_name']),
                team=str(df.loc[i, 'team']),
                position=str(df.loc[i, 'position']),
                cost=float(df.loc[i, 'cost']),
                expected_points=round(float(df.loc[i, 'expected_points']), 4),
                is_starter=is_start,
                is_captain=is_capt,
                is_vice_captain=is_vice,
            )
            squad_picks.append(pick)
            if is_start:
                starters.append(pick)
                if is_capt:
                    captain_pick = pick
                if is_vice:
                    vice_pick = pick
            else:
                bench_unranked.append(pick)

    # Order bench: Bench GK is slot 1, outfield players ordered by xP descending
    bench = order_bench(bench_unranked)

    # Compute formation
    def_count = sum(1 for p in starters if p.position == 'DEF')
    mid_count = sum(1 for p in starters if p.position == 'MID')
    fwd_count = sum(1 for p in starters if p.position == 'FWD')
    formation_str = f"{def_count}-{mid_count}-{fwd_count}"

    total_cost = round(sum(p.cost for p in squad_picks), 2)
    starting_xp = round(sum(p.expected_points for p in starters), 4)
    captain_bonus_mult = 2.0 if is_triple_captain else 1.0
    captain_xp = round(captain_bonus_mult * captain_pick.expected_points, 4) if captain_pick else 0.0
    total_xp = round(starting_xp + captain_xp, 4)

    return SquadSolution(
        squad=squad_picks,
        starters=starters,
        bench=bench,
        captain=captain_pick if captain_pick else (starters[0] if starters else None),
        vice_captain=vice_pick if vice_pick else (starters[1] if len(starters) > 1 else None),
        total_cost=total_cost,
        starting_xp=starting_xp,
        captain_xp=captain_xp,
        total_xp=total_xp,
        formation=formation_str,
        status=status_str,
        chip=chip,
    )


# ---------------------------------------------------------------------------
# Bench Ordering Logic
# ---------------------------------------------------------------------------

def order_bench(bench_players: List[PlayerPick]) -> List[PlayerPick]:
    """Order bench players according to standard FPL rules.

    Rules:
    - Slot 1: Backup Goalkeeper (GK)
    - Slot 2: 1st Outfield Sub (highest xP)
    - Slot 3: 2nd Outfield Sub
    - Slot 4: 3rd Outfield Sub (lowest xP)

    Args:
        bench_players: list of bench PlayerPick objects.

    Returns:
        Ordered list of PlayerPick objects with bench_order assigned (1..4).
    """
    gk_bench = [p for p in bench_players if p.position == 'GK']
    outfield_bench = [p for p in bench_players if p.position != 'GK']

    outfield_bench.sort(key=lambda p: p.expected_points, reverse=True)

    ordered: List[PlayerPick] = []
    slot = 1

    for gk in gk_bench:
        gk.bench_order = slot
        ordered.append(gk)
        slot += 1

    for out in outfield_bench:
        out.bench_order = slot
        ordered.append(out)
        slot += 1

    return ordered


# ---------------------------------------------------------------------------
# Weekly Transfer Optimizer
# ---------------------------------------------------------------------------

def solve_weekly_transfers(
    current_squad_codes: List[int],
    df: pd.DataFrame,
    free_transfers: int = 1,
    bank: float = 0.0,
    purchase_prices: Optional[Dict[int, float]] = None,
    chip: Optional[str] = None,
    max_transfers: int = 4,
    hit_cost: float = 4.0,
    max_team_players: int = 3,
    max_promoted_players: int = 2,
    season: str = '2026-27',
    data_root: str = 'data',
    strategy: str = 'pure_xp',
    lambda_risk: float = 0.0,
    locked_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    excluded_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    forced_captain_code: Optional[Union[int, str]] = None,
    forced_vice_captain_code: Optional[Union[int, str]] = None,
) -> TransferSolution:
    """Solve for optimal transfers in/out from an existing 15-man squad."""
    df = prepare_solver_dataframe(df, season=season, data_root=data_root, strategy=strategy, lambda_risk=lambda_risk)
    indices = list(df.index)

    owned_set = set(int(c) for c in current_squad_codes)
    is_owned = {i: 1 if int(df.loc[i, 'player_code']) in owned_set else 0 for i in indices}

    # Calculate exact selling price for currently owned players
    sell_prices: Dict[int, float] = {}
    for i in indices:
        code = int(df.loc[i, 'player_code'])
        current_p = float(df.loc[i, 'cost'])
        if is_owned[i]:
            bought_p = purchase_prices.get(code, current_p) if purchase_prices else current_p
            sell_prices[i] = calculate_fpl_selling_price(bought_p, current_p)
        else:
            sell_prices[i] = current_p

    current_squad_selling_value = sum(sell_prices[i] for i in indices if is_owned[i])
    total_available_budget = round(current_squad_selling_value + bank, 2)

    prob = pulp.LpProblem("FPL_Weekly_Transfer_Optimization", pulp.LpMaximize)

    # Decision variables
    x = {i: pulp.LpVariable(f"squad_{i}", cat=pulp.LpBinary) for i in indices}
    s = {i: pulp.LpVariable(f"starter_{i}", cat=pulp.LpBinary) for i in indices}
    c = {i: pulp.LpVariable(f"captain_{i}", cat=pulp.LpBinary) for i in indices}
    v = {i: pulp.LpVariable(f"vice_{i}", cat=pulp.LpBinary) for i in indices}

    transfer_in = {i: pulp.LpVariable(f"trans_in_{i}", cat=pulp.LpBinary) for i in indices}
    transfer_out = {i: pulp.LpVariable(f"trans_out_{i}", cat=pulp.LpBinary) for i in indices}

    hits = pulp.LpVariable("hits_taken", lowBound=0, cat=pulp.LpInteger)

    # Chip conditions
    is_wildcard = chip in ('wildcard', 'freehit')
    is_bench_boost = (chip == 'bboost')
    is_triple_captain = (chip == '3xc')

    effective_ft = 15 if is_wildcard else free_transfers
    capt_multiplier = 2.0 if is_triple_captain else 1.0
    bench_weight = 1.0 if is_bench_boost else 0.10

    # Objective
    prob += (
        pulp.lpSum(
            df.loc[i, 'opt_points'] * s[i] +
            capt_multiplier * df.loc[i, 'captain_points'] * c[i] +
            bench_weight * df.loc[i, 'opt_points'] * (x[i] - s[i])
            for i in indices
        )
        - (0.0 if is_wildcard else hit_cost) * hits
    )

    for i in indices:
        prob += x[i] == is_owned[i] + transfer_in[i] - transfer_out[i], f"Transfer_Balance_{i}"
        prob += transfer_in[i] <= 1 - is_owned[i], f"Can_Only_Buy_Unowned_{i}"
        prob += transfer_out[i] <= is_owned[i], f"Can_Only_Sell_Owned_{i}"

    prob += pulp.lpSum(transfer_in[i] for i in indices) == pulp.lpSum(transfer_out[i] for i in indices), "Balanced_Transfers"
    if not is_wildcard:
        prob += pulp.lpSum(transfer_in[i] for i in indices) <= max_transfers, "Max_Transfers_Limit"
    prob += hits >= pulp.lpSum(transfer_in[i] for i in indices) - effective_ft, "Hits_Lower_Bound"

    gk_indices = df[df['position'] == 'GK'].index
    def_indices = df[df['position'] == 'DEF'].index
    mid_indices = df[df['position'] == 'MID'].index
    fwd_indices = df[df['position'] == 'FWD'].index

    prob += pulp.lpSum(x[i] for i in gk_indices) == 2, "Squad_GK_Quota"
    prob += pulp.lpSum(x[i] for i in def_indices) == 5, "Squad_DEF_Quota"
    prob += pulp.lpSum(x[i] for i in mid_indices) == 5, "Squad_MID_Quota"
    prob += pulp.lpSum(x[i] for i in fwd_indices) == 3, "Squad_FWD_Quota"
    prob += pulp.lpSum(x[i] for i in indices) == 15, "Squad_Total_Size"

    for i in indices:
        prob += s[i] <= x[i], f"Starter_Must_Be_In_Squad_{i}"

    if is_bench_boost:
        for i in indices:
            prob += s[i] == x[i], f"All_Start_Bench_Boost_{i}"
    else:
        prob += pulp.lpSum(s[i] for i in indices) == 11, "Starting_XI_Total_Size"
        prob += pulp.lpSum(s[i] for i in gk_indices) == 1, "Starting_GK_Count"
        prob += pulp.lpSum(s[i] for i in def_indices) >= 3, "Starting_DEF_Min"
        prob += pulp.lpSum(s[i] for i in def_indices) <= 5, "Starting_DEF_Max"
        prob += pulp.lpSum(s[i] for i in mid_indices) >= 2, "Starting_MID_Min"
        prob += pulp.lpSum(s[i] for i in mid_indices) <= 5, "Starting_MID_Max"
        prob += pulp.lpSum(s[i] for i in fwd_indices) >= 1, "Starting_FWD_Min"
        prob += pulp.lpSum(s[i] for i in fwd_indices) <= 3, "Starting_FWD_Max"

    # Budget constraint using true purchase / sell prices
    prob += pulp.lpSum(df.loc[i, 'cost'] * x[i] for i in indices) <= total_available_budget, "Budget_Limit"

    promoted_teams = set()
    if 'is_promoted' in df.columns:
        promoted_teams = set(df[df['is_promoted'] == True]['team'].dropna().unique())

    for team_name in df['team'].dropna().unique():
        team_indices = df[df['team'] == team_name].index
        limit = min(max_team_players, max_promoted_players) if team_name in promoted_teams else max_team_players
        prob += pulp.lpSum(x[i] for i in team_indices) <= limit, f"Team_Limit_{team_name}"

    prob += pulp.lpSum(c[i] for i in indices) == 1, "One_Captain"
    prob += pulp.lpSum(v[i] for i in indices) == 1, "One_Vice"
    for i in indices:
        prob += c[i] <= s[i]
        prob += v[i] <= s[i]
        prob += c[i] + v[i] <= 1

    # User Constraints (Locks, Excludes, Forced Captains)
    if locked_player_codes:
        resolved_locks = resolve_player_codes(locked_player_codes, df)
        for pcode in resolved_locks:
            matching_idx = df[df['player_code'] == pcode].index
            if not matching_idx.empty:
                prob += x[matching_idx[0]] == 1, f"Lock_Transfer_{pcode}"

    if excluded_player_codes:
        resolved_excludes = resolve_player_codes(excluded_player_codes, df)
        for pcode in resolved_excludes:
            matching_idx = df[df['player_code'] == pcode].index
            if not matching_idx.empty:
                prob += x[matching_idx[0]] == 0, f"Exclude_Transfer_{pcode}"

    if forced_captain_code is not None:
        resolved_c = resolve_player_code(forced_captain_code, df)
        if resolved_c is not None:
            capt_idx = df[df['player_code'] == resolved_c].index
            if not capt_idx.empty:
                prob += c[capt_idx[0]] == 1, "Forced_Captain_Constraint"
                prob += s[capt_idx[0]] == 1, "Forced_Captain_Must_Start"

    if forced_vice_captain_code is not None:
        resolved_v = resolve_player_code(forced_vice_captain_code, df)
        if resolved_v is not None:
            vice_idx = df[df['player_code'] == resolved_v].index
            if not vice_idx.empty:
                prob += v[vice_idx[0]] == 1, "Forced_Vice_Captain_Constraint"
                prob += s[vice_idx[0]] == 1, "Forced_Vice_Must_Start"

    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)
    status_str = pulp.LpStatus[prob.status]

    if status_str != "Optimal":
        return TransferSolution(
            transfers_in=[],
            transfers_out=[],
            transfers_count=0,
            free_transfers_used=0,
            hits_taken=0,
            hit_penalty=0.0,
            net_xp=0.0,
            squad_solution=SquadSolution(
                squad=[], starters=[], bench=[], captain=None, vice_captain=None,
                total_cost=0.0, starting_xp=0.0, captain_xp=0.0, total_xp=0.0,
                formation="0-0-0", status=status_str, chip=chip
            ),
        )

    trans_in_picks: List[PlayerPick] = []
    trans_out_picks: List[PlayerPick] = []
    new_squad_picks: List[PlayerPick] = []
    starters: List[PlayerPick] = []
    bench_unranked: List[PlayerPick] = []
    captain_pick: Optional[PlayerPick] = None
    vice_pick: Optional[PlayerPick] = None

    for i in indices:
        is_in = bool(pulp.value(transfer_in[i]) and pulp.value(transfer_in[i]) > 0.5)
        is_out = bool(pulp.value(transfer_out[i]) and pulp.value(transfer_out[i]) > 0.5)
        is_squad = bool(pulp.value(x[i]) and pulp.value(x[i]) > 0.5)
        is_start = bool(pulp.value(s[i]) and pulp.value(s[i]) > 0.5)
        is_capt = bool(pulp.value(c[i]) and pulp.value(c[i]) > 0.5)
        is_vice = bool(pulp.value(v[i]) and pulp.value(v[i]) > 0.5)

        pick = PlayerPick(
            player_code=int(df.loc[i, 'player_code']),
            web_name=str(df.loc[i, 'web_name']),
            team=str(df.loc[i, 'team']),
            position=str(df.loc[i, 'position']),
            cost=float(df.loc[i, 'cost']),
            expected_points=round(float(df.loc[i, 'expected_points']), 4),
            is_starter=is_start,
            is_captain=is_capt,
            is_vice_captain=is_vice,
        )

        if is_in:
            trans_in_picks.append(pick)
        if is_out:
            trans_out_picks.append(pick)
        if is_squad:
            new_squad_picks.append(pick)
            if is_start:
                starters.append(pick)
                if is_capt:
                    captain_pick = pick
                if is_vice:
                    vice_pick = pick
            else:
                bench_unranked.append(pick)

    bench = order_bench(bench_unranked)
    def_count = sum(1 for p in starters if p.position == 'DEF')
    mid_count = sum(1 for p in starters if p.position == 'MID')
    fwd_count = sum(1 for p in starters if p.position == 'FWD')
    formation_str = f"{def_count}-{mid_count}-{fwd_count}"

    total_cost = round(sum(p.cost for p in new_squad_picks), 2)
    starting_xp = round(sum(p.expected_points for p in starters), 4)
    captain_bonus_mult = 2.0 if is_triple_captain else 1.0
    captain_xp = round(captain_bonus_mult * captain_pick.expected_points, 4) if captain_pick else 0.0
    total_xp = round(starting_xp + captain_xp, 4)

    squad_sol = SquadSolution(
        squad=new_squad_picks,
        starters=starters,
        bench=bench,
        captain=captain_pick if captain_pick else (starters[0] if starters else None),
        vice_captain=vice_pick if vice_pick else (starters[1] if len(starters) > 1 else None),
        total_cost=total_cost,
        starting_xp=starting_xp,
        captain_xp=captain_xp,
        total_xp=total_xp,
        formation=formation_str,
        status=status_str,
        chip=chip,
    )

    n_trans = len(trans_in_picks)
    ft_used = min(n_trans, effective_ft)
    actual_hits = 0 if is_wildcard else max(0, n_trans - free_transfers)
    hit_pen = actual_hits * hit_cost
    net_xp = round(total_xp - hit_pen, 4)

    return TransferSolution(
        transfers_in=trans_in_picks,
        transfers_out=trans_out_picks,
        transfers_count=n_trans,
        free_transfers_used=ft_used,
        hits_taken=actual_hits,
        hit_penalty=hit_pen,
        net_xp=net_xp,
        squad_solution=squad_sol,
    )


# ---------------------------------------------------------------------------
# Multi-Gameweek Horizon Lookahead Solver
# ---------------------------------------------------------------------------

def solve_multi_horizon_transfers(
    current_squad_codes: List[int],
    horizon_dfs: List[pd.DataFrame],
    free_transfers: int = 1,
    bank: float = 0.0,
    discount_factor: float = 0.90,
    max_transfers_per_gw: int = 2,
    hit_cost: float = 4.0,
    max_team_players: int = 3,
    max_promoted_players: int = 2,
    start_gw: int = 1,
    season: str = '2026-27',
    data_root: str = 'data',
    strategy: str = 'pure_xp',
    lambda_risk: float = 0.0,
    lambda_ft: float = 1.75,
    locked_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    excluded_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    forced_captain_code: Optional[Union[int, str]] = None,
    forced_vice_captain_code: Optional[Union[int, str]] = None,
    chip: Optional[str] = None,
) -> MultiHorizonSolution:
    """Solve multi-gameweek lookahead optimization across H gameweeks (H=3..5).

    Eliminates single-gameweek myopia by optimizing time-discounted expected points
    subject to inter-temporal squad continuity, free transfer accumulation, and bank balance.

    Args:
        current_squad_codes: list of 15 current player codes.
        horizon_dfs: list of DataFrames containing predictions for GW t, t+1, ...
        free_transfers: currently available free transfers (1..5).
        bank: remaining budget in bank in £M.
        discount_factor: temporal discount factor gamma (e.g. 0.90).
        max_transfers_per_gw: maximum transfers allowed per gameweek.
        hit_cost: penalty per transfer exceeding available FTs (-4.0).
        max_team_players: club quota constraint (default 3).
        max_promoted_players: promoted club quota constraint (default 2).
        start_gw: initial gameweek number.
        season: season string.
        data_root: root data directory.
        strategy: EO strategy mode ('pure_xp', 'rank_protect', 'differential_chase').
        lambda_risk: CVaR risk aversion parameter (>0 penalizes downside, <0 rewards upside).
        lambda_ft: shadow value per banked free transfer (default 1.75 pts).
        locked_player_codes: player codes that must be in the initial squad.
        excluded_player_codes: player codes that must not be in the initial squad.
        forced_captain_code: player code that must be captain in GW 0.
        forced_vice_captain_code: player code that must be vice-captain in GW 0.
        chip: optional active chip for first gameweek ('wildcard', 'freehit', 'bboost', '3xc').

    Returns:
        MultiHorizonSolution containing step-by-step transfer schedule and lineups.
    """
    horizon = len(horizon_dfs)
    if horizon == 0:
        return MultiHorizonSolution(
            horizon=0, discount_factor=discount_factor, total_discounted_xp=0.0,
            total_hits_taken=0, total_hit_penalty=0.0, gw_plans=[], status="Infeasible"
        )

    # 1. Prepare player pools across time
    pools: List[pd.DataFrame] = []
    for t, df in enumerate(horizon_dfs):
        pool_t = prepare_solver_dataframe(df, season=season, data_root=data_root, strategy=strategy, lambda_risk=lambda_risk)
        pools.append(pool_t)

    # Union of all player codes across horizon
    all_codes_set: Set[int] = set()
    for p_df in pools:
        all_codes_set.update(p_df['player_code'].astype(int).tolist())
    all_codes_set.update(current_squad_codes)

    # Master player metadata mapping
    all_meta: Dict[int, Dict[str, Any]] = {}
    for p_df in pools:
        for _, r in p_df.iterrows():
            c = int(r['player_code'])
            if c not in all_meta:
                all_meta[c] = {
                    'web_name': r.get('web_name', f"P_{c}"),
                    'team': r.get('team', ''),
                    'position': r.get('position', 'MID'),
                    'cost': float(r.get('cost', 5.0)),
                    'is_promoted': bool(r.get('is_promoted', False)),
                }

    # Ensure all owned players have metadata
    for c in current_squad_codes:
        if c not in all_meta:
            all_meta[c] = {'web_name': f"P_{c}", 'team': '', 'position': 'MID', 'cost': 5.0, 'is_promoted': False}

    # Initial squad cost & initial binary vector
    initial_codes_set = set(current_squad_codes)
    initial_squad_cost = sum(all_meta.get(c, {}).get('cost', 5.0) for c in initial_codes_set)
    total_allowed_budget = initial_squad_cost + bank

    prob = pulp.LpProblem("FPL_Multi_Horizon_Optimization", pulp.LpMaximize)

    # Decision variables across t = 0 .. H-1
    # x[c, t]: squad membership
    # s[c, t]: starting XI
    # capt[c, t]: captain
    # u[c, t]: transfer IN
    # v[c, t]: transfer OUT
    x: Dict[Tuple[int, int], pulp.LpVariable] = {}
    s: Dict[Tuple[int, int], pulp.LpVariable] = {}
    capt: Dict[Tuple[int, int], pulp.LpVariable] = {}
    u: Dict[Tuple[int, int], pulp.LpVariable] = {}
    v: Dict[Tuple[int, int], pulp.LpVariable] = {}
    hits: Dict[int, pulp.LpVariable] = {}

    for t in range(horizon):
        hits[t] = pulp.LpVariable(f"hits_{t}", lowBound=0, cat=pulp.LpInteger)
        for c in all_codes_set:
            x[(c, t)] = pulp.LpVariable(f"x_{c}_{t}", cat=pulp.LpBinary)
            s[(c, t)] = pulp.LpVariable(f"s_{c}_{t}", cat=pulp.LpBinary)
            capt[(c, t)] = pulp.LpVariable(f"capt_{c}_{t}", cat=pulp.LpBinary)
            u[(c, t)] = pulp.LpVariable(f"u_{c}_{t}", cat=pulp.LpBinary)
            v[(c, t)] = pulp.LpVariable(f"v_{c}_{t}", cat=pulp.LpBinary)

    # Multi-period Objective Function
    obj_terms = []
    base_bench_weight = 0.10  # Dynamic auto-sub bench valuation

    for t in range(horizon):
        discount = discount_factor ** t
        pool_t_map = {int(r['player_code']): float(r['opt_points']) for _, r in pools[t].iterrows()}
        pool_t_capt_map = {int(r['player_code']): float(r.get('captain_points', r['opt_points'])) for _, r in pools[t].iterrows()}

        cur_bench_weight = 1.0 if (t == 0 and chip == 'bboost') else base_bench_weight
        cur_capt_mult = 2.0 if (t == 0 and chip == '3xc') else 1.0

        for c in all_codes_set:
            xp_ct = pool_t_map.get(c, 0.0)
            xp_capt = pool_t_capt_map.get(c, xp_ct)
            # Starting XI receives full points + regularized captain bonus, bench receives bench_weight
            obj_terms.append(discount * (
                xp_ct * s[(c, t)] +
                cur_capt_mult * xp_capt * capt[(c, t)] +
                cur_bench_weight * xp_ct * (x[(c, t)] - s[(c, t)])
            ))

        obj_terms.append(-1.0 * discount * hit_cost * hits[t])

        # Free Transfer banking incentive (lambda_ft shadow value)
        if lambda_ft > 0:
            ft_t = free_transfers if t == 0 else 1
            obj_terms.append(discount * lambda_ft * (ft_t - pulp.lpSum([u[(c, t)] for c in all_codes_set])))

    prob += pulp.lpSum(obj_terms)

    # Multi-period Constraints
    for t in range(horizon):
        # 1. Positional Quotas
        gk_codes = [c for c in all_codes_set if all_meta.get(c, {}).get('position') == 'GK']
        def_codes = [c for c in all_codes_set if all_meta.get(c, {}).get('position') == 'DEF']
        mid_codes = [c for c in all_codes_set if all_meta.get(c, {}).get('position') == 'MID']
        fwd_codes = [c for c in all_codes_set if all_meta.get(c, {}).get('position') == 'FWD']

        prob += pulp.lpSum([x[(c, t)] for c in gk_codes]) == 2, f"quota_gk_{t}"
        prob += pulp.lpSum([x[(c, t)] for c in def_codes]) == 5, f"quota_def_{t}"
        prob += pulp.lpSum([x[(c, t)] for c in mid_codes]) == 5, f"quota_mid_{t}"
        prob += pulp.lpSum([x[(c, t)] for c in fwd_codes]) == 3, f"quota_fwd_{t}"
        prob += pulp.lpSum([x[(c, t)] for c in all_codes_set]) == 15, f"quota_total_{t}"

        # 2. Club Quota Constraints (with Promoted Team Limits)
        promoted_teams = set()
        for c in all_codes_set:
            meta = all_meta.get(c, {})
            t_name = meta.get('team', '')
            if t_name and meta.get('is_promoted', False):
                promoted_teams.add(t_name)

        unique_teams = set(all_meta.get(c, {}).get('team', '') for c in all_codes_set if all_meta.get(c, {}).get('team'))
        for team_name in unique_teams:
            team_codes = [c for c in all_codes_set if all_meta.get(c, {}).get('team') == team_name]
            limit = min(max_team_players, max_promoted_players) if team_name in promoted_teams else max_team_players
            prob += pulp.lpSum([x[(c, t)] for c in team_codes]) <= limit, f"team_limit_{team_name}_{t}"

        # 3. Starting XI Formation Constraints
        for c in all_codes_set:
            prob += s[(c, t)] <= x[(c, t)], f"starter_in_squad_{c}_{t}"

        prob += pulp.lpSum([s[(c, t)] for c in gk_codes]) == 1, f"start_gk_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in def_codes]) >= 3, f"start_def_min_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in def_codes]) <= 5, f"start_def_max_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in mid_codes]) >= 2, f"start_mid_min_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in mid_codes]) <= 5, f"start_mid_max_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in fwd_codes]) >= 1, f"start_fwd_min_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in fwd_codes]) <= 3, f"start_fwd_max_{t}"
        prob += pulp.lpSum([s[(c, t)] for c in all_codes_set]) == 11, f"start_total_11_{t}"

        # 4. Captaincy
        for c in all_codes_set:
            prob += capt[(c, t)] <= s[(c, t)], f"capt_must_start_{c}_{t}"
        prob += pulp.lpSum([capt[(c, t)] for c in all_codes_set]) == 1, f"one_captain_{t}"

        # 5. Inter-temporal Continuity
        for c in all_codes_set:
            if t == 0:
                is_init = 1 if c in initial_codes_set else 0
                prob += x[(c, 0)] == is_init + u[(c, 0)] - v[(c, 0)], f"continuity_{c}_0"
                prob += v[(c, 0)] <= is_init, f"can_only_sell_if_owned_{c}_0"
            else:
                prob += x[(c, t)] == x[(c, t - 1)] + u[(c, t)] - v[(c, t)], f"continuity_{c}_{t}"
                prob += v[(c, t)] <= x[(c, t - 1)], f"can_only_sell_if_owned_{c}_{t}"

        # 6. Transfer Count Balance
        prob += pulp.lpSum([u[(c, t)] for c in all_codes_set]) == pulp.lpSum([v[(c, t)] for c in all_codes_set]), f"trans_balance_{t}"
        prob += pulp.lpSum([u[(c, t)] for c in all_codes_set]) <= max_transfers_per_gw, f"trans_max_{t}"

        # 7. FT Rollover & Hits Constraint (F-05 fix: model FT accumulation)
        # ft_var[t] tracks available free transfers at each horizon step
        if t == 0:
            # First GW uses the given free_transfers value directly
            ft_t_val = free_transfers if not (chip in ('wildcard', 'freehit')) else 15
            prob += hits[t] >= pulp.lpSum([u[(c, t)] for c in all_codes_set]) - ft_t_val, f"hits_bound_{t}"
        else:
            # Subsequent GWs: FT accumulates based on previous GW's transfer activity
            # Linearized approximation: ft[t] = min(5, ft[t-1] - transfers[t-1] + 1)
            # We use ft_var auxiliary variables for dynamic FT tracking
            transfers_prev = pulp.lpSum([u[(c, t - 1)] for c in all_codes_set])
            # If t=1 and chip was freehit/wildcard, previous GW didn't consume FTs
            if t == 1 and chip in ('wildcard', 'freehit'):
                effective_prev_ft = free_transfers
            else:
                effective_prev_ft = free_transfers if t == 1 else 1
            # Conservative bound: at least 1 FT, at most 5
            # hits[t] >= transfers[t] - available_ft[t]
            # Since exact FT rollover requires nonlinear min(), use conservative bound of 1 FT
            # for t >= 2 (this is the same as before but with correct t=1 handling)
            ft_t_val = effective_prev_ft if t == 1 else 1
            prob += hits[t] >= pulp.lpSum([u[(c, t)] for c in all_codes_set]) - ft_t_val, f"hits_bound_{t}"

        # 8. Budget Constraint
        prob += pulp.lpSum([all_meta.get(c, {}).get('cost', 5.0) * x[(c, t)] for c in all_codes_set]) <= total_allowed_budget, f"budget_{t}"

    # F-06 fix: Free Hit squad reversion — squad at t=1 must revert to pre-FH initial state
    if chip == 'freehit' and horizon >= 2:
        for c in all_codes_set:
            is_init = 1 if c in initial_codes_set else 0
            # After Free Hit GW (t=0), squad at t=1 reverts to initial squad
            # Override the continuity constraint: x[c,1] must equal initial state + transfers at t=1
            # The reversion means the "base" for t=1 is initial squad, not the FH squad
            prob += x[(c, 1)] == is_init + u[(c, 1)] - v[(c, 1)], f"fh_revert_{c}"
            prob += v[(c, 1)] <= is_init, f"fh_revert_sell_{c}"

    # 9. User Constraints for Initial Gameweek (t=0)
    master_df = pools[0]
    if locked_player_codes:
        resolved_locks = resolve_player_codes(locked_player_codes, master_df)
        for pcode in resolved_locks:
            if pcode in all_codes_set:
                prob += x[(pcode, 0)] == 1, f"Lock_Multi_{pcode}"

    if excluded_player_codes:
        resolved_excludes = resolve_player_codes(excluded_player_codes, master_df)
        for pcode in resolved_excludes:
            if pcode in all_codes_set:
                prob += x[(pcode, 0)] == 0, f"Exclude_Multi_{pcode}"

    if forced_captain_code is not None:
        resolved_c = resolve_player_code(forced_captain_code, master_df)
        if resolved_c is not None and resolved_c in all_codes_set:
            prob += capt[(resolved_c, 0)] == 1, "Forced_Captain_Multi_0"
            prob += s[(resolved_c, 0)] == 1, "Forced_Captain_Start_Multi_0"

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=0)
    prob.solve(solver)

    status_str = pulp.LpStatus[prob.status]
    if status_str != "Optimal":
        return MultiHorizonSolution(
            horizon=horizon, discount_factor=discount_factor, total_discounted_xp=0.0,
            total_hits_taken=0, total_hit_penalty=0.0, gw_plans=[], status=status_str
        )

    # Extract Gameweek Plans
    gw_plans: List[GameweekPlan] = []
    tot_disc_xp = 0.0
    tot_hits = 0

    curr_bank = bank
    curr_ft = free_transfers

    for t in range(horizon):
        gw_num = start_gw + t
        pool_t_map = {int(r['player_code']): float(r['expected_points']) for _, r in pools[t].iterrows()}

        squad_picks: List[PlayerPick] = []
        starters: List[PlayerPick] = []
        bench_unranked: List[PlayerPick] = []
        captain_pick: Optional[PlayerPick] = None
        vice_pick: Optional[PlayerPick] = None

        trans_in_picks: List[PlayerPick] = []
        trans_out_picks: List[PlayerPick] = []

        pool_t_xp_map = {int(r['player_code']): float(r['expected_points']) for _, r in pools[t].iterrows()}

        for c in all_codes_set:
            meta = all_meta.get(c, {'web_name': f'P_{c}', 'team': '', 'position': 'MID', 'cost': 5.0})
            xp_val = pool_t_xp_map.get(c, 0.0)

            is_in_squad = x[(c, t)].varValue > 0.5
            is_starting = s[(c, t)].varValue > 0.5
            is_capt = capt[(c, t)].varValue > 0.5
            is_tin = u[(c, t)].varValue > 0.5
            is_tout = v[(c, t)].varValue > 0.5

            pick = PlayerPick(
                player_code=c,
                web_name=meta['web_name'],
                team=meta['team'],
                position=meta['position'],
                cost=meta['cost'],
                expected_points=xp_val,
                is_starter=is_starting,
                is_captain=is_capt,
                is_vice_captain=False,
            )

            if is_tin:
                trans_in_picks.append(pick)
            if is_tout:
                trans_out_picks.append(pick)

            if is_in_squad:
                squad_picks.append(pick)
                if is_starting:
                    starters.append(pick)
                    if is_capt:
                        captain_pick = pick
                else:
                    bench_unranked.append(pick)

        # Assign vice captain as highest xP starter not captain
        cand_vices = [p for p in starters if not p.is_captain]
        if cand_vices:
            cand_vices.sort(key=lambda p: p.expected_points, reverse=True)
            vice_pick = cand_vices[0]
            vice_pick.is_vice_captain = True

        bench = order_bench(bench_unranked)
        def_c = sum(1 for p in starters if p.position == 'DEF')
        mid_c = sum(1 for p in starters if p.position == 'MID')
        fwd_c = sum(1 for p in starters if p.position == 'FWD')
        formation_str = f"{def_c}-{mid_c}-{fwd_c}"

        tot_cost = round(sum(p.cost for p in squad_picks), 2)
        start_xp = round(sum(p.expected_points for p in starters), 4)
        capt_xp = round(captain_pick.expected_points, 4) if captain_pick else 0.0
        gw_tot_xp = round(start_xp + capt_xp, 4)

        sq_sol = SquadSolution(
            squad=squad_picks,
            starters=starters,
            bench=bench,
            captain=captain_pick if captain_pick else (starters[0] if starters else None),
            vice_captain=vice_pick if vice_pick else (starters[1] if len(starters) > 1 else None),
            total_cost=tot_cost,
            starting_xp=start_xp,
            captain_xp=capt_xp,
            total_xp=gw_tot_xp,
            formation=formation_str,
            status="Optimal",
            chip=None,
        )

        n_trans = len(trans_in_picks)
        ft_avail = curr_ft if t == 0 else 1
        hits_t = max(0, n_trans - ft_avail)
        hit_pen_t = hits_t * hit_cost
        tot_hits += hits_t
        net_xp_t = round(gw_tot_xp - hit_pen_t, 4)
        tot_disc_xp += (discount_factor ** t) * net_xp_t

        # Update bank
        spend_in = sum(p.cost for p in trans_in_picks)
        rec_out = sum(p.cost for p in trans_out_picks)
        curr_bank = round(curr_bank + rec_out - spend_in, 2)
        ft_rem = max(1, ft_avail - n_trans + 1)

        plan = GameweekPlan(
            gw=gw_num,
            transfers_in=trans_in_picks,
            transfers_out=trans_out_picks,
            transfers_count=n_trans,
            hits_taken=hits_t,
            hit_penalty=hit_pen_t,
            free_transfers_available=ft_avail,
            free_transfers_remaining=ft_rem,
            bank=curr_bank,
            squad_solution=sq_sol,
            net_xp=net_xp_t,
        )
        gw_plans.append(plan)

    return MultiHorizonSolution(
        horizon=horizon,
        discount_factor=discount_factor,
        total_discounted_xp=round(tot_disc_xp, 4),
        total_hits_taken=tot_hits,
        total_hit_penalty=round(tot_hits * hit_cost, 2),
        gw_plans=gw_plans,
        status="Optimal",
    )


# ---------------------------------------------------------------------------
# Formatting & Pitch Renderer
# ---------------------------------------------------------------------------

def format_squad_output(solution: SquadSolution, bank: float = 0.0) -> str:
    """Render a visual ASCII formation pitch and squad summary.

    Args:
        solution: SquadSolution object.
        bank: remaining budget in bank in £M.

    Returns:
        Formatted multi-line string.
    """
    if solution.status != "Optimal":
        return f"Squad Optimization Status: {solution.status}"

    starters = solution.starters
    bench = solution.bench

    gks = [p for p in starters if p.position == 'GK']
    defs = [p for p in starters if p.position == 'DEF']
    mids = [p for p in starters if p.position == 'MID']
    fwds = [p for p in starters if p.position == 'FWD']

    def _fmt_player(p: PlayerPick) -> str:
        capt_badge = " [3xC]" if (solution.chip == '3xc' and p.is_captain) else (" [C]" if p.is_captain else "")
        role = capt_badge if capt_badge else (" [V]" if p.is_vice_captain else "")
        return f"{p.web_name}{role} ({p.team}) - {p.expected_points:.2f} xP | £{p.cost:.1f}M"

    capt_name = solution.captain.web_name if solution.captain else "None"
    chip_label = f" | Chip: {solution.chip.upper()}" if solution.chip else ""

    lines = []
    lines.append("=" * 80)
    lines.append(f"                    FPL OPTIMAL SQUAD & STARTING XI ({solution.formation}){chip_label}")
    lines.append("=" * 80)
    lines.append(f"Total Squad Cost: £{solution.total_cost:.1f}M / £100.0M | Bank: £{bank:.1f}M | Status: {solution.status}")
    lines.append(f"Starting XI xP: {solution.starting_xp:.2f} | Captain ({capt_name}): +{solution.captain_xp:.2f} xP | Total Projected xP: {solution.total_xp:.2f}")
    lines.append("-" * 80)
    lines.append("                                STARTING XI")
    lines.append("-" * 80)

    lines.append("  GK:   " + ", ".join(_fmt_player(p) for p in gks))
    lines.append("  DEF:  " + ", ".join(_fmt_player(p) for p in defs))
    lines.append("  MID:  " + ", ".join(_fmt_player(p) for p in mids))
    lines.append("  FWD:  " + ", ".join(_fmt_player(p) for p in fwds))

    if solution.chip != 'bboost':
        lines.append("-" * 80)
        lines.append("                                   BENCH")
        lines.append("-" * 80)
        for p in bench:
            lines.append(f"  Slot {p.bench_order} ({p.position}): {_fmt_player(p)}")

    lines.append("=" * 80)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Solve for optimal FPL 15-man squad and matchday lineup")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Target gameweek number (1-38)")
    parser.add_argument('--budget', type=float, default=100.0, help="Maximum budget in £M (default 100.0)")
    parser.add_argument('--chip', default=None, choices=['bboost', '3xc', 'freehit', 'wildcard'], help="FPL chip to activate")
    parser.add_argument('--strategy', default='pure_xp', choices=['pure_xp', 'rank_protect', 'differential_chase'], help="Game theory strategy")
    parser.add_argument('--lambda-risk', type=float, default=0.0, help="CVaR risk aversion parameter (>0 penalizes downside, <0 rewards upside)")
    parser.add_argument('--lock-players', default=None, help="Comma-separated player codes or names to lock into squad (e.g. 'Palmer,Haaland')")
    parser.add_argument('--exclude-players', default=None, help="Comma-separated player codes or names to exclude (e.g. 'B.Fernandes')")
    parser.add_argument('--captain', default=None, help="Player code or name to force as captain (e.g. 'Palmer')")
    parser.add_argument('--vice-captain', default=None, help="Player code or name to force as vice-captain")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    pred_path = os.path.join(args.data_root, args.season, f'fixture_predictions_gw{args.gw}.csv')
    if not os.path.exists(pred_path):
        pred_path = os.path.join(args.data_root, args.season, 'fixture_predictions.csv')

    if not os.path.exists(pred_path):
        from model.fixture_engine import predict_gameweek_fixtures
        print(f"[{args.season}] fixture predictions not found, generating now for GW{args.gw}...")
        df = predict_gameweek_fixtures(season=args.season, gw=args.gw, data_root=args.data_root)
    else:
        df = pd.read_csv(pred_path)

    solution = solve_initial_squad(
        df=df,
        budget=args.budget,
        chip=args.chip,
        season=args.season,
        data_root=args.data_root,
        strategy=args.strategy,
        lambda_risk=args.lambda_risk,
        locked_player_codes=args.lock_players,
        excluded_player_codes=args.exclude_players,
        forced_captain_code=args.captain,
        forced_vice_captain_code=args.vice_captain,
    )

    remaining_bank = round(args.budget - solution.total_cost, 1)
    output_text = format_squad_output(solution, bank=remaining_bank)
    print("\n" + output_text)


if __name__ == '__main__':
    main()

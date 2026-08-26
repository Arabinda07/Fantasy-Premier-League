"""Dixon-Coles Bivariate Match Simulator & Monte Carlo Simulation Engine.

Provides:
1. Bivariate Dixon-Coles Poisson formulation for exact joint scoreline probabilities P(X=x, Y=y).
2. Low-scoring dependency adjustment factor tau(x, y; rho) for (0,0), (1,0), (0,1), (1,1).
3. Exact discrete matrix calculation (Home Win, Draw, Away Win, Clean Sheets, BTTS, Over/Under 2.5).
4. Vectorized Monte Carlo match engine (10,000 simulations) attributing simulated goals and assists
   via Multinomial sampling over player xG90/xA90 shares.
5. True BPS simulation allocating official 3, 2, 1 bonus points.
6. Player-level probability distributions: Mean xP, Std, Floor (p10), Median (p50), Ceiling (p90),
   and Haul Probability P(Points >= 10).

Usage:
    python -m model.match_simulator [--season 2026-27] [--gw 1] [--sims 10000]
"""
import argparse
from dataclasses import dataclass, field
import math
import os
import sys
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.fixture_engine import (
    load_fixtures_for_gw,
    compute_team_league_averages,
    compute_fixture_multipliers,
    PROMOTED_TEAM_PRIORS,
    DEFAULT_LEAGUE_AVG_XG,
    DEFAULT_LEAGUE_AVG_XGC,
    HOME_ATTACK_FACTOR,
    AWAY_ATTACK_FACTOR,
    HOME_DEFENSE_FACTOR,
    AWAY_DEFENSE_FACTOR,
)
from model.prediction_engine import (
    GOAL_POINTS,
    ASSIST_POINTS,
    CLEAN_SHEET_POINTS,
    _safe_float,
)
from model.build_dataset import build_dataset, load_teams_map


# ---------------------------------------------------------------------------
# Dixon-Coles Parameters & Mathematical Formulations
# ---------------------------------------------------------------------------

DEFAULT_RHO: float = -0.05  # Dixon-Coles low-score correlation parameter
DEFAULT_MAX_GOALS: int = 10  # Max goals per team in discrete grid
DEFAULT_N_SIMS: int = 10000  # Default Monte Carlo iterations


def dixon_coles_tau(x: int, y: int, lambda_h: float, mu_a: float, rho: float = DEFAULT_RHO) -> float:
    """Calculate the Dixon-Coles low-scoring adjustment factor tau(x, y; rho).

    Accounts for the empirical under-representation / over-representation of
    low-scoring matches in football leagues:
        tau(0, 0) = 1 - lambda * mu * rho
        tau(0, 1) = 1 + lambda * rho
        tau(1, 0) = 1 + mu * rho
        tau(1, 1) = 1 - rho
        tau(x, y) = 1.0  for all other (x, y)

    Args:
        x: Home goals (int >= 0).
        y: Away goals (int >= 0).
        lambda_h: Home Poisson intensity parameter (expected goals).
        mu_a: Away Poisson intensity parameter (expected goals).
        rho: Correlation parameter (typically between -0.15 and 0.0, default -0.05).

    Returns:
        Adjustment multiplier float (>= 0.0).
    """
    if x == 0 and y == 0:
        val = 1.0 - (lambda_h * mu_a * rho)
    elif x == 0 and y == 1:
        val = 1.0 + (lambda_h * rho)
    elif x == 1 and y == 0:
        val = 1.0 + (mu_a * rho)
    elif x == 1 and y == 1:
        val = 1.0 - rho
    else:
        val = 1.0
    return max(0.0, float(val))


def compute_dixon_coles_matrix(
    lambda_h: float,
    mu_a: float,
    rho: float = DEFAULT_RHO,
    max_goals: int = DEFAULT_MAX_GOALS,
) -> np.ndarray:
    """Generate exact (max_goals+1) x (max_goals+1) normalized bivariate probability matrix.

    P(X=x, Y=y) = tau(x, y) * Poisson(x; lambda_h) * Poisson(y; mu_a)

    Args:
        lambda_h: Home expected goals.
        mu_a: Away expected goals.
        rho: Dixon-Coles correlation adjustment.
        max_goals: Upper bound for grid dimension (default 10).

    Returns:
        2D numpy array of shape (max_goals + 1, max_goals + 1) normalized to sum to 1.0.
    """
    lambda_h = max(0.01, float(lambda_h))
    mu_a = max(0.01, float(mu_a))

    # Pre-calculate standard 1D Poisson PMFs
    x_range = np.arange(max_goals + 1)
    y_range = np.arange(max_goals + 1)

    p_x = np.array([(math.pow(lambda_h, x) * math.exp(-lambda_h)) / math.factorial(x) for x in x_range])
    p_y = np.array([(math.pow(mu_a, y) * math.exp(-mu_a)) / math.factorial(y) for y in y_range])

    # Outer product: independent Poisson probability grid
    matrix = np.outer(p_x, p_y)

    # Apply Dixon-Coles tau adjustment factors for low scorelines
    for x in range(min(2, max_goals + 1)):
        for y in range(min(2, max_goals + 1)):
            tau = dixon_coles_tau(x, y, lambda_h, mu_a, rho=rho)
            matrix[x, y] *= tau

    # Normalize matrix to strictly conserve total probability = 1.0
    total_p = np.sum(matrix)
    if total_p > 0:
        matrix = matrix / total_p

    return matrix


@dataclass
class MatchProbabilityMetrics:
    """Exact analytical and simulated match outcome probabilities."""
    home_team: str
    away_team: str
    lambda_home: float
    mu_away: float
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    home_clean_sheet_prob: float
    away_clean_sheet_prob: float
    both_teams_to_score_prob: float
    over_2_5_goals_prob: float
    under_2_5_goals_prob: float
    expected_home_goals: float
    expected_away_goals: float
    expected_total_goals: float
    most_likely_scorelines: List[Tuple[str, float]]
    probability_matrix: Optional[np.ndarray] = field(default=None, repr=False)


def analyze_bivariate_scoreline_matrix(
    matrix: np.ndarray,
    home_team: str = "Home",
    away_team: str = "Away",
    lambda_h: float = 1.35,
    mu_a: float = 1.35,
    top_scorelines_count: int = 5,
) -> MatchProbabilityMetrics:
    """Extract full suite of analytical betting, clean sheet, and match metrics from matrix."""
    # Outcome probabilities
    home_win = float(np.sum(np.tril(matrix, -1)))  # x > y (lower triangle where row index > col index)
    draw = float(np.sum(np.diag(matrix)))  # x == y
    away_win = float(np.sum(np.triu(matrix, 1)))  # x < y (upper triangle where row index < col index)

    # Clean Sheet probabilities
    home_clean_sheet = float(np.sum(matrix[:, 0]))  # y = 0 (away scored 0)
    away_clean_sheet = float(np.sum(matrix[0, :]))  # x = 0 (home scored 0)

    # BTTS: x >= 1 and y >= 1
    btts = float(np.sum(matrix[1:, 1:]))

    # Over / Under 2.5 goals
    x_idx, y_idx = np.indices(matrix.shape)
    total_goals_grid = x_idx + y_idx
    over_2_5 = float(np.sum(matrix[total_goals_grid >= 3]))
    under_2_5 = float(np.sum(matrix[total_goals_grid < 3]))

    # Exact expected goals from joint distribution
    exp_h_goals = float(np.sum(matrix * x_idx))
    exp_a_goals = float(np.sum(matrix * y_idx))

    # Ranked most likely scorelines
    scorelines: List[Tuple[str, float]] = []
    flat_indices = np.argsort(matrix.ravel())[::-1]
    for idx in flat_indices[:top_scorelines_count]:
        x = int(idx // matrix.shape[1])
        y = int(idx % matrix.shape[1])
        p = float(matrix[x, y])
        scorelines.append((f"{x}-{y}", round(p, 4)))

    return MatchProbabilityMetrics(
        home_team=home_team,
        away_team=away_team,
        lambda_home=round(lambda_h, 4),
        mu_away=round(mu_a, 4),
        home_win_prob=round(home_win, 4),
        draw_prob=round(draw, 4),
        away_win_prob=round(away_win, 4),
        home_clean_sheet_prob=round(home_clean_sheet, 4),
        away_clean_sheet_prob=round(away_clean_sheet, 4),
        both_teams_to_score_prob=round(btts, 4),
        over_2_5_goals_prob=round(over_2_5, 4),
        under_2_5_goals_prob=round(under_2_5, 4),
        expected_home_goals=round(exp_h_goals, 4),
        expected_away_goals=round(exp_a_goals, 4),
        expected_total_goals=round(exp_h_goals + exp_a_goals, 4),
        most_likely_scorelines=scorelines,
        probability_matrix=matrix,
    )


# ---------------------------------------------------------------------------
# Monte Carlo Player Simulation & True BPS Allocation
# ---------------------------------------------------------------------------

@dataclass
class PlayerSimulationDistribution:
    """Statistical summary of 10,000 Monte Carlo point outcomes for a player."""
    player_code: int
    web_name: str
    team: str
    position: str
    cost: float
    expected_points: float  # Mean (E[xP])
    std_points: float  # Standard deviation
    floor_p10: float  # 10th percentile floor
    median_p50: float  # 50th percentile median
    ceiling_p90: float  # 90th percentile ceiling
    haul_prob: float  # P(Points >= 10)
    expected_goals: float
    expected_assists: float
    expected_clean_sheet: float
    expected_bonus: float


def compute_true_bps_and_bonus(
    player_stats: List[Dict[str, Any]],
    home_gc: int,
    away_gc: int,
    home_clean_sheet: bool,
    away_clean_sheet: bool,
) -> Dict[int, int]:
    """Calculate match True BPS score and allocate official 3, 2, 1 bonus points.

    BPS Point Rules:
    - Goal: FWD/MID +24, DEF/GK +12
    - Assist: +9
    - Clean Sheet (60+ mins): GK/DEF +12
    - Saves: +2 per save (GK)
    - Playing 60+ mins: +6, 1-59 mins: +3
    - Defensive Contributions (DC/Tackles/CBI): +1 per DC
    - Goals Conceded: -4 if >= 2 GC (GK/DEF with 60+ mins)
    - Yellow Card: -3, Red Card: -9, Own Goal: -6

    Returns:
        Mapping of player_code -> bonus points awarded (0, 1, 2, or 3).
    """
    bps_scores: List[Tuple[int, float]] = []

    for p in player_stats:
        p_code = p['player_code']
        pos = p['position']
        is_home = p['is_home']
        mins_played = p.get('mins_played', 90)
        if mins_played <= 0:
            continue

        bps = 0.0

        # Minutes played BPS
        if mins_played >= 60:
            bps += 6.0
        elif mins_played > 0:
            bps += 3.0

        # Goals scored BPS
        goals = p.get('goals', 0)
        if goals > 0:
            bps += goals * (12.0 if pos in ('GK', 'DEF') else 24.0)

        # Assists BPS
        assists = p.get('assists', 0)
        if assists > 0:
            bps += assists * 9.0

        # Clean Sheet BPS
        cs = home_clean_sheet if is_home else away_clean_sheet
        if cs and pos in ('GK', 'DEF') and mins_played >= 60:
            bps += 12.0

        # Goals Conceded BPS deduction
        gc = away_gc if is_home else home_gc
        if gc >= 2 and pos in ('GK', 'DEF') and mins_played >= 60:
            bps -= 4.0

        # Saves BPS (GK)
        saves = p.get('saves', 0)
        if saves > 0 and pos == 'GK':
            bps += saves * 2.0

        # Defensive contribution BPS
        dc = p.get('dc', 0)
        bps += dc * 1.0

        # Discipline
        yc = p.get('yc', 0)
        rc = p.get('rc', 0)
        bps -= (yc * 3.0 + rc * 9.0)

        bps_scores.append((p_code, bps))

    # Rank by BPS descending
    bps_scores.sort(key=lambda x: x[1], reverse=True)

    bonus_awards: Dict[int, int] = {p['player_code']: 0 for p in player_stats}
    if not bps_scores:
        return bonus_awards

    # Distinct BPS score tiers for official tie handling
    unique_bps = sorted(list(set(b for _, b in bps_scores)), reverse=True)
    if not unique_bps:
        return bonus_awards

    first_tier = [code for code, b in bps_scores if b == unique_bps[0]]
    for code in first_tier:
        bonus_awards[code] = 3

    if len(first_tier) == 1 and len(unique_bps) > 1:
        second_tier = [code for code, b in bps_scores if b == unique_bps[1]]
        for code in second_tier:
            bonus_awards[code] = 2

        if len(second_tier) == 1 and len(unique_bps) > 2:
            third_tier = [code for code, b in bps_scores if b == unique_bps[2]]
            for code in third_tier:
                bonus_awards[code] = 1
    elif len(first_tier) == 2 and len(unique_bps) > 1:
        second_tier = [code for code, b in bps_scores if b == unique_bps[1]]
        for code in second_tier:
            bonus_awards[code] = 1

    return bonus_awards


def simulate_match_monte_carlo(
    home_team: str,
    away_team: str,
    home_players: List[Dict[str, Any]],
    away_players: List[Dict[str, Any]],
    lambda_h: float,
    mu_a: float,
    rho: float = DEFAULT_RHO,
    n_sims: int = DEFAULT_N_SIMS,
    random_seed: Optional[int] = 42,
) -> Tuple[MatchProbabilityMetrics, List[PlayerSimulationDistribution]]:
    """Simulate a single Premier League fixture N times to generate exact distributions.

    Args:
        home_team: Name of home team.
        away_team: Name of away team.
        home_players: List of dicts with player rates (player_code, web_name, pos, xg90, xa90, etc.)
        away_players: List of dicts with player rates.
        lambda_h: Poisson intensity for home team.
        mu_a: Poisson intensity for away team.
        rho: Dixon-Coles correlation parameter.
        n_sims: Number of Monte Carlo iterations (default 10,000).
        random_seed: Random seed for deterministic reproducibility.

    Returns:
        Tuple of (MatchProbabilityMetrics, List of PlayerSimulationDistribution).
    """
    # F-15 fix: use isolated Generator instead of legacy global np.random.seed
    rng = np.random.default_rng(random_seed)

    # 1. Compute exact Dixon-Coles bivariate probability grid
    matrix = compute_dixon_coles_matrix(lambda_h, mu_a, rho=rho, max_goals=DEFAULT_MAX_GOALS)
    match_metrics = analyze_bivariate_scoreline_matrix(
        matrix=matrix,
        home_team=home_team,
        away_team=away_team,
        lambda_h=lambda_h,
        mu_a=mu_a,
    )

    # 2. Flatten matrix into 1D categorical distribution for fast O(N) scoreline sampling
    flat_probs = matrix.ravel()
    flat_probs = flat_probs / np.sum(flat_probs)
    n_states = len(flat_probs)
    sampled_indices = rng.choice(n_states, size=n_sims, p=flat_probs)

    dim_y = matrix.shape[1]
    sim_home_goals = sampled_indices // dim_y
    sim_away_goals = sampled_indices % dim_y

    all_players = []
    for p in home_players:
        cp = dict(p)
        cp['is_home'] = True
        all_players.append(cp)
    for p in away_players:
        cp = dict(p)
        cp['is_home'] = False
        all_players.append(cp)

    # Prepare player attribution weight vectors
    def get_attribution_weights(players: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        xg_weights = np.array([
            max(0.001, _safe_float(p.get('xg90', p.get('long_form_expected_goals_90', 0.0))) * _safe_float(p.get('active_ratio', 0.85)))
            for p in players
        ])
        xa_weights = np.array([
            max(0.001, _safe_float(p.get('xa90', p.get('long_form_expected_assists_90', 0.0))) * _safe_float(p.get('active_ratio', 0.85)))
            for p in players
        ])
        p_start_weights = np.array([_safe_float(p.get('p_start', 0.85)) for p in players])

        xg_weights = xg_weights / np.sum(xg_weights) if np.sum(xg_weights) > 0 else np.ones(len(players)) / len(players)
        xa_weights = xa_weights / np.sum(xa_weights) if np.sum(xa_weights) > 0 else np.ones(len(players)) / len(players)
        return xg_weights, xa_weights, p_start_weights

    h_xg_w, h_xa_w, h_start_w = get_attribution_weights(home_players) if home_players else (np.array([]), np.array([]), np.array([]))
    a_xg_w, a_xa_w, a_start_w = get_attribution_weights(away_players) if away_players else (np.array([]), np.array([]), np.array([]))

    # Pre-allocate simulation point arrays
    player_sim_points: Dict[int, np.ndarray] = {p['player_code']: np.zeros(n_sims, dtype=np.float64) for p in all_players}
    player_sim_goals: Dict[int, np.ndarray] = {p['player_code']: np.zeros(n_sims, dtype=np.int32) for p in all_players}
    player_sim_assists: Dict[int, np.ndarray] = {p['player_code']: np.zeros(n_sims, dtype=np.int32) for p in all_players}
    player_sim_cs: Dict[int, np.ndarray] = {p['player_code']: np.zeros(n_sims, dtype=np.int32) for p in all_players}
    player_sim_bonus: Dict[int, np.ndarray] = {p['player_code']: np.zeros(n_sims, dtype=np.int32) for p in all_players}

    # 3. Simulate match events per iteration
    for s in range(n_sims):
        h_goals = int(sim_home_goals[s])
        a_goals = int(sim_away_goals[s])

        h_clean_sheet = (a_goals == 0)
        a_clean_sheet = (h_goals == 0)

        # Track per-player events in this simulation
        sim_stat_map: Dict[int, Dict[str, Any]] = {}
        for p in all_players:
            sim_stat_map[p['player_code']] = {
                'player_code': p['player_code'],
                'position': p['position'],
                'is_home': p['is_home'],
                'mins_played': 90 if rng.random() < _safe_float(p.get('p_start', 0.85)) else (20 if rng.random() < _safe_float(p.get('p_app', 0.15)) else 0),
                'goals': 0,
                'assists': 0,
                'saves': 0,
                'dc': rng.poisson(max(0.1, _safe_float(p.get('dc90', 2.0)) * 0.8)),
                'yc': 1 if rng.random() < _safe_float(p.get('yc90', 0.12)) else 0,
                'rc': 1 if rng.random() < _safe_float(p.get('rc90', 0.01)) else 0,
            }

        # Attribute Home Goals & Assists
        if h_goals > 0 and len(home_players) > 0:
            scorers = rng.choice(len(home_players), size=h_goals, p=h_xg_w)
            for sc_idx in scorers:
                p_code = home_players[sc_idx]['player_code']
                sim_stat_map[p_code]['goals'] += 1
                player_sim_goals[p_code][s] += 1

                # Assist attribution (75% of goals are assisted)
                if rng.random() < 0.75 and len(home_players) > 1:
                    temp_xa = h_xa_w.copy()
                    temp_xa[sc_idx] = 0.0
                    sum_xa = np.sum(temp_xa)
                    if sum_xa > 0:
                        temp_xa /= sum_xa
                        as_idx = rng.choice(len(home_players), p=temp_xa)
                        as_code = home_players[as_idx]['player_code']
                        sim_stat_map[as_code]['assists'] += 1
                        player_sim_assists[as_code][s] += 1

        # Attribute Away Goals & Assists
        if a_goals > 0 and len(away_players) > 0:
            scorers = rng.choice(len(away_players), size=a_goals, p=a_xg_w)
            for sc_idx in scorers:
                p_code = away_players[sc_idx]['player_code']
                sim_stat_map[p_code]['goals'] += 1
                player_sim_goals[p_code][s] += 1

                # Assist attribution
                if rng.random() < 0.75 and len(away_players) > 1:
                    temp_xa = a_xa_w.copy()
                    temp_xa[sc_idx] = 0.0
                    sum_xa = np.sum(temp_xa)
                    if sum_xa > 0:
                        temp_xa /= sum_xa
                        as_idx = np.random.choice(len(away_players), p=temp_xa)
                        as_code = away_players[as_idx]['player_code']
                        sim_stat_map[as_code]['assists'] += 1
                        player_sim_assists[as_code][s] += 1

        # Goalkeeper saves
        for p in all_players:
            if p['position'] == 'GK':
                opp_shots = a_goals if p['is_home'] else h_goals
                saves = max(0, int(np.random.poisson(2.5 + opp_shots * 0.5)))
                sim_stat_map[p['player_code']]['saves'] = saves

        # Compute match BPS and bonus points
        bonus_awarded = compute_true_bps_and_bonus(
            player_stats=list(sim_stat_map.values()),
            home_gc=a_goals,
            away_gc=h_goals,
            home_clean_sheet=h_clean_sheet,
            away_clean_sheet=a_clean_sheet,
        )

        # Calculate exact FPL match points for each player
        for p in all_players:
            p_code = p['player_code']
            pos = p['position']
            is_home = p['is_home']
            p_stat = sim_stat_map[p_code]
            mins = p_stat['mins_played']

            if mins <= 0:
                player_sim_points[p_code][s] = 0.0
                continue

            pts = 0.0
            # Appearance
            pts += 2.0 if mins >= 60 else 1.0

            # Goals
            g = p_stat['goals']
            pts += g * GOAL_POINTS.get(pos, 4.0)

            # Assists
            a = p_stat['assists']
            pts += a * ASSIST_POINTS

            # Clean Sheet
            cs = h_clean_sheet if is_home else a_clean_sheet
            if cs and mins >= 60:
                pts += CLEAN_SHEET_POINTS.get(pos, 0.0)
                player_sim_cs[p_code][s] = 1

            # Goals Conceded deduction (-1 per 2 GC beyond 1)
            gc = a_goals if is_home else h_goals
            if gc >= 2 and pos in ('GK', 'DEF') and mins >= 60:
                pts -= (gc // 2)

            # Saves (GK: +1 per 3 saves)
            if pos == 'GK':
                pts += (p_stat['saves'] // 3)

            # Cards
            pts -= (p_stat['yc'] * 1.0 + p_stat['rc'] * 3.0)

            # Bonus Points
            b = bonus_awarded.get(p_code, 0)
            pts += b
            player_sim_bonus[p_code][s] += b

            player_sim_points[p_code][s] = pts

    # 4. Summarize statistical distributions
    player_distributions: List[PlayerSimulationDistribution] = []
    for p in all_players:
        p_code = p['player_code']
        pts_arr = player_sim_points[p_code]

        dist = PlayerSimulationDistribution(
            player_code=p_code,
            web_name=p['web_name'],
            team=p['team'],
            position=p['position'],
            cost=_safe_float(p.get('cost', 5.0)),
            expected_points=round(float(np.mean(pts_arr)), 2),
            std_points=round(float(np.std(pts_arr)), 2),
            floor_p10=round(float(np.percentile(pts_arr, 10)), 1),
            median_p50=round(float(np.percentile(pts_arr, 50)), 1),
            ceiling_p90=round(float(np.percentile(pts_arr, 90)), 1),
            haul_prob=round(float(np.mean(pts_arr >= 10.0)), 3),
            expected_goals=round(float(np.mean(player_sim_goals[p_code])), 3),
            expected_assists=round(float(np.mean(player_sim_assists[p_code])), 3),
            expected_clean_sheet=round(float(np.mean(player_sim_cs[p_code])), 3),
            expected_bonus=round(float(np.mean(player_sim_bonus[p_code])), 3),
        )
        player_distributions.append(dist)

    # Sort descending by expected points
    player_distributions.sort(key=lambda x: x.expected_points, reverse=True)

    return match_metrics, player_distributions


# ---------------------------------------------------------------------------
# Gameweek Simulation Orchestrator
# ---------------------------------------------------------------------------

def simulate_gameweek_fixtures(
    season: str = '2026-27',
    gw: int = 1,
    n_sims: int = DEFAULT_N_SIMS,
    data_root: str = 'data',
    rho: float = DEFAULT_RHO,
    save_csv: bool = True,
) -> Dict[str, Any]:
    """Simulate all Premier League fixtures in a gameweek using the Dixon-Coles engine.

    Args:
        season: Season string (e.g. '2026-27').
        gw: Gameweek integer (1-38).
        n_sims: Number of Monte Carlo runs per fixture.
        data_root: Root data directory.
        rho: Dixon-Coles low-score parameter.
        save_csv: Whether to save simulated output to disk.

    Returns:
        Dict containing list of match metrics and aggregated player predictions dataframe.
    """
    season_dir = os.path.join(data_root, season)
    fixtures = load_fixtures_for_gw(season=season, gw=gw, data_root=data_root)
    if not fixtures:
        print(f"[!] No fixtures found for {season} GW{gw}")
        return {'match_metrics': [], 'player_distributions': pd.DataFrame()}

    # Load player dataset for the season
    dataset_df = build_dataset(season=season, data_root=data_root)
    if dataset_df.empty:
        print(f"[!] No player data found for {season}")
        return {'match_metrics': [], 'player_distributions': pd.DataFrame()}

    # Load team strengths map
    team_stats_map: Dict[str, Dict[str, float]] = {}
    for team_name in dataset_df['team'].dropna().unique():
        team_rows = dataset_df[dataset_df['team'] == team_name]
        if team_rows.empty:
            continue
        first_row = team_rows.iloc[0]
        t_long_xg = _safe_float(first_row.get('team_long_form_xg90'), DEFAULT_LEAGUE_AVG_XG)
        t_short_xg = _safe_float(first_row.get('team_short_form_xg90'), t_long_xg)
        t_long_xgc = _safe_float(first_row.get('team_long_form_xgc90'), DEFAULT_LEAGUE_AVG_XGC)
        t_short_xgc = _safe_float(first_row.get('team_short_form_xgc90'), t_long_xgc)
        team_stats_map[team_name] = {
            'xg90': (t_short_xg * 0.35 + t_long_xg * 0.65),
            'xgc90': (t_short_xgc * 0.35 + t_long_xgc * 0.65),
        }

    league_avg_xg, league_avg_xgc = compute_team_league_averages(team_stats_map)

    all_match_metrics: List[MatchProbabilityMetrics] = []
    all_player_dists: List[PlayerSimulationDistribution] = []

    print(f"\n[*] Simulating {len(fixtures)} fixtures for {season} GW{gw} ({n_sims:,} Monte Carlo runs each)...")

    for f in fixtures:
        h_team = f['home_team']
        a_team = f['away_team']

        # Calculate lambda (home expected goals) and mu (away expected goals)
        h_mults = compute_fixture_multipliers(
            team_name=h_team,
            opponent_name=a_team,
            is_home=True,
            team_stats_map=team_stats_map,
            league_avg_xg=league_avg_xg,
            league_avg_xgc=league_avg_xgc,
        )
        a_mults = compute_fixture_multipliers(
            team_name=a_team,
            opponent_name=h_team,
            is_home=False,
            team_stats_map=team_stats_map,
            league_avg_xg=league_avg_xg,
            league_avg_xgc=league_avg_xgc,
        )

        h_xg90 = team_stats_map.get(h_team, PROMOTED_TEAM_PRIORS)['xg90']
        a_xg90 = team_stats_map.get(a_team, PROMOTED_TEAM_PRIORS)['xg90']

        lambda_h = h_xg90 * h_mults['attack_mult']
        mu_a = a_xg90 * a_mults['attack_mult']

        # Gather players
        h_p_df = dataset_df[dataset_df['team'] == h_team]
        a_p_df = dataset_df[dataset_df['team'] == a_team]

        h_players = h_p_df.to_dict('records')
        a_players = a_p_df.to_dict('records')

        m_metrics, p_dists = simulate_match_monte_carlo(
            home_team=h_team,
            away_team=a_team,
            home_players=h_players,
            away_players=a_players,
            lambda_h=lambda_h,
            mu_a=mu_a,
            rho=rho,
            n_sims=n_sims,
        )

        all_match_metrics.append(m_metrics)
        all_player_dists.extend(p_dists)

    # Convert player distributions to DataFrame
    dist_df = pd.DataFrame([asdict(p) for p in all_player_dists] if all_player_dists else [])
    if not dist_df.empty:
        dist_df.sort_values('expected_points', ascending=False, inplace=True)

    if save_csv and not dist_df.empty:
        out_csv = os.path.join(season_dir, f'simulated_predictions_gw{gw}.csv')
        dist_df.to_csv(out_csv, index=False)
        print(f"[+] Saved simulated projections ({len(dist_df)} players) to {out_csv}")

    return {
        'match_metrics': all_match_metrics,
        'player_distributions': dist_df,
    }


def asdict(obj: Any) -> Dict[str, Any]:
    """Helper to convert dataclass or object to dictionary."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: getattr(obj, k) for k in obj.__dataclass_fields__}
    return dict(obj)


def main():
    parser = argparse.ArgumentParser(description="Dixon-Coles Bivariate Match Simulator & Monte Carlo Engine")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Target gameweek number")
    parser.add_argument('--sims', type=int, default=10000, help="Number of Monte Carlo simulations per match")
    parser.add_argument('--rho', type=float, default=DEFAULT_RHO, help="Dixon-Coles correlation parameter")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    results = simulate_gameweek_fixtures(
        season=args.season,
        gw=args.gw,
        n_sims=args.sims,
        data_root=args.data_root,
        rho=args.rho,
    )

    print("\n" + "=" * 80)
    print(f"       DIXON-COLES MATCH SIMULATION SUMMARY -- {args.season} GAMEWEEK {args.gw}")
    print("=" * 80)
    for m in results['match_metrics']:
        print(f"{m.home_team:<16} vs {m.away_team:<16} | Exp: {m.expected_home_goals:.2f} - {m.expected_away_goals:.2f} | W/D/L: {m.home_win_prob*100:.0f}% / {m.draw_prob*100:.0f}% / {m.away_win_prob*100:.0f}% | CS: {m.home_clean_sheet_prob*100:.0f}% / {m.away_clean_sheet_prob*100:.0f}%")
        top_scores = ", ".join([f"{s} ({p*100:.1f}%)" for s, p in m.most_likely_scorelines[:3]])
        print(f"  * Top Scorelines: {top_scores}")

    df = results['player_distributions']
    if not df.empty:
        print("\n" + "-" * 80)
        print("TOP 10 PROJECTED PLAYERS (MONTE CARLO DISTRIBUTIONS):")
        print("-" * 80)
        top10 = df.head(10)
        for _, r in top10.iterrows():
            wname = str(r['web_name']).encode('ascii', 'replace').decode('ascii')
            tname = str(r['team']).encode('ascii', 'replace').decode('ascii')
            print(f"  * {r['position']:<3} | {wname:<18} ({tname:<14}) | Mean: {r['expected_points']:>4.2f} xP | Floor (p10): {r['floor_p10']:>4.1f} | Med (p50): {r['median_p50']:>4.1f} | Ceil (p90): {r['ceiling_p90']:>4.1f} | Haul P(>=10): {r['haul_prob']*100:>4.1f}%")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()

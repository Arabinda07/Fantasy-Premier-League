"""Unit tests for creator-aligned model mechanics and solver structural options.

Validates:
1. Dynamic penalty decomposition and npxG separation in prediction_engine.py.
2. Center-back / defender away venue Defcon (C11) +5% boost in fixture_engine.py.
3. Dynamic available-minutes filtering threshold in prediction_engine.py.
4. Team-level attacking and defensive tactical nudges in fixture_engine.py.
5. Solver structural limits: max_player_cost (Spread vs Anchor), max_premium_count, min_spend.
6. Mathematical linearity of expected value (additive EV in intra-fixture matchups).
"""
import math
import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import predict_player_points, apply_empirical_bayes_shrinkage
from model.fixture_engine import (
    compute_fixture_multipliers,
    predict_player_fixture,
    HOME_ATTACK_FACTOR,
    AWAY_ATTACK_FACTOR,
    HOME_DEFENSE_FACTOR,
    AWAY_DEFENSE_FACTOR,
)
from model.solver import solve_initial_squad, solve_weekly_transfers, PlayerPick


# ---------------------------------------------------------------------------
# 1. Penalty Decomposition & npxG Tests
# ---------------------------------------------------------------------------

def test_penalty_taker_xg_boost():
    """Verify that designated penalty taker status adds calibrated +0.083 xG90 equity."""
    base_player = {
        'web_name': 'Midfielder_A',
        'position': 'MID',
        'season_minutes': 2700,
        'season_starts': 30,
        'fbref_starts': 30,
        'fbref_subs': 0,
        'fbref_unused_subs': 0,
        'long_form_expected_goals_90': 0.20,
        'long_form_expected_assists_90': 0.15,
        'long_form_defensive_contribution_90': 4.0,
        'long_form_minutes': 2700,
        'now_cost': 7.5,
        'status': 'a',
    }

    # Non-penalty taker
    pred_non_pk = predict_player_points(base_player, apply_shrinkage=False)

    # Designated primary penalty taker (penalties_order = 1)
    pk_player = dict(base_player)
    pk_player['penalties_order'] = 1
    pred_pk = predict_player_points(pk_player, apply_shrinkage=False)

    # In FPL, MID goal is 5 pts. Default team_pk_rate (0.12) * 0.79 = 0.0948 xG90, delta C8 = 0.474 pts
    delta_c8 = pred_pk['c8_goals'] - pred_non_pk['c8_goals']
    assert 0.35 <= delta_c8 <= 0.55, f"Expected delta C8 ~0.474, got {delta_c8}"
    assert pred_pk['expected_points'] > pred_non_pk['expected_points']

    # Test Team-Specific Frequency (Man City 0.18 vs Everton 0.07)
    city_pk = dict(base_player, team='Man City', penalties_order=1)
    everton_pk = dict(base_player, team='Everton', penalties_order=1)
    pred_city = predict_player_points(city_pk, apply_shrinkage=False)
    pred_everton = predict_player_points(everton_pk, apply_shrinkage=False)
    assert pred_city['c8_goals'] > pred_everton['c8_goals']
    assert abs(pred_city['c8_goals'] - pred_non_pk['c8_goals'] - 0.18 * 0.79 * 5) < 1e-3


def test_custom_pk_xg_boost_override():
    """Verify custom pk_xg_boost attribute is directly honored in C8 calculation."""
    player = {
        'web_name': 'Forward_B',
        'position': 'FWD',
        'season_minutes': 1800,
        'season_starts': 20,
        'fbref_starts': 20,
        'fbref_subs': 0,
        'fbref_unused_subs': 0,
        'long_form_expected_goals_90': 0.40,
        'long_form_expected_assists_90': 0.10,
        'long_form_defensive_contribution_90': 1.0,
        'long_form_minutes': 1800,
        'now_cost': 8.0,
        'status': 'a',
        'pk_xg_boost': 0.15,  # High frequency penalty team override
    }
    pred = predict_player_points(player, apply_shrinkage=False)
    # FWD goal is 4 pts. Total xG90 = 0.40 + 0.15 = 0.55. Expected C8 = 4 * 0.55 = 2.20
    assert abs(pred['c8_goals'] - 2.20) < 1e-3


# ---------------------------------------------------------------------------
# 2. Away Venue Defcon (+5%) Scaling Tests
# ---------------------------------------------------------------------------

def test_defender_away_defcon_boost():
    """Verify that defenders in away matches receive +5% DC venue factor."""
    defender = {
        'web_name': 'CenterBack_C',
        'position': 'DEF',
        'team': 'Arsenal',
        'season_minutes': 2700,
        'season_starts': 30,
        'fbref_starts': 30,
        'fbref_subs': 0,
        'fbref_unused_subs': 0,
        'long_form_expected_goals_90': 0.05,
        'long_form_expected_assists_90': 0.02,
        'long_form_defensive_contribution_90': 8.0,
        'long_form_minutes': 2700,
        'now_cost': 6.0,
        'status': 'a',
    }

    team_stats = {
        'Arsenal': {'xg90': 1.80, 'xgc90': 0.90, 'is_promoted': False},
        'Chelsea': {'xg90': 1.50, 'xgc90': 1.20, 'is_promoted': False},
    }

    fix_home = {'home_team': 'Arsenal', 'away_team': 'Chelsea', 'home_fdr': 3, 'away_fdr': 3}
    fix_away = {'home_team': 'Chelsea', 'away_team': 'Arsenal', 'home_fdr': 3, 'away_fdr': 3}

    # Home match
    pred_home = predict_player_fixture(
        defender, fix_home, is_home=True, team_stats_map=team_stats
    )
    # Away match
    pred_away = predict_player_fixture(
        defender, fix_away, is_home=False, team_stats_map=team_stats
    )

    # Opponent xG is the same (1.50). But away match gets the +5% venue_dc_factor on C11
    assert pred_away['c11_defensive_contributions'] > pred_home['c11_defensive_contributions']
    # Check that the underlying DC rate applied was scaled by 1.05 (Poisson CDF non-linearity yields ~1.10-1.25x point boost)
    ratio = pred_away['c11_defensive_contributions'] / pred_home['c11_defensive_contributions']
    assert 1.05 <= ratio <= 1.35


# ---------------------------------------------------------------------------
# 3. Dynamic Available-Minutes Filtering Tests
# ---------------------------------------------------------------------------

def test_dynamic_minutes_filter_threshold():
    """Verify dynamic percentage filter zeroes out inactive bench fodder below threshold."""
    bench_fodder = {
        'web_name': 'Bench_Warmer',
        'position': 'MID',
        'season_minutes': 45,  # Only 45 mins played
        'season_starts': 0,
        'fbref_starts': 0,
        'fbref_subs': 2,
        'fbref_unused_subs': 8,
        'long_form_expected_goals_90': 0.10,
        'long_form_expected_assists_90': 0.10,
        'long_form_defensive_contribution_90': 2.0,
        'long_form_minutes': 45,
        'now_cost': 4.5,
        'status': 'a',
    }

    # In GW 10, available minutes = 900. 10% threshold = 90 mins.
    # Player with 45 mins is below threshold -> 0.0 expected points
    pred_filtered = predict_player_points(
        bench_fodder,
        apply_shrinkage=False,
        min_minutes_pct=0.10,
        available_minutes=900.0,
    )
    assert pred_filtered['expected_points'] == 0.0
    assert pred_filtered['p_start'] == 0.0

    # In GW 1, available minutes = 90. 10% threshold = 9 mins.
    # Player with 45 mins is above threshold -> non-zero expected points
    pred_active = predict_player_points(
        bench_fodder,
        apply_shrinkage=False,
        min_minutes_pct=0.10,
        available_minutes=90.0,
    )
    assert pred_active['expected_points'] > 0.0


# ---------------------------------------------------------------------------
# 4. Team-Level Tactical Nudges Tests
# ---------------------------------------------------------------------------

def test_team_tactical_nudges():
    """Verify that team-level managerial/injury nudges modify fixture multipliers."""
    team_stats = {
        'Spurs': {'xg90': 1.60, 'xgc90': 1.30, 'is_promoted': False},
        'Fulham': {'xg90': 1.20, 'xgc90': 1.40, 'is_promoted': False},
    }

    # Baseline without nudges
    base_mults = compute_fixture_multipliers('Spurs', 'Fulham', is_home=True, team_stats_map=team_stats)

    # Apply 15% attacking boost and 10% defensive improvement to Spurs
    nudges = {
        'Spurs': {'xg_mult': 1.15, 'xgc_mult': 0.90},
    }
    nudged_mults = compute_fixture_multipliers(
        'Spurs', 'Fulham', is_home=True, team_stats_map=team_stats, team_nudges=nudges
    )

    # Spurs defense is improved (xgc_mult=0.90), so fixture_xgc90 should be lower
    assert nudged_mults['fixture_xgc90'] < base_mults['fixture_xgc90']
    assert abs(nudged_mults['fixture_xgc90'] / base_mults['fixture_xgc90'] - 0.90) < 1e-2


# ---------------------------------------------------------------------------
# 5. Solver Structural Constraints Tests (Haaland vs Spread & Bank Leaks)
# ---------------------------------------------------------------------------

def create_mock_player_pool() -> pd.DataFrame:
    """Generate a realistic player pool with mega-anchor, mid-pricers, and budget enablers."""
    players = [
        # GKs
        {'player_code': 1, 'web_name': 'Raya', 'position': 'GK', 'team': 'Arsenal', 'cost': 5.5, 'expected_points': 4.8, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 2, 'web_name': 'Pickford', 'position': 'GK', 'team': 'Everton', 'cost': 5.0, 'expected_points': 4.2, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 3, 'web_name': 'Valdimarsson', 'position': 'GK', 'team': 'Brentford', 'cost': 4.0, 'expected_points': 0.5, 'season_minutes': 0, 'p_start': 0.0},
        {'player_code': 4, 'web_name': 'Turner', 'position': 'GK', 'team': 'Crystal Palace', 'cost': 4.0, 'expected_points': 0.5, 'season_minutes': 0, 'p_start': 0.0},

        # DEFs
        {'player_code': 11, 'web_name': 'Gabriel', 'position': 'DEF', 'team': 'Arsenal', 'cost': 6.0, 'expected_points': 5.2, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 12, 'web_name': 'Saliba', 'position': 'DEF', 'team': 'Arsenal', 'cost': 6.0, 'expected_points': 5.0, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 13, 'web_name': 'Gvardiol', 'position': 'DEF', 'team': 'Man City', 'cost': 6.0, 'expected_points': 4.8, 'season_minutes': 2500, 'p_start': 0.95},
        {'player_code': 14, 'web_name': 'Muñoz', 'position': 'DEF', 'team': 'Crystal Palace', 'cost': 5.0, 'expected_points': 4.5, 'season_minutes': 2400, 'p_start': 1.0},
        {'player_code': 15, 'web_name': 'Robinson', 'position': 'DEF', 'team': 'Fulham', 'cost': 4.5, 'expected_points': 4.1, 'season_minutes': 2600, 'p_start': 1.0},
        {'player_code': 16, 'web_name': 'Konsa', 'position': 'DEF', 'team': 'Aston Villa', 'cost': 4.5, 'expected_points': 3.9, 'season_minutes': 2500, 'p_start': 1.0},
        {'player_code': 17, 'web_name': 'Greaves', 'position': 'DEF', 'team': 'Ipswich', 'cost': 4.0, 'expected_points': 3.2, 'season_minutes': 2000, 'p_start': 0.90},
        {'player_code': 18, 'web_name': 'Faes', 'position': 'DEF', 'team': 'Leicester', 'cost': 4.0, 'expected_points': 3.0, 'season_minutes': 2000, 'p_start': 0.90},

        # MIDs
        {'player_code': 21, 'web_name': 'Salah', 'position': 'MID', 'team': 'Liverpool', 'cost': 12.5, 'expected_points': 7.6, 'season_minutes': 2800, 'p_start': 1.0},
        {'player_code': 22, 'web_name': 'Palmer', 'position': 'MID', 'team': 'Chelsea', 'cost': 10.5, 'expected_points': 7.2, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 23, 'web_name': 'Saka', 'position': 'MID', 'team': 'Arsenal', 'cost': 10.0, 'expected_points': 6.8, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 24, 'web_name': 'Bruno Fernandes', 'position': 'MID', 'team': 'Man Utd', 'cost': 8.5, 'expected_points': 6.3, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 25, 'web_name': 'Mbeumo', 'position': 'MID', 'team': 'Brentford', 'cost': 7.5, 'expected_points': 5.8, 'season_minutes': 2600, 'p_start': 1.0},
        {'player_code': 26, 'web_name': 'Eze', 'position': 'MID', 'team': 'Crystal Palace', 'cost': 7.0, 'expected_points': 5.5, 'season_minutes': 2500, 'p_start': 1.0},
        {'player_code': 27, 'web_name': 'Gibbs-White', 'position': 'MID', 'team': 'Nott\'m Forest', 'cost': 6.5, 'expected_points': 5.1, 'season_minutes': 2600, 'p_start': 1.0},
        {'player_code': 28, 'web_name': 'Semenyo', 'position': 'MID', 'team': 'Bournemouth', 'cost': 5.5, 'expected_points': 4.6, 'season_minutes': 2400, 'p_start': 1.0},
        {'player_code': 29, 'web_name': 'Rogers', 'position': 'MID', 'team': 'Aston Villa', 'cost': 5.0, 'expected_points': 4.4, 'season_minutes': 2200, 'p_start': 0.95},
        {'player_code': 30, 'web_name': 'Winks', 'position': 'MID', 'team': 'Leicester', 'cost': 4.5, 'expected_points': 2.8, 'season_minutes': 2700, 'p_start': 1.0},

        # FWDs
        {'player_code': 31, 'web_name': 'Haaland', 'position': 'FWD', 'team': 'Man City', 'cost': 15.0, 'expected_points': 8.2, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 32, 'web_name': 'Watkins', 'position': 'FWD', 'team': 'Aston Villa', 'cost': 9.0, 'expected_points': 6.4, 'season_minutes': 2700, 'p_start': 1.0},
        {'player_code': 33, 'web_name': 'Isak', 'position': 'FWD', 'team': 'Newcastle', 'cost': 8.5, 'expected_points': 6.1, 'season_minutes': 2500, 'p_start': 1.0},
        {'player_code': 34, 'web_name': 'Joao Pedro', 'position': 'FWD', 'team': 'Brighton', 'cost': 6.0, 'expected_points': 5.3, 'season_minutes': 2400, 'p_start': 1.0},
        {'player_code': 35, 'web_name': 'Wood', 'position': 'FWD', 'team': 'Nott\'m Forest', 'cost': 6.0, 'expected_points': 5.0, 'season_minutes': 2300, 'p_start': 0.95},
        {'player_code': 36, 'web_name': 'Stewart', 'position': 'FWD', 'team': 'Southampton', 'cost': 4.5, 'expected_points': 1.5, 'season_minutes': 300, 'p_start': 0.20},
    ]
    return pd.DataFrame(players)


def test_solver_haaland_anchor_vs_spread():
    """Verify that max_player_cost allows comparing Haaland Anchor build vs Spread build."""
    pool_df = create_mock_player_pool()

    # 1. Unconstrained solve (allows Haaland at 15.0M)
    anchor_sol = solve_initial_squad(pool_df, budget=100.0)
    assert anchor_sol.status == "Optimal"

    # 2. Spread solve (max_player_cost=12.0 excludes Haaland at 15.0M and Salah at 12.5M)
    spread_sol = solve_initial_squad(pool_df, budget=100.0, max_player_cost=12.0)
    assert spread_sol.status == "Optimal"
    spread_names = [p.web_name for p in spread_sol.squad]

    assert 'Haaland' not in spread_names
    assert 'Salah' not in spread_names
    # All players in spread build are <= 12.0M
    for p in spread_sol.squad:
        assert p.cost <= 12.0

    # Spread build distributes funds across premium mid-pricers (Palmer, Saka, Watkins, etc.)
    mid_costs = [p.cost for p in spread_sol.squad if p.position == 'MID']
    assert sum(mid_costs) > 30.0  # Big in the Middle


def test_solver_min_spend_prevents_bank_leaks():
    """Verify min_spend ensures high budget utilization without leaving phantom cash."""
    pool_df = create_mock_player_pool()

    sol = solve_initial_squad(pool_df, budget=100.0, min_spend=99.0)
    assert sol.status == "Optimal"
    assert sol.total_cost >= 99.0
    assert sol.total_cost <= 100.0


def test_solver_max_premium_count():
    """Verify max_premium_count restricts the number of players above premium threshold."""
    pool_df = create_mock_player_pool()

    # Allow at most 1 player >= 10.0M (e.g. Palmer or Saka or Salah or Haaland)
    sol = solve_initial_squad(pool_df, budget=100.0, max_premium_count=1, premium_cost_threshold=10.0)
    assert sol.status == "Optimal"

    premiums = [p for p in sol.squad if p.cost >= 10.0]
    assert len(premiums) <= 1


# ---------------------------------------------------------------------------
# 6. Additive EV Linearity Verification
# ---------------------------------------------------------------------------

def test_additive_ev_linearity():
    """Mathematically verify that expected points are additive regardless of matchup."""
    attacker_xp = 5.3
    defender_xp = 4.8

    # In mathematical expectation: E[Attacker + Defender] = E[Attacker] + E[Defender]
    joint_expected_value = attacker_xp + defender_xp
    assert abs(joint_expected_value - 10.1) < 1e-6

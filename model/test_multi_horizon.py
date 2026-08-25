"""Unit tests for multi-gameweek lookahead horizon solver."""
import os
import sys
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.solver import (
    solve_initial_squad,
    solve_multi_horizon_transfers,
    MultiHorizonSolution,
)


@pytest.fixture
def sample_horizon_data():
    """Create sample 3-gameweek player pool data."""
    base_players = [
        # GKs
        {'player_code': 1, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.5, 'expected_points': 5.0},
        {'player_code': 2, 'web_name': 'Fabianski', 'team': 'West Ham', 'position': 'GK', 'cost': 4.0, 'expected_points': 1.0},
        # DEFs
        {'player_code': 3, 'web_name': 'Gabriel', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0},
        {'player_code': 4, 'web_name': 'Saliba', 'team': 'Man City', 'position': 'DEF', 'cost': 6.0, 'expected_points': 5.5},
        {'player_code': 5, 'web_name': 'Alexander-Arnold', 'team': 'Liverpool', 'position': 'DEF', 'cost': 7.0, 'expected_points': 6.0},
        {'player_code': 6, 'web_name': 'Robinson', 'team': 'Fulham', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.0},
        {'player_code': 7, 'web_name': 'Greaves', 'team': 'Ipswich', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.5},
        # MIDs
        {'player_code': 8, 'web_name': 'Salah', 'team': 'Liverpool', 'position': 'MID', 'cost': 12.5, 'expected_points': 7.5},
        {'player_code': 9, 'web_name': 'Saka', 'team': 'Arsenal', 'position': 'MID', 'cost': 10.0, 'expected_points': 6.5},
        {'player_code': 10, 'web_name': 'Palmer', 'team': 'Chelsea', 'position': 'MID', 'cost': 10.5, 'expected_points': 6.8},
        {'player_code': 11, 'web_name': 'Rogers', 'team': 'Aston Villa', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.5},
        {'player_code': 12, 'web_name': 'Winks', 'team': 'Leicester', 'position': 'MID', 'cost': 4.5, 'expected_points': 2.0},
        # FWDs
        {'player_code': 13, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 8.5},
        {'player_code': 14, 'web_name': 'Isak', 'team': 'Newcastle', 'position': 'FWD', 'cost': 8.5, 'expected_points': 6.0},
        {'player_code': 15, 'web_name': 'Wood', 'team': 'Nott\'m Forest', 'position': 'FWD', 'cost': 6.0, 'expected_points': 4.5},
        # Additional transfer targets
        {'player_code': 16, 'web_name': 'Mbeumo', 'team': 'Brentford', 'position': 'MID', 'cost': 7.0, 'expected_points': 5.5},
        {'player_code': 17, 'web_name': 'Watkins', 'team': 'Aston Villa', 'position': 'FWD', 'cost': 9.0, 'expected_points': 6.5},
    ]

    df_gw1 = pd.DataFrame(base_players)

    # GW2: Watkins and Mbeumo have easy fixtures (xP boost)
    df_gw2 = pd.DataFrame(base_players)
    df_gw2.loc[df_gw2['player_code'] == 16, 'expected_points'] = 8.0  # Mbeumo easy match
    df_gw2.loc[df_gw2['player_code'] == 17, 'expected_points'] = 9.0  # Watkins easy match

    # GW3: Standard fixtures
    df_gw3 = pd.DataFrame(base_players)

    return [df_gw1, df_gw2, df_gw3]


class TestMultiHorizonSolver:
    """Verify multi-gameweek lookahead optimization."""

    def test_multi_horizon_execution(self, sample_horizon_data):
        horizon_dfs = sample_horizon_data
        init_codes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

        sol = solve_multi_horizon_transfers(
            current_squad_codes=init_codes,
            horizon_dfs=horizon_dfs,
            free_transfers=1,
            bank=5.0,
            discount_factor=0.90,
            start_gw=1,
        )

        assert sol.status == "Optimal"
        assert sol.horizon == 3
        assert len(sol.gw_plans) == 3

        # Verify GW continuity
        gw1_squad = set(p.player_code for p in sol.gw_plans[0].squad_solution.squad)
        gw2_squad = set(p.player_code for p in sol.gw_plans[1].squad_solution.squad)

        # In GW2, player continuity holds: gw2_squad = gw1_squad + in - out
        t_in = set(p.player_code for p in sol.gw_plans[1].transfers_in)
        t_out = set(p.player_code for p in sol.gw_plans[1].transfers_out)
        assert gw2_squad == (gw1_squad - t_out) | t_in

    def test_time_discounting_impact(self, sample_horizon_data):
        horizon_dfs = sample_horizon_data
        init_codes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

        # Higher discount factor values later gameweeks more
        sol_high = solve_multi_horizon_transfers(
            current_squad_codes=init_codes,
            horizon_dfs=horizon_dfs,
            discount_factor=0.95,
        )
        sol_low = solve_multi_horizon_transfers(
            current_squad_codes=init_codes,
            horizon_dfs=horizon_dfs,
            discount_factor=0.80,
        )

        assert sol_high.status == "Optimal"
        assert sol_low.status == "Optimal"
        assert sol_high.total_discounted_xp > sol_low.total_discounted_xp

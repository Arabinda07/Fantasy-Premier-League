"""Tests for Team Value Engine (M-09) and lambda_ft=1.75 standardization in the MILP solver."""

import inspect
import pandas as pd
import pytest

from model.solver import (
    solve_multi_horizon_transfers,
    solve_weekly_transfers,
    prepare_solver_dataframe,
)
from model.backtester import run_season_backtest


def _generate_base_squad_pool():
    """Create a standard 15-man squad and market alternatives for testing."""
    players = [
        {'player_code': 1, 'web_name': 'GK1', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 2, 'web_name': 'GK2', 'team': 'Ipswich', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 3, 'web_name': 'DEF1', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 4, 'web_name': 'DEF2', 'team': 'Arsenal', 'position': 'DEF', 'cost': 5.5, 'expected_points': 5.5, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 5, 'web_name': 'DEF3', 'team': 'Liverpool', 'position': 'DEF', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 6, 'web_name': 'DEF4', 'team': 'Liverpool', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.5, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 7, 'web_name': 'DEF5', 'team': 'Everton', 'position': 'DEF', 'cost': 4.5, 'expected_points': 3.5, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 9, 'web_name': 'MID1', 'team': 'Man City', 'position': 'MID', 'cost': 10.0, 'expected_points': 7.5, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 10, 'web_name': 'MID2', 'team': 'Chelsea', 'position': 'MID', 'cost': 9.0, 'expected_points': 7.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 11, 'web_name': 'MID3', 'team': 'Spurs', 'position': 'MID', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 12, 'web_name': 'MID4', 'team': 'Brighton', 'position': 'MID', 'cost': 6.5, 'expected_points': 5.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 13, 'web_name': 'MID_Drop', 'team': 'Brentford', 'position': 'MID', 'cost': 5.5, 'expected_points': 4.0, 'status': 'a', 'price_trend': 'FALLING_LOCK'},
        {'player_code': 14, 'web_name': 'FWD1', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 8.5, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 15, 'web_name': 'FWD2', 'team': 'Liverpool', 'position': 'FWD', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a', 'price_trend': 'STABLE'},
        {'player_code': 16, 'web_name': 'FWD3', 'team': 'Leeds', 'position': 'FWD', 'cost': 5.5, 'expected_points': 4.0, 'status': 'a', 'price_trend': 'STABLE'},
    ]
    return players


class TestTeamValueAndLambdaDefaults:
    """Test suite validating standard defaults and price-aware transfer decisions."""

    def test_lambda_ft_standardized_default(self):
        """Verify that default lambda_ft is standardized to 1.75 in solver and backtester."""
        sig_solver = inspect.signature(solve_multi_horizon_transfers)
        assert sig_solver.parameters['lambda_ft'].default == 1.75

        sig_backtester = inspect.signature(run_season_backtest)
        assert sig_backtester.parameters['lambda_ft'].default == 1.75

    def test_team_value_prefers_rising_player(self):
        """When two upgrade targets have near-identical xP, the rising player is chosen."""
        base_players = _generate_base_squad_pool()
        current_codes = [p['player_code'] for p in base_players]

        # Target A: 6.0 xP, STABLE
        # Target B: 5.95 xP (slightly lower), but RISING_LOCK (+£0.1M)
        target_a = {'player_code': 101, 'web_name': 'MID_A_Stable', 'team': 'Villa', 'position': 'MID', 'cost': 5.5, 'expected_points': 6.0, 'status': 'a', 'price_trend': 'STABLE'}
        target_b = {'player_code': 102, 'web_name': 'MID_B_Rising', 'team': 'Wolves', 'position': 'MID', 'cost': 5.5, 'expected_points': 5.95, 'status': 'a', 'price_trend': 'RISING_LOCK'}

        pool_gw1 = base_players + [target_a, target_b]
        pool_gw2 = base_players + [target_a, target_b]

        df_gw1 = pd.DataFrame(pool_gw1)
        df_gw2 = pd.DataFrame(pool_gw2)

        sol = solve_multi_horizon_transfers(
            current_squad_codes=current_codes,
            horizon_dfs=[df_gw1, df_gw2],
            free_transfers=1,
            bank=0.0,
            start_gw=5,
            lambda_ft=1.0,  # low enough to permit upgrade
            enable_team_value=True,
        )

        assert sol.status == "Optimal"
        gw1_trans_in = [p.player_code for p in sol.gw_plans[0].transfers_in]
        # Target B should be preferred over Target A due to the +£0.1M RISING_LOCK value bonus
        assert 102 in gw1_trans_in

    def test_team_value_purges_falling_player(self):
        """When deciding which player to transfer out, a FALLING_LOCK player is prioritized for sale."""
        base_players = _generate_base_squad_pool()
        current_codes = [p['player_code'] for p in base_players]

        # Squad has MID_Drop (code 13, FALLING_LOCK, 4.0 xP)
        # Squad has FWD3 (code 16, STABLE, 4.0 xP)
        # Upgrade target: MID_Target (code 105, 6.5 xP, cost 5.5, STABLE)
        target = {'player_code': 105, 'web_name': 'MID_Target', 'team': 'Villa', 'position': 'MID', 'cost': 5.5, 'expected_points': 6.5, 'status': 'a', 'price_trend': 'STABLE'}

        pool_gw1 = base_players + [target]
        pool_gw2 = base_players + [target]

        df_gw1 = pd.DataFrame(pool_gw1)
        df_gw2 = pd.DataFrame(pool_gw2)

        sol = solve_multi_horizon_transfers(
            current_squad_codes=current_codes,
            horizon_dfs=[df_gw1, df_gw2],
            free_transfers=1,
            bank=0.0,
            start_gw=5,
            lambda_ft=1.0,
            enable_team_value=True,
        )

        assert sol.status == "Optimal"
        gw1_trans_out = [p.player_code for p in sol.gw_plans[0].transfers_out]
        # MID_Drop (code 13) should be purged to avoid the -£0.1M drop
        assert 13 in gw1_trans_out

    def test_team_value_decays_in_late_season(self):
        """In late season (e.g. GW26), omega_tv decays to 0 and raw xP dominates."""
        base_players = _generate_base_squad_pool()
        current_codes = [p['player_code'] for p in base_players]

        target_a = {'player_code': 101, 'web_name': 'MID_A_Stable', 'team': 'Villa', 'position': 'MID', 'cost': 5.5, 'expected_points': 6.0, 'status': 'a', 'price_trend': 'STABLE'}
        target_b = {'player_code': 102, 'web_name': 'MID_B_Rising', 'team': 'Wolves', 'position': 'MID', 'cost': 5.5, 'expected_points': 5.95, 'status': 'a', 'price_trend': 'RISING_LOCK'}

        pool_gw1 = base_players + [target_a, target_b]
        pool_gw2 = base_players + [target_a, target_b]

        df_gw1 = pd.DataFrame(pool_gw1)
        df_gw2 = pd.DataFrame(pool_gw2)

        # In GW26, omega_tv is 0.0 -> Target A (6.0 xP) must win over Target B (5.95 xP)
        sol = solve_multi_horizon_transfers(
            current_squad_codes=current_codes,
            horizon_dfs=[df_gw1, df_gw2],
            free_transfers=1,
            bank=0.0,
            start_gw=26,
            lambda_ft=1.0,
            enable_team_value=True,
        )

        assert sol.status == "Optimal"
        gw1_trans_in = [p.player_code for p in sol.gw_plans[0].transfers_in]
        assert 101 in gw1_trans_in

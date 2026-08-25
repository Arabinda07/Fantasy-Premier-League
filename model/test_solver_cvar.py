"""Unit tests for Risk-Adjusted CVaR & Auto-Sub Solver (model/solver.py)."""
import pytest
import pandas as pd
import numpy as np

from model.solver import (
    prepare_solver_dataframe,
    solve_initial_squad,
    solve_weekly_transfers,
    solve_multi_horizon_transfers,
)


class TestSolverCvarMath:
    """Test CVaR tail-risk formulation and parameter behaviors in solver."""

    def test_cvar_risk_aversion_vs_upside_chasing(self):
        """Verify that lambda_risk > 0 penalizes high-variance assets while lambda_risk < 0 rewards them."""
        # Two players with identical expected points (6.0 xP), but different risk profiles:
        # Player A: Steady starter, High floor (4.5), low variance (Ceiling 8.0)
        # Player B: Boom-or-bust differential, Low floor (1.0), high variance (Ceiling 14.0)
        df = pd.DataFrame([
            {'player_code': 101, 'web_name': 'Steady_DEF', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0, 'floor_p10': 4.5, 'ceiling_p90': 8.0, 'status': 'a'},
            {'player_code': 102, 'web_name': 'BoomBust_MID', 'team': 'Chelsea', 'position': 'MID', 'cost': 6.0, 'expected_points': 6.0, 'floor_p10': 1.0, 'ceiling_p90': 14.0, 'status': 'a'},
        ])

        # 1. Pure Expected Points (lambda_risk = 0.0)
        df_pure = prepare_solver_dataframe(df, lambda_risk=0.0)
        assert df_pure.loc[0, 'opt_points'] == df_pure.loc[1, 'opt_points']

        # 2. Risk Aversion (lambda_risk = 0.20 -> Rank Protect)
        # Steady_DEF downside risk = 6.0 - 4.5 = 1.5 -> penalty = 0.30 -> opt = 5.70
        # BoomBust_MID downside risk = 6.0 - 1.0 = 5.0 -> penalty = 1.00 -> opt = 5.00
        df_protect = prepare_solver_dataframe(df, lambda_risk=0.20)
        assert df_protect.loc[0, 'opt_points'] > df_protect.loc[1, 'opt_points']

        # 3. Upside Chasing (lambda_risk = -0.20 -> Differential Chase)
        # Steady_DEF upside reward = 8.0 - 6.0 = 2.0 -> reward = 0.40 -> opt = 6.40
        # BoomBust_MID upside reward = 14.0 - 6.0 = 8.0 -> reward = 1.60 -> opt = 7.60
        df_chase = prepare_solver_dataframe(df, lambda_risk=-0.20)
        assert df_chase.loc[1, 'opt_points'] > df_chase.loc[0, 'opt_points']

    def test_auto_sub_bench_valuation(self):
        """Verify that dynamic bench weighting (0.10) values active bench players appropriately."""
        # 16 candidate players: 2 GK, 6 DEF, 5 MID, 3 FWD
        # DEF 6 is 4.0m with 0.0 xP (non-playing) vs DEF 5 is 4.5m with 3.5 xP (playing)
        players = [
            {'player_code': 1, 'web_name': 'GK1', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a'},
            {'player_code': 2, 'web_name': 'GK2', 'team': 'Ipswich', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.0, 'status': 'a'},
            {'player_code': 3, 'web_name': 'DEF1', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0, 'status': 'a'},
            {'player_code': 4, 'web_name': 'DEF2', 'team': 'Arsenal', 'position': 'DEF', 'cost': 5.5, 'expected_points': 5.5, 'status': 'a'},
            {'player_code': 5, 'web_name': 'DEF3', 'team': 'Liverpool', 'position': 'DEF', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a'},
            {'player_code': 6, 'web_name': 'DEF4', 'team': 'Liverpool', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.5, 'status': 'a'},
            {'player_code': 7, 'web_name': 'DEF5_PlayingBench', 'team': 'Everton', 'position': 'DEF', 'cost': 4.5, 'expected_points': 3.5, 'status': 'a'},
            {'player_code': 8, 'web_name': 'DEF6_Fodder', 'team': 'Everton', 'position': 'DEF', 'cost': 4.0, 'expected_points': 0.0, 'status': 'a'},
            {'player_code': 9, 'web_name': 'MID1', 'team': 'Man City', 'position': 'MID', 'cost': 10.0, 'expected_points': 7.5, 'status': 'a'},
            {'player_code': 10, 'web_name': 'MID2', 'team': 'Chelsea', 'position': 'MID', 'cost': 9.0, 'expected_points': 7.0, 'status': 'a'},
            {'player_code': 11, 'web_name': 'MID3', 'team': 'Spurs', 'position': 'MID', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a'},
            {'player_code': 12, 'web_name': 'MID4', 'team': 'Brighton', 'position': 'MID', 'cost': 6.5, 'expected_points': 5.0, 'status': 'a'},
            {'player_code': 13, 'web_name': 'MID5', 'team': 'Brentford', 'position': 'MID', 'cost': 5.5, 'expected_points': 4.5, 'status': 'a'},
            {'player_code': 14, 'web_name': 'FWD1', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 8.5, 'status': 'a'},
            {'player_code': 15, 'web_name': 'FWD2', 'team': 'Liverpool', 'position': 'FWD', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a'},
            {'player_code': 16, 'web_name': 'FWD3', 'team': 'Leeds', 'position': 'FWD', 'cost': 5.5, 'expected_points': 4.0, 'status': 'a'},
        ]
        df = pd.DataFrame(players)

        # Solve initial squad with generous budget (105.0m) to allow selecting DEF5_PlayingBench
        sol = solve_initial_squad(df, budget=105.0)
        assert sol.status == "Optimal"
        assert len(sol.squad) == 15
        assert len(sol.starters) == 11
        assert len(sol.bench) == 4

        # Verify that DEF5_PlayingBench is selected over zero-point fodder when budget allows
        squad_codes = [p.player_code for p in sol.squad]
        assert 7 in squad_codes

    def test_free_transfer_banking_shadow_price_incentive(self):
        """Verify that lambda_ft=1.75 encourages rolling transfer when marginal delta is small."""
        # Initial 15-man squad
        current_codes = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]

        # Horizon with 2 GWs
        # Player 13 (MID5) has 4.5 xP in GW1 and 4.5 xP in GW2
        # Alternative Player 99 (MID_Trans) has 4.8 xP in GW1 and 4.8 xP in GW2 (delta = +0.3 xP per GW)
        # Because delta (+0.3 xP) is less than lambda_ft (1.75 pts), the solver should ROLL the FT in GW1!
        gw1_players = [
            {'player_code': 1, 'web_name': 'GK1', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a'},
            {'player_code': 2, 'web_name': 'GK2', 'team': 'Ipswich', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.0, 'status': 'a'},
            {'player_code': 3, 'web_name': 'DEF1', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0, 'status': 'a'},
            {'player_code': 4, 'web_name': 'DEF2', 'team': 'Arsenal', 'position': 'DEF', 'cost': 5.5, 'expected_points': 5.5, 'status': 'a'},
            {'player_code': 5, 'web_name': 'DEF3', 'team': 'Liverpool', 'position': 'DEF', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a'},
            {'player_code': 6, 'web_name': 'DEF4', 'team': 'Liverpool', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.5, 'status': 'a'},
            {'player_code': 7, 'web_name': 'DEF5', 'team': 'Everton', 'position': 'DEF', 'cost': 4.5, 'expected_points': 3.5, 'status': 'a'},
            {'player_code': 9, 'web_name': 'MID1', 'team': 'Man City', 'position': 'MID', 'cost': 10.0, 'expected_points': 7.5, 'status': 'a'},
            {'player_code': 10, 'web_name': 'MID2', 'team': 'Chelsea', 'position': 'MID', 'cost': 9.0, 'expected_points': 7.0, 'status': 'a'},
            {'player_code': 11, 'web_name': 'MID3', 'team': 'Spurs', 'position': 'MID', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a'},
            {'player_code': 12, 'web_name': 'MID4', 'team': 'Brighton', 'position': 'MID', 'cost': 6.5, 'expected_points': 5.0, 'status': 'a'},
            {'player_code': 13, 'web_name': 'MID5', 'team': 'Brentford', 'position': 'MID', 'cost': 5.5, 'expected_points': 4.5, 'status': 'a'},
            {'player_code': 14, 'web_name': 'FWD1', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 8.5, 'status': 'a'},
            {'player_code': 15, 'web_name': 'FWD2', 'team': 'Liverpool', 'position': 'FWD', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a'},
            {'player_code': 16, 'web_name': 'FWD3', 'team': 'Leeds', 'position': 'FWD', 'cost': 5.5, 'expected_points': 4.0, 'status': 'a'},
            {'player_code': 99, 'web_name': 'MID_Trans', 'team': 'Fulham', 'position': 'MID', 'cost': 5.5, 'expected_points': 4.8, 'status': 'a'},
        ]
        df_gw1 = pd.DataFrame(gw1_players)
        df_gw2 = pd.DataFrame(gw1_players)

        # Solve multi-horizon with lambda_ft=1.75
        sol_banked = solve_multi_horizon_transfers(
            current_squad_codes=current_codes,
            horizon_dfs=[df_gw1, df_gw2],
            free_transfers=1,
            bank=0.0,
            lambda_ft=1.75,
        )

        assert sol_banked.status == "Optimal"
        gw1_plan = sol_banked.gw_plans[0]
        # Verify that solver rolls the transfer (transfers_count == 0) instead of making a tiny sideways move
        assert gw1_plan.transfers_count == 0

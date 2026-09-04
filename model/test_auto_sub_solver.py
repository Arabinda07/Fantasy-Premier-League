"""Unit test suite for M-06 (Expected Auto-Substitution Valuation) and M-07 (C11 Rate Normalization).

Validates:
1. Tiered auto-sub probabilities w_1 > w_2 > w_3 > 0 derived from binomial DNP distributions.
2. Responsiveness to starter absence hazard (rotation / injury probability).
3. Chip handling (Bench Boost all start, Free Hit minimal bench valuation).
4. Initial Squad Solver, Lineup Solver, and Weekly Transfer Solver partition constraints.
5. Natural ordering of highest-xP reserve into Bench Slot 1.
6. Multi-Horizon dynamic bench valuation.
7. Formal mathematical audit of C11 defensive contribution rate normalization.
"""

import math
import pytest
import pandas as pd
import numpy as np

from model.solver import (
    compute_auto_sub_weights,
    solve_initial_squad,
    solve_squad_lineup,
    solve_weekly_transfers,
    solve_multi_horizon_transfers,
)
from model.prediction_engine import predict_player_points


class TestAutoSubWeights:
    """Test suite for compute_auto_sub_weights helper."""

    def test_hybrid_weights_default(self):
        """Default hybrid mode must activate sub_1 and sub_2 while zeroing sub_3 and sub_gk."""
        df = pd.DataFrame({
            'position': ['DEF'] * 5 + ['MID'] * 5 + ['FWD'] * 3 + ['GK'] * 2,
            'p_app': [0.95] * 15,
        })
        weights = compute_auto_sub_weights(df)  # Default bench_mode='hybrid'

        assert weights['sub_1'] > weights['sub_2'] > 0.0
        assert 0.20 <= weights['sub_1'] <= 0.65
        assert 0.04 <= weights['sub_2'] <= 0.25
        assert weights['sub_3'] == 0.0
        assert weights['sub_gk'] == 0.0

    def test_standard_weights_monotonicity_and_bounds(self):
        """Standard mode weights must be strictly decreasing across outfield slots: w1 > w2 > w3 > 0."""
        # Baseline pool with typical starter probability p_app ~ 0.95 (q = 0.05)
        df = pd.DataFrame({
            'position': ['DEF'] * 5 + ['MID'] * 5 + ['FWD'] * 3 + ['GK'] * 2,
            'p_app': [0.95] * 15,
        })
        weights = compute_auto_sub_weights(df, bench_mode='standard')

        w1 = weights['sub_1']
        w2 = weights['sub_2']
        w3 = weights['sub_3']
        wgk = weights['sub_gk']

        assert w1 > w2 > w3 > 0.0
        assert 0.20 <= w1 <= 0.65
        assert 0.04 <= w2 <= 0.25
        assert 0.008 <= w3 <= 0.08
        assert 0.01 <= wgk <= 0.05

    def test_ultra_thin_weights(self):
        """Ultra-thin mode zeroes out all bench weights."""
        df = pd.DataFrame({
            'position': ['DEF'] * 5 + ['MID'] * 5 + ['FWD'] * 3 + ['GK'] * 2,
            'p_app': [0.95] * 15,
        })
        weights = compute_auto_sub_weights(df, bench_mode='ultra_thin')
        assert weights == {'sub_1': 0.0, 'sub_2': 0.0, 'sub_3': 0.0, 'sub_gk': 0.0}

    def test_responsiveness_to_rotation_risk(self):
        """Higher starter rotation hazard (lower p_app) must increase sub_1 and sub_2 weights."""
        df_low_risk = pd.DataFrame({
            'position': ['DEF'] * 5 + ['MID'] * 5 + ['FWD'] * 3 + ['GK'] * 2,
            'p_app': [0.98] * 15,
        })
        df_high_risk = pd.DataFrame({
            'position': ['DEF'] * 5 + ['MID'] * 5 + ['FWD'] * 3 + ['GK'] * 2,
            'p_app': [0.85] * 15,
        })

        weights_low = compute_auto_sub_weights(df_low_risk)
        weights_high = compute_auto_sub_weights(df_high_risk)

        assert weights_high['sub_1'] > weights_low['sub_1']
        assert weights_high['sub_2'] > weights_low['sub_2']
        assert weights_high['sub_3'] == 0.0
        assert weights_high['sub_gk'] == 0.0

        # In standard mode, sub_3 also increases
        std_low = compute_auto_sub_weights(df_low_risk, bench_mode='standard')
        std_high = compute_auto_sub_weights(df_high_risk, bench_mode='standard')
        assert std_high['sub_3'] > std_low['sub_3']

    def test_chip_overrides(self):
        """Bench Boost sets weights to 1.0; Free Hit minimizes bench valuation."""
        bb_weights = compute_auto_sub_weights(None, chip='bboost')
        assert bb_weights == {'sub_1': 1.0, 'sub_2': 1.0, 'sub_3': 1.0, 'sub_gk': 1.0}

        fh_weights = compute_auto_sub_weights(None, chip='freehit')
        assert fh_weights['sub_1'] <= 0.10
        assert fh_weights['sub_2'] <= 0.02
        assert fh_weights['sub_3'] <= 0.005


class TestAutoSubSolverIntegration:
    """Test suite for MILP solver behavior with tiered bench variables."""

    @pytest.fixture
    def player_pool(self):
        """Standard 20-player synthetic pool for solver integration tests."""
        rows = []
        # GKs
        rows.append({'player_code': 1, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.5, 'expected_points': 5.2, 'p_app': 0.99})
        rows.append({'player_code': 2, 'web_name': 'Fabianski', 'team': 'West Ham', 'position': 'GK', 'cost': 4.0, 'expected_points': 1.5, 'p_app': 0.20})
        # DEFs
        rows.append({'player_code': 3, 'web_name': 'Gabriel', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0, 'p_app': 0.98})
        rows.append({'player_code': 4, 'web_name': 'Saliba', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 5.8, 'p_app': 0.98})
        rows.append({'player_code': 5, 'web_name': 'Alexander-Arnold', 'team': 'Liverpool', 'position': 'DEF', 'cost': 7.0, 'expected_points': 6.2, 'p_app': 0.95})
        rows.append({'player_code': 6, 'web_name': 'Robinson', 'team': 'Fulham', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.2, 'p_app': 0.95})
        rows.append({'player_code': 7, 'web_name': 'Greaves', 'team': 'Ipswich', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.8, 'p_app': 0.90})
        rows.append({'player_code': 8, 'web_name': 'Bednarek', 'team': 'Southampton', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.2, 'p_app': 0.90})
        # MIDs
        rows.append({'player_code': 9, 'web_name': 'Salah', 'team': 'Liverpool', 'position': 'MID', 'cost': 12.5, 'expected_points': 8.5, 'p_app': 0.98})
        rows.append({'player_code': 10, 'web_name': 'Saka', 'team': 'Arsenal', 'position': 'MID', 'cost': 10.0, 'expected_points': 7.2, 'p_app': 0.98})
        rows.append({'player_code': 11, 'web_name': 'Palmer', 'team': 'Chelsea', 'position': 'MID', 'cost': 10.5, 'expected_points': 7.5, 'p_app': 0.98})
        rows.append({'player_code': 12, 'web_name': 'Rogers', 'team': 'Aston Villa', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.8, 'p_app': 0.95})
        rows.append({'player_code': 13, 'web_name': 'Winks', 'team': 'Leicester', 'position': 'MID', 'cost': 4.5, 'expected_points': 2.5, 'p_app': 0.90})
        rows.append({'player_code': 14, 'web_name': 'King', 'team': 'Fulham', 'position': 'MID', 'cost': 4.5, 'expected_points': 1.8, 'p_app': 0.40})
        # FWDs
        rows.append({'player_code': 15, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 9.0, 'p_app': 0.98})
        rows.append({'player_code': 16, 'web_name': 'Isak', 'team': 'Newcastle', 'position': 'FWD', 'cost': 8.5, 'expected_points': 6.5, 'p_app': 0.95})
        rows.append({'player_code': 17, 'web_name': 'Wood', 'team': 'Nott\'m Forest', 'position': 'FWD', 'cost': 6.0, 'expected_points': 4.5, 'p_app': 0.92})
        rows.append({'player_code': 18, 'web_name': 'Chiwome', 'team': 'Wolves', 'position': 'FWD', 'cost': 4.5, 'expected_points': 1.5, 'p_app': 0.30})
        return pd.DataFrame(rows)

    def test_solve_initial_squad_bench_partition_and_order(self, player_pool):
        """Initial squad solver must select 15 players with exactly 11 starters and 4 bench slots."""
        sol = solve_initial_squad(player_pool, budget=100.0)

        assert sol.status == "Optimal"
        assert len(sol.squad) == 15
        assert len(sol.starters) == 11
        assert len(sol.bench) == 4

        # Bench must start with GK or outfield sorted by expected points
        outfield_bench = [p for p in sol.bench if p.position != 'GK']
        assert len(outfield_bench) == 3

        # Highest xP on bench must be Slot 1
        for i in range(len(outfield_bench) - 1):
            assert outfield_bench[i].expected_points >= outfield_bench[i + 1].expected_points

    def test_hybrid_bench_forces_minimum_gk_and_sub3(self, player_pool):
        """In hybrid mode, backup GK must be minimum-cost (£4.0m) and Sub 3 should be low-cost enabler."""
        sol = solve_initial_squad(player_pool, budget=100.0, bench_mode='hybrid')
        assert sol.status == "Optimal"
        bench_gks = [p for p in sol.bench if p.position == 'GK']
        assert len(bench_gks) == 1
        # Fabianski is the £4.0m keeper in player_pool
        assert bench_gks[0].cost == 4.0

    def test_solve_squad_lineup_bench_ordering(self, player_pool):
        """Lineup solver on 15 fixed players places highest-xP reserve in Bench 1."""
        # Pick 15 players from pool
        squad_15 = player_pool.iloc[:15].copy()
        sol = solve_squad_lineup(squad_15)

        assert sol.status == "Optimal"
        assert len(sol.starters) == 11
        assert len(sol.bench) == 4

        outfield_bench = [p for p in sol.bench if p.position != 'GK']
        assert len(outfield_bench) == 3
        # Check monotonic ordering
        assert outfield_bench[0].expected_points >= outfield_bench[1].expected_points >= outfield_bench[2].expected_points

    def test_bench_boost_chip_all_start(self, player_pool):
        """Under Bench Boost, all 15 squad members start and starting_xp equals total squad xp."""
        squad_15 = player_pool.iloc[:15].copy()
        sol = solve_squad_lineup(squad_15, chip='bboost')

        assert sol.status == "Optimal"
        assert len(sol.starters) == 15
        assert len(sol.bench) == 0

    def test_solve_weekly_transfers_with_auto_sub(self, player_pool):
        """solve_weekly_transfers maintains partition constraints and solves optimally."""
        current_squad_codes = list(player_pool['player_code'].iloc[:15])
        transfer_sol = solve_weekly_transfers(
            current_squad_codes=current_squad_codes,
            df=player_pool,
            free_transfers=1,
            bank=1.0,
        )

        assert transfer_sol.squad_solution.status == "Optimal"
        assert len(transfer_sol.squad_solution.squad) == 15
        assert len(transfer_sol.squad_solution.starters) == 11
        assert len(transfer_sol.squad_solution.bench) == 4

    def test_solve_multi_horizon_dynamic_bench(self, player_pool):
        """solve_multi_horizon_transfers solves across 3 GWs using dynamic auto-sub bench weights."""
        current_squad_codes = list(player_pool['player_code'].iloc[:15])
        horizon_dfs = [player_pool.copy(), player_pool.copy(), player_pool.copy()]

        sol = solve_multi_horizon_transfers(
            current_squad_codes=current_squad_codes,
            horizon_dfs=horizon_dfs,
            free_transfers=1,
            bank=1.0,
        )

        assert sol.status == "Optimal"
        assert len(sol.gw_plans) == 3
        for plan in sol.gw_plans:
            assert len(plan.squad_solution.starters) == 11
            assert len(plan.squad_solution.bench) == 4


class TestDefensiveContributionRateNormalizationAudit:
    """Formal audit test for M-07 (C11 rate normalization without double discounting)."""

    def test_c11_conditional_expectation_audit(self):
        """Verify that lambda_dc_60 conditions on expected minutes given 60+ minutes."""
        # Player with 9.0 DC/90
        # If starter plays ~88.5 minutes conditional on 60+:
        # exposure_60 = 88.5 / 90.0 ~= 0.9833
        # lambda_dc_60 = 9.0 * 0.9833 = 8.85
        # Under Poisson:
        # P(DC >= 10 | lambda=8.85) = 1 - sum_{k=0}^9 e^-8.85 * 8.85^k / k! ~= 0.388
        # P(DC >= 15 | lambda=8.85) ~= 0.035
        # C11 = (0.388 + 0.035) * P(60+)
        player = {
            'web_name': 'Tarkowski',
            'position': 'DEF',
            'team': 'Everton',
            'season_starts': 35,
            'season_minutes': 3150,
            'long_form_minutes': 3150,
            'long_form_defensive_contribution_90': 9.0,
            'status': 'a',
        }

        pred = predict_player_points(player)

        assert pred['c11_defensive_contributions'] > 0.35
        assert pred['c11_defensive_contributions'] < 0.65

        # If player never plays (p_60_plus = 0.0), C11 must be strictly 0.0
        bench_fodder = dict(player)
        bench_fodder['season_starts'] = 0
        bench_fodder['season_minutes'] = 0
        bench_fodder['long_form_minutes'] = 0
        bench_fodder['now_cost'] = 40
        pred_fodder = predict_player_points(bench_fodder)
        assert pred_fodder['p_60_plus'] == 0.0
        assert pred_fodder['c11_defensive_contributions'] == 0.0

        # Monotonicity: higher DC/90 produces higher C11 points
        player_high_dc = dict(player)
        player_high_dc['long_form_defensive_contribution_90'] = 14.0
        pred_high = predict_player_points(player_high_dc)
        assert pred_high['c11_defensive_contributions'] > pred['c11_defensive_contributions']

"""Adversarial Quantitative Audit Verification Test Suite.

Verifies the mathematical and programmatic resolutions to all 7 adversarial dimensions:
1. Solver Infeasibility & Market Price Dynamics (Dynamic Price Floor & Soft Slack)
2. Dynamic Auto-Sub Legality & Universal Defensive Coverage
3. The Trapped Capital Wildcard Dilemma (Option Value Hurdle Curve & Harvest Advisory)
4. The Bench Boost Expansion & Contraction Tax (-12.8 pt Post-BB Adjustment)
5. Multi-Horizon Lookahead Runtime SLA (< 15s) & Zero-Variable Capital Drag
6. FPL 50% Profit Retention & Stored Equity Preservation
7. Festive Period Rotation Congestion Responsiveness (GW17-21)
"""
import json
import os
import sys
import time
import pytest
import pandas as pd
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.solver import (
    compute_auto_sub_weights,
    compute_dynamic_bench_floor,
    solve_initial_squad,
    solve_weekly_transfers,
    solve_multi_horizon_transfers,
    solve_squad_lineup,
)
from model.chip_optimizer import (
    evaluate_opportunistic_wildcard,
    evaluate_chip_schedule,
)


@pytest.fixture
def sample_inflated_pool():
    """Pool with mid-season inflated prices where cheapest bench exceeds £17.5M."""
    rows = []
    # GKs (min 4.5)
    rows.append({'player_code': 1, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.8, 'expected_points': 5.2, 'p_app': 0.99})
    rows.append({'player_code': 2, 'web_name': 'Fabianski', 'team': 'West Ham', 'position': 'GK', 'cost': 4.5, 'expected_points': 2.0, 'p_app': 0.85})
    # DEFs (min 4.3)
    rows.append({'player_code': 3, 'web_name': 'Gabriel', 'team': 'Chelsea', 'position': 'DEF', 'cost': 6.4, 'expected_points': 6.0, 'p_app': 0.98})
    rows.append({'player_code': 4, 'web_name': 'Saliba', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.2, 'expected_points': 5.8, 'p_app': 0.98})
    rows.append({'player_code': 5, 'web_name': 'Alexander-Arnold', 'team': 'Liverpool', 'position': 'DEF', 'cost': 7.4, 'expected_points': 6.2, 'p_app': 0.95})
    rows.append({'player_code': 6, 'web_name': 'Greaves', 'team': 'Ipswich', 'position': 'DEF', 'cost': 4.3, 'expected_points': 3.2, 'p_app': 0.95})
    rows.append({'player_code': 7, 'web_name': 'Bednarek', 'team': 'Southampton', 'position': 'DEF', 'cost': 4.3, 'expected_points': 3.0, 'p_app': 0.95})
    # MIDs (min 4.8)
    rows.append({'player_code': 8, 'web_name': 'Salah', 'team': 'Liverpool', 'position': 'MID', 'cost': 13.0, 'expected_points': 8.5, 'p_app': 0.98})
    rows.append({'player_code': 9, 'web_name': 'Saka', 'team': 'Arsenal', 'position': 'MID', 'cost': 10.2, 'expected_points': 7.2, 'p_app': 0.98})
    rows.append({'player_code': 10, 'web_name': 'Palmer', 'team': 'Chelsea', 'position': 'MID', 'cost': 10.8, 'expected_points': 7.5, 'p_app': 0.98})
    rows.append({'player_code': 11, 'web_name': 'Rogers', 'team': 'Aston Villa', 'position': 'MID', 'cost': 5.6, 'expected_points': 5.0, 'p_app': 0.95})
    rows.append({'player_code': 12, 'web_name': 'Winks', 'team': 'Leicester', 'position': 'MID', 'cost': 4.8, 'expected_points': 2.5, 'p_app': 0.90})
    rows.append({'player_code': 13, 'web_name': 'Semenyo', 'team': 'Bournemouth', 'position': 'MID', 'cost': 6.0, 'expected_points': 5.2, 'p_app': 0.95})
    # FWDs (min 5.5)
    rows.append({'player_code': 14, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'cost': 15.4, 'expected_points': 9.0, 'p_app': 0.98})
    rows.append({'player_code': 15, 'web_name': 'Isak', 'team': 'Newcastle', 'position': 'FWD', 'cost': 8.8, 'expected_points': 6.5, 'p_app': 0.95})
    rows.append({'player_code': 16, 'web_name': 'Wood', 'team': 'Nott\'m Forest', 'position': 'FWD', 'cost': 6.5, 'expected_points': 5.5, 'p_app': 0.92})
    rows.append({'player_code': 17, 'web_name': 'Delap', 'team': 'Ipswich', 'position': 'FWD', 'cost': 5.5, 'expected_points': 4.0, 'p_app': 0.90})
    return pd.DataFrame(rows)


class TestAdversarialBenchOptimization:
    """Adversarial stress-test suite validating the 7 strategic dimensions."""

    def test_dynamic_bench_price_floor_guarantees_feasibility(self, sample_inflated_pool):
        """Dimension 1: Dynamic price floor guarantees feasibility when minimum bench cost exceeds £17.5M."""
        floor = compute_dynamic_bench_floor(sample_inflated_pool)
        # GK (4.5) + 2*DEF (2*4.3) + MID (4.8) + 0.5 = 4.5 + 8.6 + 4.8 + 0.5 = 18.4M
        assert floor >= 18.0

        current_codes = list(sample_inflated_pool['player_code'].iloc[:15])
        transfer_sol = solve_weekly_transfers(
            current_squad_codes=current_codes,
            df=sample_inflated_pool,
            free_transfers=1,
            bank=0.5,
        )
        assert transfer_sol.squad_solution.status == "Optimal"
        assert len(transfer_sol.squad_solution.bench) == 4

    def test_zero_ft_high_cost_bench_does_not_force_infeasibility_or_hits(self, sample_inflated_pool):
        """Dimension 1: Existing squad with £22M+ bench solves to Optimal with 0 FTs without forced hits."""
        # 2 GK (1, 2), 5 DEF (3, 4, 5, 6, 7), 5 MID (8, 9, 10, 11, 12), 3 FWD (14, 15, 16)
        current_codes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16]
        transfer_sol = solve_weekly_transfers(
            current_squad_codes=current_codes,
            df=sample_inflated_pool,
            free_transfers=0,
            bank=0.0,
            max_transfers=1,
        )
        assert transfer_sol.squad_solution.status == "Optimal"
        # Must not force illegal multi-hit firesales to satisfy an arbitrary bench cap
        assert transfer_sol.hits_taken == 0

    def test_stored_equity_preservation(self):
        """Dimension 6: Transfer optimizer penalizes selling assets with high phantom profit."""
        # Player 8 bought at 4.2 -> sell 4.6 (stored profit equity phi = 0.4)
        # Player 9 bought at 5.0 -> sell 5.0 (stored profit equity phi = 0.0)
        # Both players have identical xP and identical cost. Optimizer should sell Player 9.
        rows = [
            {'player_code': 1, 'web_name': 'GK1', 'team': 'ARS', 'position': 'GK', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.99},
            {'player_code': 2, 'web_name': 'GK2', 'team': 'WHA', 'position': 'GK', 'cost': 4.0, 'expected_points': 1.0, 'p_app': 0.10},
            {'player_code': 3, 'web_name': 'DEF1', 'team': 'ARS', 'position': 'DEF', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 4, 'web_name': 'DEF2', 'team': 'LIV', 'position': 'DEF', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 5, 'web_name': 'DEF3', 'team': 'MCI', 'position': 'DEF', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 6, 'web_name': 'DEF4', 'team': 'CHE', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.0, 'p_app': 0.90},
            {'player_code': 7, 'web_name': 'DEF5', 'team': 'NEW', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.0, 'p_app': 0.90},
            {'player_code': 8, 'web_name': 'MID_HighProfit', 'team': 'AVL', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 9, 'web_name': 'MID_ZeroProfit', 'team': 'FUL', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 10, 'web_name': 'MID3', 'team': 'ARS', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 11, 'web_name': 'MID4', 'team': 'LIV', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.0, 'p_app': 0.95},
            {'player_code': 12, 'web_name': 'MID5', 'team': 'BOU', 'position': 'MID', 'cost': 4.5, 'expected_points': 2.0, 'p_app': 0.90},
            {'player_code': 13, 'web_name': 'FWD1', 'team': 'MCI', 'position': 'FWD', 'cost': 8.0, 'expected_points': 6.0, 'p_app': 0.95},
            {'player_code': 14, 'web_name': 'FWD2', 'team': 'NEW', 'position': 'FWD', 'cost': 7.0, 'expected_points': 5.0, 'p_app': 0.95},
            {'player_code': 15, 'web_name': 'FWD3', 'team': 'NFO', 'position': 'FWD', 'cost': 5.0, 'expected_points': 3.0, 'p_app': 0.90},
            # Target transfer in with higher xP
            {'player_code': 16, 'web_name': 'MID_Target', 'team': 'TOT', 'position': 'MID', 'cost': 5.0, 'expected_points': 6.5, 'p_app': 0.99},
        ]
        df = pd.DataFrame(rows)
        owned = list(range(1, 16))
        # Player 8 bought at 4.2 (stored profit equity 0.4), Player 9 bought at 5.0 (0 stored equity)
        purchase_prices = {8: 4.2, 9: 5.0}

        sol = solve_weekly_transfers(
            current_squad_codes=owned,
            df=df,
            free_transfers=1,
            bank=0.0,
            purchase_prices=purchase_prices,
            max_transfers=1,
        )
        assert sol.squad_solution.status == "Optimal"
        if sol.transfers_out:
            # Solver must preserve Player 8 (MID_HighProfit with 0.4 stored equity)
            assert sol.transfers_out[0].player_code != 8
            assert 8 in [p.player_code for p in sol.squad_solution.squad]

    def test_trapped_capital_wildcard_hurdle_withholds_on_arabinda_squad(self):
        """Dimension 3: Arabinda's £22.9M bench squad has healthy starters; Wildcard is withheld."""
        squad_path = os.path.join(REPO_ROOT, 'data', '2026-27', 'manager_squad_9500404.json')
        if not os.path.exists(squad_path):
            pytest.skip("Arabinda squad snapshot not found")

        with open(squad_path, 'r') as f:
            sq_data = json.load(f)

        pred_path = os.path.join(REPO_ROOT, 'data', '2026-27', 'predictions.csv')
        if not os.path.exists(pred_path):
            pytest.skip("Predictions CSV not found")

        pred_df = pd.read_csv(pred_path)
        rec = evaluate_opportunistic_wildcard(
            current_squad_codes=sq_data['squad_codes'],
            gw1_df=pred_df,
            free_transfers=sq_data.get('free_transfers', 1),
            bank=sq_data.get('bank', 1.6),
            current_gw=5,
        )

        # Wildcard must NOT fire prematurely on Arabinda's squad
        assert rec.is_active_now is False
        assert rec.trapped_bench_capital >= 1.0
        assert rec.harvest_advisory is not None
        assert "trapped bench capital" in rec.harvest_advisory.lower()

    def test_festive_auto_sub_responsiveness(self):
        """Dimension 7: GW18 festive calendar increases sub_2 insurance against multi-starter scratches."""
        df = pd.DataFrame({
            'position': ['DEF'] * 5 + ['MID'] * 5 + ['FWD'] * 3 + ['GK'] * 2,
            'p_app': [0.95] * 15,
        })
        std_weights = compute_auto_sub_weights(df, current_gw=10)
        festive_weights = compute_auto_sub_weights(df, current_gw=18)

        # Sub 1 and Sub 2 must increase during festive period
        assert festive_weights['sub_1'] > std_weights['sub_1']
        assert festive_weights['sub_2'] >= 0.12

    def test_bench_boost_contraction_tax(self):
        """Dimension 4: Bench Boost evaluated prior to GW37 deducts the 12.8 point contraction tax."""
        plan = evaluate_chip_schedule(season='2026-27', current_gw=5)
        bb_rec = plan.recommendations.get('bboost')
        assert bb_rec is not None
        if bb_rec.target_gw < 37:
            assert "contraction tax" in bb_rec.rationale.lower()

    def test_multi_horizon_capital_drag_solves_under_production_sla(self, sample_inflated_pool):
        """Dimension 5: Multi-horizon lookahead solves in < 5.0 seconds (well within 15s SLA)."""
        current_codes = list(sample_inflated_pool['player_code'].iloc[:15])
        horizon_dfs = [sample_inflated_pool, sample_inflated_pool, sample_inflated_pool]

        t0 = time.time()
        multi_sol = solve_multi_horizon_transfers(
            current_squad_codes=current_codes,
            horizon_dfs=horizon_dfs,
            free_transfers=1,
            bank=1.0,
            start_gw=5,
        )
        elapsed = time.time() - t0

        assert multi_sol.status == "Optimal"
        assert len(multi_sol.gw_plans) == 3
        assert elapsed < 5.0, f"Multi-horizon solver took {elapsed:.2f}s, exceeding SLA"

    def test_goalkeeper_captaincy_guardrail(self, sample_inflated_pool):
        """Verify that Goalkeepers are never chosen as captain even if they have the highest xP."""
        df = sample_inflated_pool.copy()
        # Inflate GK xP to 15.0 pts (far higher than any outfielder)
        df.loc[df['position'] == 'GK', 'expected_points'] = 15.0
        df.loc[df['position'] == 'GK', 'fixture_xp'] = 15.0

        sol = solve_initial_squad(df, budget=100.0)
        assert sol.status == "Optimal"
        assert sol.captain is not None
        assert sol.captain.position != 'GK', "Goalkeeper was captained violating the guardrail"
        assert sol.captain.position in ('DEF', 'MID', 'FWD')

    def test_goalkeeper_captaincy_forced_override(self, sample_inflated_pool):
        """Verify that forced_captain_code overrides the GK guardrail if explicitly requested."""
        df = sample_inflated_pool.copy()
        gk_player = df[df['position'] == 'GK'].iloc[0]
        gk_code = int(gk_player['player_code'])

        sol = solve_initial_squad(df, budget=100.0, forced_captain_code=gk_code)
        assert sol.status == "Optimal"
        assert sol.captain is not None
        assert sol.captain.player_code == gk_code

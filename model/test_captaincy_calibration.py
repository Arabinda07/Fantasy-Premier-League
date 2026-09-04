"""Unit and integration tests for M-05: Early-Season Captaincy Bayesian Confidence Calibration.

Verifies:
1. GW1 proven starters (Haaland, Salah, Palmer, Saka) receive full captaincy confidence (capt_conf == 1.0)
   instead of artificial 40%–60% penalties.
2. GW1 fringe cameo protection is strictly preserved (capt_conf <= 0.25).
3. Monotonic transition across early gameweeks (GW1 -> GW2 -> GW3 -> GW4 -> GW8).
4. Zero-drift convergence at GW9+ where current-season minutes completely dominate (w_prior == 0.0).
5. Robustness across column schemas (unweighted vs decayed long-form minutes, now_cost vs cost).
6. End-to-end squad solver optimization electing premier talismans without early-season penalty.
"""
import pytest
import pandas as pd
import numpy as np

from model.solver import (
    compute_calibrated_captaincy_confidence,
    prepare_solver_dataframe,
    solve_initial_squad,
    solve_squad_lineup,
)


class TestCaptaincyCalibrationFormulation:
    """Mathematical validation of the Empirical Bayes calibration formulation."""

    def test_gw1_nailed_premier_starters_no_penalty(self):
        """Verify premier talismans in GW1 (0 season minutes) receive 1.0 confidence via long-form prior."""
        df = pd.DataFrame([
            {
                'player_code': 1, 'web_name': 'Haaland', 'position': 'FWD', 'team': 'Man City',
                'cost': 15.0, 'expected_points': 8.5, 'p_start': 1.0,
                'season_minutes': 0, 'long_form_unweighted_minutes': 2850.0, 'gw': 1,
            },
            {
                'player_code': 2, 'web_name': 'Salah', 'position': 'MID', 'team': 'Liverpool',
                'cost': 12.5, 'expected_points': 8.0, 'p_start': 1.0,
                'season_minutes': 0, 'long_form_unweighted_minutes': 2900.0, 'gw': 1,
            },
            {
                'player_code': 3, 'web_name': 'Palmer', 'position': 'MID', 'team': 'Chelsea',
                'cost': 10.5, 'expected_points': 7.5, 'p_start': 1.0,
                'season_minutes': 0, 'long_form_unweighted_minutes': 2700.0, 'gw': 1,
            },
            {
                'player_code': 4, 'web_name': 'Saka', 'position': 'MID', 'team': 'Arsenal',
                'cost': 10.0, 'expected_points': 7.2, 'p_start': 1.0,
                'season_minutes': 0, 'long_form_unweighted_minutes': 2400.0, 'gw': 1,
            },
        ])

        conf = compute_calibrated_captaincy_confidence(df, current_gw=1)
        # All premier starters must achieve full 1.0 confidence
        assert (conf == 1.0).all()

        # In prepare_solver_dataframe, captain_points must match opt_points exactly
        prepared = prepare_solver_dataframe(df, current_gw=1)
        np.testing.assert_allclose(prepared['captain_points'], prepared['opt_points'])

    def test_gw1_fringe_cameo_protection_preserved(self):
        """Verify unproven fringe/cameo players with low historical minutes are heavily discounted."""
        df = pd.DataFrame([
            {
                'player_code': 10, 'web_name': 'Bench_Cameo', 'position': 'MID', 'team': 'Everton',
                'cost': 4.5, 'expected_points': 5.0, 'p_start': 0.20,
                'season_minutes': 0, 'long_form_unweighted_minutes': 90.0, 'gw': 1,
            },
            {
                'player_code': 11, 'web_name': 'Unproven_Youth', 'position': 'FWD', 'team': 'Ipswich',
                'cost': 4.5, 'expected_points': 4.5, 'p_start': 0.10,
                'season_minutes': 0, 'long_form_unweighted_minutes': 0.0, 'gw': 1,
            },
        ])

        conf = compute_calibrated_captaincy_confidence(df, current_gw=1)
        # Cameo player: M_prior_equiv = 720 * (90/1800) = 36 mins.
        # capt_conf = max(0.20, (36/720)*0.20 + 4.5/25) = max(0.20, 0.01 + 0.18) = 0.20
        assert conf.loc[0] <= 0.25
        assert conf.loc[1] <= 0.20

    def test_early_season_smooth_monotonic_progression(self):
        """Verify that an established starter who plays 90 mins weekly maintains 1.0 confidence throughout."""
        # Trace a starter who plays 90 mins every match in GW1, GW2, GW3, GW4, GW6, GW8, GW9
        gws = [1, 2, 3, 4, 6, 8, 9]
        for gw in gws:
            mins_played = 90.0 * max(0, gw - 1)
            player_df = pd.DataFrame([{
                'player_code': 1, 'web_name': 'Gabriel', 'position': 'DEF', 'team': 'Arsenal',
                'cost': 6.0, 'expected_points': 5.5, 'p_start': 1.0,
                'season_minutes': mins_played, 'long_form_unweighted_minutes': 2750.0, 'gw': gw,
            }])
            conf = compute_calibrated_captaincy_confidence(player_df, current_gw=gw)
            assert conf.iloc[0] == 1.0

    def test_late_season_convergence_gw9_plus(self):
        """At GW9+, players with season_mins >= 720 have w_prior == 0.0 and current-season minutes govern 100%,
        while injured returning talismans with low season_mins retain long-form prior protection."""
        df = pd.DataFrame([
            {
                # Mature starter with 720 season minutes
                'player_code': 1, 'web_name': 'Mature_Starter', 'position': 'MID', 'team': 'Arsenal',
                'cost': 8.0, 'expected_points': 5.0, 'p_start': 0.80,
                'season_minutes': 720.0, 'long_form_unweighted_minutes': 2700.0, 'gw': 10,
            },
            {
                # Injured returning talisman with only 180 season minutes but 2700 long-form minutes
                'player_code': 2, 'web_name': 'Returning_Talisman', 'position': 'MID', 'team': 'Liverpool',
                'cost': 12.0, 'expected_points': 7.5, 'p_start': 1.0,
                'season_minutes': 180.0, 'long_form_unweighted_minutes': 2700.0, 'gw': 10,
            },
            {
                # Fringe youth player with only 180 season minutes and 0 long-form minutes
                'player_code': 3, 'web_name': 'Fringe_Youth', 'position': 'MID', 'team': 'Ipswich',
                'cost': 4.5, 'expected_points': 2.0, 'p_start': 0.20,
                'season_minutes': 180.0, 'long_form_unweighted_minutes': 0.0, 'gw': 10,
            }
        ])

        conf = compute_calibrated_captaincy_confidence(df, current_gw=10)
        # Mature starter: 100% current season minutes govern
        # capt_conf = (720 / 720) * 0.80 + (8.0 / 25.0) = 0.80 + 0.32 = 1.0 (clipped)
        assert conf.iloc[0] == 1.0

        # Returning talisman: protected by long-form prior (M_calibrated == 720.0) -> full 1.0
        assert conf.iloc[1] == 1.0

        # Fringe player: no long-form prior, regularized
        assert conf.iloc[2] <= 0.40

    def test_decayed_ewma_long_form_minutes_handling(self):
        """Verify calibration scales correctly when only EWMA-decayed long_form_minutes is available."""
        # Player has decayed long_form_minutes = 1150 (EWMA half-life = 8 GWs on ~2800 unweighted mins)
        df = pd.DataFrame([{
            'player_code': 1, 'web_name': 'Haaland', 'position': 'FWD', 'team': 'Man City',
            'cost': 15.0, 'expected_points': 8.5, 'p_start': 1.0,
            'season_minutes': 0, 'long_form_minutes': 1150.0, 'gw': 1,
        }])

        conf = compute_calibrated_captaincy_confidence(df, current_gw=1)
        # 1150 / 1100 >= 1.0 -> M_prior_equiv = 720.0 -> capt_conf = 1.0
        assert conf.iloc[0] == 1.0

    def test_schema_resilience_and_defaults(self):
        """Verify safe execution across minimal dataframes, now_cost in tenths, and missing columns."""
        # 1. Cost in tenths (now_cost = 105 -> £10.5M)
        df_tenths = pd.DataFrame([{
            'player_code': 1, 'position': 'MID', 'team': 'Chelsea',
            'now_cost': 105, 'expected_points': 7.0, 'season_minutes': 0,
            'long_form_unweighted_minutes': 2700.0, 'gw': 1,
        }])
        conf_tenths = compute_calibrated_captaincy_confidence(df_tenths)
        assert conf_tenths.iloc[0] == 1.0

        # 2. Synthetic fixture with no minutes columns at all (backward compatibility)
        df_synthetic = pd.DataFrame([{
            'player_code': 1, 'position': 'MID', 'team': 'Arsenal',
            'cost': 6.0, 'expected_points': 5.0,
        }])
        conf_synth = compute_calibrated_captaincy_confidence(df_synthetic)
        assert conf_synth.iloc[0] == 1.0

        # 3. Empty dataframe
        empty_conf = compute_calibrated_captaincy_confidence(pd.DataFrame())
        assert empty_conf.empty


class TestEndToEndSolverCaptaincy:
    """Integration tests verifying captain selection in the MILP solver for GW1–GW4."""

    @pytest.fixture
    def early_season_gw1_pool(self) -> pd.DataFrame:
        """Realistic GW1 player pool where season_minutes is 0 for all players."""
        players = [
            # GKs
            {'player_code': 1, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.5, 'expected_points': 5.2, 'season_minutes': 0, 'long_form_unweighted_minutes': 3330.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 2, 'web_name': 'Pickford', 'team': 'Everton', 'position': 'GK', 'cost': 5.0, 'expected_points': 4.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 3420.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 3, 'web_name': 'Fabianski', 'team': 'West Ham', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 180.0, 'p_start': 0.0, 'gw': 1},
            {'player_code': 4, 'web_name': 'Valdimarsson', 'team': 'Brentford', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 0.0, 'p_start': 0.0, 'gw': 1},
            # DEFs
            {'player_code': 5, 'web_name': 'Gabriel', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 2750.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 6, 'web_name': 'Saliba', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 5.8, 'season_minutes': 0, 'long_form_unweighted_minutes': 2614.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 7, 'web_name': 'Alexander-Arnold', 'team': 'Liverpool', 'position': 'DEF', 'cost': 7.0, 'expected_points': 6.2, 'season_minutes': 0, 'long_form_unweighted_minutes': 2500.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 8, 'web_name': 'Gvardiol', 'team': 'Man City', 'position': 'DEF', 'cost': 6.0, 'expected_points': 5.0, 'season_minutes': 0, 'long_form_unweighted_minutes': 2500.0, 'p_start': 0.95, 'gw': 1},
            {'player_code': 9, 'web_name': 'Robinson', 'team': 'Fulham', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.2, 'season_minutes': 0, 'long_form_unweighted_minutes': 2600.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 10, 'web_name': 'Bednarek', 'team': 'Southampton', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 2000.0, 'p_start': 0.90, 'gw': 1},
            {'player_code': 11, 'web_name': 'Greaves', 'team': 'Ipswich', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.2, 'season_minutes': 0, 'long_form_unweighted_minutes': 2000.0, 'p_start': 0.90, 'gw': 1},
            {'player_code': 12, 'web_name': 'Fodder_DEF', 'team': 'Southampton', 'position': 'DEF', 'cost': 4.0, 'expected_points': 0.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 0.0, 'p_start': 0.0, 'gw': 1},
            # MIDs
            {'player_code': 13, 'web_name': 'Salah', 'team': 'Liverpool', 'position': 'MID', 'cost': 12.5, 'expected_points': 8.2, 'season_minutes': 0, 'long_form_unweighted_minutes': 2900.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 14, 'web_name': 'Saka', 'team': 'Arsenal', 'position': 'MID', 'cost': 10.0, 'expected_points': 7.0, 'season_minutes': 0, 'long_form_unweighted_minutes': 2400.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 15, 'web_name': 'Palmer', 'team': 'Chelsea', 'position': 'MID', 'cost': 10.5, 'expected_points': 7.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 2700.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 16, 'web_name': 'Son', 'team': 'Spurs', 'position': 'MID', 'cost': 9.5, 'expected_points': 6.0, 'season_minutes': 0, 'long_form_unweighted_minutes': 2500.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 17, 'web_name': 'Rogers', 'team': 'Aston Villa', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.8, 'season_minutes': 0, 'long_form_unweighted_minutes': 2200.0, 'p_start': 0.95, 'gw': 1},
            {'player_code': 18, 'web_name': 'Winks', 'team': 'Leicester', 'position': 'MID', 'cost': 4.5, 'expected_points': 3.0, 'season_minutes': 0, 'long_form_unweighted_minutes': 2500.0, 'p_start': 0.90, 'gw': 1},
            {'player_code': 19, 'web_name': 'Fodder_MID', 'team': 'Brighton', 'position': 'MID', 'cost': 4.5, 'expected_points': 0.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 0.0, 'p_start': 0.0, 'gw': 1},
            # FWDs
            {'player_code': 20, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 9.0, 'season_minutes': 0, 'long_form_unweighted_minutes': 2850.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 21, 'web_name': 'Watkins', 'team': 'Aston Villa', 'position': 'FWD', 'cost': 9.0, 'expected_points': 6.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 2700.0, 'p_start': 1.0, 'gw': 1},
            {'player_code': 22, 'web_name': 'Wood', 'team': 'Nott\'m Forest', 'position': 'FWD', 'cost': 6.0, 'expected_points': 4.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 2200.0, 'p_start': 0.90, 'gw': 1},
            {'player_code': 23, 'web_name': 'Fodder_FWD', 'team': 'Southampton', 'position': 'FWD', 'cost': 4.5, 'expected_points': 0.5, 'season_minutes': 0, 'long_form_unweighted_minutes': 0.0, 'p_start': 0.0, 'gw': 1},
        ]
        return pd.DataFrame(players)

    def test_solve_initial_squad_gw1_elects_talisman_unpenalized(self, early_season_gw1_pool):
        """In GW1 with 0 season minutes, premier talisman must be elected captain with 100% full captain yield."""
        sol = solve_initial_squad(early_season_gw1_pool, budget=100.0, current_gw=1)

        assert sol.status == 'Optimal'
        assert sol.captain is not None
        assert sol.captain.web_name in ('Haaland', 'Salah')
        # Captain bonus points must equal 100% of the captain's expected points (e.g. 8.2), not 50%
        assert abs(sol.captain_xp - sol.captain.expected_points) < 1e-4

    def test_solve_squad_lineup_gw1_unpenalized(self, early_season_gw1_pool):
        """solve_squad_lineup in GW1 assigns vice-captain and captain without premature penalty."""
        sol = solve_initial_squad(early_season_gw1_pool, budget=100.0, current_gw=1)
        squad_df = pd.DataFrame([
            {
                'player_code': p.player_code, 'web_name': p.web_name, 'team': p.team,
                'position': p.position, 'cost': p.cost, 'expected_points': p.expected_points,
                'season_minutes': 0, 'long_form_unweighted_minutes': 2800.0, 'p_start': 1.0, 'gw': 1,
            }
            for p in sol.starters + sol.bench
        ])

        lineup_sol = solve_squad_lineup(squad_df, current_gw=1)
        assert lineup_sol.captain is not None
        assert lineup_sol.captain.web_name in ('Haaland', 'Salah')
        assert abs(lineup_sol.captain_xp - lineup_sol.captain.expected_points) < 1e-4

    def test_solve_haaland_anchor_gw1_full_yield(self, early_season_gw1_pool):
        """When Haaland is forced or highest yield, his 9.0 xP translates to exact 9.0 captain bonus."""
        sol = solve_initial_squad(
            early_season_gw1_pool, budget=100.0, current_gw=1, forced_captain_code='Haaland'
        )
        assert sol.captain is not None
        assert sol.captain.web_name == 'Haaland'
        assert abs(sol.captain_xp - 9.0) < 1e-4

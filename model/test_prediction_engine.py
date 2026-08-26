"""Tests for model.prediction_engine — the 11-component point prediction engine.

Verifies:
1. Poisson mathematical probability helper distributions (clean sheet, 2+ GC, DC threshold).
2. Position-specific scoring mechanics (FWD, MID, DEF, GK).
3. Elite player profiles (Haaland, Gabriel, Raya).
4. Edge cases (0-minute players, missing stats).
5. Vectorized batch execution vs row-by-row consistency.
"""
import math
import os
import sys
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import (
    poisson_pmf,
    poisson_cdf,
    poisson_clean_sheet_prob,
    poisson_two_plus_gc_prob,
    poisson_exact_gc_penalty,
    poisson_dc_hit_prob,
    apply_empirical_bayes_shrinkage,
    estimate_playing_probabilities,
    predict_player_points,
    predict_all_players,
    GOAL_POINTS,
    CLEAN_SHEET_POINTS,
    POSITIONAL_PRIORS,
)


class TestPoissonMath:
    """Verify Poisson distribution functions."""

    def test_poisson_pmf(self):
        # P(X=0; lambda=1.0) = e^-1 ~= 0.367879
        assert abs(poisson_pmf(0, 1.0) - math.exp(-1.0)) < 1e-6
        # P(X=1; lambda=1.0) = 1.0 * e^-1 ~= 0.367879
        assert abs(poisson_pmf(1, 1.0) - math.exp(-1.0)) < 1e-6
        # P(X=2; lambda=2.0) = (4/2) * e^-2 = 2 * e^-2 ~= 0.27067
        assert abs(poisson_pmf(2, 2.0) - (2.0 * math.exp(-2.0))) < 1e-5

    def test_clean_sheet_probability(self):
        # lambda = 0 -> 100% clean sheet
        assert poisson_clean_sheet_prob(0.0) == 1.0
        # lambda = 1.0 -> e^-1 ~= 0.3679
        assert abs(poisson_clean_sheet_prob(1.0) - 0.367879) < 1e-4
        # lambda = 0.5 -> e^-0.5 ~= 0.6065
        assert abs(poisson_clean_sheet_prob(0.5) - 0.60653) < 1e-4

    def test_two_plus_gc_probability(self):
        # lambda = 0 -> 0% chance of 2+ GC
        assert poisson_two_plus_gc_prob(0.0) == 0.0
        # lambda = 1.0 -> 1 - e^-1 - e^-1 = 1 - 2*e^-1 ~= 0.2642
        expected = 1.0 - (2.0 * math.exp(-1.0))
        assert abs(poisson_two_plus_gc_prob(1.0) - expected) < 1e-4

    def test_dc_hit_probability(self):
        # threshold 9, lambda = 9.0 -> P(X >= 9) ~= 0.544
        prob = poisson_dc_hit_prob(9.0, 9)
        assert 0.50 < prob < 0.60
        # zero lambda -> 0.0
        assert poisson_dc_hit_prob(0.0, 9) == 0.0


class TestPlayingProbabilities:
    """Verify playing time & appearance probability estimation."""

    def test_nailed_starter(self):
        probs = estimate_playing_probabilities(
            starts=35.0, subs=0.0, unused_subs=0.0, total_minutes=3150.0, position='FWD'
        )
        assert probs['p_start'] == 1.0
        assert probs['p_app'] == 1.0
        assert probs['p_60_plus'] >= 0.95

    def test_rotation_player(self):
        probs = estimate_playing_probabilities(
            starts=15.0, subs=15.0, unused_subs=5.0, total_minutes=1500.0, position='MID'
        )
        assert 0.40 <= probs['p_start'] <= 0.50
        assert probs['p_app'] > probs['p_start']

    def test_zero_minutes_player(self):
        probs = estimate_playing_probabilities(
            starts=0.0, subs=0.0, unused_subs=0.0, total_minutes=0.0, position='DEF'
        )
        assert probs['p_start'] == 0.0
        assert probs['p_app'] == 0.0
        assert probs['p_60_plus'] == 0.0


class TestPlayerPositionPredictions:
    """Verify point breakdown across FWD, MID, DEF, and GK."""

    def test_haaland_forward_prediction(self):
        haaland = {
            'web_name': 'Haaland',
            'position': 'FWD',
            'season_starts': 35,
            'season_minutes': 2953,
            'long_form_minutes': 5689,
            'long_form_expected_goals_90': 0.7499,
            'long_form_expected_assists_90': 0.0745,
            'team_long_form_xgc90': 1.0,
            'long_form_defensive_contribution_90': 3.17,
            'long_form_bonus_90': 1.31,
        }
        pred = predict_player_points(haaland)

        # FWD gets 4 points per goal
        assert GOAL_POINTS['FWD'] == 4.0
        assert pred['c8_goals'] > 2.5  # 4 * 0.75 * ~1.0 ~= 3.0
        # FWD gets 0 points for clean sheets
        assert pred['c9_clean_sheets'] == 0.0
        # FWD does not suffer 2+ GC penalties
        assert pred['c10_goals_conceded'] == 0.0
        # Total xP should be strong (~6 to 7 pts per game)
        assert 5.5 <= pred['expected_points'] <= 8.5

    def test_gabriel_defender_prediction(self):
        gabriel = {
            'web_name': 'Gabriel',
            'position': 'DEF',
            'season_starts': 34,
            'season_minutes': 2750,
            'long_form_minutes': 5000,
            'long_form_expected_goals_90': 0.15,
            'long_form_expected_assists_90': 0.04,
            'team_long_form_xgc90': 0.85,  # strong Arsenal defense
            'long_form_defensive_contribution_90': 9.5,
            'long_form_bonus_90': 0.40,
        }
        pred = predict_player_points(gabriel)

        # DEF gets 6 points per goal
        assert GOAL_POINTS['DEF'] == 6.0
        # Clean sheets should give positive points (4 * exp(-0.85) ~= 1.7)
        assert pred['c9_clean_sheets'] > 1.3
        # DC threshold is 10, with 9.5 rate gives ~0.36 pts
        assert pred['c11_defensive_contributions'] > 0.3
        # Total xP should be around 4 to 5.5 pts per game
        assert 3.5 <= pred['expected_points'] <= 6.0

    def test_raya_goalkeeper_prediction(self):
        raya = {
            'web_name': 'Raya',
            'position': 'GK',
            'season_starts': 37,
            'season_minutes': 3330,
            'long_form_minutes': 3330,
            'long_form_expected_goals_90': 0.0,
            'long_form_expected_assists_90': 0.0,
            'team_long_form_xgc90': 0.74,
            'saves_90': 2.5,
            'long_form_defensive_contribution_90': 1.0,
            'long_form_bonus_90': 0.30,
        }
        pred = predict_player_points(raya)

        # Saves points
        assert pred['c3_saves'] > 0.6  # 2.5 / 3.0 ~= 0.83
        # Clean sheets points (4 * exp(-0.74) ~= 1.9)
        assert pred['c9_clean_sheets'] > 1.5
        # Total xP around 3.5 to 5.0
        assert 3.0 <= pred['expected_points'] <= 5.5

    def test_inactive_player_zero_points(self):
        inactive = {
            'web_name': 'Ruddy',
            'position': 'GK',
            'season_starts': 0,
            'season_minutes': 0,
            'long_form_minutes': 0,
            'long_form_expected_goals_90': 0.0,
        }
        pred = predict_player_points(inactive)
        assert pred['expected_points'] == 0.0
        assert pred['c1_app_1_60'] == 0.0
        assert pred['c8_goals'] == 0.0


class TestVectorizedBatchExecution:
    """Verify predict_all_players runs on full DataFrames and matches single-row output."""

    def test_batch_prediction_consistency(self):
        players_data = [
            {
                'player_code': 223094,
                'web_name': 'Haaland',
                'position': 'FWD',
                'season_starts': 35,
                'season_minutes': 2953,
                'long_form_expected_goals_90': 0.75,
                'long_form_expected_assists_90': 0.08,
            },
            {
                'player_code': 226597,
                'web_name': 'Gabriel',
                'position': 'DEF',
                'season_starts': 34,
                'season_minutes': 2750,
                'team_long_form_xgc90': 0.85,
                'long_form_defensive_contribution_90': 9.5,
            },
            {
                'player_code': 19236,
                'web_name': 'Ruddy',
                'position': 'GK',
                'season_starts': 0,
                'season_minutes': 0,
            },
        ]
        df = pd.DataFrame(players_data)
        batch_df = predict_all_players(df)

        assert len(batch_df) == 3
        assert 'expected_points' in batch_df.columns
        assert 'c8_goals' in batch_df.columns
        assert 'c9_clean_sheets' in batch_df.columns

        # Verify Haaland's batch prediction matches single row
        single_haaland = predict_player_points(players_data[0])
        assert batch_df.iloc[0]['expected_points'] == single_haaland['expected_points']
        assert batch_df.iloc[0]['c8_goals'] == single_haaland['c8_goals']

        # Verify Ruddy has 0.0
        assert batch_df.iloc[2]['expected_points'] == 0.0


class TestEmpiricalBayesShrinkage:
    """Verify Empirical Bayes shrinkage formula and Dowman anomaly fix."""

    def test_shrinkage_formula_weights(self):
        # 152 mins with M0=500: raw weight = 152 / 652 ~= 0.2331, prior weight = 500 / 652 ~= 0.7669
        raw = 0.7046
        prior = 0.15
        adj = apply_empirical_bayes_shrinkage(raw, 152.0, prior, m0=500.0)
        expected = (152.0 / 652.0) * raw + (500.0 / 652.0) * prior
        assert abs(adj - expected) < 1e-6
        assert abs(adj - 0.2793) < 1e-3

    def test_zero_minutes_shrinkage(self):
        # 0 mins should return prior directly
        adj = apply_empirical_bayes_shrinkage(0.85, 0.0, 0.35, m0=500.0)
        assert adj == 0.35

    def test_large_sample_retains_raw_rate(self):
        # 3000 mins: raw weight = 3000 / 3500 ~= 85.7%
        adj = apply_empirical_bayes_shrinkage(0.80, 3000.0, 0.35, m0=500.0)
        assert adj > 0.73

    def test_dowman_remediated_prediction(self):
        # Dowman: 152 mins, raw xG90 = 0.7046 -> shrunken to ~0.279 xG90 -> xP drops from 7.07 to ~3.2
        dowman = {
            'web_name': 'Dowman',
            'position': 'MID',
            'season_starts': 1,
            'season_minutes': 152,
            'long_form_minutes': 152,
            'long_form_expected_goals_90': 0.7046,
            'long_form_expected_assists_90': 0.1776,
            'long_form_defensive_contribution_90': 9.4737,
            'team_long_form_xgc90': 0.7635,
        }
        pred = predict_player_points(dowman)
        # Should no longer be 7.07, should drop by ~2.5 points to ~4.5
        assert 3.5 <= pred['expected_points'] <= 4.8
        # Goals component should be ~1.4 (5 * 0.279), not 3.52
        assert 1.1 <= pred['c8_goals'] <= 1.6


class TestExactDiscreteGCPenalty:
    """Verify exact discrete Poisson GC expectation (-1 pt per 2 goals)."""

    def test_zero_xgc_zero_penalty(self):
        assert poisson_exact_gc_penalty(0.0) == 0.0

    def test_penalty_is_negative(self):
        penalty = poisson_exact_gc_penalty(1.2)
        assert penalty < 0.0

    def test_penalty_scales_with_high_xgc(self):
        pen_low = poisson_exact_gc_penalty(0.8)
        pen_high = poisson_exact_gc_penalty(2.4)
        # Higher xGC must result in more negative penalty
        assert pen_high < pen_low
        # Under 2.4 xGC, expected penalty is heavier than simple binary -1 pt * P(>=2)
        assert pen_high < -0.8


class TestStarterMinutesProration:
    """Verify starter active ratio scales by average minutes per start."""

    def test_full_90_minute_starter(self):
        probs = estimate_playing_probabilities(
            starts=30.0, subs=0.0, unused_subs=0.0, total_minutes=2700.0, position='FWD'
        )
        assert probs['active_ratio'] == 1.0

    def test_early_substitution_starter(self):
        # 20 starts, 1200 total mins -> 60 mins/start -> active_ratio = 1.0 * (60/90) = 0.6667
        probs = estimate_playing_probabilities(
            starts=20.0, subs=0.0, unused_subs=0.0, total_minutes=1200.0, position='MID'
        )
        assert abs(probs['active_ratio'] - (60.0 / 90.0)) < 1e-3

    def test_min_max_clamping(self):
        # Starts with 20 mins/start clamped at 45 mins
        probs_low = estimate_playing_probabilities(
            starts=10.0, subs=0.0, unused_subs=0.0, total_minutes=200.0, position='FWD'
        )
        assert abs(probs_low['active_ratio'] - (45.0 / 90.0)) < 1e-3


class TestColdStartPriors:
    """Verify newly transferred players with 0 historical PL minutes receive price-based priors."""

    def test_marquee_signing_prior(self):
        # £10.0M new marquee signing with 0 PL minutes
        marquee = {
            'web_name': 'Wirtz',
            'position': 'MID',
            'season_starts': 0,
            'season_minutes': 0,
            'now_cost': 100,  # £10.0M
            'status': 'a',
            'team_long_form_xgc90': 0.8,
        }
        pred = predict_player_points(marquee)
        assert pred['p_start'] >= 0.80
        assert pred['p_app'] >= 0.85
        assert pred['expected_points'] > 2.5

    def test_budget_reserve_prior(self):
        # £4.0M non-playing reserve with 0 PL minutes
        reserve = {
            'web_name': 'Youngster',
            'position': 'DEF',
            'season_starts': 0,
            'season_minutes': 0,
            'now_cost': 40,  # £4.0M
            'status': 'a',
        }
        pred = predict_player_points(reserve)
        assert pred['p_start'] == 0.0
        assert pred['expected_points'] == 0.0


class TestDisciplinaryCorrection:
    """Verify yellow card and red card deductions follow official FPL rules."""

    def test_yellow_red_separation(self):
        player = {
            'web_name': 'AggressiveMid',
            'position': 'MID',
            'season_starts': 30,
            'season_minutes': 2700,
            'yellow_cards_90': 0.30,
            'red_cards_90': 0.05,
        }
        pred = predict_player_points(player)
        # F-02 fix: in FPL, yellow cards and red cards are both deducted separately
        # c4 should be -0.30 (1.0 * 0.30 * 1.0), c5 should be -0.15 (3.0 * 0.05 * 1.0)
        assert abs(pred['c4_yellow_cards'] - (-0.30)) < 1e-3
        assert abs(pred['c5_red_cards'] - (-0.15)) < 1e-3


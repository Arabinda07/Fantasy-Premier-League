"""Unit tests for M-02: Continuous Minutes Survival Hazard Integration.

Validates:
1. Mathematical alignment of C1 (P(App)) and C2 (P(60+)) with survival analysis.
2. Manager tactical hook propensities directly reducing C2 and P(60+).
3. C11 Defensive Contributions rate normalization eliminating double-discounting.
4. European midweek congestion decay (<= 3 days rest) dampening playing probabilities.
5. Inactive bench fodder clean zeroing vs marquee signing cold-start priors.
"""
import math
import pytest
import pandas as pd

from model.prediction_engine import (
    predict_player_points,
    poisson_dc_hit_prob,
)
from model.minutes_model import (
    compute_player_minutes_hazard,
    calculate_pre60_hook_probability,
    MinutesDistributionProfile,
)


class TestMinutesHazardPointIntegration:
    """Verify integration of continuous minutes survival hazard into C1, C2, and C11."""

    def test_c1_c2_survival_hazard_alignment(self):
        """C1 and C2 must reflect P(App) and P(60+) from the continuous survival hazard engine."""
        nailed_starter = {
            'web_name': 'VanDijk',
            'position': 'DEF',
            'team': 'Liverpool',
            'season_starts': 36,
            'season_minutes': 3240,
            'long_form_minutes': 3240,
            'team_long_form_xgc90': 0.95,
            'long_form_defensive_contribution_90': 8.5,
            'status': 'a',
            'chance_of_playing_next_round': 100,
        }

        pred = predict_player_points(nailed_starter)

        # Nailed starter should have near-certain start and 60+ probability
        assert pred['p_start'] >= 0.95
        assert pred['p_app'] >= 0.95
        assert pred['p_60_plus'] >= 0.90
        assert pred['c1_app_1_60'] == pytest.approx(1.0 * pred['p_app'], abs=1e-4)
        assert pred['c2_app_60_plus'] == pytest.approx(1.0 * pred['p_60_plus'], abs=1e-4)

        # Total appearance points equals 1 * P(1<=M<60) + 2 * P(M>=60)
        p_1_to_59 = pred['p_app'] - pred['p_60_plus']
        expected_total_app = 1.0 * p_1_to_59 + 2.0 * pred['p_60_plus']
        assert pred['c1_app_1_60'] + pred['c2_app_60_plus'] == pytest.approx(expected_total_app, abs=1e-4)

    def test_tactical_hook_risk_lowers_c2(self):
        """A player under a rotation-heavy manager with lower starter duration suffers hook risk on C2."""
        # Winger subbed off early around min 60 vs Full 90 Central Defender
        winger = {
            'web_name': 'Trossard',
            'position': 'MID',
            'team': 'Arsenal',
            'season_starts': 20,
            'season_minutes': 1300,  # 65 mins per start
            'status': 'a',
            'chance_of_playing_next_round': 100,
        }
        cb = {
            'web_name': 'Saliba',
            'position': 'DEF',
            'team': 'Arsenal',
            'season_starts': 20,
            'season_minutes': 1800,  # 90 mins per start
            'status': 'a',
            'chance_of_playing_next_round': 100,
        }

        pred_winger = predict_player_points(winger)
        pred_cb = predict_player_points(cb)

        # Both have similar appearance probabilities
        assert abs(pred_winger['p_app'] - pred_cb['p_app']) < 0.05
        # But winger has significantly lower P(60+) and C2 due to early hook hazard
        assert pred_winger['p_60_plus'] < pred_cb['p_60_plus']
        assert pred_winger['c2_app_60_plus'] < pred_cb['c2_app_60_plus']

    def test_c11_defensive_contributions_rate_normalization(self):
        """C11 rate must condition on 60+ minutes played, eliminating double-discounting."""
        stopper = {
            'web_name': 'Collins',
            'position': 'DEF',
            'team': 'Brentford',
            'season_starts': 30,
            'season_minutes': 2700,
            'long_form_minutes': 2700,
            'long_form_defensive_contribution_90': 9.2,  # Strong defensive stopper
            'status': 'a',
        }

        pred = predict_player_points(stopper)

        # With 9.2 DC/90 and full 90-minute starter duration:
        # lambda_dc_60 = 9.2 * (90/90) = 9.2
        # P(DC >= 10 | lambda=9.2) ~= 0.439
        # P(DC >= 15 | lambda=9.2) ~= 0.046
        # Expected C11 ~= (0.439 + 0.046) * 1.0 ~= 0.485 pts
        assert pred['c11_defensive_contributions'] > 0.40
        assert pred['c11_defensive_contributions'] < 0.70

        # Monotonicity test: doubling DC/90 must strictly increase C11
        stopper_elite = dict(stopper)
        stopper_elite['long_form_defensive_contribution_90'] = 14.0
        pred_elite = predict_player_points(stopper_elite)
        assert pred_elite['c11_defensive_contributions'] > pred['c11_defensive_contributions']

    def test_european_midweek_congestion_dampens_c1_c2(self):
        """<=3 days turnaround for European clubs reduces P(Start), C1, and C2."""
        haaland = {
            'web_name': 'Haaland',
            'position': 'FWD',
            'team': 'Man City',
            'season_starts': 30,
            'season_minutes': 2550,
            'status': 'a',
        }

        pred_fresh = predict_player_points(haaland, days_rest=7)
        pred_congested = predict_player_points(haaland, days_rest=3)

        assert pred_congested['p_start'] < pred_fresh['p_start']
        assert pred_congested['c1_app_1_60'] < pred_fresh['c1_app_1_60']
        assert pred_congested['c2_app_60_plus'] < pred_fresh['c2_app_60_plus']
        assert pred_congested['expected_points'] < pred_fresh['expected_points']

    def test_unseeded_inactive_bench_fodder_zero_points(self):
        """A £4.0M bench player with 0 starts and 0 minutes must cleanly evaluate to 0.0 points."""
        bench_fodder = {
            'web_name': 'ReserveGK',
            'position': 'GK',
            'season_starts': 0,
            'season_minutes': 0,
            'long_form_minutes': 0,
            'now_cost': 40,  # £4.0M
            'status': 'a',
        }
        pred = predict_player_points(bench_fodder)
        assert pred['expected_points'] == 0.0
        assert pred['p_start'] == 0.0
        assert pred['p_app'] == 0.0
        assert pred['p_60_plus'] == 0.0
        assert pred['c1_app_1_60'] == 0.0
        assert pred['c2_app_60_plus'] == 0.0
        assert pred['c11_defensive_contributions'] == 0.0

    def test_marquee_cold_start_prior(self):
        """A marquee £10.0M signing with 0 historical PL minutes receives high baseline prior."""
        marquee = {
            'web_name': 'NewStar',
            'position': 'MID',
            'season_starts': 0,
            'season_minutes': 0,
            'now_cost': 100,  # £10.0M
            'long_form_expected_goals_90': 0.35,
            'long_form_expected_assists_90': 0.25,
            'status': 'a',
        }
        pred = predict_player_points(marquee)
        assert pred['p_start'] >= 0.85
        assert pred['p_app'] >= 0.85
        assert pred['c1_app_1_60'] >= 0.85
        assert pred['c2_app_60_plus'] >= 0.75
        assert pred['expected_points'] > 3.0

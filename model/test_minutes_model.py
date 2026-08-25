"""Unit tests for Continuous Minutes Hazard Engine (model/minutes_model.py)."""
import pytest
import pandas as pd
import numpy as np

from model.minutes_model import (
    calculate_pre60_hook_probability,
    compute_player_minutes_hazard,
    predict_gameweek_minutes_distribution,
    MinutesDistributionProfile,
)


class TestMinutesHazardMath:
    """Test mathematical properties and boundary constraints of the minutes hazard engine."""

    def test_pre60_hook_probability_bounds_and_hierarchy(self):
        """Verify that pre-60 hook probability scales logically with starter minutes."""
        # Goalkeeper hook probability should be negligible
        gk_hook = calculate_pre60_hook_probability(avg_starter_mins=90.0, is_goalkeeper=True)
        assert gk_hook <= 0.01

        # Central defender hook probability should be lower than winger hook probability
        def_hook = calculate_pre60_hook_probability(avg_starter_mins=75.0, is_defender=True)
        mid_hook = calculate_pre60_hook_probability(avg_starter_mins=75.0, is_defender=False)
        assert def_hook < mid_hook

        # Player with low avg minutes (e.g. 58m) should have high hook probability
        early_sub_hook = calculate_pre60_hook_probability(avg_starter_mins=58.0)
        nailed_hook = calculate_pre60_hook_probability(avg_starter_mins=90.0)
        assert early_sub_hook > nailed_hook
        assert early_sub_hook > 0.25
        assert nailed_hook < 0.05

    def test_probability_conservation(self):
        """Verify that P(Start) + P(Sub) + P(DNP) sums to 1.0 (within float precision)."""
        player = {
            'player_code': 101,
            'web_name': 'Saka',
            'team': 'Arsenal',
            'position': 'MID',
            'short_form_starts': 5,
            'short_form_matches': 6,
            'short_form_minutes': 430,
            'status': 'a',
            'chance_of_playing_next_round': 100,
        }
        prof = compute_player_minutes_hazard(player, days_rest=7)
        total_p = prof.p_start + prof.p_sub + prof.p_dnp
        assert abs(total_p - 1.0) < 1e-4

        # Verify appearance xP matches FPL point rules
        # appearance_xp = 1 * P(1<=M<60) + 2 * P(M>=60)
        p_1_to_59 = (prof.p_start + prof.p_sub) - prof.p_60_plus
        expected_app = p_1_to_59 * 1.0 + prof.p_60_plus * 2.0
        assert abs(prof.appearance_xp - expected_app) < 1e-4

    def test_injury_status_zeroing(self):
        """Verify that status='i' or chance=0 forces P(DNP)=1.0 and 0.0 expected minutes."""
        injured_player = {
            'player_code': 102,
            'web_name': 'Odegaard',
            'team': 'Arsenal',
            'position': 'MID',
            'status': 'i',
            'chance_of_playing_next_round': 0,
        }
        prof = compute_player_minutes_hazard(injured_player)
        assert prof.p_start == 0.0
        assert prof.p_sub == 0.0
        assert prof.p_dnp == 1.0
        assert prof.p_60_plus == 0.0
        assert prof.expected_minutes == 0.0
        assert prof.appearance_xp == 0.0
        assert any("UNAVAILABLE" in f for f in prof.hazard_flags)

    def test_midweek_european_rest_hazard(self):
        """Verify that <=3 days rest dampens P(Start) for European clubs."""
        player = {
            'player_code': 103,
            'web_name': 'Haaland',
            'team': 'Man City',
            'position': 'FWD',
            'short_form_starts': 6,
            'short_form_matches': 6,
            'short_form_minutes': 540,
            'status': 'a',
            'chance_of_playing_next_round': 100,
        }
        prof_fresh = compute_player_minutes_hazard(player, days_rest=7)
        prof_fatigued = compute_player_minutes_hazard(player, days_rest=3)

        assert prof_fatigued.p_start < prof_fresh.p_start
        assert prof_fatigued.expected_minutes < prof_fresh.expected_minutes
        assert any("MIDWEEK_CONGESTION" in f for f in prof_fatigued.hazard_flags)

    def test_flagged_news_dampening(self):
        """Verify that 75% or 50% chance flags correctly dampen starter probability."""
        player_75 = {
            'player_code': 104,
            'web_name': 'Palmer',
            'team': 'Chelsea',
            'position': 'MID',
            'short_form_starts': 6,
            'short_form_matches': 6,
            'short_form_minutes': 510,
            'status': 'd',
            'chance_of_playing_next_round': 75,
        }
        player_50 = {
            'player_code': 105,
            'web_name': 'Palmer_Doubt',
            'team': 'Chelsea',
            'position': 'MID',
            'short_form_starts': 6,
            'short_form_matches': 6,
            'short_form_minutes': 510,
            'status': 'd',
            'chance_of_playing_next_round': 50,
        }
        prof_75 = compute_player_minutes_hazard(player_75)
        prof_50 = compute_player_minutes_hazard(player_50)

        assert prof_75.p_start > prof_50.p_start
        assert prof_75.expected_minutes > prof_50.expected_minutes

    def test_predict_gameweek_minutes_distribution_dataframe(self):
        """Verify DataFrame batch processing for gameweek minutes distribution."""
        df = pd.DataFrame([
            {'player_code': 1, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'short_form_starts': 6, 'short_form_matches': 6, 'short_form_minutes': 540, 'status': 'a'},
            {'player_code': 2, 'web_name': 'Gabriel', 'team': 'Arsenal', 'position': 'DEF', 'short_form_starts': 6, 'short_form_matches': 6, 'short_form_minutes': 530, 'status': 'a'},
            {'player_code': 3, 'web_name': 'Martinelli', 'team': 'Arsenal', 'position': 'MID', 'short_form_starts': 5, 'short_form_matches': 6, 'short_form_minutes': 380, 'sub_minute_p50': 62.0, 'status': 'a'},
            {'player_code': 4, 'web_name': 'BenchDefender', 'team': 'Ipswich Town', 'position': 'DEF', 'short_form_starts': 0, 'short_form_matches': 3, 'short_form_minutes': 35, 'status': 'a'},
        ])

        res = predict_gameweek_minutes_distribution(df, days_rest=7)
        assert len(res) == 4
        assert 'p_start' in res.columns
        assert 'p_60_plus' in res.columns
        assert 'expected_minutes' in res.columns
        assert 'p_dnp' in res.columns

        # Raya (GK) should have near 0 hook hazard
        raya_row = res[res['web_name'] == 'Raya'].iloc[0]
        assert raya_row['p_60_plus'] > 0.90
        assert raya_row['p_pre60_hook'] < 0.02

        # Martinelli (frequent sub) should have higher hook hazard than Raya
        martinelli_row = res[res['web_name'] == 'Martinelli'].iloc[0]
        assert martinelli_row['p_pre60_hook'] > raya_row['p_pre60_hook']

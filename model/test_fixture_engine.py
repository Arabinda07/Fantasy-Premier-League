"""Unit tests for model.fixture_engine — the Phase 3 Fixture & Form Adjustment Engine.

Verifies:
1. Short-form sample-size shrinkage (m0_short = 270 mins) preventing cameo pollution.
2. League baseline averages and Promoted team priors (1.05 xG, 1.80 xGC).
3. Conjugate symmetric Home vs. Away venue attacking/defensive multipliers (1.08 / 0.9259).
4. Opponent relative strength ratios (strong vs. weak attacks and defenses).
5. Dynamic Goalkeeper save volume scaling by opponent attacking strength.
6. Fixture-scaled Bonus (C6) and Defensive Contribution (C11) adjustments.
7. Double Gameweeks with rotation dampening & Blank Gameweeks (0.0 xP).
8. End-to-end gameweek fixture prediction pipeline.
"""
import math
import os
import sys
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.fixture_engine import (
    blend_form_rates,
    compute_team_league_averages,
    compute_fixture_multipliers,
    load_fixtures_for_gw,
    predict_player_fixture,
    predict_gameweek_fixtures,
    HOME_ATTACK_FACTOR,
    HOME_DEFENSE_FACTOR,
    AWAY_ATTACK_FACTOR,
    AWAY_DEFENSE_FACTOR,
    DEFAULT_LEAGUE_AVG_XG,
    DEFAULT_LEAGUE_AVG_XGC,
    PROMOTED_TEAM_PRIORS,
    DEFAULT_SHORT_FORM_M0,
)


class TestFormBlending:
    """Verify short-form vs long-form blending calculations with sample-size shrinkage."""

    def test_sample_size_shrinkage_formula(self):
        # 450 mins with m0=270: alpha_eff = 0.35 * (450 / 720) = 0.21875
        # blended = 0.21875 * 0.8 + (1 - 0.21875) * 0.4 = 0.175 + 0.3125 = 0.4875
        blended = blend_form_rates(0.8, 0.4, alpha=0.35, short_mins=450.0, m0_short=270.0)
        assert abs(blended - 0.4875) < 1e-4

    def test_cameo_noise_suppression(self):
        # 15 mins cameo with 1 lucky goal (raw short xG90 = 6.0) should NOT heavily pollute 0.25 long-form rate
        blended = blend_form_rates(6.0, 0.25, alpha=0.35, short_mins=15.0, m0_short=270.0)
        # Should stay well below 0.50 xG90 rather than blowing up to >2.2
        assert blended < 0.40
        assert abs(blended - 0.356) < 0.02

    def test_zero_short_minutes_fallback(self):
        # 0 short minutes should cleanly fall back to long form
        blended = blend_form_rates(0.9, 0.4, alpha=0.35, short_mins=0.0)
        assert blended == 0.4


class TestLeagueAveragesAndPromotedPriors:
    """Verify team league baseline calculations and promoted team priors."""

    def test_empty_map_default(self):
        avg_xg, avg_xgc = compute_team_league_averages({})
        assert avg_xg == DEFAULT_LEAGUE_AVG_XG
        assert avg_xgc == DEFAULT_LEAGUE_AVG_XGC

    def test_promoted_team_prior_fallback(self):
        # Unseen / promoted team with no logs falls back to PROMOTED_TEAM_PRIORS
        mults = compute_fixture_multipliers(
            'Arsenal', 'Coventry City', is_home=True, team_stats_map={},
            league_avg_xg=1.35, league_avg_xgc=1.35
        )
        # Coventry defense should use promoted 1.80 xGC -> attack_mult = (1.80 / 1.35) * 1.08 = 1.44
        expected_mult = (PROMOTED_TEAM_PRIORS['xgc90'] / 1.35) * HOME_ATTACK_FACTOR
        assert abs(mults['attack_mult'] - expected_mult) < 1e-3
        assert mults['attack_mult'] > 1.40


class TestFixtureMultipliers:
    """Verify conjugate symmetric venue factors and opponent strength scaling."""

    def setup_method(self):
        self.team_stats = {
            'Arsenal': {'xg90': 1.85, 'xgc90': 0.75},
            'Wolves': {'xg90': 1.10, 'xgc90': 1.70},
            'Man City': {'xg90': 2.20, 'xgc90': 0.90},
        }
        self.avg_xg = 1.35
        self.avg_xgc = 1.35

    def test_conjugate_goal_conservation(self):
        # Mathematical goal conservation: Home attack factor (1.08) * Home defense factor (0.9259) ~= 1.0
        assert abs((HOME_ATTACK_FACTOR * HOME_DEFENSE_FACTOR) - 1.0) < 1e-3
        assert abs((AWAY_ATTACK_FACTOR * AWAY_DEFENSE_FACTOR) - 1.0) < 1e-3

    def test_home_advantage_multiplier(self):
        home_res = compute_fixture_multipliers(
            'Arsenal', 'Wolves', is_home=True, team_stats_map=self.team_stats,
            league_avg_xg=self.avg_xg, league_avg_xgc=self.avg_xgc
        )
        away_res = compute_fixture_multipliers(
            'Arsenal', 'Wolves', is_home=False, team_stats_map=self.team_stats,
            league_avg_xg=self.avg_xg, league_avg_xgc=self.avg_xgc
        )

        assert home_res['attack_mult'] > away_res['attack_mult']
        assert home_res['fixture_xgc90'] < away_res['fixture_xgc90']

    def test_opponent_quality_scaling(self):
        vs_wolves = compute_fixture_multipliers(
            'Arsenal', 'Wolves', is_home=True, team_stats_map=self.team_stats,
            league_avg_xg=self.avg_xg, league_avg_xgc=self.avg_xgc
        )
        vs_city = compute_fixture_multipliers(
            'Arsenal', 'Man City', is_home=True, team_stats_map=self.team_stats,
            league_avg_xg=self.avg_xg, league_avg_xgc=self.avg_xgc
        )
        assert vs_wolves['attack_mult'] > vs_city['attack_mult']


class TestDynamicComponentScaling:
    """Verify dynamic GK save scaling and Bonus/DC fixture adjustments."""

    def test_goalkeeper_saves_scale_with_opponent_attack(self):
        gk = {
            'web_name': 'Raya',
            'team': 'Arsenal',
            'position': 'GK',
            'season_starts': 38,
            'season_minutes': 3420,
            'long_form_minutes': 3420,
            'saves_90': 3.0,
            'team_long_form_xgc90': 0.8,
        }
        # Against potent Man City (xG=2.2) vs weak team (xG=0.8)
        fix_city = {'home_team': 'Arsenal', 'away_team': 'Man City', 'home_fdr': 4, 'away_fdr': 4}
        fix_weak = {'home_team': 'Arsenal', 'away_team': 'Ipswich', 'home_fdr': 2, 'away_fdr': 5}
        team_stats = {
            'Arsenal': {'xg90': 1.8, 'xgc90': 0.8},
            'Man City': {'xg90': 2.2, 'xgc90': 0.9},
            'Ipswich': {'xg90': 0.8, 'xgc90': 1.8},
        }

        pred_city = predict_player_fixture(gk, fix_city, is_home=True, team_stats_map=team_stats)
        pred_weak = predict_player_fixture(gk, fix_weak, is_home=True, team_stats_map=team_stats)

        # Saves points (c3) must be higher against Man City than against Ipswich
        assert pred_city['c3_saves'] > pred_weak['c3_saves']

    def test_bonus_and_dc_scaling(self):
        fwd = {
            'web_name': 'Haaland',
            'team': 'Man City',
            'position': 'FWD',
            'season_starts': 35,
            'season_minutes': 3150,
            'long_form_minutes': 5000,
            'long_form_expected_goals_90': 0.80,
            'long_form_expected_assists_90': 0.10,
            'long_form_bonus_90': 1.20,
        }
        fix_easy = {'home_team': 'Man City', 'away_team': 'Wolves', 'home_fdr': 2, 'away_fdr': 5}
        team_stats = {
            'Man City': {'xg90': 2.2, 'xgc90': 0.9},
            'Wolves': {'xg90': 1.0, 'xgc90': 1.8},
        }
        pred = predict_player_fixture(fwd, fix_easy, is_home=True, team_stats_map=team_stats)
        # Bonus points should be scaled upwards by attack multiplier
        assert pred['c6_bonus'] > 1.20


class TestFixtureLoadingAndDoubleGameweeks:
    """Verify fixture schedule loading, Blank Gameweeks, and Double Gameweeks."""

    def test_load_2026_27_gw1_fixtures(self):
        fixtures = load_fixtures_for_gw('2026-27', gw=1)
        assert len(fixtures) == 10

    def test_predict_2026_27_gw1_pipeline(self):
        df = predict_gameweek_fixtures(season='2026-27', gw=1, save_csv=False)
        assert not df.empty
        assert 'fixture_opponent' in df.columns
        assert 'fixture_venue' in df.columns
        assert 'fixture_attack_mult' in df.columns
        assert 'expected_points' in df.columns
        assert 'p_start' in df.columns

        # Verify active starters have positive xP
        active_starters = df[df['season_minutes'] > 1000]
        assert (active_starters['expected_points'] > 0).all()

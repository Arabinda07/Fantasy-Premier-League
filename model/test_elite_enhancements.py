"""Unit tests for Elite Enhancement modules.

Covers:
- set_pieces.py: PK/FK/CK equity calculations and role fallback logic.
- ownership_engine.py: EO computation and strategy utility curves.
- price_predictor.py: Net transfer velocity and alert thresholds.
- rotation_intelligence.py: European congestion decay and news flag proration.
"""
import math
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.set_pieces import (
    compute_set_piece_equity,
    PK_XG_VALUE,
    PK_CONVERSION_RATE,
    DEFAULT_TEAM_PK_RATE_PER_90,
    DEFAULT_TEAM_CK_PER_90,
    DEFAULT_TEAM_FK_PER_90,
    XA_PER_CORNER,
    XA_PER_DIRECT_FK,
)
from model.ownership_engine import (
    compute_eo,
    estimate_captaincy_share,
    rank_adjusted_utility,
    RANK_PROTECT_SHIELD_WEIGHT,
    DIFFERENTIAL_REWARD_WEIGHT,
    DIFFERENTIAL_THRESHOLD,
)
from model.price_predictor import (
    compute_net_transfer_velocity,
    estimate_price_threshold,
    classify_price_trend,
    compute_player_price_trend,
    RISING_LOCK,
    RISING_ALERT,
    STABLE,
    FALLING_ALERT,
    FALLING_LOCK,
)
from model.rotation_intelligence import (
    compute_midweek_hazard,
    compute_sub60_vulnerability,
    compute_news_dampening,
    compute_rotation_hazard,
    MIDWEEK_HAZARD_SEVERE,
    MIDWEEK_HAZARD_MODERATE,
    MIDWEEK_HAZARD_NONE,
)


# ===========================================================================
# SET-PIECE MODULE TESTS
# ===========================================================================

class TestSetPieceEquity:
    """Tests for set_pieces.compute_set_piece_equity."""

    def test_primary_pk_taker_positive_equity(self):
        """Primary PK taker (order=1) should receive positive xG equity."""
        result = compute_set_piece_equity(
            player_code=1,
            position='FWD',
            pk_order=1.0,
            fk_order=0.0,
            ck_order=0.0,
            p_on_pitch=1.0,
        )
        assert result['delta_xg_pk'] > 0.0
        expected_xg = 1.0 * DEFAULT_TEAM_PK_RATE_PER_90 * PK_XG_VALUE
        assert abs(result['delta_xg_pk'] - expected_xg) < 1e-4
        assert result['is_pk_taker'] is True

    def test_secondary_pk_taker_reduced_equity(self):
        """Secondary PK taker (order=2) should receive reduced equity."""
        primary = compute_set_piece_equity(
            player_code=1, position='MID',
            pk_order=1.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        secondary = compute_set_piece_equity(
            player_code=2, position='MID',
            pk_order=2.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        assert secondary['delta_xg_pk'] > 0.0
        assert secondary['delta_xg_pk'] < primary['delta_xg_pk']
        assert secondary['is_pk_taker'] is True

    def test_no_pk_role_zero_equity(self):
        """Non-takers (order=0/NaN) should receive zero PK equity."""
        result = compute_set_piece_equity(
            player_code=3, position='DEF',
            pk_order=0.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        assert result['delta_xg_pk'] == 0.0
        assert result['is_pk_taker'] is False

    def test_pk_equity_scales_with_p_on_pitch(self):
        """PK equity should scale proportionally with P(on pitch)."""
        full = compute_set_piece_equity(
            player_code=1, position='FWD',
            pk_order=1.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        half = compute_set_piece_equity(
            player_code=1, position='FWD',
            pk_order=1.0, fk_order=0.0, ck_order=0.0, p_on_pitch=0.5,
        )
        assert abs(half['delta_xg_pk'] - full['delta_xg_pk'] * 0.5) < 1e-6

    def test_primary_ck_taker_positive_xa(self):
        """Primary corner taker (order=1) should receive positive xA equity."""
        result = compute_set_piece_equity(
            player_code=10, position='MID',
            pk_order=0.0, fk_order=0.0, ck_order=1.0, p_on_pitch=1.0,
        )
        assert result['delta_xa_ck'] > 0.0
        expected_xa = 1.0 * DEFAULT_TEAM_CK_PER_90 * XA_PER_CORNER
        assert abs(result['delta_xa_ck'] - expected_xa) < 1e-4
        assert result['is_ck_taker'] is True

    def test_primary_fk_taker_positive_xa(self):
        """Primary direct FK taker should receive positive xA equity."""
        result = compute_set_piece_equity(
            player_code=11, position='MID',
            pk_order=0.0, fk_order=1.0, ck_order=0.0, p_on_pitch=1.0,
        )
        assert result['delta_xa_fk'] > 0.0
        expected_xa = 1.0 * DEFAULT_TEAM_FK_PER_90 * XA_PER_DIRECT_FK
        assert abs(result['delta_xa_fk'] - expected_xa) < 1e-4
        assert result['is_fk_taker'] is True

    def test_c8_goal_points_vary_by_position(self):
        """Goal point equity should reflect position-based scoring (4/5/6 pts)."""
        fwd = compute_set_piece_equity(
            player_code=1, position='FWD',
            pk_order=1.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        mid = compute_set_piece_equity(
            player_code=2, position='MID',
            pk_order=1.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        defen = compute_set_piece_equity(
            player_code=3, position='DEF',
            pk_order=1.0, fk_order=0.0, ck_order=0.0, p_on_pitch=1.0,
        )
        # DEF/GK get 6pts, MID gets 5pts, FWD gets 4pts per goal
        assert defen['delta_c8_goals'] > mid['delta_c8_goals']
        assert mid['delta_c8_goals'] > fwd['delta_c8_goals']

    def test_combined_pk_and_ck_taker(self):
        """A player on both PK and CK duties should accumulate both equities."""
        result = compute_set_piece_equity(
            player_code=10, position='MID',
            pk_order=1.0, fk_order=0.0, ck_order=1.0, p_on_pitch=0.90,
        )
        assert result['delta_xg_pk'] > 0.0
        assert result['delta_xa_ck'] > 0.0
        assert result['delta_c7_assists'] > 0.0
        assert result['delta_c8_goals'] > 0.0


# ===========================================================================
# OWNERSHIP ENGINE TESTS
# ===========================================================================

class TestOwnershipEngine:
    """Tests for ownership_engine module."""

    def test_eo_basic_calculation(self):
        """EO = ownership + captaincy + triple_captaincy."""
        eo = compute_eo(0.85, 0.60, 0.0)
        assert abs(eo - 1.45) < 1e-6

    def test_eo_exceeds_one(self):
        """EO can exceed 1.0 for heavily captained talismans."""
        eo = compute_eo(0.90, 0.70, 0.05)
        assert eo > 1.0
        assert abs(eo - 1.65) < 1e-6

    def test_eo_zero_ownership(self):
        """Player with 0 ownership should have 0 EO."""
        eo = compute_eo(0.0, 0.0, 0.0)
        assert eo == 0.0

    def test_captaincy_estimate_positive_for_high_xp(self):
        """High-xP, high-owned players should have positive captaincy share."""
        cap = estimate_captaincy_share(0.80, 8.0, league_max_xp=10.0)
        assert cap > 0.0

    def test_captaincy_estimate_zero_for_low_ownership(self):
        """Zero-owned players should have zero captaincy share."""
        cap = estimate_captaincy_share(0.0, 8.0, league_max_xp=10.0)
        assert cap == 0.0

    def test_pure_xp_strategy_no_adjustment(self):
        """pure_xp strategy should return raw xP with no EO adjustment."""
        util = rank_adjusted_utility(6.5, eo=1.50, strategy='pure_xp')
        assert abs(util - 6.5) < 1e-6

    def test_rank_protect_rewards_high_eo(self):
        """rank_protect should reward holding high-EO assets (utility > xP)."""
        util = rank_adjusted_utility(6.5, eo=1.50, strategy='rank_protect')
        assert util > 6.5
        expected_phi = RANK_PROTECT_SHIELD_WEIGHT * (1.50 - 1.0)
        assert abs(util - (6.5 + expected_phi)) < 1e-6

    def test_rank_protect_no_effect_below_threshold(self):
        """rank_protect should have no effect for players with EO < 1.0."""
        util = rank_adjusted_utility(4.0, eo=0.50, strategy='rank_protect')
        assert abs(util - 4.0) < 1e-6

    def test_differential_chase_rewards_low_eo(self):
        """differential_chase should reward low-EO differentials."""
        util = rank_adjusted_utility(5.0, eo=0.05, strategy='differential_chase')
        assert util > 5.0
        expected_phi = DIFFERENTIAL_REWARD_WEIGHT * (DIFFERENTIAL_THRESHOLD - 0.05)
        assert abs(util - (5.0 + expected_phi)) < 1e-6

    def test_differential_chase_penalises_high_eo(self):
        """differential_chase should penalise high-EO template picks."""
        util = rank_adjusted_utility(7.0, eo=1.50, strategy='differential_chase')
        assert util < 7.0

    def test_invalid_strategy_falls_back_to_pure_xp(self):
        """Invalid strategy string should default to pure_xp."""
        util = rank_adjusted_utility(5.0, eo=1.50, strategy='invalid_mode')
        assert abs(util - 5.0) < 1e-6


# ===========================================================================
# PRICE PREDICTOR TESTS
# ===========================================================================

class TestPricePredictor:
    """Tests for price_predictor module."""

    def test_net_velocity_positive(self):
        """Positive net velocity when more transfers in than out."""
        vel = compute_net_transfer_velocity(150000, 50000)
        assert vel == 100000

    def test_net_velocity_negative(self):
        """Negative net velocity when more transfers out."""
        vel = compute_net_transfer_velocity(20000, 80000)
        assert vel == -60000

    def test_threshold_scales_with_ownership(self):
        """Higher ownership should increase the price change threshold."""
        threshold_low = estimate_price_threshold(0.05)
        threshold_high = estimate_price_threshold(0.50)
        assert threshold_high > threshold_low

    def test_classify_rising_lock(self):
        """Net velocity at or above threshold should be RISING_LOCK."""
        result = classify_price_trend(100000, 100000.0)
        assert result == RISING_LOCK

    def test_classify_rising_alert(self):
        """Net velocity at 75-99% of threshold should be RISING_ALERT."""
        result = classify_price_trend(80000, 100000.0)
        assert result == RISING_ALERT

    def test_classify_stable(self):
        """Low net velocity should be STABLE."""
        result = classify_price_trend(10000, 100000.0)
        assert result == STABLE

    def test_classify_falling_alert(self):
        """Net velocity at -75% to -99% of threshold should be FALLING_ALERT."""
        result = classify_price_trend(-80000, 100000.0)
        assert result == FALLING_ALERT

    def test_classify_falling_lock(self):
        """Net velocity at or below negative threshold should be FALLING_LOCK."""
        result = classify_price_trend(-100000, 100000.0)
        assert result == FALLING_LOCK

    def test_compute_player_trend_end_to_end(self):
        """End-to-end trend computation should return valid structure."""
        result = compute_player_price_trend(
            transfers_in_event=200000,
            transfers_out_event=50000,
            ownership_pct=0.10,
        )
        assert 'net_velocity' in result
        assert 'trend' in result
        assert result['net_velocity'] == 150000
        assert result['trend'] in (RISING_LOCK, RISING_ALERT, STABLE, FALLING_ALERT, FALLING_LOCK)

    def test_zero_threshold_returns_stable(self):
        """Zero threshold should not cause division by zero, return STABLE."""
        result = classify_price_trend(50000, 0.0)
        assert result == STABLE


# ===========================================================================
# ROTATION INTELLIGENCE TESTS
# ===========================================================================

class TestRotationIntelligence:
    """Tests for rotation_intelligence module."""

    def test_midweek_hazard_no_europe(self):
        """Non-European team should have no midweek hazard (1.0)."""
        h = compute_midweek_hazard('Brighton', days_rest=3)
        assert h == MIDWEEK_HAZARD_NONE

    def test_midweek_hazard_ucl_short_rest(self):
        """UCL team with ≤3 days rest should have severe/moderate hazard."""
        h = compute_midweek_hazard('Arsenal', days_rest=3)
        assert h <= MIDWEEK_HAZARD_MODERATE

    def test_midweek_hazard_rotation_heavy_manager(self):
        """Rotation-heavy manager with ≤3 days rest gets severe hazard."""
        h = compute_midweek_hazard('Man City', days_rest=3)
        assert h == MIDWEEK_HAZARD_SEVERE

    def test_midweek_hazard_normal_rest(self):
        """UCL team with ≥5 days rest should have no hazard."""
        h = compute_midweek_hazard('Arsenal', days_rest=5)
        assert h == MIDWEEK_HAZARD_NONE

    def test_sub60_default_prior(self):
        """Zero starts should return default prior 0.85."""
        prob = compute_sub60_vulnerability(0, 0)
        assert abs(prob - 0.85) < 1e-6

    def test_sub60_full_minutes(self):
        """Player always playing 60+ should return 1.0."""
        prob = compute_sub60_vulnerability(20, 20)
        assert abs(prob - 1.0) < 1e-6

    def test_sub60_partial(self):
        """Player playing 60+ in 15/20 starts → 0.75."""
        prob = compute_sub60_vulnerability(20, 15)
        assert abs(prob - 0.75) < 1e-6

    def test_news_dampening_injured(self):
        """Injured status should zero out both probabilities."""
        result = compute_news_dampening('i', None)
        assert result['p_start_mult'] == 0.0
        assert result['p_app_mult'] == 0.0

    def test_news_dampening_suspended(self):
        """Suspended status should zero out both probabilities."""
        result = compute_news_dampening('s', None)
        assert result['p_start_mult'] == 0.0
        assert result['p_app_mult'] == 0.0

    def test_news_dampening_75_chance(self):
        """75% chance should dampen P(Start) to 0.75."""
        result = compute_news_dampening('d', 75.0)
        assert abs(result['p_start_mult'] - 0.75) < 1e-6

    def test_news_dampening_50_chance(self):
        """50% chance should dampen P(Start) to 0.40."""
        result = compute_news_dampening('d', 50.0)
        assert abs(result['p_start_mult'] - 0.40) < 1e-6

    def test_news_dampening_available(self):
        """Available status with no flags → no dampening."""
        result = compute_news_dampening('a', None)
        assert result['p_start_mult'] == 1.0
        assert result['p_app_mult'] == 1.0

    def test_combined_rotation_hazard(self):
        """Combined hazard should multiply midweek and news factors."""
        result = compute_rotation_hazard(
            team_name='Man City',
            status='a',
            chance_of_playing=None,
            days_rest=3,
        )
        assert result['midweek_hazard'] == MIDWEEK_HAZARD_SEVERE
        assert result['combined_p_start_mult'] == MIDWEEK_HAZARD_SEVERE
        assert result['combined_p_app_mult'] == 1.0  # News is fine

    def test_combined_injured_overrides_midweek(self):
        """Injured status should override midweek hazard to zero."""
        result = compute_rotation_hazard(
            team_name='Man City',
            status='i',
            chance_of_playing=None,
            days_rest=3,
        )
        assert result['combined_p_start_mult'] == 0.0
        assert result['combined_p_app_mult'] == 0.0

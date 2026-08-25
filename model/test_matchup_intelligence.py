"""Unit tests for model.matchup_intelligence.

Verifies:
1. Empirical Bayesian H2H shrinkage formula (zero minutes, partial sample, full sample).
2. H2H multiplier bounding within [0.80, 1.35].
3. Tactical archetype calculations (high-line vs low-block defenses).
4. Combined matchup multiplier generation.
5. End-to-end DataFrame enrichment with matchup intelligence.
"""
import math
import os
import sys
import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.matchup_intelligence import (
    compute_h2h_multiplier,
    compute_tactical_archetype_multiplier,
    compute_combined_matchup_multiplier,
    enrich_predictions_with_matchup_intelligence,
    DEFAULT_H2H_M0,
    MIN_H2H_MULT,
    MAX_H2H_MULT,
)


class TestH2HMultiplier:
    """Tests for compute_h2h_multiplier."""

    def test_zero_minutes_fallback_to_one(self):
        """Zero H2H minutes should cleanly return neutral 1.0."""
        mult = compute_h2h_multiplier(
            h2h_mins=0.0, h2h_xg=0.0, h2h_xa=0.0,
            career_mins=1800.0, career_xg=10.0, career_xa=5.0,
        )
        assert mult == 1.00

    def test_zero_career_minutes_fallback_to_one(self):
        """Zero career minutes should cleanly return neutral 1.0."""
        mult = compute_h2h_multiplier(
            h2h_mins=180.0, h2h_xg=2.0, h2h_xa=1.0,
            career_mins=0.0, career_xg=0.0, career_xa=0.0,
        )
        assert mult == 1.00

    def test_bayesian_shrinkage_partial_sample(self):
        """Partial sample (180 mins) should shrink toward 1.0."""
        # Career rate: 10 xG+xA in 1800 mins = 0.50 per 90
        # H2H rate: 2.5 xG+xA in 180 mins = 1.25 per 90 (2.5x career rate)
        # Weight with M0=270: 180 / (180 + 270) = 180 / 450 = 0.40
        # Shrunken = 0.40 * 2.5 + 0.60 * 1.0 = 1.0 + 0.6 = 1.60 -> bounded by MAX_H2H_MULT
        mult = compute_h2h_multiplier(
            h2h_mins=180.0, h2h_xg=2.0, h2h_xa=0.5,
            career_mins=1800.0, career_xg=7.0, career_xa=3.0,
        )
        assert mult > 1.0
        assert mult <= MAX_H2H_MULT

    def test_maximum_bound_enforced(self):
        """Extremely high sample outlier must be capped at MAX_H2H_MULT (1.35)."""
        mult = compute_h2h_multiplier(
            h2h_mins=900.0, h2h_xg=20.0, h2h_xa=10.0,
            career_mins=1800.0, career_xg=5.0, career_xa=5.0,
        )
        assert mult == MAX_H2H_MULT

    def test_minimum_bound_enforced(self):
        """Extremely poor H2H record must not drop below MIN_H2H_MULT (0.80)."""
        mult = compute_h2h_multiplier(
            h2h_mins=900.0, h2h_xg=0.0, h2h_xa=0.0,
            career_mins=1800.0, career_xg=15.0, career_xa=10.0,
        )
        assert mult >= MIN_H2H_MULT


class TestTacticalArchetypeMultiplier:
    """Tests for compute_tactical_archetype_multiplier."""

    def test_high_line_benefits_transition_playmaker(self):
        """High-line opponent (Brighton / Spurs) should boost transition playmaker."""
        mult_brighton = compute_tactical_archetype_multiplier(
            opponent_team='Brighton',
            player_name='Palmer',
        )
        assert mult_brighton > 1.0
        assert mult_brighton >= 1.10

    def test_low_block_neutral_or_dampened_for_playmaker(self):
        """Low-block opponent (Everton) should not give a high-line transition boost."""
        mult_everton = compute_tactical_archetype_multiplier(
            opponent_team='Everton',
            player_name='Palmer',
        )
        assert mult_everton < 1.0

    def test_standard_player_defaults_to_one(self):
        """Standard unclassified player should return 1.00."""
        mult = compute_tactical_archetype_multiplier(
            opponent_team='Brighton',
            player_name='GenericPlayer',
        )
        assert mult == 1.00


class TestCombinedMatchupMultiplier:
    """Tests for compute_combined_matchup_multiplier."""

    def test_palmer_vs_brighton_combined_boost(self):
        """Palmer vs Brighton should accumulate both H2H and tactical boosts."""
        res = compute_combined_matchup_multiplier(
            player_name='Palmer',
            opponent_team='Brighton',
            h2h_mins=270.0,
            h2h_xg=2.80,
            h2h_xa=0.90,
            career_mins=3000.0,
            career_xg=22.0,
            career_xa=11.0,
        )
        assert res['h2h_mult'] > 1.0
        assert res['tactical_mult'] > 1.0
        assert res['combined_mult'] > 1.15
        assert res['combined_mult'] <= 1.40


class TestEnrichPredictions:
    """Tests for enrich_predictions_with_matchup_intelligence."""

    def test_dataframe_enrichment_columns(self):
        """Enrichment should add all 3 matchup columns to predictions."""
        sample_df = pd.DataFrame([
            {'player_code': 244851, 'web_name': 'Palmer', 'fixture_opponent': 'Brighton', 'expected_points': 5.0, 'c8_goals': 1.8, 'c7_assists': 0.8},
            {'player_code': 448, 'web_name': 'Haaland', 'fixture_opponent': 'Crystal Palace', 'expected_points': 6.0, 'c8_goals': 2.4, 'c7_assists': 0.3},
        ])
        enriched = enrich_predictions_with_matchup_intelligence(sample_df)

        assert 'h2h_mult' in enriched.columns
        assert 'tactical_mult' in enriched.columns
        assert 'combined_matchup_mult' in enriched.columns

        # Palmer should receive a positive point boost vs Brighton
        palmer_row = enriched[enriched['web_name'] == 'Palmer'].iloc[0]
        assert palmer_row['combined_matchup_mult'] > 1.0
        assert palmer_row['expected_points'] > 5.0

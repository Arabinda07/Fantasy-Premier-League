"""Unit tests for Milestone M-03: Exponential Recency Decay (EWMA) in Rolling Form.

Validates:
1. Exact mathematical formulation of compute_ewma_weight and calculate_gw_lag.
2. Exact half-life halving at Delta t = 8.0 gameweeks (weight == 0.500).
3. Cross-season gameweek distance continuity across season boundaries.
4. Recency monotonicity: recent performances carry strictly higher per-90 influence than distant ones.
5. Backwards compatibility: half_life=None produces identical flat unweighted aggregates.
6. Integration with build_player_form_dataset and build_team_form_dataset.
"""
import math
import os
import sys
import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.rolling_form import (
    calculate_gw_lag,
    compute_ewma_weight,
    compute_player_form,
    compute_team_form,
    build_player_form_dataset,
    build_team_form_dataset,
    DEFAULT_HALF_LIFE,
)

DATA_ROOT = os.path.join(REPO_ROOT, 'data')
SEASON = '2025-26'
MAX_GW = 38


class TestEwmaFormulas:
    """Test core mathematical functions calculate_gw_lag and compute_ewma_weight."""

    def test_calculate_gw_lag_same_season(self):
        """Gameweek lag within the same season is current_gw - match_gw."""
        assert calculate_gw_lag('2025-26', 10, '2025-26', 10) == 0
        assert calculate_gw_lag('2025-26', 8, '2025-26', 10) == 2
        assert calculate_gw_lag('2025-26', 1, '2025-26', 10) == 9
        # Match in future relative to eval is clamped to 0
        assert calculate_gw_lag('2025-26', 12, '2025-26', 10) == 0

    def test_calculate_gw_lag_cross_season_boundary(self):
        """Lag across season boundary connects GW38 of prior season to GW1 of current with summer gap."""
        # Default summer break gap is 4 equivalent GWs (~90 days off-season)
        # GW38 of prior season relative to GW1 of current season is 1 + 4 = 5 GWs
        assert calculate_gw_lag('2024-25', 38, '2025-26', 1) == 5
        # GW38 of prior season relative to GW2 of current season is 2 + 4 = 6 GWs
        assert calculate_gw_lag('2024-25', 38, '2025-26', 2) == 6
        # With summer_gap=0, exact raw match distance is preserved
        assert calculate_gw_lag('2024-25', 38, '2025-26', 1, summer_gap=0) == 1
        assert calculate_gw_lag('2024-25', 38, '2025-26', 2, summer_gap=0) == 2

    def test_calculate_gw_lag_multi_season(self):
        """Lag across two seasons adds 38 gameweeks per full intermediate season plus summer gap."""
        # 2 seasons ago (2023-24 GW38 to 2025-26 GW1 with default summer_gap=4): 1 + 38 + 4 = 43
        assert calculate_gw_lag('2023-24', 38, '2025-26', 1) == 43
        assert calculate_gw_lag('2023-24', 38, '2025-26', 1, summer_gap=0) == 39

    def test_compute_ewma_weight_exact_half_life(self):
        """At lag = 8 and half_life = 8.0, weight must be exactly 0.5."""
        w0 = compute_ewma_weight(0, half_life=8.0)
        assert w0 == pytest.approx(1.0, rel=1e-6)

        w4 = compute_ewma_weight(4, half_life=8.0)
        assert w4 == pytest.approx(math.pow(2.0, -0.5), rel=1e-6)
        assert w4 == pytest.approx(0.707106, rel=1e-4)

        w8 = compute_ewma_weight(8, half_life=8.0)
        assert w8 == pytest.approx(0.500000, rel=1e-6)

        w16 = compute_ewma_weight(16, half_life=8.0)
        assert w16 == pytest.approx(0.250000, rel=1e-6)

        w24 = compute_ewma_weight(24, half_life=8.0)
        assert w24 == pytest.approx(0.125000, rel=1e-6)

        w38 = compute_ewma_weight(38, half_life=8.0)
        assert w38 == pytest.approx(math.pow(2.0, -38.0 / 8.0), rel=1e-6)
        assert w38 == pytest.approx(0.037163, rel=1e-4)

    def test_compute_ewma_weight_disabled(self):
        """When half_life is None or <= 0, weight must strictly evaluate to 1.0."""
        assert compute_ewma_weight(0, half_life=None) == 1.0
        assert compute_ewma_weight(10, half_life=None) == 1.0
        assert compute_ewma_weight(38, half_life=None) == 1.0
        assert compute_ewma_weight(10, half_life=0.0) == 1.0


class TestEwmaPlayerFormIntegration:
    """Test EWMA decay behavior on actual historical player match data."""

    def test_recency_weighting_discounts_distant_fixtures(self):
        """Under half_life=8.0, total effective minutes must be significantly less than unweighted."""
        result_flat = compute_player_form(SEASON, MAX_GW, window_gws=None, half_life=None, data_root=DATA_ROOT)
        result_decay = compute_player_form(SEASON, MAX_GW, window_gws=None, half_life=8.0, data_root=DATA_ROOT)

        haaland_flat = result_flat[result_flat['code'] == 223094].iloc[0]
        haaland_decay = result_decay[result_decay['code'] == 223094].iloc[0]

        # Unweighted minutes are preserved identically in unweighted_minutes
        assert haaland_decay['unweighted_minutes'] == haaland_flat['minutes']
        assert haaland_decay['unweighted_minutes'] == 5689

        # Effective decayed minutes must be much lower due to exponential discount on 76 GW horizon
        assert haaland_decay['minutes'] < 1200
        assert haaland_decay['minutes'] > 500

    def test_monotonic_half_life_scaling(self):
        """Shorter half-life must strictly produce fewer effective minutes and more aggressive recency weighting."""
        h4 = compute_player_form(SEASON, MAX_GW, window_gws=None, half_life=4.0, data_root=DATA_ROOT)
        h8 = compute_player_form(SEASON, MAX_GW, window_gws=None, half_life=8.0, data_root=DATA_ROOT)
        h16 = compute_player_form(SEASON, MAX_GW, window_gws=None, half_life=16.0, data_root=DATA_ROOT)

        mins_h4 = h4[h4['code'] == 223094].iloc[0]['minutes']
        mins_h8 = h8[h8['code'] == 223094].iloc[0]['minutes']
        mins_h16 = h16[h16['code'] == 223094].iloc[0]['minutes']

        assert mins_h4 < mins_h8 < mins_h16

    def test_unweighted_compatibility_mode(self):
        """Passing half_life=None must yield identical results to flat summation."""
        result_none = compute_player_form(SEASON, MAX_GW, window_gws=6, half_life=None, data_root=DATA_ROOT)
        haaland = result_none[result_none['code'] == 223094].iloc[0]

        assert haaland['minutes'] == 450
        assert abs(haaland['expected_goals'] - 3.86) < 0.1
        assert abs(haaland['expected_assists'] - 0.73) < 0.1


class TestEwmaTeamFormIntegration:
    """Test EWMA decay behavior on team match evaluations."""

    def test_team_form_ewma_effective_matches(self):
        """Team minutes and match weighting under EWMA must reflect decayed matches."""
        team_flat = compute_team_form(SEASON, MAX_GW, window_gws=38, half_life=None, data_root=DATA_ROOT)
        team_decay = compute_team_form(SEASON, MAX_GW, window_gws=38, half_life=8.0, data_root=DATA_ROOT)

        liv_flat = team_flat[team_flat['team'] == 'Liverpool'].iloc[0]
        liv_decay = team_decay[team_decay['team'] == 'Liverpool'].iloc[0]

        # Raw match count is 38 in both
        assert liv_flat['matches'] == 38
        assert liv_decay['matches'] == 38

        # Flat team minutes is 38 * 90 = 3420
        assert liv_flat['team_minutes'] == 3420.0
        # Decayed team minutes is ~10-12 effective matches * 90
        assert liv_decay['team_minutes'] < 1500.0
        assert liv_decay['team_minutes'] > 800.0

        # Team rates per 90 remain stable and in realistic range
        assert 1.0 <= liv_decay['team_xg90'] <= 2.5
        assert 0.8 <= liv_decay['team_xgc90'] <= 2.0


class TestEwmaDatasetBuilders:
    """Verify build_player_form_dataset and build_team_form_dataset with EWMA configuration."""

    def test_build_player_form_dataset_with_ewma(self):
        """build_player_form_dataset incorporates EWMA decayed long-form and flat short-form by default."""
        df = build_player_form_dataset(SEASON, MAX_GW, short_form_window=6, data_root=DATA_ROOT)

        assert not df.empty
        assert 'long_form_minutes' in df.columns
        assert 'short_form_minutes' in df.columns
        assert 'long_form_expected_goals_90' in df.columns
        assert 'short_form_expected_goals_90' in df.columns

        haaland = df[df['player_code'] == 223094].iloc[0]
        # Long-form has EWMA decay applied (default 8.0)
        assert haaland['long_form_minutes'] < 1200
        # Short-form is flat 6-GW window (default None)
        assert haaland['short_form_minutes'] == 450

    def test_build_team_form_dataset_with_ewma(self):
        """build_team_form_dataset generates decayed long-form rates and flat short-form rates."""
        df = build_team_form_dataset(SEASON, MAX_GW, short_form_window=6, data_root=DATA_ROOT)

        assert not df.empty
        assert 'team_long_form_xg90' in df.columns
        assert 'team_short_form_xg90' in df.columns
        assert len(df) == 23


class TestEwmaDecouplingAndExperienceGate:
    """Verify P1 hardening fixes decoupling EWMA minutes from sample evidence and minutes model gates."""

    def test_empirical_bayes_uses_unweighted_minutes_for_shrinkage(self):
        """Veterans with decayed long_form_minutes preserve true sample evidence via long_form_unweighted_minutes."""
        from model.prediction_engine import predict_player_points

        # Player with decayed long_form_minutes = 400, but unweighted = 3000, xG90 = 0.80
        # If shrunk by 400 mins (M0 = 500): weight = 400/900 = 0.444 -> xg90 ~ 0.444*0.80 + 0.556*0.35 = 0.550
        # If shrunk by 3000 mins (M0 = 500): weight = 3000/3500 = 0.857 -> xg90 ~ 0.857*0.80 + 0.143*0.35 = 0.736
        player_with_unweighted = {
            'player_code': 999991,
            'web_name': 'VeteranFWD',
            'position': 'FWD',
            'team': 'MCI',
            'season_starts': 2,
            'season_minutes': 180,
            'fbref_squads_made': 2,
            'long_form_minutes': 400.0,
            'long_form_unweighted_minutes': 3000.0,
            'long_form_expected_goals_90': 0.80,
            'long_form_expected_assists_90': 0.20,
            'long_form_defensive_contribution_90': 2.0,
            'long_form_expected_goals_conceded_90': 1.0,
            'status': 'a',
            'now_cost': 120,
        }
        res = predict_player_points(player_with_unweighted, apply_shrinkage=True)
        # Expected goals c8 is 4.0 * total_xg90 * active_ratio
        # With unweighted minutes, xg90 is ~0.736, so c8 > 2.5
        assert res['c8_goals'] > 2.5

    def test_minutes_hazard_recognizes_unweighted_veteran_experience(self):
        """Minutes hazard model uses long_form_unweighted_minutes to satisfy long_mins >= 1800 experience check."""
        from model.minutes_model import compute_player_minutes_hazard

        veteran_starter = {
            'player_code': 999992,
            'web_name': 'ProvenStarter',
            'position': 'MID',
            'team': 'ARS',
            'season_starts': 2,
            'season_minutes': 180,
            'fbref_squads_made': 2,
            'long_form_minutes': 1100.0,            # < 1800 due to EWMA decay
            'long_form_unweighted_minutes': 3200.0, # >= 1800 physical minutes
            'status': 'a',
            'cost': 8.0,
        }
        prof = compute_player_minutes_hazard(veteran_starter, days_rest=7)
        # Proven starter with starts == matches_cnt (2/2) and long_mins >= 1800 gets 0.90 start prior
        assert prof.p_start >= 0.90


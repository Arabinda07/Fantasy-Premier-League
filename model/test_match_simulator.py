"""Unit tests for Dixon-Coles Bivariate Match Simulator & Monte Carlo Engine (model/match_simulator.py)."""
import math
import numpy as np
import pandas as pd
import pytest

from model.match_simulator import (
    dixon_coles_tau,
    compute_dixon_coles_matrix,
    analyze_bivariate_scoreline_matrix,
    compute_true_bps_and_bonus,
    simulate_match_monte_carlo,
    simulate_gameweek_fixtures,
    MatchProbabilityMetrics,
    PlayerSimulationDistribution,
    DEFAULT_RHO,
)


class TestDixonColesMath:
    """Test mathematical formulas and boundary properties of Dixon-Coles model."""

    def test_dixon_coles_tau_adjustment_factors(self):
        lh = 1.5
        ma = 1.2
        rho = -0.05

        # (0, 0): 1 - lambda * mu * rho = 1 - (1.5 * 1.2 * -0.05) = 1 + 0.09 = 1.09
        tau_00 = dixon_coles_tau(0, 0, lh, ma, rho=rho)
        assert pytest.approx(tau_00, 1e-5) == 1.0 - (lh * ma * rho)
        assert tau_00 > 1.0  # Inflation of 0-0 when rho < 0

        # (0, 1): 1 + lambda * rho = 1 + (1.5 * -0.05) = 0.925
        tau_01 = dixon_coles_tau(0, 1, lh, ma, rho=rho)
        assert pytest.approx(tau_01, 1e-5) == 1.0 + (lh * rho)

        # (1, 0): 1 + mu * rho = 1 + (1.2 * -0.05) = 0.94
        tau_10 = dixon_coles_tau(1, 0, lh, ma, rho=rho)
        assert pytest.approx(tau_10, 1e-5) == 1.0 + (ma * rho)

        # (1, 1): 1 - rho = 1 - (-0.05) = 1.05
        tau_11 = dixon_coles_tau(1, 1, lh, ma, rho=rho)
        assert pytest.approx(tau_11, 1e-5) == 1.0 - rho

        # Other scorelines must be exactly 1.0
        assert dixon_coles_tau(2, 0, lh, ma, rho=rho) == 1.0
        assert dixon_coles_tau(2, 1, lh, ma, rho=rho) == 1.0
        assert dixon_coles_tau(3, 2, lh, ma, rho=rho) == 1.0

    def test_probability_matrix_normalization_and_conservation(self):
        matrix = compute_dixon_coles_matrix(lambda_h=1.85, mu_a=1.15, rho=-0.05, max_goals=10)
        assert matrix.shape == (11, 11)
        assert np.all(matrix >= 0.0)
        # Total probability strictly conserved to 1.0
        assert pytest.approx(float(np.sum(matrix)), 1e-6) == 1.0

    def test_outcome_partition_and_betting_metrics(self):
        matrix = compute_dixon_coles_matrix(lambda_h=2.0, mu_a=0.8, rho=-0.05, max_goals=10)
        metrics = analyze_bivariate_scoreline_matrix(
            matrix=matrix,
            home_team="Arsenal",
            away_team="Southampton",
            lambda_h=2.0,
            mu_a=0.8,
        )

        # Outcomes sum to 1.0
        total_outcome = metrics.home_win_prob + metrics.draw_prob + metrics.away_win_prob
        assert pytest.approx(total_outcome, 1e-4) == 1.0

        # Strong home favorite should have home_win > away_win
        assert metrics.home_win_prob > metrics.away_win_prob
        assert metrics.home_win_prob > 0.60

        # Over / Under 2.5 goals sum to 1.0
        assert pytest.approx(metrics.over_2_5_goals_prob + metrics.under_2_5_goals_prob, 1e-4) == 1.0

        # Clean sheet probabilities in valid range
        assert 0.0 < metrics.home_clean_sheet_prob < 1.0
        assert 0.0 < metrics.away_clean_sheet_prob < 1.0
        # Home defense facing weak attack (0.8 xG) should have higher CS prob than away defense facing 2.0 xG
        assert metrics.home_clean_sheet_prob > metrics.away_clean_sheet_prob

        # Expected goals match inputs closely
        assert pytest.approx(metrics.expected_home_goals, abs=0.15) == 2.0
        assert pytest.approx(metrics.expected_away_goals, abs=0.15) == 0.8

        # Top scorelines list populated and sorted descending
        assert len(metrics.most_likely_scorelines) == 5
        probs = [p for _, p in metrics.most_likely_scorelines]
        assert probs == sorted(probs, reverse=True)


class TestTrueBpsAndBonus:
    """Test True BPS simulation and official 3/2/1 bonus points assignment."""

    def test_bonus_point_clear_hierarchy(self):
        player_stats = [
            {'player_code': 101, 'position': 'FWD', 'is_home': True, 'mins_played': 90, 'goals': 2, 'assists': 0, 'dc': 1, 'yc': 0, 'rc': 0},
            {'player_code': 102, 'position': 'MID', 'is_home': True, 'mins_played': 90, 'goals': 1, 'assists': 1, 'dc': 3, 'yc': 0, 'rc': 0},
            {'player_code': 103, 'position': 'DEF', 'is_home': True, 'mins_played': 90, 'goals': 0, 'assists': 0, 'dc': 8, 'yc': 0, 'rc': 0},
            {'player_code': 201, 'position': 'GK', 'is_home': False, 'mins_played': 90, 'goals': 0, 'assists': 0, 'saves': 5, 'dc': 0, 'yc': 0, 'rc': 0},
        ]
        # Home won 3-0: Home clean sheet = True, Away clean sheet = False
        bonus = compute_true_bps_and_bonus(
            player_stats=player_stats,
            home_gc=0,
            away_gc=3,
            home_clean_sheet=True,
            away_clean_sheet=False,
        )

        # 2-goal FWD should get 3 bonus points
        assert bonus[101] == 3
        # 1-goal + 1-assist MID gets 2 bonus points
        assert bonus[102] == 2
        # High-DC DEF or GK gets 1 bonus point
        assert bonus[103] in (1, 2) or bonus[201] in (1, 2)

    def test_bonus_point_tie_handling(self):
        # Two players with identical top BPS
        player_stats = [
            {'player_code': 1, 'position': 'MID', 'is_home': True, 'mins_played': 90, 'goals': 1, 'assists': 0, 'dc': 2, 'yc': 0, 'rc': 0},
            {'player_code': 2, 'position': 'MID', 'is_home': True, 'mins_played': 90, 'goals': 1, 'assists': 0, 'dc': 2, 'yc': 0, 'rc': 0},
            {'player_code': 3, 'position': 'DEF', 'is_home': True, 'mins_played': 90, 'goals': 0, 'assists': 0, 'dc': 2, 'yc': 0, 'rc': 0},
        ]
        bonus = compute_true_bps_and_bonus(
            player_stats=player_stats,
            home_gc=0,
            away_gc=2,
            home_clean_sheet=True,
            away_clean_sheet=False,
        )
        # Both top players get 3 bonus points
        assert bonus[1] == 3
        assert bonus[2] == 3


class TestMonteCarloSimulation:
    """Test vectorized Monte Carlo match engine and quantile distributions."""

    def test_simulate_match_monte_carlo_player_distributions(self):
        home_players = [
            {'player_code': 11, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'xg90': 0.95, 'xa90': 0.15, 'p_start': 0.95, 'cost': 15.0},
            {'player_code': 12, 'web_name': 'De Bruyne', 'team': 'Man City', 'position': 'MID', 'xg90': 0.25, 'xa90': 0.55, 'p_start': 0.90, 'cost': 9.5},
            {'player_code': 13, 'web_name': 'Gvardiol', 'team': 'Man City', 'position': 'DEF', 'xg90': 0.10, 'xa90': 0.05, 'dc90': 5.0, 'p_start': 0.90, 'cost': 6.0},
            {'player_code': 14, 'web_name': 'Ederson', 'team': 'Man City', 'position': 'GK', 'xg90': 0.0, 'xa90': 0.0, 'dc90': 1.0, 'p_start': 0.95, 'cost': 5.5},
        ]
        away_players = [
            {'player_code': 21, 'web_name': 'Bowen', 'team': 'West Ham', 'position': 'MID', 'xg90': 0.35, 'xa90': 0.20, 'p_start': 0.95, 'cost': 7.5},
            {'player_code': 22, 'web_name': 'Areola', 'team': 'West Ham', 'position': 'GK', 'xg90': 0.0, 'xa90': 0.0, 'dc90': 1.0, 'p_start': 0.95, 'cost': 4.5},
        ]

        metrics, dists = simulate_match_monte_carlo(
            home_team='Man City',
            away_team='West Ham',
            home_players=home_players,
            away_players=away_players,
            lambda_h=2.4,
            mu_a=0.8,
            n_sims=5000,
            random_seed=123,
        )

        assert isinstance(metrics, MatchProbabilityMetrics)
        assert len(dists) == 6

        # Haaland distribution checks
        haaland_dist = next(d for d in dists if d.web_name == 'Haaland')
        assert haaland_dist.expected_points > 5.0
        assert haaland_dist.floor_p10 <= haaland_dist.median_p50 <= haaland_dist.ceiling_p90
        assert haaland_dist.ceiling_p90 >= 10.0  # High haul ceiling for premium captain
        assert haaland_dist.haul_prob > 0.15  # At least 15% haul chance
        assert haaland_dist.expected_goals > 0.50

        # Gvardiol Clean Sheet check
        gvardiol_dist = next(d for d in dists if d.web_name == 'Gvardiol')
        assert 0.30 <= gvardiol_dist.expected_clean_sheet <= 0.60

    def test_simulate_gameweek_fixtures_execution(self):
        results = simulate_gameweek_fixtures(
            season='2026-27',
            gw=1,
            n_sims=500,
            data_root='data',
            save_csv=False,
        )
        assert 'match_metrics' in results
        assert 'player_distributions' in results
        assert len(results['match_metrics']) > 0
        df = results['player_distributions']
        assert not df.empty
        assert 'expected_points' in df.columns
        assert 'haul_prob' in df.columns
        assert 'floor_p10' in df.columns
        assert 'ceiling_p90' in df.columns

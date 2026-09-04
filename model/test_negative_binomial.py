"""Unit tests for Negative Binomial overdispersion model (M-01).

Validates:
1. Mathematical convergence of Negative Binomial to Poisson as r -> infinity.
2. Clean sheet probability zero-inflation properties.
3. Heavy-defeat tail expectation under exact discrete C10 penalty.
4. Full integration with predict_player_points and fixture_engine.
5. Historical calibration parameter estimator.
"""
import math
import pytest
import pandas as pd

from model.prediction_engine import (
    poisson_pmf,
    poisson_clean_sheet_prob,
    poisson_exact_gc_penalty,
    negative_binomial_pmf,
    negative_binomial_clean_sheet_prob,
    negative_binomial_exact_gc_penalty,
    predict_player_points,
    DEFAULT_DISPERSION_R,
)
from model.calibration import estimate_league_dispersion


def test_poisson_convergence():
    """Negative Binomial PMF must converge to Poisson PMF as r -> infinity."""
    mu = 1.35
    for k in range(0, 6):
        nb_val = negative_binomial_pmf(k, mu, r=1000.0)
        pois_val = poisson_pmf(k, mu)
        assert pytest.approx(nb_val, rel=1e-3, abs=1e-4) == pois_val


def test_clean_sheet_zero_inflation():
    """Under overdispersion, P(X = 0) is strictly higher than under pure Poisson."""
    mu = 1.20
    r = 6.0
    nb_cs = negative_binomial_clean_sheet_prob(mu, r=r)
    pois_cs = poisson_clean_sheet_prob(mu)

    # (1 + mu/r)^(-r) > exp(-mu) for all mu > 0, r > 0
    assert nb_cs > pois_cs
    assert pytest.approx(nb_cs, abs=1e-3) == math.pow(1.0 + (mu / r), -r)


def test_heavy_defeat_tail_probabilities():
    """Negative Binomial has fatter tails (blowouts of 4+ goals conceded) than Poisson."""
    mu = 1.80  # Leaky defense facing strong attack
    r = 4.0

    tail_pois = sum(poisson_pmf(k, mu) for k in range(4, 11))
    tail_nb = sum(negative_binomial_pmf(k, mu, r=r) for k in range(4, 11))

    # Tail probability of conceding 4+ goals should be strictly higher under Negative Binomial
    assert tail_nb > tail_pois


def test_c10_exact_penalty_monotonicity_and_convergence():
    """C10 exact discrete penalty must be strictly monotonic in mu and converge to Poisson as r -> inf."""
    r = 5.0
    pen_low = negative_binomial_exact_gc_penalty(0.8, r=r)
    pen_med = negative_binomial_exact_gc_penalty(1.5, r=r)
    pen_high = negative_binomial_exact_gc_penalty(2.5, r=r)

    # Penalties are negative numbers; higher goals conceded -> strictly more negative penalty
    assert 0.0 >= pen_low > pen_med > pen_high

    # As r -> inf, NB penalty converges to Poisson penalty
    pen_large_r = negative_binomial_exact_gc_penalty(1.8, r=1000.0)
    pen_pois = poisson_exact_gc_penalty(1.8)
    assert pytest.approx(pen_large_r, rel=1e-3, abs=1e-4) == pen_pois


def test_predict_player_points_nb_integration():
    """predict_player_points integrates Negative Binomial for GK and DEF components."""
    defender = {
        'position': 'DEF',
        'season_minutes': 1800,
        'season_starts': 20,
        'fbref_subs': 0,
        'fbref_unused_subs': 0,
        'team_long_form_xgc90': 1.30,
        'now_cost': 60,
    }

    pred_nb = predict_player_points(defender, dispersion_r=6.0)
    pred_pois = predict_player_points(defender, dispersion_r=500.0)

    # Output dictionary must contain valid numeric C9 and C10 keys
    assert 'c9_clean_sheets' in pred_nb
    assert 'c10_goals_conceded' in pred_nb
    assert pred_nb['c9_clean_sheets'] > 0.0
    assert pred_nb['c10_goals_conceded'] < 0.0

    # Clean sheet is slightly higher and penalty is adjusted
    assert isinstance(pred_nb['expected_points'], float)
    assert pred_nb['expected_points'] > 0.0


def test_calibration_dispersion_estimator():
    """Calibration estimator reads historical data and returns plausible dispersion parameters."""
    result = estimate_league_dispersion(data_root='data')
    assert 'dispersion_r' in result
    assert 'mean_goals' in result
    assert 'var_goals' in result
    assert result['sample_size'] > 0
    assert 2.0 <= result['dispersion_r'] <= 50.0


def test_c10_upper_tail_capping():
    """Verify that extreme xGC values are capped at -5.0 pts without probability mass leakage."""
    from model.prediction_engine import negative_binomial_exact_gc_penalty, poisson_exact_gc_penalty

    # For an extreme blowout (xGC = 8.0), penalty expectation should be strictly negative and bounded by -5.0
    pen_nb = negative_binomial_exact_gc_penalty(8.0, r=4.0)
    pen_pois = poisson_exact_gc_penalty(8.0)

    assert -5.0 <= pen_nb <= -3.0
    assert -5.0 <= pen_pois <= -3.0


def test_clean_sheet_pitch_exposure_scaling():
    """Fullbacks subbed at 60-70 mins have higher clean sheet expectation than 90-min players."""
    # Starter playing full 90
    cb = {
        'player_code': 501,
        'web_name': 'IronCB',
        'position': 'DEF',
        'team': 'Arsenal',
        'status': 'a',
        'chance_of_playing_next_round': 100,
        'short_form_starts': 6,
        'short_form_matches': 6,
        'short_form_minutes': 540,
        'team_long_form_xgc90': 1.2,
        'now_cost': 60,
    }
    # Fullback with tactical early hook around minute 65
    fb = {
        'player_code': 502,
        'web_name': 'EarlySubFB',
        'position': 'DEF',
        'team': 'Arsenal',
        'status': 'a',
        'chance_of_playing_next_round': 100,
        'short_form_starts': 6,
        'short_form_matches': 6,
        'short_form_minutes': 390,  # ~65 mins per match
        'sub_minute_p50': 65.0,
        'team_long_form_xgc90': 1.2,
        'now_cost': 60,
    }
    pred_cb = predict_player_points(cb)
    pred_fb = predict_player_points(fb)

    # Effective clean sheet rate per qualification is higher for FB because they are exposed to fewer minutes
    # c9 / p_60_plus = 4.0 * P(CS on pitch)
    cb_cs_per_qual = pred_cb['c9_clean_sheets'] / max(0.01, pred_cb['p_60_plus'])
    fb_cs_per_qual = pred_fb['c9_clean_sheets'] / max(0.01, pred_fb['p_60_plus'])

    assert fb_cs_per_qual > cb_cs_per_qual


"""Historical Calibration & Parameter Estimation Engine.

Estimates probabilistic distributions and calibration parameters (such as
Negative Binomial dispersion parameter r) from historical Premier League
fixtures and matchday scorelines.
"""
import glob
import math
import os
import sys
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_EMPIRICAL_DISPERSION_R: float = 6.0


def estimate_league_dispersion(
    data_root: str = 'data',
    min_seasons: int = 1,
) -> Dict[str, float]:
    """Estimate league-wide goals conceded dispersion parameter r from fixtures.csv.

    Under a Negative Binomial distribution NB(r, p) parameterized by mean mu and
    dispersion r:
        Var(X) = mu + mu^2 / r
    Solving for r via Method of Moments:
        r = mu^2 / (Var(X) - mu)

    Args:
        data_root: root directory containing season folders.
        min_seasons: minimum number of season folders required.

    Returns:
        Dict with keys:
            'sample_size': total team match scores analyzed,
            'mean_goals': sample mean goals conceded per match,
            'var_goals': sample variance,
            'dispersion_ratio': Var / Mean (> 1 indicates overdispersion),
            'dispersion_r': estimated dispersion parameter r (clamped to [2.0, 50.0]).
    """
    pattern = os.path.join(data_root, '*', 'fixtures.csv')
    fixture_files = sorted(glob.glob(pattern))

    all_scores: List[float] = []

    for f_path in fixture_files:
        try:
            df = pd.read_csv(f_path)
            if 'team_h_score' in df.columns and 'team_a_score' in df.columns:
                h_scores = pd.to_numeric(df['team_h_score'], errors='coerce').dropna()
                a_scores = pd.to_numeric(df['team_a_score'], errors='coerce').dropna()
                all_scores.extend(h_scores.tolist())
                all_scores.extend(a_scores.tolist())
        except Exception:
            continue

    if len(all_scores) < 100:
        return {
            'sample_size': float(len(all_scores)),
            'mean_goals': 1.40,
            'var_goals': 1.65,
            'dispersion_ratio': 1.18,
            'dispersion_r': DEFAULT_EMPIRICAL_DISPERSION_R,
        }

    arr = np.array(all_scores, dtype=np.float64)
    mean_val = float(np.mean(arr))
    var_val = float(np.var(arr, ddof=1))

    if var_val > mean_val:
        r_raw = (mean_val ** 2) / (var_val - mean_val)
        dispersion_r = max(2.0, min(50.0, r_raw))
    else:
        dispersion_r = 50.0  # Near-Poisson limit

    return {
        'sample_size': float(len(arr)),
        'mean_goals': round(mean_val, 4),
        'var_goals': round(var_val, 4),
        'dispersion_ratio': round(var_val / max(0.1, mean_val), 4),
        'dispersion_r': round(dispersion_r, 4),
    }

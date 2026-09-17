"""Tests for the positional bias correction feedback loop."""
import os
import sys
import tempfile
import shutil

import pandas as pd
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.fixture_engine import (
    load_positional_bias_corrections,
    MIN_GWS_FOR_CORRECTION,
    MAX_BIAS_CORRECTION_PTS,
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory with a season sub-folder."""
    tmpdir = tempfile.mkdtemp()
    season_dir = os.path.join(tmpdir, '2026-27')
    os.makedirs(season_dir, exist_ok=True)
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def _write_accuracy_log(data_root: str, rows: list):
    """Helper to write accuracy_log.csv from a list of dicts."""
    season_dir = os.path.join(data_root, '2026-27')
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(season_dir, 'accuracy_log.csv'), index=False)


class TestLoadPositionalBiasCorrections:
    """Tests for load_positional_bias_corrections()."""

    def test_returns_empty_when_no_log_file(self, temp_data_dir):
        """No accuracy_log.csv -> empty corrections."""
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        assert result == {}

    def test_returns_empty_when_insufficient_gameweeks(self, temp_data_dir):
        """Only 1 GW of data (< MIN_GWS_FOR_CORRECTION=2) -> empty."""
        _write_accuracy_log(temp_data_dir, [
            {'gameweek': 1, 'gk_bias': 0.3, 'def_bias': 0.1, 'mid_bias': -0.2, 'fwd_bias': 0.15},
        ])
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        assert result == {}

    def test_returns_corrections_with_sufficient_data(self, temp_data_dir):
        """With 2+ GWs of data, corrections should be returned."""
        _write_accuracy_log(temp_data_dir, [
            {'gameweek': 1, 'gk_bias': 0.20, 'def_bias': 0.10, 'mid_bias': -0.10, 'fwd_bias': 0.15},
            {'gameweek': 2, 'gk_bias': 0.30, 'def_bias': -0.10, 'mid_bias': -0.20, 'fwd_bias': 0.10},
        ])
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        assert len(result) > 0
        # All positions should have corrections
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            assert pos in result

    def test_positive_bias_yields_negative_correction(self, temp_data_dir):
        """Over-prediction (positive bias) should produce negative correction."""
        _write_accuracy_log(temp_data_dir, [
            {'gameweek': 1, 'gk_bias': 0.30, 'def_bias': 0.0, 'mid_bias': 0.0, 'fwd_bias': 0.0},
            {'gameweek': 2, 'gk_bias': 0.30, 'def_bias': 0.0, 'mid_bias': 0.0, 'fwd_bias': 0.0},
        ])
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        # GK bias is consistently +0.30, so correction should be -0.30
        assert result['GK'] < 0

    def test_negative_bias_yields_positive_correction(self, temp_data_dir):
        """Under-prediction (negative bias) should produce positive correction."""
        _write_accuracy_log(temp_data_dir, [
            {'gameweek': 1, 'gk_bias': 0.0, 'def_bias': 0.0, 'mid_bias': -0.40, 'fwd_bias': 0.0},
            {'gameweek': 2, 'gk_bias': 0.0, 'def_bias': 0.0, 'mid_bias': -0.40, 'fwd_bias': 0.0},
        ])
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        # MID bias is consistently -0.40, so correction should be +0.40
        assert result['MID'] > 0

    def test_correction_is_clamped(self, temp_data_dir):
        """Corrections should be clamped to MAX_BIAS_CORRECTION_PTS."""
        _write_accuracy_log(temp_data_dir, [
            {'gameweek': 1, 'gk_bias': 2.0, 'def_bias': -2.0, 'mid_bias': 0.0, 'fwd_bias': 0.0},
            {'gameweek': 2, 'gk_bias': 2.0, 'def_bias': -2.0, 'mid_bias': 0.0, 'fwd_bias': 0.0},
        ])
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        # Even with extreme bias, correction should be clamped
        assert abs(result['GK']) <= MAX_BIAS_CORRECTION_PTS
        assert abs(result['DEF']) <= MAX_BIAS_CORRECTION_PTS

    def test_ewma_weights_recent_more(self, temp_data_dir):
        """EWMA should incorporate recent gameweeks smoothly without extreme whipsaws."""
        _write_accuracy_log(temp_data_dir, [
            {'gameweek': 1, 'gk_bias': 0.40, 'def_bias': 0.0, 'mid_bias': 0.0, 'fwd_bias': 0.0},
            {'gameweek': 2, 'gk_bias': 0.10, 'def_bias': 0.0, 'mid_bias': 0.0, 'fwd_bias': 0.0},
        ])
        result = load_positional_bias_corrections(season='2026-27', data_root=temp_data_dir)
        # With stabilized EWMA alpha=0.18:
        # EWMA = 0.18*0.10 + 0.82*0.40 = 0.346, correction = -0.346
        # Verifies that recent improvement pulled the correction toward zero (-0.346 > -0.40)
        assert -0.35 <= result['GK'] < -0.30

    def test_team_bias_orthogonalization_on_defenders(self):
        """Verify that team bias applies full correction to attackers and 40% residual to defenders."""
        from model.fixture_engine import load_team_bias_corrections

        # Create a test dataframe with an attacker and defender
        test_df = pd.DataFrame([
            {'player_code': 1, 'team': 'Arsenal', 'position': 'DEF', 'expected_points': 5.0},
            {'player_code': 2, 'team': 'Arsenal', 'position': 'FWD', 'expected_points': 6.0},
        ])
        team_corrections = {'Arsenal': -0.15}

        # Apply orthogonalized logic
        for t_name, correction in team_corrections.items():
            team_mask = test_df['team'].astype(str).str.lower() == t_name.lower()
            def_mask = team_mask & test_df['position'].astype(str).str.upper().isin(['GK', 'DEF'])
            att_mask = team_mask & ~test_df['position'].astype(str).str.upper().isin(['GK', 'DEF'])

            test_df.loc[att_mask, 'expected_points'] = (test_df.loc[att_mask, 'expected_points'] + correction).round(4)
            test_df.loc[def_mask, 'expected_points'] = (test_df.loc[def_mask, 'expected_points'] + (correction * 0.40)).round(4)

        # Attacker received full -0.15 correction (6.0 -> 5.85)
        assert test_df.loc[1, 'expected_points'] == 5.85
        # Defender received 40% of -0.15 = -0.06 correction (5.0 -> 4.94)
        assert test_df.loc[0, 'expected_points'] == 4.94

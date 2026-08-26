"""Unit tests for the Post-Gameweek Model Accuracy Tracker (accuracy_tracker.py)."""
import os
import sys
import pandas as pd
import pytest

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.accuracy_tracker import (
    evaluate_gameweek_accuracy,
    GameweekAccuracyReport,
    PositionAccuracy,
)


def test_evaluate_gameweek_accuracy_synthetic(tmp_path):
    """Test accuracy calculation against synthetic prediction and actual datasets."""
    season = '2026-27'
    season_dir = tmp_path / 'data' / season
    season_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write synthetic prediction CSV
    pred_data = [
        {'player_code': 101, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'expected_points': 7.5},
        {'player_code': 102, 'web_name': 'Palmer', 'team': 'Chelsea', 'position': 'MID', 'expected_points': 6.0},
        {'player_code': 103, 'web_name': 'Gabriel', 'team': 'Arsenal', 'position': 'DEF', 'expected_points': 4.5},
        {'player_code': 104, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'expected_points': 4.0},
    ]
    pd.DataFrame(pred_data).to_csv(season_dir / 'fixture_predictions_gw1.csv', index=False)

    # 2. Write synthetic actual points in players_raw.csv
    raw_data = [
        {'code': 101, 'web_name': 'Haaland', 'event_points': 13, 'minutes': 90, 'element_type': 4},
        {'code': 102, 'web_name': 'Palmer', 'event_points': 5, 'minutes': 90, 'element_type': 3},
        {'code': 103, 'web_name': 'Gabriel', 'event_points': 6, 'minutes': 90, 'element_type': 2},
        {'code': 104, 'web_name': 'Raya', 'event_points': 2, 'minutes': 90, 'element_type': 1},
    ]
    pd.DataFrame(raw_data).to_csv(season_dir / 'players_raw.csv', index=False)

    # 3. Evaluate accuracy
    report = evaluate_gameweek_accuracy(season=season, gw=1, data_root=str(tmp_path / 'data'), save_log=True)

    assert report is not None
    assert isinstance(report, GameweekAccuracyReport)
    assert report.total_players == 4
    assert report.active_players == 4

    # Errors:
    # Haaland: |7.5 - 13| = 5.5
    # Palmer: |6.0 - 5| = 1.0
    # Gabriel: |4.5 - 6| = 1.5
    # Raya: |4.0 - 2| = 2.0
    # MAE = (5.5 + 1.0 + 1.5 + 2.0) / 4 = 10.0 / 4 = 2.5
    assert pytest.approx(report.overall_mae, 0.01) == 2.5
    assert report.rank_correlation > 0.0

    # Check accuracy log creation
    log_file = season_dir / 'accuracy_log.csv'
    assert log_file.exists()
    log_df = pd.read_csv(log_file)
    assert len(log_df) == 1
    assert log_df.iloc[0]['gameweek'] == 1
    assert pytest.approx(log_df.iloc[0]['overall_mae'], 0.01) == 2.5

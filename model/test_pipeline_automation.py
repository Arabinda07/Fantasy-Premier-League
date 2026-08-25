"""Unit tests for FPL Live Data Pipeline Automation Engine."""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.pipeline_automation import (
    detect_active_gameweek,
    sync_api_data,
    record_price_snapshot,
    rebuild_dataset,
    generate_predictions,
    run_live_solver,
    run_live_pipeline,
    PipelineResult,
    StageResult,
)


class TestDetectActiveGameweek:
    """Verify gameweek detection from local fixtures data and API fallback."""

    def test_detect_from_local_fixtures(self):
        """Should resolve current GW from local fixtures.csv when offline."""
        current_gw, next_gw, deadline = detect_active_gameweek(
            season='2026-27', data_root='data', offline=True,
        )
        # With actual 2026-27 data on disk (pre-season: no finished fixtures),
        # current_gw=0 and next_gw=1
        assert current_gw is not None
        assert next_gw is not None
        assert next_gw >= 1

    def test_detect_offline_returns_tuple(self):
        """Should always return a 3-tuple even if detection fails."""
        result = detect_active_gameweek(
            season='nonexistent-season', data_root='data', offline=True,
        )
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_detect_missing_season_returns_nones(self):
        """For a nonexistent season, all values should be None."""
        current_gw, next_gw, deadline = detect_active_gameweek(
            season='1999-00', data_root='data', offline=True,
        )
        assert current_gw is None
        assert next_gw is None
        assert deadline is None


class TestPriceSnapshotAndVelocity:
    """Verify daily price velocity snapshotting and alert generation."""

    def test_price_snapshot_creates_file(self):
        """Should create a price_history/<date>.csv file."""
        result = record_price_snapshot(season='2026-27', data_root='data')
        assert result.success is True
        assert 'alerts' in result.message

        # Verify the snapshot file was created
        price_dir = os.path.join('data', '2026-27', 'price_history')
        assert os.path.isdir(price_dir)

        csv_files = [f for f in os.listdir(price_dir) if f.endswith('.csv')]
        assert len(csv_files) >= 1

    def test_price_snapshot_content_structure(self):
        """Snapshot CSV should have required columns."""
        result = record_price_snapshot(season='2026-27', data_root='data')
        assert result.success

        price_dir = os.path.join('data', '2026-27', 'price_history')
        csv_files = sorted([f for f in os.listdir(price_dir) if f.endswith('.csv')])
        latest = pd.read_csv(os.path.join(price_dir, csv_files[-1]))

        required_cols = ['date', 'player_code', 'web_name', 'now_cost',
                         'net_velocity', 'velocity_ratio', 'trend']
        for col in required_cols:
            assert col in latest.columns, f"Missing column: {col}"

        # Trend values should be valid tiers
        valid_tiers = {'RISING_LOCK', 'RISING_ALERT', 'STABLE', 'FALLING_ALERT', 'FALLING_LOCK'}
        assert set(latest['trend'].unique()).issubset(valid_tiers)

    def test_price_snapshot_missing_season(self):
        """Should fail gracefully for nonexistent season."""
        result = record_price_snapshot(season='1999-00', data_root='data')
        assert result.success is False
        assert result.error is not None


class TestSyncModeExecution:
    """Verify pipeline execution in sync mode with offline fallback."""

    def test_offline_sync_pipeline(self):
        """Full offline sync should exercise all stages with local data."""
        result = run_live_pipeline(
            season='2026-27',
            gw=2,
            mode='sync',
            bank=0.0,
            free_transfers=1,
            horizon=2,
            data_root='data',
            offline=True,
            export_excel=False,
            export_json=False,
        )
        assert isinstance(result, PipelineResult)
        assert result.season == '2026-27'
        assert result.gameweek == 2
        assert result.mode == 'sync'
        # In offline mode, API sync reports success (skipped)
        api_stages = [s for s in result.stages if s.stage == 'api_sync']
        assert len(api_stages) == 1
        assert api_stages[0].success is True

    def test_sync_produces_price_snapshot(self):
        """Sync mode should always produce a price velocity snapshot."""
        result = run_live_pipeline(
            season='2026-27',
            gw=2,
            mode='sync',
            data_root='data',
            offline=True,
            export_excel=False,
            export_json=False,
        )
        price_stages = [s for s in result.stages if s.stage == 'price_snapshot']
        assert len(price_stages) == 1
        assert price_stages[0].success is True


class TestSolverOnlyMode:
    """Verify solver_only mode skips API, dataset, and prediction stages."""

    def test_solver_only_skips_early_stages(self):
        """solver_only should not include api_sync, price_snapshot, or predictions stages."""
        result = run_live_pipeline(
            season='2026-27',
            gw=2,
            mode='solver_only',
            bank=0.0,
            free_transfers=1,
            horizon=2,
            data_root='data',
            export_excel=False,
            export_json=False,
        )
        assert isinstance(result, PipelineResult)
        assert result.mode == 'solver_only'

        stage_names = [s.stage for s in result.stages]
        assert 'api_sync' not in stage_names
        assert 'price_snapshot' not in stage_names
        assert 'dataset_rebuild' not in stage_names
        assert 'predictions' not in stage_names
        assert 'live_solver' in stage_names

    def test_solver_only_produces_solution(self):
        """solver_only should produce a valid solver result."""
        result = run_live_pipeline(
            season='2026-27',
            gw=2,
            mode='solver_only',
            bank=0.0,
            free_transfers=1,
            horizon=2,
            data_root='data',
            export_excel=False,
            export_json=False,
        )
        solver_stages = [s for s in result.stages if s.stage == 'live_solver']
        assert len(solver_stages) == 1
        assert solver_stages[0].success is True
        assert 'xP' in solver_stages[0].message


class TestErrorHandlingAndFallback:
    """Verify graceful degradation on missing data or API failures."""

    def test_pipeline_with_nonexistent_season(self):
        """Pipeline should handle nonexistent season data gracefully."""
        result = run_live_pipeline(
            season='1999-00',
            gw=1,
            mode='solver_only',
            data_root='data',
            offline=True,
            export_excel=False,
            export_json=False,
        )
        # Should complete (possibly with failures) but not crash
        assert isinstance(result, PipelineResult)

    def test_stage_result_structure(self):
        """StageResult should have correct fields."""
        sr = StageResult(stage='test', success=True, duration_seconds=1.5, message='OK')
        assert sr.stage == 'test'
        assert sr.success is True
        assert sr.duration_seconds == 1.5
        assert sr.message == 'OK'
        assert sr.error is None

    def test_pipeline_result_structure(self):
        """PipelineResult should have correct default fields."""
        pr = PipelineResult(
            season='2026-27', gameweek=1, mode='sync', success=True,
        )
        assert pr.season == '2026-27'
        assert pr.gameweek == 1
        assert pr.stages == []
        assert pr.price_alerts_count == 0
        assert pr.matchday_result is None

    def test_predictions_only_mode(self):
        """predictions_only should skip API, dataset, and solver stages."""
        result = run_live_pipeline(
            season='2026-27',
            gw=2,
            mode='predictions_only',
            data_root='data',
            offline=True,
            export_excel=False,
            export_json=False,
        )
        stage_names = [s.stage for s in result.stages]
        assert 'api_sync' not in stage_names
        assert 'price_snapshot' not in stage_names
        assert 'live_solver' not in stage_names
        assert 'predictions' in stage_names

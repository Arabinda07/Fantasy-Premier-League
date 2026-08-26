"""Unit tests for the Native FPL Opta Dataset Builder (model/build_dataset.py)."""
import os
import pandas as pd
import pytest

from model.build_dataset import (
    build_dataset,
    compute_native_participation,
    load_teams_map,
    determine_current_gw,
)

DATA_ROOT = 'data'
SEASON = '2026-27'


class TestNativeParticipationStats:
    """Test suite for native FPL API participation extraction."""

    def test_compute_native_participation_returns_dataframe(self):
        df = compute_native_participation(season=SEASON, gw=1, data_root=DATA_ROOT)
        assert isinstance(df, pd.DataFrame)
        if not df.empty:
            assert 'player_code' in df.columns
            assert 'season_starts' in df.columns
            assert 'season_subs' in df.columns
            assert 'fbref_starts' in df.columns
            assert 'fbref_subs' in df.columns
            assert len(df) > 500

    def test_native_participation_values_are_valid(self):
        df = compute_native_participation(season=SEASON, gw=1, data_root=DATA_ROOT)
        if not df.empty:
            # Starts and subs should be non-negative integers
            assert (df['season_starts'] >= 0).all()
            assert (df['season_subs'] >= 0).all()
            assert (df['fbref_starts'] >= 0).all()
            assert (df['fbref_subs'] >= 0).all()

    def test_compute_native_participation_nonexistent_season(self):
        df = compute_native_participation(season='1990-91', gw=1, data_root=DATA_ROOT)
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestBuildDatasetNative:
    """Test suite for consolidated native dataset builder."""

    def test_teams_map_loading(self):
        teams_map = load_teams_map(season=SEASON, data_root=DATA_ROOT)
        assert isinstance(teams_map, dict)
        assert len(teams_map) == 20
        assert 'Arsenal' in teams_map.values()
        assert 'Man City' in teams_map.values()

    def test_determine_current_gw(self):
        gw = determine_current_gw(season=SEASON, data_root=DATA_ROOT)
        assert isinstance(gw, int)
        assert 1 <= gw <= 38

    def test_build_dataset_offline_creates_model_dataset(self):
        df = build_dataset(
            season=SEASON,
            gw=1,
            data_root=DATA_ROOT,
            skip_scrape=True,
        )
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) >= 600

        # Verify key identifiers
        assert 'player_code' in df.columns
        assert 'web_name' in df.columns
        assert 'team' in df.columns
        assert 'position' in df.columns

        # Verify rolling form metrics
        assert 'long_form_minutes' in df.columns
        assert 'long_form_expected_goals_90' in df.columns
        assert 'long_form_expected_assists_90' in df.columns
        assert 'long_form_expected_goals_conceded_90' in df.columns
        assert 'short_form_expected_goals_90' in df.columns

        # Verify team rates
        assert 'team_long_form_xg90' in df.columns
        assert 'team_long_form_xgc90' in df.columns

        # Verify participation metrics
        assert 'season_starts' in df.columns
        assert 'season_minutes' in df.columns
        assert 'fbref_starts' in df.columns
        assert 'fbref_subs' in df.columns

    def test_build_dataset_persists_csv_file(self):
        out_csv = os.path.join(DATA_ROOT, SEASON, 'model_dataset.csv')
        assert os.path.exists(out_csv)
        file_df = pd.read_csv(out_csv, encoding='utf-8')
        assert len(file_df) >= 600

"""Unit tests for DataStore seam (model/data_store.py)."""
import os
import shutil
import tempfile
import pandas as pd
import pytest

from model.data_store import DataStore, default_data_store


class TestDataStoreBasics:
    """Test DataStore path resolution and read behaviors."""

    def test_default_instance_exists(self):
        """Default singleton should be instantiated with data/ root."""
        assert default_data_store is not None
        assert str(default_data_store.data_root) == "data"

    def test_path_resolution(self):
        """Verify season directory and relative file path resolution."""
        ds = DataStore(data_root="data")
        assert ds.season_dir("2026-27") == ds.data_root / "2026-27"
        assert ds.file_path("2026-27", "gws", "merged_gw.csv") == ds.data_root / "2026-27" / "gws" / "merged_gw.csv"

    def test_season_exists_check(self):
        """Should return True for existing seasons and False for missing ones."""
        ds = DataStore(data_root="data")
        assert ds.season_exists("2026-27") is True
        assert ds.season_exists("1999-00") is False

    def test_missing_season_returns_empty_dataframes(self):
        """Querying a nonexistent season should safely return empty DataFrames without raising."""
        ds = DataStore(data_root="data")
        assert ds.get_players_raw("1999-00").empty
        assert ds.get_merged_gw("1999-00").empty
        assert ds.get_fixtures("1999-00").empty
        assert ds.get_teams("1999-00").empty
        assert ds.get_teams_map("1999-00") == {}
        assert ds.get_element_to_code_map("1999-00") == {}
        assert ds.get_code_to_element_map("1999-00") == {}


class TestDataStoreActiveSeason:
    """Verify DataStore reads real active season datasets."""

    def test_load_players_raw_and_mappings(self):
        """Verify players_raw and element/code mappings for 2026-27."""
        ds = DataStore(data_root="data")
        df = ds.get_players_raw("2026-27")
        assert not df.empty
        assert "id" in df.columns
        assert "code" in df.columns

        elem_to_code = ds.get_element_to_code_map("2026-27")
        code_to_elem = ds.get_code_to_element_map("2026-27")
        assert len(elem_to_code) == len(df)
        assert len(code_to_elem) == len(df)

        # Invertibility check
        first_id = df.iloc[0]["id"]
        first_code = df.iloc[0]["code"]
        assert elem_to_code[first_id] == first_code
        assert code_to_elem[first_code] == first_id

    def test_caching_behavior(self):
        """Verify cached DataFrame is returned and clear_cache works."""
        ds = DataStore(data_root="data", cache=True)
        df1 = ds.get_players_raw("2026-27")
        df2 = ds.get_players_raw("2026-27")
        assert df1.equals(df2)
        assert f"2026-27:players_raw" in ds._df_cache

        ds.clear_cache()
        assert len(ds._df_cache) == 0


class TestDataStoreSaveRoundtrip:
    """Verify write and read roundtrip in an isolated temporary directory."""

    @pytest.fixture
    def temp_store(self):
        tmp_dir = tempfile.mkdtemp()
        store = DataStore(data_root=tmp_dir)
        yield store, tmp_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_model_dataset_roundtrip(self, temp_store):
        store, _ = temp_store
        sample_df = pd.DataFrame([{"player_code": 118748, "web_name": "Salah", "xP": 8.5}])
        out_path = store.save_model_dataset("2026-27", sample_df)
        assert os.path.exists(out_path)

        loaded_df = store.get_model_dataset("2026-27")
        assert len(loaded_df) == 1
        assert loaded_df.iloc[0]["web_name"] == "Salah"

    def test_manager_snapshot_roundtrip(self, temp_store):
        store, _ = temp_store
        sample_profile = {"entry_id": 9500404, "manager_name": "Arabinda", "bank": 1.5}
        
        # Save team-specific snapshot
        path1 = store.save_manager_squad_snapshot("2026-27", sample_profile, entry_id=9500404)
        assert os.path.exists(path1)
        loaded1 = store.get_manager_squad_snapshot("2026-27", entry_id=9500404)
        assert loaded1["manager_name"] == "Arabinda"

        # Save global snapshot
        path2 = store.save_manager_squad_snapshot("2026-27", sample_profile, entry_id=None)
        assert os.path.exists(path2)
        loaded2 = store.get_manager_squad_snapshot("2026-27", entry_id=None)
        assert loaded2["entry_id"] == 9500404

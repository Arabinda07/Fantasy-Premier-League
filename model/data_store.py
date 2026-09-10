"""Unified Data Access Seam & Repository Store for FPL Model Datasets.

Provides a clean, deep-module interface (small surface area, comprehensive implementation)
hiding filesystem paths, directory layout, schema loading, and caching from callers across
the predictive intelligence and squad solver pipelines.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import pandas as pd


class DataStore:
    """Encapsulated data access seam for FPL historical and active season datasets.
    
    Hides all disk storage details, path resolution, in-memory caching, and serialization
    from calculation, simulation, and optimization engines.
    """

    def __init__(self, data_root: Union[str, Path] = "data", cache: bool = True) -> None:
        """Initialize DataStore.
        
        Args:
            data_root: Root directory where season folders reside (default: 'data').
            cache: Whether to retain read DataFrames in memory for repeated lookups.
        """
        self.data_root = Path(data_root)
        self.use_cache = cache
        self._df_cache: Dict[str, pd.DataFrame] = {}
        self._json_cache: Dict[str, Any] = {}

    def clear_cache(self) -> None:
        """Clear all in-memory cached datasets."""
        self._df_cache.clear()
        self._json_cache.clear()

    # -----------------------------------------------------------------------
    # Path Resolution Helpers
    # -----------------------------------------------------------------------

    def season_dir(self, season: str) -> Path:
        """Return Path to a season directory."""
        return self.data_root / season

    def file_path(self, season: str, *parts: str) -> Path:
        """Resolve a file path relative to a season directory."""
        return self.season_dir(season).joinpath(*parts)

    def season_exists(self, season: str) -> bool:
        """Check if season folder exists and contains valid data."""
        sdir = self.season_dir(season)
        return sdir.is_dir() and (sdir / "players_raw.csv").is_file()

    # -----------------------------------------------------------------------
    # Ingest / Core Datasets
    # -----------------------------------------------------------------------

    def get_players_raw(self, season: str) -> pd.DataFrame:
        """Load players_raw.csv for the given season.
        
        Returns:
            DataFrame containing players_raw data, or empty DataFrame if not found.
        """
        cache_key = f"{season}:players_raw"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "players_raw.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path, low_memory=False)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def get_merged_gw(self, season: str) -> pd.DataFrame:
        """Load gws/merged_gw.csv for the given season.
        
        Returns:
            DataFrame containing merged gameweek match logs.
        """
        cache_key = f"{season}:merged_gw"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "gws", "merged_gw.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path, low_memory=False)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def get_fixtures(self, season: str) -> pd.DataFrame:
        """Load fixtures.csv for the given season.
        
        Returns:
            DataFrame of scheduled/played fixtures.
        """
        cache_key = f"{season}:fixtures"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "fixtures.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def get_teams(self, season: str) -> pd.DataFrame:
        """Load teams.csv for the given season."""
        cache_key = f"{season}:teams"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "teams.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def get_teams_map(self, season: str) -> Dict[int, str]:
        """Load team ID -> team name mapping dictionary."""
        teams_df = self.get_teams(season)
        if teams_df.empty or 'id' not in teams_df.columns or 'name' not in teams_df.columns:
            return {}
        return dict(zip(teams_df['id'].astype(int), teams_df['name'].astype(str)))

    def get_element_to_code_map(self, season: str) -> Dict[int, int]:
        """Map FPL 1-based element ID -> permanent Opta player code."""
        players_df = self.get_players_raw(season)
        if players_df.empty or 'id' not in players_df.columns or 'code' not in players_df.columns:
            return {}
        return dict(zip(players_df['id'].astype(int), players_df['code'].astype(int)))

    def get_code_to_element_map(self, season: str) -> Dict[int, int]:
        """Map permanent Opta player code -> FPL 1-based element ID."""
        players_df = self.get_players_raw(season)
        if players_df.empty or 'id' not in players_df.columns or 'code' not in players_df.columns:
            return {}
        return dict(zip(players_df['code'].astype(int), players_df['id'].astype(int)))

    # -----------------------------------------------------------------------
    # Feature Store & Model Datasets
    # -----------------------------------------------------------------------

    def get_model_dataset(self, season: str) -> pd.DataFrame:
        """Load unified feature dataset (data/<season>/model_dataset.csv)."""
        cache_key = f"{season}:model_dataset"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "model_dataset.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path, low_memory=False)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def save_model_dataset(self, season: str, df: pd.DataFrame) -> Path:
        """Save model_dataset.csv for the given season."""
        out_dir = self.season_dir(season)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "model_dataset.csv"
        df.to_csv(path, index=False)
        if self.use_cache:
            self._df_cache[f"{season}:model_dataset"] = df.copy()
        return path

    # -----------------------------------------------------------------------
    # Prediction Artifacts
    # -----------------------------------------------------------------------

    def get_predictions(self, season: str) -> pd.DataFrame:
        """Load baseline 11-component predictions (data/<season>/predictions.csv)."""
        cache_key = f"{season}:predictions"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "predictions.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path, low_memory=False)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def save_predictions(self, season: str, df: pd.DataFrame) -> Path:
        """Save predictions.csv for the given season."""
        out_dir = self.season_dir(season)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "predictions.csv"
        df.to_csv(path, index=False)
        if self.use_cache:
            self._df_cache[f"{season}:predictions"] = df.copy()
        return path

    def get_fixture_predictions(self, season: str) -> pd.DataFrame:
        """Load fixture-adjusted predictions (data/<season>/fixture_predictions.csv)."""
        cache_key = f"{season}:fixture_predictions"
        if self.use_cache and cache_key in self._df_cache:
            return self._df_cache[cache_key].copy()

        path = self.file_path(season, "fixture_predictions.csv")
        if not path.is_file():
            return pd.DataFrame()

        df = pd.read_csv(path, low_memory=False)
        if self.use_cache:
            self._df_cache[cache_key] = df
        return df.copy()

    def save_fixture_predictions(self, season: str, df: pd.DataFrame) -> Path:
        """Save fixture_predictions.csv for the given season."""
        out_dir = self.season_dir(season)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "fixture_predictions.csv"
        df.to_csv(path, index=False)
        if self.use_cache:
            self._df_cache[f"{season}:fixture_predictions"] = df.copy()
        return path

    # -----------------------------------------------------------------------
    # Squad & Live Sync State Snapshots
    # -----------------------------------------------------------------------

    def get_manager_squad_snapshot(
        self, season: str, entry_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Load manager squad JSON snapshot."""
        filename = f"manager_squad_{entry_id}.json" if entry_id is not None else "current_squad.json"
        path = self.file_path(season, filename)
        if not path.is_file():
            return None

        cache_key = f"{season}:{filename}"
        if self.use_cache and cache_key in self._json_cache:
            return self._json_cache[cache_key]

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if self.use_cache:
            self._json_cache[cache_key] = data
        return data

    def save_manager_squad_snapshot(
        self, season: str, profile_dict: Dict[str, Any], entry_id: Optional[int] = None
    ) -> Path:
        """Save manager squad JSON snapshot."""
        filename = f"manager_squad_{entry_id}.json" if entry_id is not None else "current_squad.json"
        out_dir = self.season_dir(season)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile_dict, f, indent=2)

        if self.use_cache:
            self._json_cache[f"{season}:{filename}"] = profile_dict
        return path


# Canonical singleton instance for convenient import
default_data_store = DataStore()

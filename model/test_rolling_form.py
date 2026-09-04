"""Tests for model.rolling_form — the rolling form calculator.

Uses the completed 2025-26 season data (data/2025-26/gws/merged_gw.csv)
as the ground truth. Expected values are hand-computed from that data.
"""
import os
import sys

import pytest
import pandas as pd

# Ensure the repo root is on the path so model/ and data/ are findable.
REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, REPO_ROOT)

from model.rolling_form import (
    compute_player_form,
    compute_team_form,
    build_player_form_dataset,
    build_team_form_dataset,
    _previous_season,
)


DATA_ROOT = os.path.join(REPO_ROOT, 'data')
SEASON = '2025-26'
MAX_GW = 38  # Full season


class TestPreviousSeason:
    """Tests for the _previous_season helper."""

    def test_normal(self):
        assert _previous_season('2025-26') == '2024-25'

    def test_early_boundary(self):
        assert _previous_season('2016-17') is None

    def test_century_boundary(self):
        assert _previous_season('2020-21') == '2019-20'


class TestPlayerFormHaaland:
    """Verify Haaland's (code=223094) rolling form against hand-computed values.

    Long-form (window_gws=None) includes 2024-25 + 2025-26 seasons:
        2024-25: 2736 minutes
        2025-26: 2953 minutes
        Combined: 5689 minutes, xG=47.40, xA=4.71
        xG/90: 0.7499, xA/90: 0.0745

    Short-form (window_gws=6, last 6 GWs of 2025-26: GW33-38):
        Haaland played in GW33(x2), GW35, GW36(x2), GW37, GW38
        Minutes: 450, xG: 3.86, xA: 0.73
        xG/90: 0.7720, xA/90: 0.1460
    """

    def test_long_form_two_seasons(self):
        """Long-form unweighted (full season(s) to date at GW38) for Haaland."""
        result = compute_player_form(SEASON, MAX_GW, window_gws=None,
                                      half_life=None,
                                      data_root=DATA_ROOT)
        assert not result.empty
        haaland = result[result['code'] == 223094]
        assert len(haaland) == 1

        row = haaland.iloc[0]
        assert row['minutes'] == 5689
        assert abs(row['expected_goals'] - 47.40) < 0.1
        assert abs(row['expected_assists'] - 4.71) < 0.1
        assert abs(row['expected_goals_90'] - 0.7499) < 0.01
        assert abs(row['expected_assists_90'] - 0.0745) < 0.01

    def test_short_form_last_6_gws(self):
        """Short-form unweighted (last 6 calendar gameweeks) for Haaland.

        GWs 33-38: Haaland's actual appearances are in GW33(x2), 35, 36(x2),
        37, 38. He missed GW34. Minutes = 450.
        """
        result = compute_player_form(SEASON, MAX_GW, window_gws=6,
                                      half_life=None,
                                      data_root=DATA_ROOT)
        assert not result.empty
        haaland = result[result['code'] == 223094]
        assert len(haaland) == 1

        row = haaland.iloc[0]
        assert row['minutes'] == 450
        assert abs(row['expected_goals'] - 3.86) < 0.1
        assert abs(row['expected_assists'] - 0.73) < 0.1

    def test_single_season_only(self):
        """When window_gws covers just 2025-26, Haaland should have
        2953 minutes (not the combined 5689) in unweighted form.
        """
        result = compute_player_form(SEASON, MAX_GW, window_gws=38,
                                      half_life=None,
                                      data_root=DATA_ROOT)
        haaland = result[result['code'] == 223094]
        assert len(haaland) == 1
        assert haaland.iloc[0]['minutes'] == 2953

    def test_haaland_ewma_decay(self):
        """Under M-03 EWMA decay (half_life=8.0), historical minutes are discounted."""
        result = compute_player_form(SEASON, MAX_GW, window_gws=None,
                                      half_life=8.0,
                                      data_root=DATA_ROOT)
        haaland = result[result['code'] == 223094]
        assert len(haaland) == 1
        row = haaland.iloc[0]
        # Weighted effective minutes are substantially discounted from 5689
        assert row['minutes'] < 1200
        assert row['unweighted_minutes'] == 5689
        # Per-90 rate remains high-performing and positive
        assert row['expected_goals_90'] > 0.60


class TestZeroMinutesPlayer:
    """A player with 0 minutes across both seasons should not cause
    division-by-zero errors and should report 0.0 for all per-90 rates.

    John Ruddy (code=19236): 0 total minutes in both 2024-25 and 2025-26.
    """

    def test_zero_minutes_rates(self):
        result = compute_player_form(SEASON, MAX_GW, window_gws=None,
                                      data_root=DATA_ROOT)
        ruddy = result[result['code'] == 19236]
        assert len(ruddy) == 1

        row = ruddy.iloc[0]
        assert row['minutes'] == 0
        assert row['expected_goals_90'] == 0.0
        assert row['expected_assists_90'] == 0.0
        assert row['expected_goals_conceded_90'] == 0.0


class TestTeamFormSingleSeason:
    """Verify Liverpool's team-level form for 2025-26 season ONLY
    (using window_gws=38 to keep it to one season).

    Hand-computed (2025-26 only, 38 matches):
        total xG (sum of all player xG): 60.57
        total xGC (max per match, summed): 47.63
        xG per match (xG/90): 1.5939
        xGC per match (xGC/90): 1.2534
    """

    def test_liverpool_single_season(self):
        result = compute_team_form(SEASON, MAX_GW, window_gws=38,
                                    half_life=None,
                                    data_root=DATA_ROOT)
        assert not result.empty
        lvp = result[result['team'] == 'Liverpool']
        assert len(lvp) == 1

        row = lvp.iloc[0]
        assert row['matches'] == 38
        assert abs(row['team_xg'] - 60.57) < 0.1
        assert abs(row['team_xgc'] - 47.63) < 0.1
        assert abs(row['team_xg90'] - 1.5939) < 0.01
        assert abs(row['team_xgc90'] - 1.2534) < 0.01


class TestTeamFormLongForm:
    """Long-form team form spans two seasons — results in more than 20
    teams (promoted/relegated teams add up) and more matches.
    """

    def test_cross_season_has_more_teams(self):
        result = compute_team_form(SEASON, MAX_GW, window_gws=None,
                                    data_root=DATA_ROOT)
        # 23 unique teams across 2024-25 and 2025-26
        assert len(result) == 23


class TestBuildPlayerFormDataset:
    """Integration test for build_player_form_dataset."""

    def test_output_has_player_code(self):
        result = build_player_form_dataset(SEASON, MAX_GW,
                                            data_root=DATA_ROOT)
        assert 'player_code' in result.columns
        # Haaland's code should be present
        assert 223094 in result['player_code'].values

    def test_output_has_long_and_short_form(self):
        result = build_player_form_dataset(SEASON, MAX_GW,
                                            data_root=DATA_ROOT)
        assert 'long_form_minutes' in result.columns
        assert 'short_form_minutes' in result.columns
        assert 'long_form_expected_goals_90' in result.columns
        assert 'short_form_expected_goals_90' in result.columns


class TestBuildTeamFormDataset:
    """Integration test for build_team_form_dataset."""

    def test_output_has_expected_columns(self):
        result = build_team_form_dataset(SEASON, MAX_GW,
                                          data_root=DATA_ROOT)
        assert not result.empty
        assert 'team_long_form_xg90' in result.columns
        assert 'team_short_form_xg90' in result.columns
        # Long-form spans two seasons → 23 teams
        assert len(result) == 23

    def test_single_season_short_form_has_20_teams(self):
        """Short-form (6 GWs) stays within 2025-26 → 20 teams."""
        result = build_team_form_dataset(SEASON, MAX_GW, short_form_window=6,
                                          data_root=DATA_ROOT)
        # Short-form column should have exactly 20 non-null values
        non_null = result['team_short_form_xg90'].dropna()
        assert len(non_null) == 20

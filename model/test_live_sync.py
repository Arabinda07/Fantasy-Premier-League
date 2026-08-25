"""Unit tests for Direct FPL Ingestion & Live Sync Engine (model/live_sync.py)."""
import json
import os
from unittest.mock import patch, MagicMock
import pytest

from model.live_sync import (
    load_element_to_code_map,
    load_code_to_element_map,
    fetch_fpl_entry_summary,
    fetch_fpl_entry_picks,
    fetch_fpl_entry_transfers,
    fetch_fpl_league_standings,
    calculate_available_free_transfers,
    sync_manager_profile,
    LiveSyncProfile,
)
from model.live_manager import manage_gameweek


class TestLiveSyncUnit:
    """Test unit functionality of live FPL API parsers and transformers."""

    def test_element_to_code_mapping(self):
        elem_to_code = load_element_to_code_map(season='2026-27', data_root='data')
        assert isinstance(elem_to_code, dict)
        assert len(elem_to_code) > 0
        # Check that Raya (id=1, code=154561) maps correctly
        assert elem_to_code.get(1) == 154561

        code_to_elem = load_code_to_element_map(season='2026-27', data_root='data')
        assert code_to_elem.get(154561) == 1

    def test_fetch_fpl_entry_summary_mock(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'id': 99999,
            'player_first_name': 'Magnus',
            'player_last_name': 'Carlsen',
            'name': 'Chess Masters FC',
            'summary_overall_rank': 42,
            'summary_overall_points': 1420,
            'last_deadline_bank': 15,  # £1.5M
            'last_deadline_value': 1045,  # £104.5M
            'last_deadline_total_transfers': 8,
            'current_event': 18,
        }

        with patch('requests.get', return_value=mock_resp):
            data = fetch_fpl_entry_summary(entry_id=99999, use_cache=False)
            assert data['id'] == 99999
            assert data['player_first_name'] == 'Magnus'
            assert data['summary_overall_rank'] == 42
            assert data['last_deadline_bank'] == 15

    def test_fetch_fpl_entry_picks_mock(self):
        mock_picks = [
            {'element': 1, 'position': 1, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': False, 'selling_price': 60, 'purchase_price': 55},
            {'element': 4, 'position': 2, 'multiplier': 1, 'is_captain': False, 'is_vice_captain': False, 'selling_price': 80, 'purchase_price': 80},
            {'element': 5, 'position': 11, 'multiplier': 2, 'is_captain': True, 'is_vice_captain': False, 'selling_price': 105, 'purchase_price': 100},
            {'element': 6, 'position': 12, 'multiplier': 0, 'is_captain': False, 'is_vice_captain': False, 'selling_price': 40, 'purchase_price': 40},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'active_chip': '3xc',
            'entry_history': {'event': 1, 'points': 72, 'bank': 15, 'value': 1025},
            'picks': mock_picks,
        }

        with patch('requests.get', return_value=mock_resp):
            data = fetch_fpl_entry_picks(entry_id=99999, gw=1, use_cache=False)
            assert data['active_chip'] == '3xc'
            assert len(data['picks']) == 4
            assert data['picks'][2]['is_captain'] is True

    def test_calculate_available_free_transfers(self):
        # GW1 default
        assert calculate_available_free_transfers({}, [], current_gw=1) == 1

        # No transfers in previous GW -> 2 FTs accumulated
        assert calculate_available_free_transfers({}, [], current_gw=3) == 2

        # 1 transfer made in previous GW
        history = [{'event': 2, 'element_in': 10, 'element_out': 20}]
        assert calculate_available_free_transfers({}, history, current_gw=3) == 1

    def test_fetch_fpl_league_standings_mock(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'league': {'id': 1234, 'name': 'Alpha Mini League'},
            'standings': {
                'results': [
                    {'entry': 101, 'player_name': 'Alice', 'entry_name': 'Wonderland XI', 'rank': 1, 'total': 1500, 'event_total': 65},
                    {'entry': 102, 'player_name': 'Bob', 'entry_name': 'Builder FC', 'rank': 2, 'total': 1485, 'event_total': 58},
                ]
            }
        }
        with patch('requests.get', return_value=mock_resp):
            data = fetch_fpl_league_standings(league_id=1234, use_cache=False)
            assert data['league']['name'] == 'Alpha Mini League'
            assert len(data['standings']['results']) == 2

    def test_sync_manager_profile_end_to_end_mock(self):
        # Mock summary, picks, transfers, standings
        mock_summary = {
            'id': 77777,
            'player_first_name': 'Erling',
            'player_last_name': 'Robot',
            'name': 'Haaland Goal Machine',
            'summary_overall_rank': 120,
            'summary_overall_points': 1520,
            'last_deadline_bank': 20,  # £2.0M
            'last_deadline_value': 1050,  # £105.0M
            'current_event': 2,
        }
        # 15 player picks (elements 1..15)
        mock_picks = [
            {'element': i, 'position': i, 'multiplier': 2 if i == 9 else (0 if i > 11 else 1), 'is_captain': (i == 9), 'is_vice_captain': (i == 10), 'selling_price': 50, 'purchase_price': 50}
            for i in range(1, 16)
        ]
        mock_picks_resp = {
            'active_chip': None,
            'entry_history': {'event': 2, 'bank': 20, 'value': 1050},
            'picks': mock_picks,
        }

        with patch('model.live_sync.fetch_fpl_entry_summary', return_value=mock_summary), \
             patch('model.live_sync.fetch_fpl_entry_picks', return_value=mock_picks_resp), \
             patch('model.live_sync.fetch_fpl_entry_transfers', return_value=[]), \
             patch('model.live_sync.fetch_fpl_league_standings', return_value={'standings': {'results': []}}):

            profile = sync_manager_profile(
                entry_id=77777,
                gw=2,
                league_id=None,
                season='2026-27',
                data_root='data',
                use_cache=False,
            )

            assert isinstance(profile, LiveSyncProfile)
            assert profile.entry_id == 77777
            assert profile.manager_name == 'Erling Robot'
            assert profile.team_name == 'Haaland Goal Machine'
            assert profile.bank == 2.0
            assert profile.team_value == 105.0
            assert len(profile.squad_codes) == 15
            assert len(profile.starter_codes) == 11
            assert len(profile.bench_codes) == 4

    def test_live_manager_integration_with_team_id(self):
        mock_summary = {
            'id': 88888,
            'player_first_name': 'Cole',
            'player_last_name': 'Palmer',
            'name': 'Cold Palmer FC',
            'summary_overall_rank': 500,
            'summary_overall_points': 1400,
            'last_deadline_bank': 10,
            'last_deadline_value': 1030,
            'current_event': 1,
        }
        # 15 valid squad elements (2 GK, 5 DEF, 5 MID, 3 FWD)
        valid_elements = [1, 2, 4, 8, 9, 10, 11, 12, 13, 14, 15, 17, 25, 26, 27]
        mock_picks = [
            {'element': elem, 'position': idx + 1, 'multiplier': 2 if idx == 11 else (0 if idx >= 11 else 1), 'is_captain': (idx == 11), 'is_vice_captain': (idx == 12)}
            for idx, elem in enumerate(valid_elements)
        ]
        mock_picks_resp = {
            'active_chip': None,
            'entry_history': {'event': 1, 'bank': 10, 'value': 1030},
            'picks': mock_picks,
        }

        with patch('model.live_sync.fetch_fpl_entry_summary', return_value=mock_summary), \
             patch('model.live_sync.fetch_fpl_entry_picks', return_value=mock_picks_resp), \
             patch('model.live_sync.fetch_fpl_entry_transfers', return_value=[]):

            res = manage_gameweek(
                season='2026-27',
                gw=1,
                team_id=88888,
                horizon=1,
                data_root='data',
                export_excel=False,
                export_json=False,
            )

            assert 'action_summary' in res
            assert res['live_profile'] is not None
            assert res['live_profile'].entry_id == 88888
            assert res['live_profile'].manager_name == 'Cole Palmer'

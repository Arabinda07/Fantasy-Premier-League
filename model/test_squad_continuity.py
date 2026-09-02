"""Tests for Squad Snapshot Persistence, Deep Historical Fallback, and Guardrails (Fix 1)."""
import json
import os
import shutil
import sys
import tempfile
from typing import Dict, Any, List

import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.live_sync import (
    LiveSyncProfile,
    save_manager_squad_snapshot,
    load_manager_squad_snapshot,
)
from model.live_manager import manage_gameweek
from model.solver import SquadSolution, MultiHorizonSolution, GameweekPlan, PlayerPick


@pytest.fixture
def temp_env():
    """Create a temporary environment with standard directory structure."""
    tmpdir = tempfile.mkdtemp()
    season = '2026-27'
    season_dir = os.path.join(tmpdir, season)
    cache_dir = os.path.join(season_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)

    yield {
        'root': tmpdir,
        'season': season,
        'season_dir': season_dir,
        'cache_dir': cache_dir,
    }
    shutil.rmtree(tmpdir, ignore_errors=True)


def _make_dummy_profile(entry_id: int = 12345) -> LiveSyncProfile:
    """Helper to create a valid 15-player LiveSyncProfile."""
    dummy_codes = list(range(1001, 1016))
    return LiveSyncProfile(
        entry_id=entry_id,
        manager_name="Test Manager",
        team_name="Test FC",
        overall_rank=50000,
        overall_points=120,
        bank=1.0,
        team_value=101.0,
        free_transfers=1,
        active_chip=None,
        squad_codes=dummy_codes,
        starter_codes=dummy_codes[:11],
        bench_codes=dummy_codes[11:],
        captain_code=dummy_codes[0],
        vice_captain_code=dummy_codes[1],
        selling_prices={c: 6.0 for c in dummy_codes},
        purchase_prices={c: 6.0 for c in dummy_codes},
    )


def _make_dummy_solution(codes: List[int]) -> MultiHorizonSolution:
    """Helper to construct a mock MultiHorizonSolution."""
    sample_picks = [
        PlayerPick(
            player_code=c,
            web_name=f"P{c}",
            team="TeamA",
            position="MID",
            cost=6.0,
            expected_points=4.0,
            is_starter=(idx < 11),
            is_captain=(idx == 0),
            is_vice_captain=(idx == 1),
            bench_order=None if idx < 11 else (idx - 10),
        )
        for idx, c in enumerate(codes)
    ]
    sample_sol = SquadSolution(
        squad=sample_picks, starters=sample_picks[:11], bench=sample_picks[11:],
        captain=sample_picks[0], vice_captain=sample_picks[1],
        total_cost=90.0, starting_xp=44.0, captain_xp=4.0, total_xp=48.0,
        formation="3-5-2", status="Optimal",
    )
    plan = GameweekPlan(
        gw=2, transfers_in=[], transfers_out=[], transfers_count=0,
        hits_taken=0, hit_penalty=0.0, free_transfers_available=1, free_transfers_remaining=1,
        bank=1.0, squad_solution=sample_sol, net_xp=48.0,
    )
    return MultiHorizonSolution(
        horizon=1, discount_factor=0.90, total_discounted_xp=48.0,
        total_hits_taken=0, total_hit_penalty=0.0, gw_plans=[plan], status="Optimal",
    )


class TestSquadSnapshotPersistence:
    """Tests for saving and loading manager squad snapshots."""

    def test_save_and_load_roundtrip(self, temp_env):
        """Saving a snapshot should allow loading it back accurately."""
        profile = _make_dummy_profile(entry_id=99999)
        team_path = save_manager_squad_snapshot(profile, season=temp_env['season'], data_root=temp_env['root'])
        assert os.path.exists(team_path)

        current_path = os.path.join(temp_env['season_dir'], 'current_squad.json')
        assert os.path.exists(current_path)

        # Load with entry_id
        loaded = load_manager_squad_snapshot(entry_id=99999, season=temp_env['season'], data_root=temp_env['root'])
        assert loaded is not None
        assert loaded['entry_id'] == 99999
        assert len(loaded['squad_codes']) == 15
        assert loaded['squad_codes'] == profile.squad_codes

        # Load without entry_id (should find current_squad.json)
        loaded_global = load_manager_squad_snapshot(entry_id=None, season=temp_env['season'], data_root=temp_env['root'])
        assert loaded_global is not None
        assert loaded_global['squad_codes'] == profile.squad_codes

    def test_load_ignores_incomplete_squad(self, temp_env):
        """Snapshots with fewer than 15 player codes must be ignored."""
        incomplete_path = os.path.join(temp_env['season_dir'], 'current_squad.json')
        with open(incomplete_path, 'w', encoding='utf-8') as f:
            json.dump({'squad_codes': [101, 102, 103]}, f)

        loaded = load_manager_squad_snapshot(season=temp_env['season'], data_root=temp_env['root'])
        assert loaded is None


class TestLiveManagerContinuityGuardrail:
    """Tests for squad continuity guardrails in manage_gameweek."""

    def test_guardrail_aborts_on_missing_squad_for_gw_gt_1(self, temp_env, monkeypatch):
        """When gw > 1 and no squad exists, manage_gameweek must raise RuntimeError."""
        monkeypatch.setattr(
            'model.live_manager.predict_gameweek_fixtures',
            lambda **kwargs: pd.DataFrame({'player_code': list(range(1001, 1025)), 'expected_points': [4.0]*24})
        )
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_matchup_intelligence', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_set_pieces', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_ownership', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_price_trends', lambda df, **kw: df)

        with pytest.raises(RuntimeError) as excinfo:
            manage_gameweek(
                season=temp_env['season'],
                gw=2,
                team_id=None,
                data_root=temp_env['root'],
                export_excel=False,
                export_json=False,
            )
        assert "Cannot optimize transfers for GW2: No existing 15-man squad could be found" in str(excinfo.value)
        assert "Calling solve_initial_squad after GW1" in str(excinfo.value)

    def test_guardrail_bypassed_with_force_new_squad(self, temp_env, monkeypatch):
        """Passing force_new_squad=True must permit solving an initial squad."""
        dummy_codes = list(range(1001, 1016))
        multi_sol = _make_dummy_solution(dummy_codes)

        monkeypatch.setattr(
            'model.live_manager.predict_gameweek_fixtures',
            lambda **kwargs: pd.DataFrame({'player_code': list(range(1001, 1025)), 'expected_points': [4.0]*24})
        )
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_matchup_intelligence', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_set_pieces', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_ownership', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_price_trends', lambda df, **kw: df)

        monkeypatch.setattr('model.live_manager.solve_initial_squad', lambda **kw: multi_sol.gw_plans[0].squad_solution)
        monkeypatch.setattr('model.live_manager.solve_multi_horizon_transfers', lambda **kw: multi_sol)

        # Should execute without raising RuntimeError
        res = manage_gameweek(
            season=temp_env['season'],
            gw=2,
            data_root=temp_env['root'],
            force_new_squad=True,
            export_excel=False,
            export_json=False,
        )
        assert res is not None
        assert res['squad_solution'] is not None

    def test_guardrail_bypassed_with_wildcard(self, temp_env, monkeypatch):
        """Activating chip='wildcard' must permit solving an initial squad."""
        dummy_codes = list(range(1001, 1016))
        multi_sol = _make_dummy_solution(dummy_codes)

        monkeypatch.setattr(
            'model.live_manager.predict_gameweek_fixtures',
            lambda **kwargs: pd.DataFrame({'player_code': list(range(1001, 1025)), 'expected_points': [4.0]*24})
        )
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_matchup_intelligence', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_set_pieces', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_ownership', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_price_trends', lambda df, **kw: df)

        monkeypatch.setattr('model.live_manager.solve_initial_squad', lambda **kw: multi_sol.gw_plans[0].squad_solution)
        monkeypatch.setattr('model.live_manager.solve_multi_horizon_transfers', lambda **kw: multi_sol)

        res = manage_gameweek(
            season=temp_env['season'],
            gw=2,
            chip='wildcard',
            data_root=temp_env['root'],
            export_excel=False,
            export_json=False,
        )
        assert res is not None
        assert res['squad_solution'] is not None

    def test_deep_backward_search_finds_gw1_when_gw2_missing(self, temp_env, monkeypatch):
        """When running GW3 and GW2 file is absent, GW1 file squad should be discovered."""
        gw1_file = os.path.join(temp_env['season_dir'], 'fpl_matchday_live_gw1.json')
        dummy_codes = list(range(1001, 1016))
        gw1_data = {
            'starters': [{'player_code': c, 'web_name': f"P{c}"} for c in dummy_codes[:11]],
            'bench': [{'player_code': c, 'web_name': f"P{c}"} for c in dummy_codes[11:]],
        }
        with open(gw1_file, 'w', encoding='utf-8') as f:
            json.dump(gw1_data, f)

        monkeypatch.setattr(
            'model.live_manager.predict_gameweek_fixtures',
            lambda **kwargs: pd.DataFrame({'player_code': list(range(1001, 1025)), 'expected_points': [4.0]*24})
        )
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_matchup_intelligence', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_set_pieces', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_ownership', lambda df, **kw: df)
        monkeypatch.setattr('model.live_manager.enrich_predictions_with_price_trends', lambda df, **kw: df)

        multi_sol = _make_dummy_solution(dummy_codes)
        captured_codes = []
        def mock_multi_solver(*args, **kwargs):
            captured_codes.extend(kwargs.get('current_squad_codes', []))
            return multi_sol

        monkeypatch.setattr('model.live_manager.solve_multi_horizon_transfers', mock_multi_solver)

        # Run GW3 with no GW2 file present
        res = manage_gameweek(
            season=temp_env['season'],
            gw=3,
            data_root=temp_env['root'],
            export_excel=False,
            export_json=False,
        )
        # Should have found the GW1 squad through backward traversal
        assert captured_codes == dummy_codes

"""Unit tests for Live Gameweek Matchday Manager."""
import os
import sys
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.live_manager import (
    manage_gameweek,
    apply_live_injury_dampening,
)


class TestLiveManager:
    """Verify live injury dampening and live matchday management."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        squad_path = os.path.join('data', '2026-27', 'current_squad.json')
        orig_content = None
        if os.path.exists(squad_path):
            with open(squad_path, 'r', encoding='utf-8', newline='') as f:
                orig_content = f.read()
        try:
            yield
        finally:
            if orig_content is not None:
                with open(squad_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(orig_content)

    def test_injury_dampening(self):
        sample_df = pd.DataFrame([
            {'player_code': 100, 'web_name': 'FitPlayer', 'expected_points': 6.0, 'p_start': 0.9, 'p_app': 0.95},
        ])
        res_df = apply_live_injury_dampening(sample_df, season='2026-27')
        assert len(res_df) == 1
        assert res_df.loc[0, 'expected_points'] == 6.0

    def test_live_manager_execution(self):
        res = manage_gameweek(
            season='2026-27',
            gw=1,
            bank=0.0,
            free_transfers=1,
            horizon=2,
            export_excel=False,
            export_json=False,
        )
        assert 'action_summary' in res
        assert 'squad_solution' in res
        assert 'multi_horizon_solution' in res
        assert 'chip_plan' in res
        assert res['squad_solution'].status == "Optimal"
        assert res['multi_horizon_solution'].status == "Optimal"

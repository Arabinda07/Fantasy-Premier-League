"""Unit Tests for Press Conference Intelligence & Jev System One Integration."""
import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from model.press_conference_intelligence import (
    INJURY_SEVERITY_OPTIONS,
    MANAGER_CANDOR_LEGEND,
    PREMIER_LEAGUE_MANAGERS,
    PressConferenceEvaluation,
    PressConferenceIntelligence,
    get_press_evaluations_path,
    load_press_evaluations,
    save_press_evaluations,
)
from model.rotation_intelligence import (
    apply_rotation_dampening,
    compute_rotation_hazard,
)
from model.typesafe_bridge import TypeSafeBridge, TypeSafeResponse


@pytest.fixture
def temp_data_root():
    """Create a temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestPressConferenceIntelligence:
    """Test suite for Jev press conference evaluation engine."""

    def test_evaluate_uninjured_player_offline(self):
        """Test default offline evaluation for an unflagged player."""
        pci = PressConferenceIntelligence()
        res = pci.evaluate_player_news(
            player_code=1001,
            player_name="Bukayo Saka",
            team_name="Arsenal",
            status="a",
            chance_of_playing=100.0,
            news_text="",
        )
        assert isinstance(res, PressConferenceEvaluation)
        assert res.player_code == 1001
        assert res.team == "Arsenal"
        assert res.manager == "Mikel Arteta"
        assert res.p_start >= 0.85
        assert res.calibrated_p_start_mult >= 0.85
        assert res.calibrated_p_app_mult >= 0.85
        assert res.injury_severity in INJURY_SEVERITY_OPTIONS

    def test_evaluate_doubtful_player_with_quote(self):
        """Test evaluation of doubtful player with manager quotes."""
        pci = PressConferenceIntelligence()
        res = pci.evaluate_player_news(
            player_code=1002,
            player_name="Erling Haaland",
            team_name="Man City",
            status="d",
            chance_of_playing=75.0,
            news_text="Manager quotes: 'Felt something in his groin, we will assess tomorrow morning' - 75% chance",
            days_rest=3,
        )
        assert res.player_name == "Erling Haaland"
        assert res.manager == "Pep Guardiola"
        assert 0.0 < res.p_start <= 1.0
        assert res.sub_60_hook_risk >= 0.0
        assert res.cameo_risk >= 0.0
        assert res.manager_candor_score >= 1.0

    def test_evaluate_permanently_ruled_out_player(self):
        """Test that ruled out player (status 'i' and chance 0) immediately returns zero."""
        pci = PressConferenceIntelligence()
        res = pci.evaluate_player_news(
            player_code=1003,
            player_name="Rodri",
            team_name="Man City",
            status="i",
            chance_of_playing=0.0,
            news_text="ACL surgery - Expected back next season",
        )
        assert res.p_start == 0.0
        assert res.sub_60_hook_risk == 0.0
        assert res.calibrated_p_start_mult == 0.0
        assert res.calibrated_p_app_mult == 0.0
        assert res.injury_severity == "unfit_ruled_out"

    def test_live_bridge_mock_response(self):
        """Test custom calibrated Jev response via mock bridge."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "p_start": {"type": "noul", "noul": 0.62},
                "sub_60_hook_risk": {"type": "noul", "noul": 0.45},
                "cameo_risk": {"type": "noul", "noul": 0.25},
                "injury_severity": {"type": "choice", "choice": "managed_minutes_risk", "confidence": 0.88},
                "manager_candor": {"type": "score", "score": 2.8, "confidence": 0.90},
            },
            usage={"input_tokens": 120, "output_tokens": 15},
            cached=False,
        )

        pci = PressConferenceIntelligence(bridge=mock_bridge)
        res = pci.evaluate_player_news(
            player_code=1004,
            player_name="Cole Palmer",
            team_name="Chelsea",
            status="d",
            chance_of_playing=50.0,
            news_text="Knee swelling, did not train Thursday.",
        )

        assert res.p_start == 0.62
        assert res.sub_60_hook_risk == 0.45
        assert res.cameo_risk == 0.25
        assert res.injury_severity == "managed_minutes_risk"
        assert res.manager_candor_score == 2.8
        assert res.calibrated_p_start_mult == 0.62
        # P(App) = 0.62 + (1 - 0.62) * 0.25 = 0.62 + 0.095 = 0.715
        assert res.calibrated_p_app_mult == 0.715

    def test_evaluate_flagged_players_batch(self, temp_data_root):
        """Test batch evaluation over a realistic players_raw DataFrame."""
        pci = PressConferenceIntelligence()

        df = pd.DataFrame([
            {"code": 101, "web_name": "Saka", "team": "Arsenal", "status": "d", "chance_of_playing_this_round": 75.0, "news": "Knock in training"},
            {"code": 102, "web_name": "Saliba", "team": "Arsenal", "status": "a", "chance_of_playing_this_round": 100.0, "news": ""},
            {"code": 103, "web_name": "De Bruyne", "team": "Man City", "status": "d", "chance_of_playing_this_round": 50.0, "news": "Hamstring tightness"},
            {"code": 104, "web_name": "Cash", "team": "Aston Villa", "status": "i", "chance_of_playing_this_round": 0.0, "news": "Calf strain"},
        ])

        evals = pci.evaluate_flagged_players(
            players_df=df,
            season="2026-27",
            data_root=temp_data_root,
            persist=True,
        )

        # Only 101, 103, 104 should be evaluated (Saliba is unflagged)
        assert len(evals) == 3
        assert 101 in evals
        assert 103 in evals
        assert 104 in evals
        assert 102 not in evals

        # Verify disk persistence
        loaded = load_press_evaluations(season="2026-27", data_root=temp_data_root)
        assert len(loaded) == 3
        assert loaded[101]["player_name"] == "Saka"


class TestRotationIntelligenceIntegration:
    """Test suite verifying integration of Jev press intel into rotation_intelligence.py."""

    def test_compute_rotation_hazard_without_press_intel_backward_compatibility(self):
        """Verify baseline behavior is completely unchanged when press_intel is omitted."""
        hazard = compute_rotation_hazard(
            team_name="Man City",
            status="d",
            chance_of_playing=75.0,
            days_rest=7,
        )
        assert hazard["midweek_hazard"] == 1.00
        assert hazard["news_p_start_mult"] == 0.75
        assert hazard["news_p_app_mult"] == 0.85
        assert hazard["combined_p_start_mult"] == 0.75
        assert hazard["press_intel_applied"] is False

    def test_compute_rotation_hazard_with_press_intel(self):
        """Verify Jev press intel overrides discrete tiers and adjusts sub60 hook hazard."""
        press_intel = {
            "calibrated_p_start_mult": 0.64,
            "calibrated_p_app_mult": 0.78,
            "sub_60_hook_risk": 0.40,
        }

        hazard = compute_rotation_hazard(
            team_name="Man City",
            status="d",
            chance_of_playing=75.0,
            days_rest=7,
            total_starts=10.0,
            starts_60_plus=9.0,  # Base sub60_prob = 0.90
            press_intel=press_intel,
        )

        assert hazard["news_p_start_mult"] == 0.64
        assert hazard["news_p_app_mult"] == 0.78
        assert hazard["combined_p_start_mult"] == 0.64
        assert hazard["combined_p_app_mult"] == 0.78
        # sub60 adjusted: 0.90 * (1 - 0.40) = 0.54
        assert hazard["sub60_prob"] == 0.54
        assert hazard["press_intel_applied"] is True

    def test_apply_rotation_dampening_with_press_evaluations(self, temp_data_root):
        """Test apply_rotation_dampening applying loaded press evaluations."""
        # Create mock predictions
        pred_df = pd.DataFrame([
            {"player_code": 201, "team": "Arsenal", "p_start": 0.90, "p_app": 0.95, "expected_points": 7.5},
            {"player_code": 202, "team": "Arsenal", "p_start": 0.85, "p_app": 0.90, "expected_points": 6.0},
        ])

        # Create press evaluation for player 201
        press_evals = {
            201: {
                "calibrated_p_start_mult": 0.50,
                "calibrated_p_app_mult": 0.65,
                "sub_60_hook_risk": 0.30,
            }
        }

        damped_df = apply_rotation_dampening(
            pred_df=pred_df,
            season="2026-27",
            data_root=temp_data_root,
            press_evaluations=press_evals,
        )

        assert "press_intel_applied" in damped_df.columns
        assert bool(damped_df.loc[0, "press_intel_applied"]) is True
        assert bool(damped_df.loc[1, "press_intel_applied"]) is False

        # Player 201 should be damped
        assert damped_df.loc[0, "p_start"] == round(0.90 * 0.50, 4)
        assert damped_df.loc[0, "p_app"] == round(0.95 * 0.65, 4)
        assert damped_df.loc[0, "expected_points"] < 7.5

        # Player 202 should remain unimpacted by press intel
        assert damped_df.loc[1, "p_start"] == 0.85
        assert damped_df.loc[1, "expected_points"] == 6.0

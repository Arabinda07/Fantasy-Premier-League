"""Unit Tests for Pipeline Automated Sanity Guardrail Engine."""
import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock

import pytest

from model.pipeline_automation import run_pipeline_guardrail_stage
from model.pipeline_guardrail import (
    ANOMALY_TYPE_OPTIONS,
    GUARDRAIL_SEVERITY_LEGEND,
    RECOMMENDATION_OPTIONS,
    GuardrailVerdict,
    PipelineGuardrail,
    get_guardrail_log_path,
    record_guardrail_verdict,
)
from model.typesafe_bridge import TypeSafeBridge, TypeSafeResponse


@pytest.fixture
def temp_data_root():
    """Create a temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def create_sample_matchday_payload(corrupt: bool = False, extreme_xp: bool = False) -> dict:
    """Helper to generate a realistic matchday solver output payload."""
    starters = [
        {"player_code": 101, "web_name": "Raya", "position": "GK", "expected_points": 4.5},
        {"player_code": 102, "web_name": "Gabriel", "position": "DEF", "expected_points": 5.2},
        {"player_code": 103, "web_name": "Alexander-Arnold", "position": "DEF", "expected_points": 6.1},
        {"player_code": 104, "web_name": "Gvardiol", "position": "DEF", "expected_points": 4.8},
        {"player_code": 105, "web_name": "Saka", "position": "MID", "expected_points": 7.5},
        {"player_code": 106, "web_name": "Palmer", "position": "MID", "expected_points": 8.0},
        {"player_code": 107, "web_name": "Mbeumo", "position": "MID", "expected_points": 6.2},
        {"player_code": 108, "web_name": "Rogers", "position": "MID", "expected_points": 4.5},
        {"player_code": 109, "web_name": "B.Fernandes", "position": "MID", "expected_points": 5.8},
        {"player_code": 110, "web_name": "Haaland", "position": "FWD", "expected_points": 35.0 if extreme_xp else 9.5},
        {"player_code": 111, "web_name": "Wood", "position": "FWD", "expected_points": 5.0},
    ]
    bench = [
        {"player_code": 112, "web_name": "Fabianski", "position": "GK", "expected_points": 0.5},
        {"player_code": 113, "web_name": "Harwood-Bellis", "position": "DEF", "expected_points": 1.5},
        {"player_code": 114, "web_name": "Greaves", "position": "DEF", "expected_points": 1.2},
        {"player_code": 115, "web_name": "Stewart", "position": "FWD", "expected_points": 1.0},
    ]

    if corrupt:
        # Corrupt squad by removing 4 starters
        starters = starters[:7]

    return {
        "season": "2026-27",
        "gameweek": 27,
        "action_summary": "EXECUTE TRANSFERS (-4 pts): [IN] Palmer | [OUT] Foden",
        "captain": "Haaland",
        "vice_captain": "Palmer",
        "recommended_starters": starters,
        "recommended_bench": bench,
        "recommended_starting_xp": sum(p["expected_points"] for p in starters),
        "recommended_total_xp": sum(p["expected_points"] for p in starters) + sum(p["expected_points"] for p in bench),
    }


class TestPipelineGuardrail:
    """Test suite for Jev automated pipeline guardrail."""

    def test_audit_healthy_payload_offline(self, temp_data_root):
        """Test that a healthy, rational squad passes guardrail audit offline."""
        guardrail = PipelineGuardrail()
        payload = create_sample_matchday_payload(corrupt=False)

        verdict = guardrail.audit_matchday_output(
            season="2026-27",
            gw=27,
            matchday_payload=payload,
            data_root=temp_data_root,
        )

        assert isinstance(verdict, GuardrailVerdict)
        assert verdict.passed is True
        assert verdict.severity_score <= 1.5
        assert verdict.abort_probability < 0.50
        assert verdict.anomaly_type == "clean"
        assert verdict.recommendation == "proceed"
        assert "Verified healthy" in verdict.message or "Passed" in verdict.message

    def test_audit_corrupt_squad_fails_deterministic_gate(self, temp_data_root):
        """Test that missing squad members trigger immediate deterministic halt."""
        guardrail = PipelineGuardrail()
        payload = create_sample_matchday_payload(corrupt=True)

        verdict = guardrail.audit_matchday_output(
            season="2026-27",
            gw=27,
            matchday_payload=payload,
            data_root=temp_data_root,
        )

        assert verdict.passed is False
        assert verdict.severity_score == 3.0
        assert verdict.abort_probability == 1.0
        assert verdict.anomaly_type == "formation_invalid"
        assert verdict.recommendation == "emergency_halt"
        assert "Invalid starting XI count" in verdict.message

    def test_audit_extreme_xp_anomaly(self, temp_data_root):
        """Test detection of extreme mathematical projection outlier."""
        guardrail = PipelineGuardrail()
        payload = create_sample_matchday_payload(extreme_xp=True)

        verdict = guardrail.audit_matchday_output(
            season="2026-27",
            gw=27,
            matchday_payload=payload,
            data_root=temp_data_root,
        )

        assert verdict.passed is False
        assert verdict.abort_probability >= 0.70
        assert verdict.anomaly_type == "extreme_xp_outlier"
        assert "Extreme single player projection" in verdict.message

    def test_audit_missing_payload_on_disk(self, temp_data_root):
        """Test that complete absence of matchday files triggers emergency halt."""
        guardrail = PipelineGuardrail()

        verdict = guardrail.audit_matchday_output(
            season="2026-27",
            gw=27,
            matchday_payload=None,
            data_root=temp_data_root,
        )

        assert verdict.passed is False
        assert verdict.severity_score == 3.0
        assert verdict.anomaly_type == "data_corruption"
        assert verdict.recommendation == "emergency_halt"

    def test_live_bridge_mock_evaluation(self, temp_data_root):
        """Test custom calibrated Jev evaluation via mock bridge."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "pipeline_severity_score": {"type": "score", "score": 2.7, "confidence": 0.95},
                "abort_execution": {"type": "noul", "noul": 0.88},
                "anomaly_type": {"type": "choice", "choice": "talisman_dump", "confidence": 0.92},
                "recommendation": {"type": "choice", "choice": "emergency_halt", "confidence": 0.95},
            },
            usage={"input_tokens": 150, "output_tokens": 18},
            cached=False,
        )

        guardrail = PipelineGuardrail(bridge=mock_bridge)
        payload = create_sample_matchday_payload(corrupt=False)

        verdict = guardrail.audit_matchday_output(
            season="2026-27",
            gw=27,
            matchday_payload=payload,
            data_root=temp_data_root,
        )

        assert verdict.passed is False
        assert verdict.severity_score == 2.7
        assert verdict.abort_probability == 0.88
        assert verdict.anomaly_type == "talisman_dump"
        assert verdict.recommendation == "emergency_halt"

    def test_audit_log_persistence(self, temp_data_root):
        """Test that audit verdicts are correctly appended to guardrail_audit_log.json."""
        verdict = GuardrailVerdict(
            passed=True,
            severity_score=0.1,
            abort_probability=0.02,
            anomaly_type="clean",
            recommendation="proceed",
            message="Clean execution",
            timestamp="2026-09-19T00:00:00Z",
            details={},
        )

        log_path = record_guardrail_verdict(verdict, season="2026-27", gw=27, data_root=temp_data_root)
        assert os.path.exists(log_path)

        with open(log_path, "r", encoding="utf-8") as f:
            history = json.load(f)

        assert len(history) == 1
        assert history[0]["gameweek"] == 27
        assert history[0]["passed"] is True


class TestPipelineAutomationStageIntegration:
    """Test suite verifying run_pipeline_guardrail_stage within pipeline_automation.py."""

    def test_run_pipeline_guardrail_stage_success(self, temp_data_root):
        """Test successful execution of Stage 5b guardrail."""
        payload = create_sample_matchday_payload(corrupt=False)
        stage_res = run_pipeline_guardrail_stage(
            season="2026-27",
            gw=27,
            matchday_payload=payload,
            data_root=temp_data_root,
        )

        assert stage_res.stage == "pipeline_guardrail"
        assert stage_res.success is True
        assert stage_res.error is None
        assert "Passed" in stage_res.message or "verified healthy" in stage_res.message
        assert stage_res.data is not None
        assert stage_res.data["severity_score"] <= 1.5

    def test_run_pipeline_guardrail_stage_aborted(self, temp_data_root):
        """Test stage failure and abort message when payload is corrupt."""
        payload = create_sample_matchday_payload(corrupt=True)
        stage_res = run_pipeline_guardrail_stage(
            season="2026-27",
            gw=27,
            matchday_payload=payload,
            data_root=temp_data_root,
        )

        assert stage_res.stage == "pipeline_guardrail"
        assert stage_res.success is False
        assert stage_res.error == "formation_invalid"
        assert "Invalid starting XI count" in stage_res.message

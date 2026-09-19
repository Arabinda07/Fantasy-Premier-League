"""Pipeline Automated Sanity Guardrail Engine for Fantasy Premier League.

Utilizes TypeSafe AI System One (Jev) to audit automated matchday pipeline outputs,
squad recommendations, and transfer plans against data corruption and solver anomalies.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.typesafe_bridge import TypeSafeBridge

# Severity Rubric (Score 0-3)
GUARDRAIL_SEVERITY_LEGEND: Dict[str, str] = {
    "0": "Routine & Healthy: Standard rational FPL squad meeting all mathematical, tactical, and game constraints.",
    "1": "Minor Caution: Mild deviation (e.g. captain carrying minor knock flag, low remaining bank, unusual bench order).",
    "2": "Suspicious Anomaly: Questionable transfer structure (e.g. selling healthy top-scoring talisman for an inactive sub, massive negative budget).",
    "3": "Fatal Corruption / Emergency Abort: Critical solver or data failure (e.g. empty squad, impossible formations, corrupted zero-minute players, invalid player codes)."
}

# Anomaly Types (Choice)
ANOMALY_TYPE_OPTIONS: Dict[str, str] = {
    "clean": "Clean: No anomalies detected; squad and transfers are completely sane.",
    "data_corruption": "Data Corruption: Corrupted player IDs, null values, or missing squad members.",
    "formation_invalid": "Formation Invalid: Illegal formation or invalid position counts.",
    "talisman_dump": "Talisman Dump: Bizarre transfer dumping an elite talisman for an inactive bench player without injury rationale.",
    "extreme_xp_outlier": "Extreme Outlier: Unrealistic projected point values indicative of projection model malfunction.",
    "negative_budget": "Negative Budget: Squad cost exceeds available budget without viable hit math."
}

# Recommendation Summary (Choice)
RECOMMENDATION_OPTIONS: Dict[str, str] = {
    "proceed": "Proceed: Approved for automated deployment and matchday publishing.",
    "flag_for_review": "Flag for Review: Non-fatal warnings present; flag in dugout cockpit for manager inspection.",
    "emergency_halt": "Emergency Halt: Critical error detected; halt automated deployment immediately."
}


@dataclass
class GuardrailVerdict:
    passed: bool
    severity_score: float
    abort_probability: float
    anomaly_type: str
    recommendation: str
    message: str
    timestamp: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_guardrail_log_path(season: str = '2026-27', data_root: str = 'data') -> str:
    """Return path to season guardrail_audit_log.json."""
    if os.path.isabs(data_root):
        season_dir = os.path.join(data_root, season)
    else:
        season_dir = os.path.join(REPO_ROOT, data_root, season)
    return os.path.join(season_dir, 'guardrail_audit_log.json')


def record_guardrail_verdict(
    verdict: GuardrailVerdict,
    season: str = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
) -> str:
    """Append guardrail verdict to disk audit log."""
    fpath = get_guardrail_log_path(season, data_root)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    history = []
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            history = []

    payload = verdict.to_dict()
    payload['gameweek'] = gw
    history.append(payload)

    # Keep latest 50 entries
    if len(history) > 50:
        history = history[-50:]

    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    return fpath


class PipelineGuardrail:
    """Automated sanity and integrity guardian powered by Jev System One."""

    def __init__(self, bridge: Optional[TypeSafeBridge] = None):
        self.bridge = bridge or TypeSafeBridge()

    def audit_matchday_output(
        self,
        season: str = '2026-27',
        gw: int = 1,
        matchday_payload: Optional[Dict[str, Any]] = None,
        data_root: str = 'data',
    ) -> GuardrailVerdict:
        """Audit the matchday manager output and transfer plan.

        Args:
            season: season string.
            gw: target gameweek number.
            matchday_payload: dictionary returned by manage_gameweek or loaded from disk.
            data_root: root data directory.

        Returns:
            GuardrailVerdict indicating whether the pipeline should proceed or abort.
        """
        now_ts = datetime.now(timezone.utc).isoformat()

        # If payload not passed, attempt to load from current_squad.json or gw{gw}_matchday.json
        if not matchday_payload:
            matchday_path = os.path.join(data_root, season, f'gw{gw}_matchday.json')
            squad_path = os.path.join(data_root, season, 'current_squad.json')
            if os.path.exists(matchday_path):
                try:
                    with open(matchday_path, 'r', encoding='utf-8') as f:
                        matchday_payload = json.load(f)
                except Exception:
                    pass
            elif os.path.exists(squad_path):
                try:
                    with open(squad_path, 'r', encoding='utf-8') as f:
                        matchday_payload = json.load(f)
                except Exception:
                    pass

        if not matchday_payload:
            verdict = GuardrailVerdict(
                passed=False,
                severity_score=3.0,
                abort_probability=1.0,
                anomaly_type="data_corruption",
                recommendation="emergency_halt",
                message="No matchday payload or squad snapshot found on disk to audit.",
                timestamp=now_ts,
                details={"error": "missing_payload"},
            )
            record_guardrail_verdict(verdict, season=season, gw=gw, data_root=data_root)
            return verdict

        # -------------------------------------------------------------------
        # 1. Deterministic Structural Invariant Checks
        # -------------------------------------------------------------------
        starters = matchday_payload.get('recommended_starters') or matchday_payload.get('starters') or []
        bench = matchday_payload.get('recommended_bench') or matchday_payload.get('bench') or []
        captain = matchday_payload.get('captain')
        starting_xp = float(matchday_payload.get('recommended_starting_xp', matchday_payload.get('starting_xp', 0.0)))
        total_xp = float(matchday_payload.get('recommended_total_xp', matchday_payload.get('total_xp', 0.0)))
        action_summary = str(matchday_payload.get('action_summary', ''))

        total_players = len(starters) + len(bench)
        outlier_flags: List[str] = []

        # Squad size check
        if total_players != 15 and total_players != 0:
            outlier_flags.append(f"Invalid squad size: {total_players} players (expected 15)")

        # Starting XI count check
        if len(starters) != 11 and len(starters) != 0:
            outlier_flags.append(f"Invalid starting XI count: {len(starters)} players (expected 11)")

        # Captain validity
        if not captain and len(starters) > 0:
            outlier_flags.append("No captain designated for starting XI")

        # Project xP range check
        if starting_xp <= 0.0 and len(starters) > 0:
            outlier_flags.append("Starting XI projected xP is 0.0 or negative")
        elif starting_xp > 150.0:
            outlier_flags.append(f"Unrealistically extreme starting XI xP: {starting_xp:.1f}")

        # Individual player extreme xP
        for p in starters:
            pxp = float(p.get('expected_points', 0.0))
            pname = str(p.get('web_name', 'Unknown'))
            if pxp > 28.0:
                outlier_flags.append(f"Extreme single player projection: {pname} projected for {pxp:.1f} xP")

        # Immediate deterministic abort if critical structure is broken
        if any("Invalid squad size" in f or "Invalid starting XI" in f for f in outlier_flags):
            verdict = GuardrailVerdict(
                passed=False,
                severity_score=3.0,
                abort_probability=1.0,
                anomaly_type="formation_invalid",
                recommendation="emergency_halt",
                message="; ".join(outlier_flags),
                timestamp=now_ts,
                details={"outlier_flags": outlier_flags},
            )
            record_guardrail_verdict(verdict, season=season, gw=gw, data_root=data_root)
            return verdict

        # -------------------------------------------------------------------
        # 2. TypeSafe Jev System One Sanity Evaluation
        # -------------------------------------------------------------------
        starters_summary = [f"{p.get('web_name', '?')} ({p.get('position', '?')}, {p.get('expected_points', 0)} xP)" for p in starters]
        bench_summary = [f"{p.get('web_name', '?')} ({p.get('position', '?')}, {p.get('expected_points', 0)} xP)" for p in bench]

        state = {
            "season": season,
            "gameweek": gw,
            "action_summary": action_summary,
            "starting_xp": starting_xp,
            "total_xp": total_xp,
            "captain": captain,
            "starters": starters_summary[:11],
            "bench": bench_summary[:4],
            "deterministic_flags": outlier_flags,
        }

        questions = {
            "pipeline_severity_score": {
                "type": "score",
                "instructions": "Grade the integrity and sanity of this automated FPL matchday output and proposed transfers.",
                "legend": GUARDRAIL_SEVERITY_LEGEND,
            },
            "abort_execution": {
                "type": "noul",
                "instructions": "Calibrated probability that this automated pipeline result contains corrupted data or solver anomalies and must be aborted."
            },
            "anomaly_type": {
                "type": "choice",
                "instructions": "Categorize any anomaly detected in the matchday payload.",
                "options": ANOMALY_TYPE_OPTIONS,
            },
            "recommendation": {
                "type": "choice",
                "instructions": "Final deployment recommendation for the automated pipeline.",
                "options": RECOMMENDATION_OPTIONS,
            }
        }

        # Safe offline mock fallback
        has_flags = len(outlier_flags) > 0
        mock_fallback = {
            "pipeline_severity_score": {"type": "score", "score": 2.5 if has_flags else 0.1, "confidence": 0.85},
            "abort_execution": {"type": "noul", "noul": 0.95 if has_flags else 0.02},
            "anomaly_type": {"type": "choice", "choice": "extreme_xp_outlier" if has_flags else "clean", "confidence": 0.90},
            "recommendation": {"type": "choice", "choice": "emergency_halt" if has_flags else "proceed", "confidence": 0.90},
        }

        resp = self.bridge.ask(state, questions, mock_fallback=mock_fallback)
        ans = resp.answers or {}

        severity = float((ans.get("pipeline_severity_score") or {}).get("score", 0.0))
        abort_prob = float((ans.get("abort_execution") or {}).get("noul", 0.0))
        anomaly = str((ans.get("anomaly_type") or {}).get("choice", "clean"))
        rec = str((ans.get("recommendation") or {}).get("choice", "proceed"))

        # Calibrated Hysteresis Decision Logic:
        # Severity >= 2.0 indicates suspicious anomaly; abort_prob >= 0.60 indicates significant doubt.
        should_abort = (abort_prob >= 0.60) or (severity >= 2.0) or (rec == "emergency_halt")
        passed = not should_abort

        if not passed:
            msg = f"Guardrail Halt: {anomaly} (Severity: {severity:.2f}, Abort Prob: {abort_prob:.0%})"
            if outlier_flags:
                msg += f" — {'; '.join(outlier_flags)}"
        elif severity >= 1.5 or rec == "flag_for_review":
            msg = f"Guardrail Warning: {anomaly} (Severity: {severity:.2f}, Abort Prob: {abort_prob:.0%})"
        else:
            msg = f"Guardrail Passed: Squad verified healthy (Severity: {severity:.2f}, Abort Prob: {abort_prob:.0%})"

        verdict = GuardrailVerdict(
            passed=passed,
            severity_score=round(severity, 2),
            abort_probability=round(abort_prob, 4),
            anomaly_type=anomaly,
            recommendation=rec,
            message=msg,
            timestamp=now_ts,
            details={
                "starting_xp": starting_xp,
                "captain": captain,
                "action_summary": action_summary,
                "outlier_flags": outlier_flags,
            },
        )

        record_guardrail_verdict(verdict, season=season, gw=gw, data_root=data_root)
        return verdict

"""Unit Tests for Qualitative Constitution & DESIGN.md Linter."""
import json
import os
from unittest.mock import MagicMock

import pytest

from model.typesafe_bridge import TypeSafeBridge, TypeSafeResponse
from scripts.jev_constitution_linter import (
    ConstitutionLinter,
    ConstitutionLintReport,
    LintViolation,
    parse_unified_diff,
)


class TestConstitutionLinterDeterministicRules:
    """Test suite for fast deterministic invariant checks."""

    def test_detect_hardcoded_hex_colors_in_frontend_jsx(self):
        """Verify hardcoded hex colors in JSX are caught as blockers."""
        linter = ConstitutionLinter()
        diff_lines = [
            (10, '  return <div style={{ backgroundColor: "#3b82f6", color: "#fff" }}>Alert</div>;'),
            (11, '  const padding = "16px";'),
        ]

        violations = linter.check_deterministic_invariants(
            file_path="frontend/src/components/MyCard.jsx",
            diff_lines=diff_lines,
        )

        assert len(violations) == 2
        assert violations[0].rule == "DESIGN_ZERO_HEX_COLORS"
        assert violations[0].severity == "BLOCKER"
        assert "#3b82f6" in violations[0].message
        assert "#fff" in violations[1].message

    def test_allow_tokenized_css_variables_in_frontend(self):
        """Verify tokenized CSS variables produce no hex violations."""
        linter = ConstitutionLinter()
        diff_lines = [
            (10, '  return <div className="surface-scope-1" style={{ color: "var(--primary-emerald)" }}>Alert</div>;'),
        ]

        violations = linter.check_deterministic_invariants(
            file_path="frontend/src/components/MyCard.jsx",
            diff_lines=diff_lines,
        )

        assert len(violations) == 0

    def test_detect_quarantined_scraper_modification(self):
        """Verify modifications to quarantined legacy scrapers trigger blocker."""
        linter = ConstitutionLinter()
        diff_lines = [
            (5, 'def scrape_historical_data():'),
            (6, '    pass'),
        ]

        violations = linter.check_deterministic_invariants(
            file_path="collector.py",
            diff_lines=diff_lines,
        )

        assert len(violations) >= 1
        assert violations[0].rule == "CONSTITUTION_TIER_QUARANTINE"
        assert violations[0].severity == "BLOCKER"
        assert "collector.py" in violations[0].message

    def test_detect_position_mapping_redeclaration(self):
        """Verify redeclaring element_type mapping outside positions.py is blocked."""
        linter = ConstitutionLinter()
        diff_lines = [
            (22, "element_type = {'1': 'GK', '2': 'DEF', '3': 'MID', '4': 'FWD'}"),
        ]

        violations = linter.check_deterministic_invariants(
            file_path="model/my_custom_script.py",
            diff_lines=diff_lines,
        )

        assert len(violations) >= 1
        assert violations[0].rule == "POSITIONS_SINGLE_SOURCE_OF_TRUTH"
        assert violations[0].severity == "BLOCKER"


class TestConstitutionLinterJevQualitativeAudit:
    """Test suite for Jev System One qualitative evaluation and agent feedback."""

    def test_lint_diff_with_clean_code(self):
        """Verify clean diff passes with high tone score and proceed status."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "voice_and_tone_grade": {"type": "score", "score": 2.9, "confidence": 0.95},
                "has_untokenized_design_elements": {"type": "noul", "noul": 0.02},
                "constitution_verdict": {"type": "choice", "choice": "clean", "confidence": 0.98},
            },
            usage={"input_tokens": 100, "output_tokens": 12},
            cached=False,
        )

        linter = ConstitutionLinter(bridge=mock_bridge)
        clean_diff = """diff --git a/frontend/src/components/PitchSquad.jsx b/frontend/src/components/PitchSquad.jsx
--- a/frontend/src/components/PitchSquad.jsx
+++ b/frontend/src/components/PitchSquad.jsx
@@ -10,3 +10,4 @@
+  return <div className="surface-scope-2 font-mono text-sm">Squad Lineup</div>;
"""
        report = linter.lint_diff_string(clean_diff)

        assert isinstance(report, ConstitutionLintReport)
        assert report.passed is True
        assert report.verdict == "clean"
        assert report.tone_score == 2.9
        assert report.untokenized_style_probability == 0.02
        assert len(report.violations) == 0
        assert "fully compliant" in report.agent_fix_hint.lower()

    def test_lint_diff_with_hardcoded_hex_escalates_to_blocked_style(self):
        """Verify hardcoded hex color escalates verdict to blocked_style and blocks pass."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "voice_and_tone_grade": {"type": "score", "score": 2.0, "confidence": 0.85},
                "has_untokenized_design_elements": {"type": "noul", "noul": 0.95},
                "constitution_verdict": {"type": "choice", "choice": "blocked_style", "confidence": 0.95},
            },
            usage={"input_tokens": 100, "output_tokens": 12},
            cached=False,
        )

        linter = ConstitutionLinter(bridge=mock_bridge)
        dirty_diff = """diff --git a/frontend/src/components/DirtyCard.jsx b/frontend/src/components/DirtyCard.jsx
--- a/frontend/src/components/DirtyCard.jsx
+++ b/frontend/src/components/DirtyCard.jsx
@@ -10,3 +10,4 @@
+  return <div style={{ color: "#10b981" }}>Dirty Color</div>;
"""
        report = linter.lint_diff_string(dirty_diff)

        assert report.passed is False
        assert report.verdict == "blocked_style"
        assert any(v.rule == "DESIGN_ZERO_HEX_COLORS" for v in report.violations)
        assert "var(--" in report.agent_fix_hint

    def test_parse_unified_diff_extracts_added_lines_accurately(self):
        """Test unified diff parsing extracts added lines and line numbers."""
        raw_diff = """diff --git a/model/foo.py b/model/foo.py
index 1234567..89abcdef 100644
--- a/model/foo.py
+++ b/model/foo.py
@@ -15,4 +15,6 @@ def calculate_xp():
     base_xp = 4.0
+    bonus_xp = 1.5
+    return base_xp + bonus_xp
"""
        parsed = parse_unified_diff(raw_diff)
        assert "model/foo.py" in parsed
        assert len(parsed["model/foo.py"]) == 2
        assert parsed["model/foo.py"][0] == (16, "    bonus_xp = 1.5")
        assert parsed["model/foo.py"][1] == (17, "    return base_xp + bonus_xp")


class TestAdversarialConstitutionLinterIntegrity:
    """Stress tests for regex bypasses, untracked files, and threshold cutoffs."""

    def test_allow_html_anchors_with_hex_like_words(self):
        """Verify anchor tags with words like #feed, #bad, #cab do not trigger false positive blockers."""
        linter = ConstitutionLinter()
        diff_lines = [
            (10, '  return <a href="#feed">Matchday Feed</a>;'),
            (11, '  return <a href="#bad">Report</a>;'),
            (12, '  return <a href="#cab">Taxi</a>;'),
            (13, '  return <a href="#beef">Beef</a>;'),
        ]
        violations = linter.check_deterministic_invariants(
            file_path="frontend/src/components/Nav.jsx",
            diff_lines=diff_lines,
        )
        assert len(violations) == 0

    def test_block_raw_color_functions_rgb_hsl_oklch(self):
        """Verify rgb(), rgba(), hsl(), and oklch() are caught as blockers."""
        linter = ConstitutionLinter()
        diff_lines = [
            (15, '  <div style={{ color: "rgb(255, 0, 0)", backgroundColor: "hsl(120, 100%, 50%)" }} />'),
            (16, '  <span style={{ borderColor: "oklch(0.7 0.2 150)" }} />'),
        ]
        violations = linter.check_deterministic_invariants(
            file_path="frontend/src/components/Card.jsx",
            diff_lines=diff_lines,
        )
        assert len(violations) >= 2
        rules = [v.rule for v in violations]
        assert "DESIGN_ZERO_RAW_COLORS" in rules

    def test_block_historical_vault_and_mergers_modifications(self):
        """Verify edits to data/2023-24/ and mergers.py are strictly blocked."""
        linter = ConstitutionLinter()
        v_hist = linter.check_deterministic_invariants(
            file_path="data/2023-24/cleaned_players.csv",
            diff_lines=[(1, "new,row,data")],
        )
        assert any(v.rule == "CONSTITUTION_HISTORICAL_VAULT_IMMUTABLE" for v in v_hist)

        v_merger = linter.check_deterministic_invariants(
            file_path="mergers.py",
            diff_lines=[(10, "def merge_data(): pass")],
        )
        assert any(v.rule == "CONSTITUTION_TIER_QUARANTINE" for v in v_merger)

    def test_enforce_tone_score_cutoff_below_threshold(self):
        """Verify tone_score < 1.50 forces failure even if Jev returns warning_copy."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "voice_and_tone_grade": {"type": "score", "score": 0.5, "confidence": 0.9},
                "has_untokenized_design_elements": {"type": "noul", "noul": 0.05},
                "constitution_verdict": {"type": "choice", "choice": "warning_copy", "confidence": 0.9},
            },
            usage={"input_tokens": 50, "output_tokens": 10},
        )
        linter = ConstitutionLinter(bridge=mock_bridge)
        raw_diff = """diff --git a/frontend/src/components/PlayerCard.jsx b/frontend/src/components/PlayerCard.jsx
--- a/frontend/src/components/PlayerCard.jsx
+++ b/frontend/src/components/PlayerCard.jsx
@@ -10,2 +10,3 @@
 context
+export const Copy = () => <div>Asset portfolio downside risk</div>;
"""
        report = linter.lint_diff_string(raw_diff)
        assert report.passed is False
        assert report.tone_score == 0.5
        assert report.verdict == "blocked_copy"
        assert any(v.rule == "VOICE_AND_TONE_DEVIATION" for v in report.violations)

    def test_enforce_untokenized_style_probability_cutoff(self):
        """Verify untokenized_prob >= 0.60 forces failure even if Jev returns warning_copy."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "voice_and_tone_grade": {"type": "score", "score": 2.5, "confidence": 0.9},
                "has_untokenized_design_elements": {"type": "noul", "noul": 0.85},
                "constitution_verdict": {"type": "choice", "choice": "warning_copy", "confidence": 0.9},
            },
            usage={"input_tokens": 50, "output_tokens": 10},
        )
        linter = ConstitutionLinter(bridge=mock_bridge)
        raw_diff = """diff --git a/frontend/src/components/CustomPill.jsx b/frontend/src/components/CustomPill.jsx
--- /dev/null
+++ b/frontend/src/components/CustomPill.jsx
@@ -0,0 +1,2 @@
+export const Pill = () => <div className="custom-bubble-pill">Pill</div>;
+"""
        report = linter.lint_diff_string(raw_diff)
        assert report.passed is False
        assert report.untokenized_style_probability == 0.85
        assert report.verdict == "blocked_style"
        assert any(v.rule == "DESIGN_UNTOKENIZED_STYLING" for v in report.violations)

    def test_detect_unregistered_component_studio_component(self):
        """Verify new UI component without ComponentStudio.jsx registration is blocked."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        linter = ConstitutionLinter(bridge=mock_bridge)
        new_comp_diff = """diff --git a/frontend/src/components/BrandNewWidget.jsx b/frontend/src/components/BrandNewWidget.jsx
new file mode 100644
--- /dev/null
+++ b/frontend/src/components/BrandNewWidget.jsx
@@ -0,0 +1,3 @@
+export default function BrandNewWidget() {
+    return <div className="surface-scope-1">Brand New Widget</div>;
+}
+"""
        report = linter.lint_diff_string(new_comp_diff)
        assert report.passed is False
        assert any(v.rule == "DESIGN_RECIPROCAL_COMPONENT_STUDIO_REGISTRATION" for v in report.violations)

    def test_pre_filtering_skips_backend_csv_and_models(self):
        """Verify backend CSV and Python files do not invoke Jev qualitative evaluation."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        linter = ConstitutionLinter(bridge=mock_bridge)
        backend_diff = """diff --git a/data/2026-27/predictions.csv b/data/2026-27/predictions.csv
--- a/data/2026-27/predictions.csv
+++ b/data/2026-27/predictions.csv
@@ -1,2 +1,3 @@
 id,name,xp
+1,Haaland,7.5
"""
        report = linter.lint_diff_string(backend_diff)
        # Verify bridge was never queried for CSV changes
        mock_bridge.ask.assert_not_called()
        assert report.passed is True
        assert report.tone_score == 3.0
        assert report.untokenized_style_probability == 0.0

    def test_parse_unified_diff_with_quoted_paths_and_multi_hunks(self):
        """Verify diff parser handles paths with quotes and multiple @@ hunks."""
        raw_diff = """diff --git "a/frontend/src/components/Sub Folder/My Card.jsx" "b/frontend/src/components/Sub Folder/My Card.jsx"
--- "a/frontend/src/components/Sub Folder/My Card.jsx"
+++ "b/frontend/src/components/Sub Folder/My Card.jsx"
@@ -10,3 +10,4 @@
 context line
+added hunk 1
@@ -30,2 +31,3 @@
 context line 2
+added hunk 2
"""
        parsed = parse_unified_diff(raw_diff)
        key = "frontend/src/components/Sub Folder/My Card.jsx"
        assert key in parsed
        assert len(parsed[key]) == 2
        assert parsed[key][0] == (11, "added hunk 1")
        assert parsed[key][1] == (32, "added hunk 2")

    def test_lint_git_working_tree_discovers_untracked_files(self, monkeypatch, tmp_path):
        """Verify lint_git_working_tree discovers and audits untracked files in working tree."""
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        linter = ConstitutionLinter(bridge=mock_bridge)

        def fake_subprocess_run(cmd, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.returncode = 0
            if 'status' in cmd:
                mock_res.stdout = "?? frontend/src/components/UntrackedCard.jsx\n"
            else:
                mock_res.stdout = ""
            return mock_res

        # Patch subprocess.run and file existence
        monkeypatch.setattr("subprocess.run", fake_subprocess_run)
        monkeypatch.setattr("os.path.isfile", lambda p: True)

        fake_content = (
            "export default function UntrackedCard() {\n"
            "    return <div style={{ color: '#ff0000' }}>Untracked</div>;\n"
            "}\n"
        )
        from unittest.mock import mock_open
        monkeypatch.setattr("builtins.open", mock_open(read_data=fake_content))

        report = linter.lint_git_working_tree()
        assert report.passed is False
        assert any(v.rule == "DESIGN_ZERO_HEX_COLORS" for v in report.violations)



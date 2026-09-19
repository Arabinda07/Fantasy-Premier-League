#!/usr/bin/env python3
"""FPL Dugout — Qualitative Constitution & DESIGN.md Linter.

Audits git diffs and source files using TypeSafe AI System One (Jev) alongside
deterministic AST/regex filters to enforce:
1. Project Constitution (CONSTITUTION.md & AGENTS.md codebase tiers).
2. DESIGN.md design system compliance (zero hardcoded hex colors, surface scopes, typography).
3. Voice and Tone Guide (docs/voice-and-tone-guide.md: no corporate jargon, raw math, or AI slop).
4. Reciprocal registration of UI components in ComponentStudio.jsx.
5. Single source of truth for element_type in positions.py.

Usage:
    python scripts/jev_constitution_linter.py
    python scripts/jev_constitution_linter.py --staged
    python scripts/jev_constitution_linter.py --file frontend/src/components/BenchCard.jsx
    python scripts/jev_constitution_linter.py --diff-target HEAD~1
    python scripts/jev_constitution_linter.py --json
"""
import argparse
from dataclasses import asdict, dataclass
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.typesafe_bridge import TypeSafeBridge

# Quarantined legacy scrapers (Tier 2 & 3)
QUARANTINED_FILES = {
    'collector.py',
    'getters.py',
    'parsers.py',
    'global_scraper.py',
    'teams_scraper.py',
    'mergers.py',
}

# Hex Color Pattern (exempting comments and token definitions)
HEX_COLOR_REGEX = re.compile(r'(?<![\w-])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b')

# Raw functional color formats (rgb, rgba, hsl, hsla, inline oklch)
RAW_COLOR_FN_REGEX = re.compile(r'\b(?:rgb|rgba|hsl|hsla|oklch)\s*\([^)]+\)', re.IGNORECASE)

# Exclusion pattern for HTML anchor targets and CSS IDs (e.g. href="#feed", href="#bad", href="#cab", id="#foo")
ANCHOR_OR_ID_EXCLUSION_REGEX = re.compile(
    r'''(?:href\s*=\s*['"]#[a-zA-Z0-9_-]+['"]|id\s*=\s*['"]#[a-zA-Z0-9_-]+['"]|url\(#[a-zA-Z0-9_-]+\)|['"]#[a-zA-Z0-9_-]+['"]\s*:)''',
    re.IGNORECASE
)

# Position re-declaration pattern outside positions.py
POSITION_REDECLARATION_REGEX = re.compile(
    r"""(?:element_type|positions?_map|pos_map|element_types)\s*=\s*\{\s*['"]?1['"]?\s*:\s*['"]?GK""",
    re.IGNORECASE
)

# Strict Mathematical Blocker Thresholds
TONE_SCORE_BLOCKER_THRESHOLD = 1.50
UNTOKENIZED_STYLE_BLOCKER_THRESHOLD = 0.60

# Voice & Tone Rubric (Score 0-3)
TONE_RUBRIC_LEGEND: Dict[str, str] = {
    "0": "Prohibited: Contains corporate jargon (assets, portfolio, capital, downside risk), robotic AI puffery, or raw statistical symbols (Poisson, Dixon-Coles).",
    "1": "Weak: Bland, overly abstract, or generic copy that fails dugout tone.",
    "2": "Compliant: Crisp, functional FPL matchday dugout terminology.",
    "3": "Exemplary: Masterful dugout voice matching tone guide tokens."
}

# Constitution Verdict Options (Choice)
VERDICT_OPTIONS: Dict[str, str] = {
    "clean": "Clean: Diff strictly complies with all constitutional, design, and voice rules.",
    "warning_copy": "Copy Warning: Minor copy improvement suggested, but safe to proceed.",
    "blocked_copy": "Copy Blocked: Direct violation of voice and tone guide (banned corporate jargon, AI slop, or raw math).",
    "blocked_style": "Style Blocked: Direct violation of DESIGN.md tokens, surface scopes, or hardcoded colors.",
    "blocked_architecture": "Architecture Blocked: Direct violation of codebase tiers or architectural invariants."
}


@dataclass
class LintViolation:
    file: str
    line_number: Optional[int]
    rule: str
    severity: str  # 'BLOCKER', 'WARNING', 'SUGGESTION'
    message: str
    suggestion: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConstitutionLintReport:
    passed: bool
    verdict: str  # 'clean', 'warning_copy', 'blocked_copy', 'blocked_style', 'blocked_architecture'
    tone_score: float
    untokenized_style_probability: float
    violations: List[LintViolation]
    agent_fix_hint: str
    files_checked: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'verdict': self.verdict,
            'tone_score': self.tone_score,
            'untokenized_style_probability': self.untokenized_style_probability,
            'violations': [v.to_dict() for v in self.violations],
            'agent_fix_hint': self.agent_fix_hint,
            'files_checked': self.files_checked,
        }


def is_evaluable_frontend_file(norm_path: str) -> bool:
    """Determine whether a file contains user-facing UI code or copy to be evaluated by Jev."""
    return (
        norm_path.startswith('frontend/src/')
        and norm_path.endswith(('.jsx', '.tsx', '.js', '.html'))
        and not norm_path.endswith(('.test.js', '.test.jsx', '.spec.js', '.spec.jsx'))
        and not norm_path.startswith('frontend/src/data/')
    )


def check_component_studio_registration(
    file_diffs: Dict[str, List[Tuple[int, str]]],
    diff_text: str = "",
) -> List[LintViolation]:
    """Verify that any newly created UI component is registered in ComponentStudio.jsx."""
    violations: List[LintViolation] = []

    # Identify newly created components in frontend/src/components/
    new_component_names: List[Tuple[str, str]] = []
    for fpath in file_diffs.keys():
        norm_fpath = fpath.replace('\\', '/')
        if (
            norm_fpath.startswith('frontend/src/components/')
            and norm_fpath.endswith('.jsx')
            and os.path.basename(norm_fpath) not in (
                'ComponentStudio.jsx',
                'App.jsx',
                'ErrorBoundary.jsx',
                'Header.jsx',
                'Footer.jsx',
            )
        ):
            # Check if this file is newly created in the diff
            is_new = bool(
                re.search(rf'diff --git [^\n]*{re.escape(fpath)}[^\n]*\n(?:[^\n]*\n)*?--- /dev/null', diff_text, re.MULTILINE)
                or re.search(rf'diff --git [^\n]*{re.escape(fpath)}[^\n]*\n(?:[^\n]*\n)*?new file mode', diff_text, re.MULTILINE)
            )
            if is_new:
                comp_name = os.path.splitext(os.path.basename(norm_fpath))[0]
                new_component_names.append((norm_fpath, comp_name))

    if not new_component_names:
        return violations

    # Read working tree ComponentStudio.jsx
    studio_path = 'frontend/src/components/ComponentStudio.jsx'
    full_studio_content = ""
    disk_studio = os.path.join(REPO_ROOT, studio_path)
    if os.path.exists(disk_studio):
        try:
            with open(disk_studio, 'r', encoding='utf-8', errors='replace') as f:
                full_studio_content = f.read()
        except Exception:
            pass

    # Added lines in ComponentStudio.jsx within this diff
    studio_added_text = "\n".join(text for _, text in file_diffs.get(studio_path, []))

    for norm_path, comp_name in new_component_names:
        if comp_name not in full_studio_content and comp_name not in studio_added_text:
            violations.append(LintViolation(
                file=norm_path,
                line_number=None,
                rule="DESIGN_RECIPROCAL_COMPONENT_STUDIO_REGISTRATION",
                severity="BLOCKER",
                message=f"New UI component '{comp_name}' is not registered in ComponentStudio.jsx.",
                suggestion=f"Import and register <{comp_name} /> in frontend/src/components/ComponentStudio.jsx as mandated by AGENTS.md.",
            ))

    return violations


class ConstitutionLinter:
    """Qualitative Constitution and DESIGN.md Linter powered by Jev System One."""

    def __init__(self, bridge: Optional[TypeSafeBridge] = None):
        self.bridge = bridge or TypeSafeBridge()

    def check_deterministic_invariants(
        self,
        file_path: str,
        diff_lines: List[Tuple[int, str]],
    ) -> List[LintViolation]:
        """Perform fast regex & AST checks on added diff lines."""
        violations: List[LintViolation] = []
        norm_path = file_path.replace('\\', '/')
        basename = os.path.basename(norm_path)

        # 1. Quarantined Tier 2 & 3 Scrapers Check
        if basename in QUARANTINED_FILES and not norm_path.startswith('tests/'):
            violations.append(LintViolation(
                file=norm_path,
                line_number=None,
                rule="CONSTITUTION_TIER_QUARANTINE",
                severity="BLOCKER",
                message=f"Direct edit to quarantined legacy script '{basename}'.",
                suggestion="Do not refactor or modify Tier 2/3 legacy scrapers without explicit constitutional amendment.",
            ))

        # Check for modifications to historical seasons (data/2016-17 to data/2025-26) or archive/
        if (
            re.match(r'^data/20(1[6-9]|2[0-5])-\d{2}/', norm_path)
            or norm_path.startswith('archive/')
        ):
            violations.append(LintViolation(
                file=norm_path,
                line_number=None,
                rule="CONSTITUTION_HISTORICAL_VAULT_IMMUTABLE",
                severity="BLOCKER",
                message=f"Direct modification to read-only historical vault file '{norm_path}'.",
                suggestion="Historical seasons (data/2016-17 through data/2025-26) and archive/ are strictly read-only for backtesting per CONSTITUTION.md Article 1.2.",
            ))

        # 2. Position Single Source of Truth Check
        if basename != 'positions.py' and not basename.startswith('test_'):
            for line_no, content in diff_lines:
                if POSITION_REDECLARATION_REGEX.search(content):
                    violations.append(LintViolation(
                        file=norm_path,
                        line_number=line_no,
                        rule="POSITIONS_SINGLE_SOURCE_OF_TRUTH",
                        severity="BLOCKER",
                        message="Redeclaring element_type mapping outside positions.py.",
                        suggestion="Import element_type mappings from 'positions.py'; never redeclare in local code.",
                    ))

        # 3. Hardcoded Hex / Raw Colors in Frontend (excluding tokens/index.css)
        is_frontend_code = (
            norm_path.startswith('frontend/src/')
            and norm_path.endswith(('.jsx', '.js', '.css', '.tsx', '.ts'))
            and not norm_path.endswith(('index.css', 'tokens.css', 'copyTokens.js'))
            and not norm_path.endswith(('.test.js', '.test.jsx', '.spec.js', '.spec.jsx'))
            and not norm_path.startswith('frontend/src/data/')
        )
        if is_frontend_code:
            for line_no, content in diff_lines:
                # Ignore commented lines and SVG data URLs
                clean_content = content.strip()
                if clean_content.startswith('//') or clean_content.startswith('/*') or clean_content.startswith('*'):
                    continue
                if 'data:image/svg' in clean_content or 'phosphor-icons' in clean_content:
                    continue

                # Strip anchor targets and CSS IDs to eliminate false positives on href="#feed", etc.
                scrubbed_content = ANCHOR_OR_ID_EXCLUSION_REGEX.sub('', clean_content)

                hex_matches = HEX_COLOR_REGEX.findall(scrubbed_content)
                for hex_code in hex_matches:
                    violations.append(LintViolation(
                        file=norm_path,
                        line_number=line_no,
                        rule="DESIGN_ZERO_HEX_COLORS",
                        severity="BLOCKER",
                        message=f"Hardcoded hex color '{hex_code}' found in UI component.",
                        suggestion="Use CSS custom properties (var(--...)) or surface scopes (.surface-scope-*) defined in DESIGN.md.",
                    ))

                raw_color_matches = RAW_COLOR_FN_REGEX.findall(scrubbed_content)
                for raw_color in raw_color_matches:
                    violations.append(LintViolation(
                        file=norm_path,
                        line_number=line_no,
                        rule="DESIGN_ZERO_RAW_COLORS",
                        severity="BLOCKER",
                        message=f"Hardcoded functional color '{raw_color}' found in UI component.",
                        suggestion="Use CSS custom properties (var(--...)) or surface scopes (.surface-scope-*) defined in DESIGN.md.",
                    ))

        return violations

    def evaluate_qualitative_diff(
        self,
        file_path: str,
        diff_text: str,
        deterministic_flags: List[LintViolation],
    ) -> Dict[str, Any]:
        """Query TypeSafe Jev System One for qualitative voice, tone, and design assessment."""
        # Prioritize substantive text over boilerplate imports for evaluation
        diff_lines_text = diff_text.splitlines()
        substantive = [l for l in diff_lines_text if not l.strip().startswith(('import ', 'export default function', 'from '))]
        condensed_diff = "\n".join(substantive if substantive else diff_lines_text)
        snippet = condensed_diff[:1500]
        if len(condensed_diff) > 1500:
            snippet += "\n[... truncated for qualitative evaluation ...]"

        det_messages = [f"[{v.rule}] {v.message}" for v in deterministic_flags]
        state = {
            "file": file_path,
            "diff_snippet": snippet,
            "deterministic_violations": det_messages,
        }

        questions = {
            "voice_and_tone_grade": {
                "type": "score",
                "instructions": "Grade any user-facing text, copy, or tooltips in this diff against the FPL Dugout Voice & Tone Guide.",
                "legend": TONE_RUBRIC_LEGEND,
            },
            "has_untokenized_design_elements": {
                "type": "noul",
                "instructions": "True if the diff introduces hardcoded colors, arbitrary bubble pills, or non-tokenized styling instead of .surface-scope-* and CSS variables."
            },
            "constitution_verdict": {
                "type": "choice",
                "instructions": "Classify whether this diff is safe to commit under repository rules.",
                "options": VERDICT_OPTIONS,
            },
        }

        # Safe mock fallback
        has_blockers = any(v.severity == "BLOCKER" for v in deterministic_flags)
        default_verdict = "blocked_style" if has_blockers else "clean"
        mock_fallback = {
            "voice_and_tone_grade": {"type": "score", "score": 1.5 if has_blockers else 2.8, "confidence": 0.85},
            "has_untokenized_design_elements": {"type": "noul", "noul": 0.90 if has_blockers else 0.05},
            "constitution_verdict": {"type": "choice", "choice": default_verdict, "confidence": 0.90},
        }

        resp = self.bridge.ask(state, questions, mock_fallback=mock_fallback)
        ans = resp.answers or {}

        tone_score = float((ans.get("voice_and_tone_grade") or {}).get("score", 2.5))
        untokenized_prob = float((ans.get("has_untokenized_design_elements") or {}).get("noul", 0.05))
        verdict = str((ans.get("constitution_verdict") or {}).get("choice", default_verdict))

        # Enforce mathematical thresholds
        if tone_score < TONE_SCORE_BLOCKER_THRESHOLD:
            verdict = "blocked_copy"
        elif untokenized_prob >= UNTOKENIZED_STYLE_BLOCKER_THRESHOLD:
            verdict = "blocked_style"

        # Deterministic override: if deterministic blockers exist, force blocked verdict
        if has_blockers:
            if any(v.rule in ("CONSTITUTION_TIER_QUARANTINE", "CONSTITUTION_HISTORICAL_VAULT_IMMUTABLE", "POSITIONS_SINGLE_SOURCE_OF_TRUTH") for v in deterministic_flags):
                verdict = "blocked_architecture"
            else:
                verdict = "blocked_style"

        return {
            "tone_score": tone_score,
            "untokenized_prob": untokenized_prob,
            "verdict": verdict,
        }

    def lint_diff_string(self, diff_text: str) -> ConstitutionLintReport:
        """Lint a raw git diff string."""
        file_diffs = parse_unified_diff(diff_text)
        all_violations: List[LintViolation] = []
        worst_verdict = "clean"
        min_tone = 3.0
        max_untokenized_prob = 0.0
        files_checked = list(file_diffs.keys())

        # Reciprocal ComponentStudio Registration Check
        studio_violations = check_component_studio_registration(file_diffs, diff_text)
        all_violations.extend(studio_violations)
        if studio_violations:
            worst_verdict = "blocked_style"

        for file_path, lines in file_diffs.items():
            norm_path = file_path.replace('\\', '/')

            # 1. Deterministic invariant checks
            det_violations = self.check_deterministic_invariants(norm_path, lines)
            all_violations.extend(det_violations)

            # Reconstruct added text for qualitative analysis
            added_content = "\n".join(text for _, text in lines)

            # 2. Qualitative Jev evaluation (only for user-facing frontend code)
            if is_evaluable_frontend_file(norm_path) and added_content.strip():
                eval_res = self.evaluate_qualitative_diff(norm_path, added_content, det_violations)

                v = eval_res["verdict"]
                t = eval_res["tone_score"]
                u = eval_res["untokenized_prob"]

                if t < min_tone:
                    min_tone = t
                if u > max_untokenized_prob:
                    max_untokenized_prob = u

                # Enforce hard mathematical threshold blockers
                if t < TONE_SCORE_BLOCKER_THRESHOLD:
                    v = "blocked_copy"
                    all_violations.append(LintViolation(
                        file=norm_path,
                        line_number=None,
                        rule="VOICE_AND_TONE_DEVIATION",
                        severity="BLOCKER",
                        message=f"Qualitative voice & tone score {t:.2f}/3.00 is below minimum threshold {TONE_SCORE_BLOCKER_THRESHOLD:.2f}.",
                        suggestion="Refine copy to match docs/voice-and-tone-guide.md. Replace corporate jargon (assets, portfolio, downside risk) with dugout language.",
                    ))
                if u >= UNTOKENIZED_STYLE_BLOCKER_THRESHOLD:
                    if v not in ("blocked_architecture", "blocked_copy"):
                        v = "blocked_style"
                    all_violations.append(LintViolation(
                        file=norm_path,
                        line_number=None,
                        rule="DESIGN_UNTOKENIZED_STYLING",
                        severity="BLOCKER",
                        message=f"Untokenized design probability {u:.1%} exceeds allowable threshold {UNTOKENIZED_STYLE_BLOCKER_THRESHOLD:.0%}.",
                        suggestion="Replace ad-hoc inline styles or bubble pills with DESIGN.md tokens (var(--...)) and .surface-scope-*.",
                    ))

                # Escalate verdict
                verdict_precedence = ["clean", "warning_copy", "blocked_copy", "blocked_style", "blocked_architecture"]
                if verdict_precedence.index(v) > verdict_precedence.index(worst_verdict):
                    worst_verdict = v

        passed = worst_verdict in ("clean", "warning_copy") and not any(v.severity == "BLOCKER" for v in all_violations)

        # Formulate agent fix directive
        if worst_verdict == "blocked_architecture":
            agent_hint = "Do not modify quarantined Tier 2/3 scrapers or historical vault data; import element_type strictly from positions.py."
        elif worst_verdict == "blocked_style":
            agent_hint = "Replace all raw/hex/rgb colors with tokenized CSS variables (var(--primary-emerald), var(--surface-1)), wrap cards in .surface-scope-*, and register components in ComponentStudio.jsx."
        elif worst_verdict == "blocked_copy":
            agent_hint = "Refine user-facing copy to eliminate corporate jargon (assets -> players, portfolio -> squad) and raw math names per docs/voice-and-tone-guide.md."
        elif worst_verdict == "warning_copy":
            agent_hint = "Minor copy refinement suggested: match dugout vocabulary in docs/voice-and-tone-guide.md."
        else:
            agent_hint = "Diff is fully compliant with repository constitution and design standards."

        return ConstitutionLintReport(
            passed=passed,
            verdict=worst_verdict,
            tone_score=round(min_tone, 2),
            untokenized_style_probability=round(max_untokenized_prob, 4),
            violations=all_violations,
            agent_fix_hint=agent_hint,
            files_checked=files_checked,
        )

    def lint_git_working_tree(
        self,
        staged_only: bool = False,
        diff_target: Optional[str] = None,
    ) -> ConstitutionLintReport:
        """Lint git changes from the active workspace."""
        cmd = ['git', 'diff']
        if staged_only:
            cmd.append('--cached')
        elif diff_target:
            cmd.append(diff_target)

        try:
            res = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True,
            )
            diff_text = res.stdout or ""
        except Exception as e:
            return ConstitutionLintReport(
                passed=False,
                verdict="blocked_architecture",
                tone_score=0.0,
                untokenized_style_probability=1.0,
                violations=[LintViolation(
                    file="git",
                    line_number=None,
                    rule="GIT_EXECUTION_ERROR",
                    severity="BLOCKER",
                    message=f"Failed to extract git diff: {e}",
                    suggestion="Ensure git is available and repo root is valid.",
                )],
                agent_fix_hint="Fix git workspace status.",
                files_checked=[],
            )

        # Untracked files inspection: audit uncommitted new files in working tree
        if not staged_only and not diff_target:
            try:
                status_res = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                )
                if status_res.returncode == 0:
                    for line in status_res.stdout.splitlines():
                        if line.startswith('?? '):
                            raw_file = line[3:].strip().strip('"')
                            norm_file = raw_file.replace('\\', '/')
                            full_path = os.path.join(REPO_ROOT, norm_file)
                            if os.path.isfile(full_path) and norm_file.endswith(('.jsx', '.js', '.tsx', '.ts', '.css', '.py', '.html')):
                                try:
                                    with open(full_path, 'r', encoding='utf-8', errors='replace') as uf:
                                        u_lines = uf.readlines()
                                    diff_text += f"\ndiff --git a/{norm_file} b/{norm_file}\nnew file mode 100644\n--- /dev/null\n+++ b/{norm_file}\n@@ -0,0 +1,{len(u_lines)} @@\n"
                                    diff_text += "".join("+" + l.rstrip('\r\n') + "\n" for l in u_lines)
                                except Exception:
                                    pass
            except Exception:
                pass

        if not diff_text.strip():
            return ConstitutionLintReport(
                passed=True,
                verdict="clean",
                tone_score=3.0,
                untokenized_style_probability=0.0,
                violations=[],
                agent_fix_hint="No changes detected in working tree.",
                files_checked=[],
            )

        return self.lint_diff_string(diff_text)


def parse_unified_diff(diff_text: str) -> Dict[str, List[Tuple[int, str]]]:
    """Parse a unified git diff into added lines per file.

    Returns:
        Dict mapping file path to list of (line_number, line_text) for added lines (+).
    """
    file_diffs: Dict[str, List[Tuple[int, str]]] = {}
    current_file = None
    current_line_no = 0

    for raw_line in diff_text.splitlines():
        if raw_line.startswith('diff --git'):
            m = re.search(r'\s+"?b/(.+?)"?$', raw_line)
            if m:
                current_file = m.group(1).strip().strip('"')
            else:
                parts = raw_line.split(' b/')
                current_file = parts[-1].strip().strip('"') if len(parts) >= 2 else None
            if current_file:
                if current_file not in file_diffs:
                    file_diffs[current_file] = []
        elif raw_line.startswith('@@'):
            m = re.search(r'\+(\d+)', raw_line)
            if m:
                current_line_no = int(m.group(1))
        elif raw_line.startswith('+') and not raw_line.startswith('+++'):
            if current_file:
                added_text = raw_line[1:]
                file_diffs[current_file].append((current_line_no, added_text))
                current_line_no += 1
        elif not raw_line.startswith('-'):
            current_line_no += 1

    return file_diffs


def print_cli_report(report: ConstitutionLintReport) -> None:
    """Print human-readable and agent-friendly formatted report."""
    print("\n" + "=" * 80)
    print("  FPL DUGOUT — QUALITATIVE CONSTITUTION & DESIGN LINTER (JEV SYSTEM ONE)")
    print("=" * 80)

    verdict_badge = {
        "clean": "[PASS] CLEAN",
        "warning_copy": "[WARN] COPY WARNING",
        "blocked_copy": "[FAIL] COPY BLOCKED",
        "blocked_style": "[FAIL] STYLE BLOCKED",
        "blocked_architecture": "[FAIL] ARCHITECTURE BLOCKED",
    }.get(report.verdict, f"[FAIL] {report.verdict}")

    status_color = "PASS" if report.passed else "FAIL"
    print(f"Verdict: {verdict_badge} (Status: {status_color})")
    print(f"Tone Score: {report.tone_score:.2f}/3.00 | Untokenized Style Prob: {report.untokenized_style_probability:.1%}")
    print(f"Files Evaluated: {len(report.files_checked)}")
    print("-" * 80)

    if report.violations:
        print("\nViolations Detected:")
        for idx, v in enumerate(report.violations, 1):
            loc = f"{v.file}:{v.line_number}" if v.line_number else v.file
            print(f"  {idx}. [{v.severity}] {v.rule} at {loc}")
            print(f"     Problem:    {v.message}")
            print(f"     Suggestion: {v.suggestion}")

    print("\nAgent Action Directive (AX):")
    print(f"  -> {report.agent_fix_hint}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Qualitative Constitution & DESIGN.md Linter with Jev System One")
    parser.add_argument('--staged', action='store_true', default=False, help="Lint staged git changes only")
    parser.add_argument('--diff-target', default=None, help="Git revision or commit to diff against (e.g. HEAD~1)")
    parser.add_argument('--file', default=None, help="Lint a specific single file")
    parser.add_argument('--json', action='store_true', default=False, help="Output machine-readable JSON for agents/CI")

    args = parser.parse_args()
    linter = ConstitutionLinter()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' does not exist.", file=sys.stderr)
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8', errors='replace') as f:
            lines = [(idx + 1, line.rstrip('\n')) for idx, line in enumerate(f)]
        file_diff_text = f"diff --git a/{args.file} b/{args.file}\n--- a/{args.file}\n+++ b/{args.file}\n@@ -0,0 +1,{len(lines)} @@\n" + "\n".join(f"+{t}" for _, t in lines)
        report = linter.lint_diff_string(file_diff_text)
    else:
        report = linter.lint_git_working_tree(staged_only=args.staged, diff_target=args.diff_target)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_cli_report(report)

    sys.exit(0 if report.passed else 1)


if __name__ == '__main__':
    main()


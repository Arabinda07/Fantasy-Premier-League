#!/usr/bin/env python3
"""
FPL Dugout — Automated Frontend Voice, Tone & Copy Validator

Scans all frontend source files (JSX, JS, HTML) to enforce:
1. Strict adherence to the 3-Tier Vocabulary Filter (docs/voice-and-tone-guide.md).
2. Elimination of Tier 3 banned words (assets, portfolio, capital, downside protection, etc.).
3. Proper translation of Tier 2 statistical terms into fan-friendly English.
4. Elimination of AI slop, corporate puffery, and robotic phrasing.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Banned / Flagged Rules with suggestions
BANNED_RULES = [
    # Tier 3: Forbidden Corporate & Financial Jargon
    {
        "pattern": r"\bassets?\b",
        "category": "Tier 3: Corporate Jargon",
        "message": "Use 'player', 'squad', or 'picks' instead of 'asset/assets'.",
        "suggestion": "player / squad / picks",
        "exempt_code": True,  # exempt variable names, import paths, CSS asset references
    },
    {
        "pattern": r"\bportfolios?\b",
        "category": "Tier 3: Corporate Jargon",
        "message": "Use 'squad' or 'team' instead of 'portfolio'.",
        "suggestion": "squad / team",
    },
    {
        "pattern": r"\bcapital\b(?!\s+(?:letter|city))",
        "category": "Tier 3: Corporate Jargon",
        "message": "Use 'budget' or 'bank balance' instead of 'capital'.",
        "suggestion": "budget / bank balance",
    },
    {
        "pattern": r"\bfunds\s+depletion\b",
        "category": "Tier 3: Corporate Jargon",
        "message": "Use 'extra cost' or 'not enough bank balance'.",
        "suggestion": "extra cost / bank balance",
    },
    {
        "pattern": r"\bdownside\s+(?:protection|risk)\b",
        "category": "Tier 3: Corporate Jargon",
        "message": "Use 'protecting your lead' or 'safe template picks'.",
        "suggestion": "protecting your lead / safe picks",
    },
    {
        "pattern": r"\bexecution\s+error\b",
        "category": "Tier 3: Robotic Error",
        "message": "Use 'Formation Alert' or 'Transfer Error'.",
        "suggestion": "Formation Alert / Transfer Error",
    },
    {
        "pattern": r"\bsub-?optimal\b",
        "category": "Tier 3: Robotic Jargon",
        "message": "Use 'invalid squad' or 'lower-scoring pick'.",
        "suggestion": "invalid squad / lower-scoring pick",
    },
    {
        "pattern": r"\broster\s+composition\b",
        "category": "Tier 3: Robotic Jargon",
        "message": "Use 'squad formation' or 'team lineup'.",
        "suggestion": "squad formation / team lineup",
    },
    {
        "pattern": r"\brisk\s+profile\b",
        "category": "Tier 3: Corporate Jargon",
        "message": "Use 'play style' or 'tactical goal'.",
        "suggestion": "play style / tactical goal",
    },
    # Tier 2: Un-translated Statistical / Academic Models in UI text
    {
        "pattern": r"\bexpected\s+value\b",
        "category": "Tier 2: Statistical Term",
        "message": "Translate to 'Expected Points', 'Exp Pts', or 'Projected Points'.",
        "suggestion": "Expected Points / Exp Pts",
    },
    {
        "pattern": r"\b(?:bivariate\s+)?dixon-?coles\b",
        "category": "Tier 2: Raw Model Name",
        "message": "Translate to 'Match Preview' or 'Clean Sheet Odds'.",
        "suggestion": "Match Preview · Clean Sheet Odds",
    },
    {
        "pattern": r"\bpoisson\s+(?:distribution|model|pmf)\b",
        "category": "Tier 2: Raw Model Name",
        "message": "Translate to 'Clean Sheet Chances' or 'Scoreline Odds'.",
        "suggestion": "Scoreline Chances & Clean Sheet Odds",
    },
    {
        "pattern": r"\b(?:empirical\s+)?bayesian\s+shrinkage\b",
        "category": "Tier 2: Raw Model Name",
        "message": "Translate to 'Blending Recent Form with Career Record'.",
        "suggestion": "Blending Recent Form with Career Record",
    },
    # Anti-Slop & Robotic Phrasing
    {
        "pattern": r"\bmonopolizes?\b",
        "category": "Anti-Slop: Overstated Verb",
        "message": "Use 'takes all corners/free-kicks' instead of 'monopolizes'.",
        "suggestion": "takes all / delivers all",
    },
    {
        "pattern": r"\bstands?\s+as\s+a\s+testament\b",
        "category": "Anti-Slop: AI Filler",
        "message": "Cut inflated phrasing; state the fact directly.",
        "suggestion": "shows / is",
    },
    {
        "pattern": r"\bdelivering\s+higher\s+baseline\s+security\b",
        "category": "Anti-Slop: Corporate Fluff",
        "message": "Use 'safest pick' or 'reliable points floor'.",
        "suggestion": "safest pick / reliable points floor",
    },
    {
        "pattern": r"\bhere's\s+the\s+thing\b",
        "category": "Anti-Slop: Throat-Clearing",
        "message": "Cut throat-clearing and state the point directly.",
        "suggestion": "[state point directly]",
    },
    {
        "pattern": r"\blet\s+that\s+sink\s+in\b",
        "category": "Anti-Slop: Emphasis Crutch",
        "message": "Cut emphasis crutch.",
        "suggestion": "[remove phrase]",
    },
    {
        "pattern": r"\bseamlessly\b",
        "category": "Anti-Slop: Corporate Buzzword",
        "message": "Cut 'seamlessly' or use 'easily/smoothly'.",
        "suggestion": "easily / smoothly",
    },
    {
        "pattern": r"\bleverage\s+(?:your|our|their|the)\b",
        "category": "Anti-Slop: Corporate Buzzword",
        "message": "Use 'use' or 'take advantage of' instead of 'leverage'.",
        "suggestion": "use / back",
    },
]


def extract_user_facing_strings(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Extract user-facing text from JSX/JS files, identifying strings
    inside JSX text children, string literals in props (title, placeholder,
    aria-label, alt), and copy token definitions, while ignoring CSS classes,
    import paths, and internal identifiers.
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    extracted = []

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        # Skip imports and pure variable declarations
        if stripped.startswith("import ") or stripped.startswith("import{"):
            continue

        # If line contains className="...", remove the className portion so we don't flag CSS class tokens
        cleaned_line = re.sub(r'className=(?:\{[^}]*\}|"[^"]*"|\'[^\']*\')', '', line)

        # Check for string literals (single, double quotes, template literals)
        string_matches = re.findall(r"['\"`]([^'\"`\n]{3,})['\"`]", cleaned_line)
        for s in string_matches:
            # Skip code identifiers (e.g. import paths, css classes, state ids, colors)
            if s.startswith("./") or s.startswith("../") or s.startswith("http") or s.startswith("var(--") or s.startswith("#") or s.startswith("rgba"):
                continue
            if s.endswith(".css") or s.endswith(".js") or s.endswith(".jsx") or s.endswith(".json") or s.endswith(".svg"):
                continue
            # Skip short internal keys / camelCase variable names
            if re.match(r"^[a-z0-9_]+$", s) and len(s.split()) == 1:
                continue
            extracted.append((line_idx, s, line))

        # Check for JSX text outside tag brackets (e.g. <span>Some Text</span>)
        jsx_texts = re.findall(r">([^<>{}\n]{3,})<", line)
        for jt in jsx_texts:
            clean_jt = jt.strip()
            if clean_jt:
                extracted.append((line_idx, clean_jt, line))

    return extracted



def validate_file(file_path: Path) -> List[Dict]:
    """Validate a single frontend file for copy violations."""
    violations = []
    extracted = extract_user_facing_strings(file_path)

    for line_no, text_sample, full_line in extracted:
        for rule in BANNED_RULES:
            match = re.search(rule["pattern"], text_sample, re.IGNORECASE)
            if match:
                # Filter out false positives in code-only contexts (e.g. is_bench_asset variable)
                matched_word = match.group(0)
                if rule.get("exempt_code"):
                    # If this is in a variable or property name like is_bench_asset or asset_id, ignore
                    if f"{matched_word}_" in full_line or f"_{matched_word}" in full_line or f".{matched_word}" in full_line:
                        continue
                    # If it's part of an asset path like dist/assets, ignore
                    if f"assets/" in full_line or f"/assets" in full_line:
                        continue

                violations.append({
                    "file": str(file_path),
                    "line": line_no,
                    "matched": matched_word,
                    "category": rule["category"],
                    "message": rule["message"],
                    "suggestion": rule["suggestion"],
                    "text_sample": text_sample,
                    "full_line": full_line.strip()
                })

    return violations


def scan_frontend_directory(frontend_root: Path) -> Tuple[int, List[Dict]]:
    """Scan all frontend source files for voice and tone violations."""
    src_dir = frontend_root / "src"
    if not src_dir.exists():
        src_dir = frontend_root

    total_files = 0
    all_violations = []

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".jsx") or file.endswith(".js") or file.endswith(".html"):
                total_files += 1
                file_path = Path(root) / file
                file_violations = validate_file(file_path)
                all_violations.extend(file_violations)

    return total_files, all_violations


def main():
    repo_root = Path(__file__).resolve().parent.parent
    frontend_root = repo_root / "frontend"

    print("=" * 70)
    print("[INFO] FPL Dugout Voice, Tone & Copy Validator")
    print("       Enforcing docs/voice-and-tone-guide.md standards")
    print("=" * 70)

    total_files, violations = scan_frontend_directory(frontend_root)
    print(f"Scanned {total_files} frontend files across {frontend_root.name}/src\n")

    if violations:
        print(f"[FAIL] Found {len(violations)} copy violation(s):\n")
        # Deduplicate violations per line/rule
        seen = set()
        for v in violations:
            key = (v["file"], v["line"], v["matched"])
            if key in seen:
                continue
            seen.add(key)

            rel_path = Path(v["file"]).relative_to(repo_root).as_posix()
            print(f"  * {rel_path}:{v['line']}")
            print(f"     Category:   {v['category']}")
            print(f"     Matched:    '{v['matched']}'")
            print(f"     Line:       {v['full_line']}")
            print(f"     Guidance:   {v['message']}")
            print(f"     Suggested:  {v['suggestion']}\n")

        print("=" * 70)
        print("Please fix the copy violations above or update docs/voice-and-tone-guide.md.")
        sys.exit(1)
    else:
        print("[PASS] All frontend copy conforms to the FPL Dugout Voice & Tone Guide.")
        print("       0 banned words or un-translated terms detected.\n")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()


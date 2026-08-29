"""
Unit test for Voice, Tone & Frontend Copy Compliance.
Automatically validates frontend components against docs/voice-and-tone-guide.md.
"""

import sys
from pathlib import Path

# Add scripts directory to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "scripts"))

from validate_frontend_copy import scan_frontend_directory


def test_frontend_copy_conformance():
    """Verify that all frontend source files adhere to the Voice & Tone Guide."""
    frontend_root = repo_root / "frontend"
    total_files, violations = scan_frontend_directory(frontend_root)

    assert total_files > 0, "Should find frontend source files to scan"

    if violations:
        error_lines = [
            f"{Path(v['file']).relative_to(repo_root).as_posix()}:{v['line']} [{v['category']}] "
            f"Matched: '{v['matched']}' -> {v['message']} (Suggested: {v['suggestion']})"
            for v in violations
        ]
        assert not violations, "Found copy violations:\n" + "\n".join(error_lines)

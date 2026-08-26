"""
Open Knowledge Format (OKF v0.2) Bundle Validator

Validates conformance of knowledge/ bundle against the OKF v0.2 specification:
1. Every concept file (.md) contains parseable YAML frontmatter with required 'type'.
2. Reserved filenames (index.md, log.md) follow structural conventions.
3. Bundle-relative links (/path/to/concept.md) and relative links resolve to existing files.
4. Timestamps follow ISO-8601 format.
"""

import datetime
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    yaml = None


def parse_frontmatter(content: str) -> Tuple[dict, str, List[str]]:
    """Extract and parse YAML frontmatter from markdown content."""
    errors = []
    if not content.startswith("---"):
        return {}, content, ["Missing opening frontmatter delimiter ('---' on line 1)"]
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content, ["Unclosed frontmatter delimiter (missing closing '---')"]
    
    yaml_text = parts[1]
    body = parts[2]
    
    data = {}
    if yaml:
        try:
            data = yaml.safe_load(yaml_text) or {}
        except Exception as e:
            errors.append(f"YAML parse error: {e}")
    else:
        for line in yaml_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()
                
    return data, body, errors


def is_valid_iso8601(val) -> bool:
    if isinstance(val, (datetime.datetime, datetime.date)):
        return True
    val_str = str(val).strip()
    iso_regex = r"^\d{4}-\d{2}-\d{2}([T\s]\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:?\d{2})?)?$"
    return bool(re.match(iso_regex, val_str))


def validate_concept_file(file_path: Path, bundle_root: Path, repo_root: Path) -> List[str]:
    """Validate a non-reserved OKF concept document."""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Failed to read file: {e}"]

    frontmatter, body, fm_errors = parse_frontmatter(content)
    errors.extend(fm_errors)
    
    if not isinstance(frontmatter, dict):
        return errors + ["Frontmatter must be a key-value mapping"]
    
    # 1. Required 'type' field
    if "type" not in frontmatter or not str(frontmatter["type"]).strip():
        errors.append("Missing required frontmatter field: 'type'")
        
    # 2. Validate Attested Computation specific fields
    if frontmatter.get("type") == "Attested Computation":
        if "runtime" not in frontmatter:
            errors.append("Attested Computation must specify 'runtime'")
            
    # 3. Validate timestamp formats
    if "stale_after" in frontmatter and frontmatter["stale_after"]:
        if not is_valid_iso8601(frontmatter["stale_after"]):
            errors.append(f"Invalid ISO-8601 format for 'stale_after': '{frontmatter['stale_after']}'")
            
    if "generated" in frontmatter and isinstance(frontmatter["generated"], dict):
        if "at" in frontmatter["generated"]:
            if not is_valid_iso8601(frontmatter["generated"]["at"]):
                errors.append(f"Invalid ISO-8601 format for 'generated.at': '{frontmatter['generated']['at']}'")
        if "by" not in frontmatter["generated"]:
            errors.append("Field 'generated' must specify 'by'")

    # 4. Check links in markdown body
    link_regex = r"\[([^\]]+)\]\(([^)]+)\)"
    for match in re.finditer(link_regex, body):
        link_target = match.group(2).strip()
        if (
            link_target.startswith("http://")
            or link_target.startswith("https://")
            or link_target.startswith("mailto:")
            or link_target.startswith("#")
        ):
            continue
            
        if link_target.startswith("file:///"):
            # Normalize file URI
            cleaned_path = link_target.replace("file:///", "").replace("/", "\\")
            if not Path(cleaned_path).exists():
                errors.append(f"Broken file URI: '{link_target}'")
            continue

        path_part = link_target.split("#")[0]
        if not path_part:
            continue
            
        if path_part.startswith("/"):
            target_path = bundle_root / path_part.lstrip("/")
        else:
            target_path = (file_path.parent / path_part).resolve()
            
        if not target_path.exists():
            errors.append(f"Broken markdown link: '{link_target}' (resolved to non-existent: {target_path})")

    return errors


def validate_index_file(file_path: Path, bundle_root: Path) -> List[str]:
    """Validate an index.md file."""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Failed to read index file: {e}"]

    is_root = file_path.resolve() == bundle_root.resolve() / "index.md"
    if content.startswith("---"):
        if not is_root:
            errors.append("Frontmatter is only permitted in the bundle-root index.md (§12)")
        else:
            frontmatter, body, fm_errors = parse_frontmatter(content)
            errors.extend(fm_errors)
            if "okf_version" not in frontmatter:
                errors.append("Root index.md frontmatter should declare 'okf_version'")
                
    return errors


def validate_log_file(file_path: Path) -> List[str]:
    """Validate a log.md file."""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Failed to read log file: {e}"]

    date_heading_regex = r"^##\s+(\d{4}-\d{2}-\d{2})"
    lines = content.splitlines()
    for line in lines:
        if line.startswith("## "):
            if not re.match(date_heading_regex, line):
                errors.append(f"Log date heading must use ISO-8601 YYYY-MM-DD: '{line}'")
    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent
    bundle_root = repo_root / "knowledge"

    if not bundle_root.exists():
        print(f"[ERROR] Knowledge bundle directory does not exist: {bundle_root}")
        sys.exit(1)

    print(f"=== Validating OKF Bundle: {bundle_root} ===")
    
    total_files = 0
    total_errors = 0
    file_error_map: Dict[str, List[str]] = {}

    for root, dirs, files in os.walk(bundle_root):
        for file in files:
            if not file.endswith(".md") and not file.endswith(".py"):
                continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to(bundle_root).as_posix()
            total_files += 1

            if file == "index.md":
                errs = validate_index_file(file_path, bundle_root)
            elif file == "log.md":
                errs = validate_log_file(file_path)
            elif file.endswith(".md"):
                errs = validate_concept_file(file_path, bundle_root, repo_root)
            else:
                errs = []

            if errs:
                file_error_map[rel_path] = errs
                total_errors += len(errs)

    print(f"Scanned {total_files} files across the knowledge catalog.")
    
    if total_errors > 0:
        print(f"\n[FAIL] Found {total_errors} validation errors:\n")
        for file, errs in file_error_map.items():
            print(f"  File: {file}")
            for err in errs:
                print(f"    - {err}")
        sys.exit(1)
    else:
        print("\n[PASS] OKF v0.2 bundle conformance verified. 0 errors found.")
        sys.exit(0)


if __name__ == "__main__":
    main()

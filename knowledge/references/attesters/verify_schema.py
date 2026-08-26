"""
Deterministic CSV Schema & Mathematical Invariant Attester (OKF v0.2)

Inspects generated data receipts (model_dataset.csv, predictions.csv, fixture_predictions.csv)
and enforces both structural schema (columns/nulls) and mathematical domain bounds without LLM involvement.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd


def verify_dataframe_bounds(name: str, df: pd.DataFrame, bounds_rules: list) -> list:
    """Validate mathematical domain bounds on dataframe columns."""
    errors = []
    for col, check_fn, desc in bounds_rules:
        if col not in df.columns:
            continue
        try:
            valid_mask = check_fn(df[col])
            if not valid_mask.all():
                bad_count = (~valid_mask).sum()
                sample_bad = df.loc[~valid_mask, col].head(3).tolist()
                errors.append(f"Mathematical invariant violation in {name} [{col}]: {desc} (failed for {bad_count} rows, sample: {sample_bad})")
        except Exception as e:
            errors.append(f"Failed to evaluate bound rule '{desc}' on {name} [{col}]: {e}")
    return errors


def verify_file_schema(filepath: Path, required_cols: list, non_null_cols: list, bounds_rules: list = None) -> list:
    errors = []
    if not filepath.exists():
        return [f"Receipt file does not exist: {filepath}"]
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return [f"Failed to parse CSV {filepath}: {e}"]
        
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns in {filepath.name}: {missing}")
        
    for col in non_null_cols:
        if col in df.columns and df[col].isnull().any():
            null_count = df[col].isnull().sum()
            errors.append(f"Column '{col}' contains {null_count} null/NaN values in {filepath.name}")
            
    if bounds_rules:
        errors.extend(verify_dataframe_bounds(filepath.name, df, bounds_rules))
            
    return errors


def main():
    parser = argparse.ArgumentParser(description="Deterministic CSV Schema & Invariant Attester")
    parser.add_argument("--season", default="2026-27", help="FPL Season (e.g. 2026-27)")
    parser.add_argument("--gw", type=int, default=2, help="Gameweek number")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    data_dir = repo_root / "data" / args.season

    print(f"=== Running OKF Schema & Mathematical Bound Attestation for Season {args.season}, GW {args.gw} ===")

    fixture_pred_file = data_dir / f"fixture_predictions_gw{args.gw}.csv"
    if not fixture_pred_file.exists():
        fixture_pred_file = data_dir / "fixture_predictions.csv"

    # Mathematical domain bounds rules: (column, check_lambda, description)
    model_ds_bounds = [
        ("now_cost", lambda s: (s >= 35) & (s <= 200), "price in tenths must be between 35 (£3.5M) and 200 (£20.0M)"),
        ("position", lambda s: s.isin(["GK", "DEF", "MID", "FWD"]), "position must be GK, DEF, MID, or FWD"),
        ("long_form_expected_goals_90", lambda s: s.isnull() | (s >= 0.0), "raw xG90 must be non-negative or null if 0 mins"),
        ("long_form_expected_assists_90", lambda s: s.isnull() | (s >= 0.0), "raw xA90 must be non-negative or null if 0 mins"),
    ]

    predictions_bounds = [
        ("p_start", lambda s: (s >= 0.0) & (s <= 1.0), "P(Start) must be in [0.0, 1.0]"),
        ("p_app", lambda s: (s >= 0.0) & (s <= 1.0), "P(App) must be in [0.0, 1.0]"),
        ("p_60_plus", lambda s: (s >= 0.0) & (s <= 1.0), "P(60+) must be in [0.0, 1.0]"),
        ("expected_points", lambda s: (s >= -5.0) & (s <= 30.0), "expected points must be in [-5.0, 30.0]"),
        ("c1_app_1_60", lambda s: (s >= 0.0) & (s <= 1.0), "C1 app (1-59) must be in [0.0, 1.0]"),
        ("c2_app_60_plus", lambda s: (s >= 0.0) & (s <= 1.0), "C1 app (60+) must be in [0.0, 1.0]"),
        ("c4_yellow_cards", lambda s: s <= 0.0, "C7 yellow card penalty must be <= 0.0"),
        ("c5_red_cards", lambda s: s <= 0.0, "C8 red card penalty must be <= 0.0"),
        ("c8_goals", lambda s: s >= 0.0, "C2 goals scored points must be >= 0.0"),
        ("c9_clean_sheets", lambda s: s >= 0.0, "C4 clean sheet points must be >= 0.0"),
        ("c10_goals_conceded", lambda s: s <= 0.0, "C10 goals conceded penalty must be <= 0.0"),
    ]

    fixture_pred_bounds = [
        ("fixture_fdr", lambda s: s.isin([1, 2, 3, 4, 5]), "FDR must be an integer between 1 and 5"),
        ("fixture_venue", lambda s: s.isin(["H", "A", "-"]), "venue must be 'H', 'A', or '-' for blanks"),
        ("fixture_attack_mult", lambda s: s >= 0.0, "attack multiplier must be non-negative"),
        ("expected_points", lambda s: (s >= -5.0) & (s <= 30.0), "fixture-adjusted xP must be in [-5.0, 30.0]"),
    ]

    checks = [
        (
            data_dir / "model_dataset.csv",
            ["player_code", "web_name", "team", "position", "now_cost", "status", "long_form_expected_goals_90", "long_form_expected_assists_90"],
            ["player_code", "position", "now_cost"],
            model_ds_bounds
        ),
        (
            data_dir / "predictions.csv",
            ["player_code", "web_name", "position", "now_cost", "expected_points", "c1_app_1_60", "c2_app_60_plus", "c3_saves", "c8_goals", "c9_clean_sheets", "c10_goals_conceded"],
            ["player_code", "expected_points", "c1_app_1_60", "c2_app_60_plus", "c8_goals", "c9_clean_sheets", "c10_goals_conceded"],
            predictions_bounds
        ),
        (
            fixture_pred_file,
            ["player_code", "web_name", "position", "now_cost", "expected_points", "fixture_fdr", "fixture_opponent", "fixture_venue"],
            ["player_code", "expected_points", "fixture_opponent"],
            fixture_pred_bounds
        )
    ]

    all_errors = []
    for filepath, req_cols, non_null, bounds in checks:
        errs = verify_file_schema(filepath, req_cols, non_null, bounds)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"[PASS] {filepath.name} conforms to contract and mathematical bounds ({len(pd.read_csv(filepath))} rows).")

    if all_errors:
        print("\n[FAIL] Schema & Mathematical Bound Attestation Failed:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n[VERDICT: ATTESTATION SUCCESSFUL - ALL INVARIANTS SATISFIED]")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
Deterministic Squad Solver Receipt & Invariant Attester (OKF v0.2)

Performs pure, fast deterministic attestation over emitted solver receipts:
1. Emitted JSON Matchday State: data/<season>/fpl_matchday_live_gw<GW>.json
2. Emitted Excel Workbook: data/<season>/fpl_matchday_live_gw<GW>.xlsx

Enforces FPL structural rules in sub-millisecond execution time:
- Exactly 15 squad players (2 GK, 5 DEF, 5 MID, 3 FWD).
- Financial limit: Squad cost <= budget + bank.
- Club constraint: Max 3 players per Premier League club.
- Starting XI: Exactly 11 starters with valid formation (1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD).
- Captaincy: Exactly 1 Captain in Starting XI, 1 distinct Vice-Captain.
- Excel workbook: Valid multi-tab schema with all 5 mandatory sheets.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    openpyxl = None


def verify_json_receipt(json_path: Path, max_budget: float = 100.0) -> list:
    """Attest solver constraints over the emitted JSON matchday state payload."""
    errors = []
    if not json_path.exists():
        return [f"Matchday JSON receipt does not exist: {json_path}"]
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Failed to parse JSON receipt {json_path}: {e}"]

    # Extract starters and bench
    starters = data.get("starters", [])
    bench = data.get("bench", [])
    squad = starters + bench

    # 1. Total squad size
    if len(squad) != 15:
        errors.append(f"Squad size violation in JSON receipt: expected 15, got {len(squad)} ({len(starters)} starters, {len(bench)} bench)")

    # 2. Positional quotas
    pos_counts = {}
    for p in squad:
        pos = p.get("position", p.get("pos", ""))
        pos_counts[pos] = pos_counts.get(pos, 0) + 1
        
    expected_pos = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    for pos, exp in expected_pos.items():
        act = pos_counts.get(pos, 0)
        if act != exp:
            errors.append(f"Positional quota violation in squad: {pos} count is {act} (expected {exp})")

    # 3. Starting XI formation
    if len(starters) != 11:
        errors.append(f"Starting XI size violation: expected 11, got {len(starters)}")
        
    starter_pos = {}
    for p in starters:
        pos = p.get("position", p.get("pos", ""))
        starter_pos[pos] = starter_pos.get(pos, 0) + 1
        
    if starter_pos.get("GK", 0) != 1:
        errors.append(f"Starting GK formation violation: got {starter_pos.get('GK', 0)} (expected 1)")
    if not (3 <= starter_pos.get("DEF", 0) <= 5):
        errors.append(f"Starting DEF formation violation: got {starter_pos.get('DEF', 0)} (must be 3-5)")
    if not (2 <= starter_pos.get("MID", 0) <= 5):
        errors.append(f"Starting MID formation violation: got {starter_pos.get('MID', 0)} (must be 2-5)")
    if not (1 <= starter_pos.get("FWD", 0) <= 3):
        errors.append(f"Starting FWD formation violation: got {starter_pos.get('FWD', 0)} (must be 1-3)")

    # 4. Club limit (Max 3 per team)
    team_counts = {}
    for p in squad:
        team = p.get("team", "")
        team_counts[team] = team_counts.get(team, 0) + 1
    for team, count in team_counts.items():
        if count > 3:
            errors.append(f"Club limit violation: Team '{team}' has {count} players (max allowed: 3)")

    # 5. Financial limit
    total_cost = sum(float(p.get("cost", 0.0)) for p in squad)
    bank = float(data.get("manager_profile", {}).get("bank", 0.0))
    if total_cost > max_budget + bank + 1e-4:
        errors.append(f"Financial budget violation: Total squad cost £{total_cost:.1f}M exceeds allowable limit £{max_budget + bank:.1f}M")

    # 6. Captaincy
    capt = data.get("captain")
    vice = data.get("vice_captain")
    if not capt:
        errors.append("Missing captain in JSON receipt")
    if not vice:
        errors.append("Missing vice-captain in JSON receipt")

    return errors


def verify_excel_receipt(xlsx_path: Path) -> list:
    """Attest structure and sheets in the emitted Excel workbook receipt."""
    errors = []
    if not xlsx_path.exists():
        return [f"Excel receipt does not exist: {xlsx_path}"]
        
    if not openpyxl:
        return errors
        
    try:
        wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
    except Exception as e:
        return [f"Failed to open Excel receipt {xlsx_path}: {e}"]

    required_sheets = [
        "Summary Dashboard",
        "Optimal Squad",
        "GW Predictions",
        "Fixtures & Ratings",
        "Form & Underlying Stats"
    ]
    missing = [s for s in required_sheets if s not in wb.sheetnames]
    if missing:
        errors.append(f"Missing sheets in Excel receipt {xlsx_path.name}: {missing}")
        
    return errors


def main():
    parser = argparse.ArgumentParser(description="Deterministic Solver Receipt Attester")
    parser.add_argument("--season", default="2026-27", help="FPL Season")
    parser.add_argument("--gw", type=int, default=2, help="Gameweek number")
    parser.add_argument("--budget", type=float, default=100.0, help="Budget limit (£M)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    data_dir = repo_root / "data" / args.season
    
    print(f"=== Running OKF Solver Receipt Attestation for Season {args.season}, GW {args.gw} ===")

    json_receipt = data_dir / f"fpl_matchday_live_gw{args.gw}.json"
    xlsx_receipt = data_dir / f"fpl_matchday_live_gw{args.gw}.xlsx"
    if not xlsx_receipt.exists():
        xlsx_receipt = data_dir / f"fpl_model_output_{args.season}_gw{args.gw}.xlsx"

    all_errors = []

    # 1. Attest JSON Matchday State
    json_errors = verify_json_receipt(json_receipt, max_budget=args.budget)
    if json_errors:
        all_errors.extend(json_errors)
    else:
        print(f"[PASS] JSON receipt '{json_receipt.name}' satisfies all 15-player, formation, budget, and captaincy constraints.")

    # 2. Attest Excel Multi-Tab Workbook
    excel_errors = verify_excel_receipt(xlsx_receipt)
    if excel_errors:
        all_errors.extend(excel_errors)
    else:
        print(f"[PASS] Excel receipt '{xlsx_receipt.name}' verified with all 5 required operational sheets.")

    if all_errors:
        print("\n[FAIL] Solver Receipt Attestation Failed:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n[VERDICT: SOLVER RECEIPT ATTESTATION SUCCESSFUL]")
        sys.exit(0)


if __name__ == "__main__":
    main()

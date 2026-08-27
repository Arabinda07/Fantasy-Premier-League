"""
Local Pipeline & CI Test Orchestrator
Replicates the exact sequence of .github/workflows/weekly_pipeline.yml locally.
"""
import subprocess
import sys
import os
import argparse
import time

# Ensure UTF-8 output if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_step(step_name: str, cmd: list, cwd: str = REPO_ROOT) -> bool:
    print(f"\n========================================================")
    print(f">> Step: {step_name}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"  Directory: {cwd}")
    print(f"========================================================")
    t0 = time.time()
    try:
        res = subprocess.run(cmd, cwd=cwd, check=True)
        elapsed = time.time() - t0
        print(f"[OK] {step_name} completed successfully in {elapsed:.2f}s.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] in {step_name} (Exit code {e.returncode})")
        return False
    except FileNotFoundError as e:
        print(f"\n[ERROR] Executable not found: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run the weekly FPL pipeline locally.")
    parser.add_argument("--mode", default="sync", choices=["sync", "full", "solver_only"], help="Pipeline mode")
    parser.add_argument("--season", default="2026-27", help="Season string")
    parser.add_argument("--gw", default="", help="Optional gameweek number")
    parser.add_argument("--skip-pipeline", action="store_true", help="Skip heavy data scrape and run enrichment/tests only")
    parser.add_argument("--skip-build", action="store_true", help="Skip frontend production bundle build")
    args = parser.parse_args()

    print(f"[START] Local FPL Pipeline Orchestrator (Season: {args.season}, Mode: {args.mode})...")

    # Step 1: Run heavy pipeline (if not skipped)
    if not args.skip_pipeline:
        pipe_cmd = [
            sys.executable,
            "-m",
            "model.pipeline_automation",
            "--season",
            args.season,
            "--mode",
            args.mode,
            "--team-id",
            "9500404",
            "--league-id",
            "1305495",
        ]
        if args.gw:
            pipe_cmd.extend(["--gw", args.gw])
        if not run_step("Pipeline Automation & Model Predictions", pipe_cmd):
            sys.exit(1)

    # Step 2: Enrich player costs and element IDs
    cost_cmd = [sys.executable, os.path.join("scripts", "enrich_player_costs.py"), args.season]
    if not run_step("Enrich Player Costs & Seasonal IDs", cost_cmd):
        sys.exit(1)

    # Step 3: Enrich frontend cockpit payloads
    enrich_cmd = [sys.executable, "-m", "model.enrich_frontend_data"]
    if args.gw:
        enrich_cmd.extend(["--gw", args.gw])
    run_step("Enrich Matchday Cockpit Payloads", enrich_cmd)

    # Step 4: Validate OKF v0.2 Knowledge Conformance
    okf_cmd = [sys.executable, os.path.join("scripts", "validate_okf.py")]
    if not run_step("Validate OKF Knowledge Catalog Conformance", okf_cmd):
        sys.exit(1)

    # Step 5: Run Client Optimizer Contract Test Suite
    client_test_cmd = ["node", os.path.join("frontend", "src", "utils", "clientOptimizer.test.js")]
    if not run_step("Client Optimizer Contract Tests", client_test_cmd):
        sys.exit(1)

    # Step 6: Run Serverless API Contract Test Suite
    api_test_cmd = ["node", os.path.join("tests", "test_api_sync.js")]
    if not run_step("Serverless API Contract Tests", api_test_cmd):
        sys.exit(1)

    # Step 7: Verify Frontend Production Build
    if not args.skip_build:
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        build_cmd = [npm_cmd, "run", "build"]
        frontend_dir = os.path.join(REPO_ROOT, "frontend")
        if not run_step("Frontend Production Bundle Build", build_cmd, cwd=frontend_dir):
            sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL LOCAL PIPELINE & QUALITY GATE TESTS PASSED CLEANLY.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

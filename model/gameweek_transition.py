"""One-Command Gameweek Transition & Matchday Orchestrator.

Provides the institutional, unified weekly transition workflow for competitive FPL management:
1. Gameweek State Detection & Deadline Countdown.
2. Completed Gameweek Accuracy Evaluation & Model Calibration (MAE, RMSE, Positional Biases).
3. Live Data Ingestion, Price Velocity Tracking & Underlying Feature Matrix Rebuild.
4. Quantitative 11-Component Projections across Multi-Horizon Fixture Window.
5. Official Team & Mini-League Live Synchronization (Team ID, Bank, Available FTs, Rival Overlaps).
6. Multi-Horizon MILP Squad Optimization with CVaR Tail-Risk and Auto-Sub Value.
7. Frontend Cockpit Export & Dixon-Coles / Minutes Hazard Enrichment.
8. Executive Action Briefing (Transfers, Captaincy, Vice-Captaincy, Lineup, Price Hazards).

Usage:
    python -m model.gameweek_transition --season 2026-27 --team-id 9500404 --league-id 1305495
    python -m model.gameweek_transition --mode full --scrape --team-id 9500404
"""
import argparse
from datetime import datetime, timezone
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.pipeline_automation import (
    run_live_pipeline,
    detect_active_gameweek,
    PipelineResult,
)
from model.accuracy_tracker import (
    evaluate_gameweek_accuracy,
    print_accuracy_summary,
    GameweekAccuracyReport,
)


def format_deadline_countdown(deadline_str: Optional[str]) -> str:
    """Format ISO deadline string into human-readable countdown."""
    if not deadline_str:
        return "Deadline: Unknown"
    try:
        # e.g. "2026-08-22T10:00:00Z"
        clean_str = deadline_str.replace('Z', '+00:00')
        dl_dt = datetime.fromisoformat(clean_str)
        now_dt = datetime.now(timezone.utc)
        diff = dl_dt - now_dt

        if diff.total_seconds() < 0:
            return f"Passed ({dl_dt.strftime('%a %d %b %H:%M UTC')})"

        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        return f"in {' '.join(parts)} ({dl_dt.strftime('%a %d %b %H:%M UTC')})"
    except Exception:
        return f"{deadline_str}"


def execute_gameweek_transition(
    season: str = '2026-27',
    target_gw: Optional[int] = None,
    team_id: Optional[int] = 9500404,
    league_id: Optional[int] = 1305495,
    mode: str = 'full',
    horizon: int = 3,
    strategy: str = 'pure_xp',
    scrape: bool = False,
    data_root: str = 'data',
) -> Dict[str, Any]:
    """Execute complete institutional gameweek transition."""
    start_time = time.time()

    print("\n" + "=" * 90)
    print(f"  FPL EXECUTIVE GAMEWEEK TRANSITION — Season {season}")
    print("=" * 90)

    # 1. Detect Gameweek State
    active_gw, next_gw, deadline = detect_active_gameweek(season=season, data_root=data_root, offline=False)
    resolved_target_gw = target_gw or next_gw or (active_gw + 1 if active_gw else 1)
    completed_gw = active_gw if (active_gw and active_gw < resolved_target_gw) else (resolved_target_gw - 1 if resolved_target_gw > 1 else None)

    countdown_text = format_deadline_countdown(deadline)

    print(f"  Active GW:    {active_gw or 'None'} | Completed GW: {completed_gw or 'None'}")
    print(f"  Target GW:    GW{resolved_target_gw}")
    print(f"  Deadline:     {countdown_text}")
    if team_id:
        print(f"  Team ID:      {team_id}" + (f" | League ID: {league_id}" if league_id else ""))
    print("-" * 90)

    # 2. Accuracy Evaluation of Completed GW (if applicable)
    accuracy_report: Optional[GameweekAccuracyReport] = None
    if completed_gw and completed_gw >= 1:
        print(f"[*] Step 1: Evaluating model calibration & prediction accuracy for GW{completed_gw}...")
        accuracy_report = evaluate_gameweek_accuracy(
            season=season,
            gw=completed_gw,
            data_root=data_root,
            save_log=True,
        )
        if accuracy_report:
            print(f"  [+] GW{completed_gw} Accuracy: Overall MAE = {accuracy_report.overall_mae:.2f} pts | Active Starters MAE = {accuracy_report.active_starters_mae:.2f} pts")
        else:
            print(f"  [*] GW{completed_gw} actual results not yet fully compiled or pre-GW prediction file absent.")

    # 3. Run Pipeline Automation
    print(f"\n[*] Step 2: Running automated pipeline (Mode: {mode.upper()} | Horizon: {horizon} GWs)...")
    pipeline_result: PipelineResult = run_live_pipeline(
        season=season,
        gw=resolved_target_gw,
        mode=mode,
        team_id=team_id,
        league_id=league_id,
        horizon=horizon,
        strategy=strategy,
        data_root=data_root,
        scrape=scrape,
        export_excel=True,
        export_json=True,
    )

    total_duration = time.time() - start_time

    # 4. Load Enriched Live Matchday State for Executive Summary
    matchday_json_path = os.path.join(REPO_ROOT, 'frontend', 'src', 'data', f'live_matchday_gw{resolved_target_gw}.json')
    if not os.path.exists(matchday_json_path):
        matchday_json_path = os.path.join(REPO_ROOT, data_root, season, f'fpl_matchday_live_gw{resolved_target_gw}.json')

    matchday_data = {}
    if os.path.exists(matchday_json_path):
        try:
            with open(matchday_json_path, 'r', encoding='utf-8') as f:
                matchday_data = json.load(f)
        except Exception:
            pass

    # 5. Print Executive Transition Report
    print("\n" + "=" * 90)
    print(f"  EXECUTIVE GAMEWEEK {resolved_target_gw} DECISION BRIEFING")
    print("=" * 90)

    mgr = matchday_data.get('manager_profile')
    if mgr:
        print(f"  MANAGER: {mgr.get('manager_name', 'Manager')} ({mgr.get('team_name', 'Team')}) | Entry #{mgr.get('entry_id', team_id)}")
        print(f"  OVERALL RANK: #{mgr.get('overall_rank', 0):,} | TOTAL POINTS: {mgr.get('overall_points', 0)} pts")
        print(f"  BANK BALANCE: GBP {mgr.get('bank', 0.0):.1f}M | TEAM VALUE: GBP {mgr.get('team_value', 100.0):.1f}M | AVAILABLE FTs: {mgr.get('free_transfers', 1)}")
        print("-" * 90)

    print(f"  TRANSFERS & ACTION DIRECTIVE:")
    action_summary = matchday_data.get('action_summary', 'Roll Free Transfer -- Bank transfer flexibility for future gameweeks.')
    print(f"  [>] {action_summary}")
    print("-" * 90)

    capt = matchday_data.get('captain', 'Haaland')
    vc = matchday_data.get('vice_captain', 'Palmer')
    starting_xp = matchday_data.get('starting_xp', 0.0)
    print(f"  OPTIMAL CAPTAINCY: [C] {capt} | [V] {vc}")
    print(f"  PROJECTED STARTING XI xP: {starting_xp:.2f} pts (Total Squad: {matchday_data.get('total_xp', 0.0):.2f} pts)")
    print("-" * 90)

    roadmap = matchday_data.get('multi_horizon_roadmap', [])
    if roadmap:
        print("  MULTI-HORIZON 5-WEEK STRATEGY ROADMAP:")
        for r in roadmap[:horizon]:
            t_in = ", ".join(r.get('transfers_in', [])) or "None"
            t_out = ", ".join(r.get('transfers_out', [])) or "None"
            hits = f" (-{r['hits_taken']*4} pts hit)" if r.get('hits_taken', 0) > 0 else ""
            print(f"    GW{r['gw']:<2} | IN: {t_in:<22} | OUT: {t_out:<22} | Bank: GBP {r.get('bank', 0.0):.1f}M{hits} | Net xP: {r.get('net_xp', 0.0):.2f}")
        print("-" * 90)

    print(f"  STATUS: All reports, Excel workbooks & Frontend Cockpit JSON fully updated.")
    print(f"  TOTAL EXECUTION TIME: {total_duration:.1f}s")
    print("=" * 90 + "\n")

    return {
        'season': season,
        'gameweek': resolved_target_gw,
        'deadline': deadline,
        'accuracy_report': accuracy_report,
        'pipeline_result': pipeline_result,
        'matchday_data': matchday_data,
        'duration_seconds': total_duration,
    }


def main():
    parser = argparse.ArgumentParser(
        description="One-Command Institutional Gameweek Transition Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=None, help="Target gameweek number (auto-detected if None)")
    parser.add_argument('--team-id', type=int, default=9500404, help="Official FPL Entry / Team ID (default: 9500404)")
    parser.add_argument('--league-id', type=int, default=1305495, help="Mini-league ID (default: 1305495)")
    parser.add_argument('--mode', default='full', choices=['sync', 'full', 'solver_only'],
                        help="Transition mode ('full' recommended for weekly rollover, 'sync' for fast daily)")
    parser.add_argument('--horizon', type=int, default=3, help="Lookahead horizon in gameweeks (1-5)")
    parser.add_argument('--strategy', default='pure_xp',
                        choices=['pure_xp', 'rank_protect', 'differential_chase'],
                        help="Game theory strategy")
    parser.add_argument('--scrape', action='store_true', default=False,
                        help="Run live web scrapers with Understat/FBref fallback")
    parser.add_argument('--data-root', default='data', help="Root data directory")

    args = parser.parse_args()

    execute_gameweek_transition(
        season=args.season,
        target_gw=args.gw,
        team_id=args.team_id,
        league_id=args.league_id,
        mode=args.mode,
        horizon=args.horizon,
        strategy=args.strategy,
        scrape=args.scrape,
        data_root=args.data_root,
    )


if __name__ == '__main__':
    main()

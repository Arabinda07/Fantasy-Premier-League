"""Live Data Pipeline Automation Engine for Fantasy Premier League.

Provides a unified, multi-stage orchestration system that automates the entire
FPL data ingestion, prediction, and optimization pipeline:
- Stage 1: API Sync & Price Velocity Tracking
- Stage 2: Historical Ingest & Aggregation (full mode)
- Stage 3: Feature Matrix & Dataset Rebuild
- Stage 4: Quantitative Point Projections
- Stage 5: Live Matchday Solver & Multi-Channel Export

Supports four execution modes:
- 'sync':             Fast daily sync (API + price delta + predictions + solver)
- 'full':             Complete post-gameweek rebuild (player histories + merged_gw + dataset)
- 'predictions_only': Re-run projections and fixture engine without network calls
- 'solver_only':      Re-run MILP solver and export without re-predicting

Usage:
    python -m model.pipeline_automation --season 2026-27 --mode sync
    python -m model.pipeline_automation --season 2026-27 --mode full
    python -m model.pipeline_automation --season 2026-27 --mode solver_only --bank 1.5 --ft 2
    python -m model.pipeline_automation --season 2026-27 --daemon --interval-hours 6
"""
import argparse
import csv
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ---------------------------------------------------------------------------
# Pipeline Result Dataclass
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    """Result of a single pipeline stage execution."""
    stage: str
    success: bool
    duration_seconds: float = 0.0
    message: str = ''
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Result of a complete pipeline execution."""
    season: str
    gameweek: int
    mode: str
    success: bool
    total_duration_seconds: float = 0.0
    stages: List[StageResult] = field(default_factory=list)
    active_gameweek: Optional[int] = None
    next_gameweek: Optional[int] = None
    deadline: Optional[str] = None
    price_alerts_count: int = 0
    matchday_result: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Stage 1: API Sync & Price Velocity
# ---------------------------------------------------------------------------

def detect_active_gameweek(
    season: str = '2026-27',
    data_root: str = 'data',
    offline: bool = False,
) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Detect the current and next gameweek from FPL API events.

    Args:
        season: season string.
        data_root: root data directory.
        offline: if True, skip API call and use cached fixtures.csv.

    Returns:
        Tuple of (current_gw, next_gw, deadline_iso_str).
        Returns (None, None, None) if detection fails.
    """
    current_gw = None
    next_gw = None
    deadline = None

    if not offline:
        try:
            from getters import get_data
            data = get_data()
            events = data.get('events', [])
            for event in events:
                if event.get('is_current'):
                    current_gw = int(event['id'])
                if event.get('is_next'):
                    next_gw = int(event['id'])
                    deadline = event.get('deadline_time')
            return current_gw, next_gw, deadline
        except Exception as e:
            print(f"[Pipeline] Warning: Could not fetch live API events: {e}")

    # Fallback: infer from local fixtures.csv
    fixtures_path = os.path.join(data_root, season, 'fixtures.csv')
    if os.path.exists(fixtures_path):
        fix_df = pd.read_csv(fixtures_path)
        if 'event' in fix_df.columns and 'finished' in fix_df.columns:
            finished = fix_df[fix_df['finished'] == True]
            if not finished.empty:
                current_gw = int(finished['event'].max())
                next_gw = min(38, current_gw + 1)
            else:
                # Pre-season or very early: no fixtures finished yet
                current_gw = 0
                next_gw = int(fix_df['event'].min()) if not fix_df.empty else 1
        elif 'event' in fix_df.columns:
            current_gw = 0
            next_gw = int(fix_df['event'].min()) if not fix_df.empty else 1

    return current_gw, next_gw, deadline


def sync_api_data(
    season: str = '2026-27',
    data_root: str = 'data',
    offline: bool = False,
) -> StageResult:
    """Stage 1a: Fetch bootstrap-static and fixtures from FPL API, update local CSVs.

    Args:
        season: season string.
        data_root: root data directory.
        offline: if True, skip network calls entirely.

    Returns:
        StageResult indicating success or failure.
    """
    stage_start = time.time()
    season_dir = os.path.join(data_root, season)
    os.makedirs(season_dir, exist_ok=True)

    if offline:
        return StageResult(
            stage='api_sync',
            success=True,
            duration_seconds=time.time() - stage_start,
            message='Skipped API sync (offline mode). Using local cached data.',
        )

    try:
        from getters import get_data, get_fixtures_data
        from parsers import parse_players, parse_fixtures, parse_team_data

        # Fetch bootstrap-static
        print("[Pipeline] Stage 1a: Fetching FPL bootstrap-static API...")
        data = get_data()

        # Write players_raw.csv
        base_filename = season_dir + '/'
        parse_players(data['elements'], base_filename)
        print(f"[Pipeline]   -> Updated players_raw.csv ({len(data['elements'])} players)")

        # Write teams.csv
        parse_team_data(data['teams'], base_filename)
        print(f"[Pipeline]   -> Updated teams.csv ({len(data['teams'])} teams)")

        # Write cleaned_players.csv and player_idlist.csv
        from global_scraper import clean_players, id_players
        clean_players(os.path.join(season_dir, 'players_raw.csv'), base_filename)
        id_players(os.path.join(season_dir, 'players_raw.csv'), base_filename)
        print("[Pipeline]   -> Updated cleaned_players.csv and player_idlist.csv")

        # Fetch and write fixtures
        print("[Pipeline] Stage 1a: Fetching FPL fixtures API...")
        fixtures_data = get_fixtures_data()
        parse_fixtures(fixtures_data, base_filename)
        print(f"[Pipeline]   -> Updated fixtures.csv ({len(fixtures_data)} fixtures)")

        return StageResult(
            stage='api_sync',
            success=True,
            duration_seconds=time.time() - stage_start,
            message=f'Synced {len(data["elements"])} players, {len(data["teams"])} teams, {len(fixtures_data)} fixtures.',
        )

    except Exception as e:
        return StageResult(
            stage='api_sync',
            success=False,
            duration_seconds=time.time() - stage_start,
            message='API sync failed. Falling back to local cached data.',
            error=str(e),
        )


def record_price_snapshot(
    season: str = '2026-27',
    data_root: str = 'data',
) -> StageResult:
    """Stage 1b: Record daily price velocity snapshot and classify alerts.

    Reads current transfer event data from players_raw.csv, computes net
    velocity for each player, and appends a timestamped snapshot to
    data/<season>/price_history/<date>.csv.

    Args:
        season: season string.
        data_root: root data directory.

    Returns:
        StageResult with count of price alerts generated.
    """
    stage_start = time.time()
    season_dir = os.path.join(data_root, season)
    raw_path = os.path.join(season_dir, 'players_raw.csv')

    if not os.path.exists(raw_path):
        return StageResult(
            stage='price_snapshot',
            success=False,
            duration_seconds=time.time() - stage_start,
            message='Cannot record price snapshot: players_raw.csv not found.',
            error='players_raw.csv not found',
        )

    try:
        from model.price_predictor import (
            compute_player_price_trend,
            RISING_LOCK, RISING_ALERT,
            FALLING_LOCK, FALLING_ALERT,
        )

        p_raw = pd.read_csv(raw_path)
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        price_dir = os.path.join(season_dir, 'price_history')
        os.makedirs(price_dir, exist_ok=True)
        snapshot_path = os.path.join(price_dir, f'{today_str}.csv')

        rows = []
        alert_count = 0
        for _, r in p_raw.iterrows():
            code = int(r.get('code', 0))
            web_name = str(r.get('web_name', ''))
            now_cost = float(r.get('now_cost', 0)) / 10.0
            t_in = int(float(r.get('transfers_in_event', 0) or 0))
            t_out = int(float(r.get('transfers_out_event', 0) or 0))
            sel_pct = float(r.get('selected_by_percent', 0) or 0) / 100.0

            trend_result = compute_player_price_trend(
                transfers_in_event=t_in,
                transfers_out_event=t_out,
                ownership_pct=sel_pct,
            )

            trend = trend_result['trend']
            if trend in (RISING_LOCK, RISING_ALERT, FALLING_LOCK, FALLING_ALERT):
                alert_count += 1

            rows.append({
                'date': today_str,
                'player_code': code,
                'web_name': web_name,
                'now_cost': now_cost,
                'transfers_in_event': t_in,
                'transfers_out_event': t_out,
                'net_velocity': trend_result['net_velocity'],
                'velocity_ratio': trend_result['velocity_ratio'],
                'trend': trend,
            })

        snapshot_df = pd.DataFrame(rows)
        snapshot_df.to_csv(snapshot_path, index=False)
        print(f"[Pipeline] Stage 1b: Price snapshot saved to {snapshot_path} ({alert_count} alerts)")

        # Print top alerts
        alerts_df = snapshot_df[snapshot_df['trend'].isin([RISING_LOCK, RISING_ALERT, FALLING_LOCK, FALLING_ALERT])]
        if not alerts_df.empty:
            rising = alerts_df[alerts_df['trend'].isin([RISING_LOCK, RISING_ALERT])].sort_values('net_velocity', ascending=False).head(5)
            falling = alerts_df[alerts_df['trend'].isin([FALLING_LOCK, FALLING_ALERT])].sort_values('net_velocity').head(5)
            for _, r in rising.iterrows():
                print(f"  [^] [{r['trend']}] {r['web_name']} | GBP {r['now_cost']:.1f}M | +{r['net_velocity']:,} net")
            for _, r in falling.iterrows():
                print(f"  [v] [{r['trend']}] {r['web_name']} | GBP {r['now_cost']:.1f}M | {r['net_velocity']:,} net")

        return StageResult(
            stage='price_snapshot',
            success=True,
            duration_seconds=time.time() - stage_start,
            message=f'Recorded price snapshot: {len(rows)} players, {alert_count} alerts.',
        )

    except Exception as e:
        return StageResult(
            stage='price_snapshot',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Price snapshot failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Stage 2: Historical Ingest & Aggregation (full mode only)
# ---------------------------------------------------------------------------

def rebuild_historical_data(
    season: str = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
) -> StageResult:
    """Stage 2: Pull individual player histories and rebuild merged_gw.csv.

    This is the expensive network-heavy step that fetches per-player match
    records from the FPL API for all active players. Only run in 'full' mode.

    Args:
        season: season string.
        gw: current gameweek number.
        data_root: root data directory.

    Returns:
        StageResult indicating success or failure.
    """
    stage_start = time.time()
    season_dir = os.path.join(data_root, season)

    try:
        from getters import get_individual_player_data
        from parsers import parse_player_history, parse_player_gw_history
        from collector import collect_gw, merge_gw
        from global_scraper import get_player_ids, id_players

        # Ensure player_idlist.csv exists
        players_raw_path = os.path.join(season_dir, 'players_raw.csv')
        base_filename = season_dir + '/'
        if os.path.exists(players_raw_path):
            id_players(players_raw_path, base_filename)

        player_ids = get_player_ids(base_filename)
        player_base = os.path.join(season_dir, 'players/')
        gw_base = os.path.join(season_dir, 'gws/')
        os.makedirs(gw_base, exist_ok=True)

        print(f"[Pipeline] Stage 2: Fetching individual data for {len(player_ids)} players...")
        fetched = 0
        for pid, name in player_ids.items():
            try:
                pdata = get_individual_player_data(pid)
                parse_player_history(pdata.get('history_past', []), player_base, name, pid)
                parse_player_gw_history(pdata.get('history', []), player_base, name, pid)
                fetched += 1
                if fetched % 100 == 0:
                    print(f"[Pipeline]   → Fetched {fetched}/{len(player_ids)} players...")
            except Exception as e:
                print(f"[Pipeline]   Warning: Failed to fetch player {name} ({pid}): {e}")

        print(f"[Pipeline]   → Fetched {fetched}/{len(player_ids)} player histories.")

        # Collect and merge gameweek data
        if gw > 0:
            print(f"[Pipeline] Stage 2: Collecting and merging GW{gw} data...")
            collect_gw(gw, player_base, gw_base, base_filename)
            merge_gw(gw, gw_base)
            print(f"[Pipeline]   → Merged gameweek data up to GW{gw}.")

        return StageResult(
            stage='historical_ingest',
            success=True,
            duration_seconds=time.time() - stage_start,
            message=f'Fetched {fetched} player histories, merged GW{gw} data.',
        )

    except Exception as e:
        return StageResult(
            stage='historical_ingest',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Historical data rebuild failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Stage 3: Feature Matrix & Dataset Rebuild
# ---------------------------------------------------------------------------

def rebuild_dataset(
    season: str = '2026-27',
    gw: Optional[int] = None,
    data_root: str = 'data',
    skip_scrape: bool = True,
) -> StageResult:
    """Stage 3: Rebuild model_dataset.csv from rolling form, FBref, and Understat.

    Args:
        season: season string.
        gw: target gameweek (auto-detected if None).
        data_root: root data directory.
        skip_scrape: if True, skip live Understat/FBref web scraping.

    Returns:
        StageResult indicating success or failure.
    """
    stage_start = time.time()

    try:
        from model.build_dataset import build_dataset

        print(f"[Pipeline] Stage 3: Rebuilding model dataset...")
        ds = build_dataset(
            season=season,
            gw=gw,
            data_root=data_root,
            skip_scrape=skip_scrape,
        )

        player_count = len(ds) if ds is not None and not ds.empty else 0
        return StageResult(
            stage='dataset_rebuild',
            success=True,
            duration_seconds=time.time() - stage_start,
            message=f'Rebuilt model_dataset.csv with {player_count} players.',
        )

    except Exception as e:
        return StageResult(
            stage='dataset_rebuild',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Dataset rebuild failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Stage 4: Quantitative Point Projections
# ---------------------------------------------------------------------------

def generate_predictions(
    season: str = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
) -> StageResult:
    """Stage 4: Generate baseline and fixture-adjusted point projections.

    Runs prediction_engine.py for baseline 11-component xP, then
    fixture_engine.py for opponent/venue-scaled projections.

    Args:
        season: season string.
        gw: target gameweek number.
        data_root: root data directory.

    Returns:
        StageResult indicating success or failure.
    """
    stage_start = time.time()

    try:
        from model.prediction_engine import predict_all_players
        from model.fixture_engine import predict_gameweek_fixtures

        print(f"[Pipeline] Stage 4: Generating baseline predictions for GW{gw}...")
        pred_df = predict_all_players(season=season, data_root=data_root)
        pred_count = len(pred_df) if pred_df is not None and not pred_df.empty else 0
        print(f"[Pipeline]   -> Baseline predictions: {pred_count} players")

        print(f"[Pipeline] Stage 4: Generating fixture-adjusted predictions for GW{gw}...")
        fix_df = predict_gameweek_fixtures(
            season=season, gw=gw, data_root=data_root, save_csv=True,
        )
        fix_count = len(fix_df) if fix_df is not None and not fix_df.empty else 0
        print(f"[Pipeline]   -> Fixture predictions: {fix_count} players")

        return StageResult(
            stage='predictions',
            success=True,
            duration_seconds=time.time() - stage_start,
            message=f'Generated predictions for {pred_count} players (baseline), {fix_count} (fixture-adjusted).',
        )

    except Exception as e:
        return StageResult(
            stage='predictions',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Prediction generation failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Stage 5: Live Matchday Solver & Export
# ---------------------------------------------------------------------------

def run_live_solver(
    season: str = '2026-27',
    gw: int = 1,
    team_id: Optional[int] = None,
    league_id: Optional[int] = None,
    bank: float = 0.0,
    free_transfers: int = 1,
    horizon: int = 3,
    strategy: str = 'pure_xp',
    data_root: str = 'data',
    export_excel: bool = True,
    export_json: bool = True,
) -> StageResult:
    """Stage 5: Run the live matchday manager with MILP solver and export artifacts.

    Args:
        season: season string.
        gw: target gameweek number.
        team_id: optional official FPL team / entry ID for 1-click sync.
        league_id: optional mini-league ID for rival threat analysis.
        bank: current bank balance in £M.
        free_transfers: available free transfers.
        horizon: multi-gameweek lookahead horizon.
        strategy: game theory strategy ('pure_xp', 'rank_protect', 'differential_chase').
        data_root: root data directory.
        export_excel: generate Excel workbook.
        export_json: generate JSON state payload.

    Returns:
        StageResult indicating success or failure.
    """
    stage_start = time.time()

    try:
        from model.live_manager import manage_gameweek

        print(f"[Pipeline] Stage 5: Running live matchday solver for GW{gw}...")
        result = manage_gameweek(
            season=season,
            gw=gw,
            team_id=team_id,
            league_id=league_id,
            bank=bank,
            free_transfers=free_transfers,
            horizon=horizon,
            strategy=strategy,
            data_root=data_root,
            export_excel=export_excel,
            export_json=export_json,
        )

        total_xp = 0.0
        if result and result.get('squad_solution'):
            total_xp = result['squad_solution'].total_xp

        msg_extra = f" (Team ID: {team_id})" if team_id else ""
        return StageResult(
            stage='live_solver',
            success=True,
            duration_seconds=time.time() - stage_start,
            message=f'Solver complete. Total projected xP: {total_xp:.2f}{msg_extra}',
        )

    except Exception as e:
        return StageResult(
            stage='live_solver',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Live solver failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Stage 6: Frontend Enrichment
# ---------------------------------------------------------------------------

def enrich_frontend_stage(
    season: str = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
) -> StageResult:
    """Stage 6: Enrich matchday JSON with Dixon-Coles matrices and minutes hazard."""
    stage_start = time.time()

    try:
        from model.enrich_frontend_data import enrich_matchday_json
        print(f"[Pipeline] Stage 6: Enriching matchday JSON with Dixon-Coles & minutes hazard for GW{gw}...")
        success = enrich_matchday_json(gw=gw, season=season, data_root=data_root)

        if success:
            return StageResult(
                stage='frontend_enrichment',
                success=True,
                duration_seconds=time.time() - stage_start,
                message=f'Enriched GW{gw} matchday data with Dixon-Coles matrices & minutes hazard.',
            )
        else:
            return StageResult(
                stage='frontend_enrichment',
                success=False,
                duration_seconds=time.time() - stage_start,
                message=f'Enrichment skipped or incomplete for GW{gw}.',
            )
    except Exception as e:
        return StageResult(
            stage='frontend_enrichment',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Frontend enrichment failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Stage 7 & Post-GW Calibration: Player Costs & Accuracy Evaluation
# ---------------------------------------------------------------------------

def run_accuracy_tracking_stage(
    season: str = '2026-27',
    completed_gw: int = 1,
    data_root: str = 'data',
) -> StageResult:
    """Evaluate and record model accuracy for completed gameweeks."""
    stage_start = time.time()
    try:
        from model.accuracy_tracker import evaluate_gameweek_accuracy
        print(f"[Pipeline] Post-GW Calibration: Evaluating accuracy for completed GW{completed_gw}...")
        report = evaluate_gameweek_accuracy(
            season=season,
            gw=completed_gw,
            data_root=data_root,
            save_log=True,
        )
        if report:
            return StageResult(
                stage='accuracy_tracking',
                success=True,
                duration_seconds=time.time() - stage_start,
                message=f'Evaluated GW{completed_gw}: Overall MAE {report.overall_mae:.2f} pts, Active MAE {report.active_starters_mae:.2f} pts, Rank Corr {report.rank_correlation:.3f}.',
            )
        else:
            return StageResult(
                stage='accuracy_tracking',
                success=True,
                duration_seconds=time.time() - stage_start,
                message=f'No historical prediction artifact found for completed GW{completed_gw} to evaluate.',
            )
    except Exception as e:
        return StageResult(
            stage='accuracy_tracking',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Accuracy evaluation failed: {e}',
            error=str(e),
        )


def run_player_cost_enrichment_stage(
    season: str = '2026-27',
) -> StageResult:
    """Enrich players_full.json with seasonal Opta codes, element IDs, and now_costs."""
    stage_start = time.time()
    try:
        from scripts.enrich_player_costs import enrich_player_costs
        print("[Pipeline] Enriching frontend players_full.json with latest costs and element IDs...")
        success = enrich_player_costs(season=season)
        return StageResult(
            stage='player_cost_enrichment',
            success=success,
            duration_seconds=time.time() - stage_start,
            message='Enriched players_full.json with latest market costs and Opta element IDs.' if success else 'Player cost enrichment incomplete.',
        )
    except Exception as e:
        return StageResult(
            stage='player_cost_enrichment',
            success=False,
            duration_seconds=time.time() - stage_start,
            message=f'Player cost enrichment failed: {e}',
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Master Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_live_pipeline(
    season: str = '2026-27',
    gw: Optional[int] = None,
    mode: str = 'sync',
    team_id: Optional[int] = None,
    league_id: Optional[int] = None,
    bank: float = 0.0,
    free_transfers: int = 1,
    horizon: int = 3,
    strategy: str = 'pure_xp',
    data_root: str = 'data',
    offline: bool = False,
    scrape: bool = False,
    export_excel: bool = True,
    export_json: bool = True,
) -> PipelineResult:
    """Execute end-to-end automated FPL data synchronization and model generation.

    Modes:
        'sync':             Fast daily sync — API fetch + price delta + predictions + solver.
        'full':             Complete rebuild — player histories + merged_gw + dataset + everything.
        'predictions_only': Re-run predictions and fixture engine only (no network, no solver).
        'solver_only':      Re-run MILP solver and export only (no predictions, no network).

    Args:
        season: season string (e.g. '2026-27').
        gw: target gameweek. Auto-detected if None.
        mode: execution mode ('sync', 'full', 'predictions_only', 'solver_only').
        bank: current bank balance in £M.
        free_transfers: available free transfers (1-5).
        horizon: multi-gameweek lookahead horizon (1-5).
        strategy: game theory strategy.
        data_root: root data directory.
        offline: if True, skip all network calls.
        export_excel: generate Excel workbook.
        export_json: generate JSON state payload.

    Returns:
        PipelineResult with stage-by-stage execution details.
    """
    pipeline_start = time.time()
    stages: List[StageResult] = []

    print("=" * 90)
    print(f"  FPL LIVE DATA PIPELINE — Season {season} | Mode: {mode.upper()}")
    print("=" * 90)

    # ------------------------------------------------------------------
    # Resolve gameweek
    # ------------------------------------------------------------------
    active_gw, next_gw, deadline = None, None, None

    if mode in ('sync', 'full'):
        active_gw, next_gw, deadline = detect_active_gameweek(
            season=season, data_root=data_root, offline=offline,
        )
        resolved_gw = gw or next_gw or active_gw or 1
    else:
        resolved_gw = gw or 1

    print(f"[Pipeline] Active GW: {active_gw} | Next GW: {next_gw} | Target GW: {resolved_gw} | Deadline: {deadline or 'N/A'}")
    print("-" * 90)

    # ------------------------------------------------------------------
    # Stage 1: API Sync & Price Velocity (sync + full modes)
    # ------------------------------------------------------------------
    price_alerts = 0
    if mode in ('sync', 'full'):
        # 1a. API data sync
        sync_result = sync_api_data(
            season=season, data_root=data_root, offline=offline,
        )
        stages.append(sync_result)
        if not sync_result.success:
            print(f"[Pipeline] Warning: API sync failed — {sync_result.error}")
            print("[Pipeline] Continuing with local cached data...")

        # 1b. Price velocity snapshot
        price_result = record_price_snapshot(
            season=season, data_root=data_root,
        )
        stages.append(price_result)
        price_alerts = int(price_result.message.split(', ')[-1].split(' ')[0]) if price_result.success else 0

        # 1c. Completed Gameweek Accuracy Tracking & Calibration
        completed_gw = active_gw if (active_gw and active_gw < resolved_gw) else (resolved_gw - 1 if resolved_gw > 1 else None)
        if completed_gw:
            acc_result = run_accuracy_tracking_stage(
                season=season, completed_gw=completed_gw, data_root=data_root,
            )
            stages.append(acc_result)

    # ------------------------------------------------------------------
    # Stage 2: Historical Ingest (full mode only)
    # ------------------------------------------------------------------
    if mode == 'full':
        hist_result = rebuild_historical_data(
            season=season, gw=resolved_gw, data_root=data_root,
        )
        stages.append(hist_result)
        if not hist_result.success:
            print(f"[Pipeline] Warning: Historical rebuild failed — {hist_result.error}")

    # ------------------------------------------------------------------
    # Stage 3: Dataset Rebuild (sync + full modes)
    # ------------------------------------------------------------------
    if mode in ('sync', 'full'):
        ds_result = rebuild_dataset(
            season=season, gw=resolved_gw, data_root=data_root,
            skip_scrape=not scrape,
        )
        stages.append(ds_result)
        if not ds_result.success:
            print(f"[Pipeline] Warning: Dataset rebuild failed — {ds_result.error}")

    # ------------------------------------------------------------------
    # Stage 4: Predictions (sync + full + predictions_only modes)
    # ------------------------------------------------------------------
    if mode in ('sync', 'full', 'predictions_only'):
        pred_result = generate_predictions(
            season=season, gw=resolved_gw, data_root=data_root,
        )
        stages.append(pred_result)
        if not pred_result.success:
            print(f"[Pipeline] Warning: Predictions failed — {pred_result.error}")

    # ------------------------------------------------------------------
    # Stage 5: Live Solver (sync + full + solver_only modes)
    # ------------------------------------------------------------------
    if mode in ('sync', 'full', 'solver_only'):
        solver_result = run_live_solver(
            season=season,
            gw=resolved_gw,
            team_id=team_id,
            league_id=league_id,
            bank=bank,
            free_transfers=free_transfers,
            horizon=horizon,
            strategy=strategy,
            data_root=data_root,
            export_excel=export_excel,
            export_json=export_json,
        )
        stages.append(solver_result)

    # ------------------------------------------------------------------
    # Stage 6: Frontend Enrichment (when JSON export is enabled)
    # ------------------------------------------------------------------
    if export_json and mode in ('sync', 'full', 'solver_only'):
        enrich_result = enrich_frontend_stage(
            season=season, gw=resolved_gw, data_root=data_root,
        )
        stages.append(enrich_result)

    # ------------------------------------------------------------------
    # Stage 7: Player Cost & ID Enrichment (sync + full modes)
    # ------------------------------------------------------------------
    if mode in ('sync', 'full'):
        cost_result = run_player_cost_enrichment_stage(season=season)
        stages.append(cost_result)

    # ------------------------------------------------------------------
    # Pipeline Summary
    # ------------------------------------------------------------------
    total_time = time.time() - pipeline_start
    all_success = all(s.success for s in stages)

    print("\n" + "=" * 90)
    print(f"  PIPELINE EXECUTION SUMMARY")
    print("=" * 90)
    for s in stages:
        status = "OK" if s.success else "FAIL"
        print(f"  [{status:<4}] {s.stage:<22} | {s.duration_seconds:>6.1f}s | {s.message}")
    print("-" * 90)
    print(f"  Total Duration: {total_time:.1f}s | Overall: {'SUCCESS' if all_success else 'PARTIAL FAILURE'}")
    print("=" * 90 + "\n")

    return PipelineResult(
        season=season,
        gameweek=resolved_gw,
        mode=mode,
        success=all_success,
        total_duration_seconds=total_time,
        stages=stages,
        active_gameweek=active_gw,
        next_gameweek=next_gw,
        deadline=deadline,
        price_alerts_count=price_alerts,
    )


# ---------------------------------------------------------------------------
# Daemon / Scheduler
# ---------------------------------------------------------------------------

def run_scheduler_daemon(
    season: str = '2026-27',
    interval_hours: float = 6.0,
    mode: str = 'sync',
    team_id: Optional[int] = None,
    league_id: Optional[int] = None,
    bank: float = 0.0,
    free_transfers: int = 1,
    horizon: int = 3,
    strategy: str = 'pure_xp',
    data_root: str = 'data',
    scrape: bool = False,
    max_iterations: Optional[int] = None,
) -> None:
    """Run the pipeline on a repeating schedule.

    Args:
        season: season string.
        interval_hours: hours between pipeline executions.
        mode: pipeline execution mode.
        team_id: optional official FPL team ID.
        league_id: optional mini-league ID.
        bank: bank balance.
        free_transfers: available free transfers.
        horizon: lookahead horizon.
        strategy: game theory strategy.
        data_root: root data directory.
        scrape: run live scrapers.
        max_iterations: maximum number of runs (None = infinite).
    """
    interval_seconds = interval_hours * 3600.0
    iteration = 0

    print(f"[Daemon] Starting pipeline scheduler: every {interval_hours:.1f}h | mode={mode}")
    print(f"[Daemon] Season: {season} | Strategy: {strategy}" + (f" | Team ID: {team_id}" if team_id else ""))
    if max_iterations:
        print(f"[Daemon] Max iterations: {max_iterations}")
    print()

    while True:
        iteration += 1
        if max_iterations and iteration > max_iterations:
            print(f"[Daemon] Reached max iterations ({max_iterations}). Stopping.")
            break

        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[Daemon] === Iteration {iteration} at {now} ===")

        try:
            result = run_live_pipeline(
                season=season,
                mode=mode,
                team_id=team_id,
                league_id=league_id,
                bank=bank,
                free_transfers=free_transfers,
                horizon=horizon,
                strategy=strategy,
                data_root=data_root,
                scrape=scrape,
            )
            status = 'SUCCESS' if result.success else 'PARTIAL FAILURE'
            print(f"[Daemon] Pipeline result: {status} ({result.total_duration_seconds:.1f}s)")
        except Exception as e:
            print(f"[Daemon] Pipeline error: {e}")
            traceback.print_exc()

        if max_iterations and iteration >= max_iterations:
            break

        print(f"[Daemon] Sleeping {interval_hours:.1f}h until next run...\n")
        time.sleep(interval_seconds)


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FPL Live Data Pipeline Automation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fast daily sync with team & league sync:
  python -m model.pipeline_automation --season 2026-27 --mode sync --team-id 9500404 --league-id 1305495

  # Complete post-gameweek rebuild with live scrapers:
  python -m model.pipeline_automation --season 2026-27 --mode full --scrape --team-id 9500404

  # Re-run solver only (no network, no re-prediction):
  python -m model.pipeline_automation --season 2026-27 --mode solver_only --bank 1.5 --ft 2

  # Re-run predictions only:
  python -m model.pipeline_automation --season 2026-27 --mode predictions_only --gw 2

  # Scheduled daemon (every 6 hours):
  python -m model.pipeline_automation --season 2026-27 --daemon --interval-hours 6 --team-id 9500404
        """,
    )
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=None, help="Target gameweek number (auto-detected if omitted)")
    parser.add_argument('--mode', default='sync', choices=['sync', 'full', 'predictions_only', 'solver_only'],
                        help="Pipeline execution mode")
    parser.add_argument('--team-id', type=int, default=None, help="Official FPL Entry / Team ID for 1-click live squad sync")
    parser.add_argument('--league-id', type=int, default=None, help="Mini-league ID for rival threat analysis")
    parser.add_argument('--bank', type=float, default=0.0, help="Bank balance in £M")
    parser.add_argument('--ft', type=int, default=1, help="Available free transfers (1-5)")
    parser.add_argument('--horizon', type=int, default=3, help="Lookahead horizon in gameweeks (1-5)")
    parser.add_argument('--strategy', default='pure_xp',
                        choices=['pure_xp', 'rank_protect', 'differential_chase'],
                        help="Game theory strategy")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    parser.add_argument('--offline', action='store_true', default=False,
                        help="Skip all network calls, use local cached data only")
    parser.add_argument('--scrape', action='store_true', default=False,
                        help="Run live web scrapers (FBref, Understat) during dataset rebuild")
    parser.add_argument('--daemon', action='store_true', default=False,
                        help="Run as a repeating scheduler daemon")
    parser.add_argument('--interval-hours', type=float, default=6.0,
                        help="Hours between daemon runs (default: 6)")
    parser.add_argument('--max-iterations', type=int, default=None,
                        help="Maximum daemon iterations (default: unlimited)")
    parser.add_argument('--no-excel', action='store_true', default=False,
                        help="Skip Excel workbook generation")
    parser.add_argument('--no-json', action='store_true', default=False,
                        help="Skip JSON state payload generation")

    args = parser.parse_args()

    if args.daemon:
        run_scheduler_daemon(
            season=args.season,
            interval_hours=args.interval_hours,
            mode=args.mode,
            team_id=args.team_id,
            league_id=args.league_id,
            bank=args.bank,
            free_transfers=args.ft,
            horizon=args.horizon,
            strategy=args.strategy,
            data_root=args.data_root,
            scrape=args.scrape,
            max_iterations=args.max_iterations,
        )
    else:
        run_live_pipeline(
            season=args.season,
            gw=args.gw,
            mode=args.mode,
            team_id=args.team_id,
            league_id=args.league_id,
            bank=args.bank,
            free_transfers=args.ft,
            horizon=args.horizon,
            strategy=args.strategy,
            data_root=args.data_root,
            offline=args.offline,
            scrape=args.scrape,
            export_excel=not args.no_excel,
            export_json=not args.no_json,
        )


if __name__ == '__main__':
    main()

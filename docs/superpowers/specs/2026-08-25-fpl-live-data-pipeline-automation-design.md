# Design Specification: FPL Live Data Pipeline Automation Engine

**Document Type:** Technical Architecture & Implementation Spec  
**Target Module:** `model/pipeline_automation.py`, `model/test_pipeline_automation.py`  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  
**Date:** 2026-08-25  

---

## 1. Executive Summary & Problem Statement

Currently, running the FPL predictive model requires manually executing a series of disparate scripts across the repository:
1. `global_scraper.py` (FPL REST API fetch, per-player histories)
2. `collector.py` (Gameweek aggregation into `gws/merged_gw.csv`)
3. `model/build_dataset.py` (Understat/FBref reconciliation into `model_dataset.csv`)
4. `model/prediction_engine.py` (11 scoring components computation)
5. `model/fixture_engine.py` (Conjugate venue scaling and opponent difficulty)
6. `model/live_manager.py` (Live injury dampening, MILP solver, Excel & JSON generation)

This manual sequence is prone to user friction, stale data, omitted steps, and execution errors.

### The Solution
The **Live Data Pipeline Automation Engine (`model/pipeline_automation.py`)** provides a **unified, multi-stage orchestration system** that:
- Detects the current active and upcoming gameweek automatically from the FPL API.
- Supports both **Fast Sync** (lightweight API + price delta + live solver run) and **Full Rebuild** (per-player historical pull + `merged_gw.csv` + dataset rebuild).
- Continuously tracks **Daily Net Transfer Velocity ($\Delta T$)** to alert on imminent price rises/falls before 01:30 UTC price changes.
- Automatically generates all matchday artifacts (`fixture_predictions.csv`, `fpl_matchday_live_gw<GW>.json`, `fpl_matchday_live_gw<GW>.xlsx`).
- Provides daemon/scheduler capabilities for autonomous pre-deadline and post-gameweek execution.

---

## 2. System Architecture & Pipeline Stages

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             FPL LIVE DATA PIPELINE AUTOMATION ENGINE                             │
├───────────────────┬───────────────────┬───────────────────┬───────────────────┬──────────────────┤
│ Stage 1:          │ Stage 2:          │ Stage 3:          │ Stage 4:          │ Stage 5:         │
│ API Sync &        │ Historical Ingest │ Feature Matrix &  │ Quantitative      │ Matchday Solver  │
│ Price Velocity    │ & Aggregation     │ Dataset Rebuild   │ xP Projections    │ & Export Engine  │
├───────────────────┼───────────────────┼───────────────────┼───────────────────┼──────────────────┤
│ • Bootstrap-Static│ • Player History  │ • collector.py    │ • 11 Components   │ • MILP Solver    │
│ • Fixtures API    │   Pull (Full Mode)│ • build_dataset   │ • Fixture Engine  │ • Captaincy & XI │
│ • Delta Velocity  │ • gws/gw*.csv     │ • Rolling Form    │ • Set-Pieces & PKs│ • Excel & JSON   │
│ • Price Alerts    │   Assembly        │ • Understat Merge │ • Matchup & Hazard│ • Web State Broadcast
└───────────────────┴───────────────────┴───────────────────┴───────────────────┴──────────────────┘
```

### Stage 1: API Sync & Price Velocity Tracker
- Fetches `bootstrap-static` and `fixtures` via official FPL endpoints (with fallback to cached local files when offline/testing).
- Extracts `current_gw`, `next_gw`, and deadline countdown timestamp.
- Updates `players_raw.csv`, `teams.csv`, `fixtures.csv`, `player_idlist.csv`, and `cleaned_players.csv`.
- Computes daily net transfer delta against stored historical snapshots in `data/<season>/price_history/` to trigger `RISING_LOCK`, `RISING_ALERT`, `FALLING_ALERT`, and `FALLING_LOCK` flags.

### Stage 2: Historical Ingest & Aggregation (`mode='full'`)
- Pulls per-player match records for active Premier League players.
- Invokes `collect_gw()` and `merge_gw()` to regenerate `data/<season>/gws/merged_gw.csv`.

### Stage 3: Feature Matrix & Dataset Rebuild
- Re-runs `model/build_dataset.py` to align Opta IDs, Understat expected metrics, FBref start/substitute frequencies, and dual-window rolling form.
- Writes validated `data/<season>/model_dataset.csv`.

### Stage 4: Quantitative Point Projections
- Invokes `model/prediction_engine.py` to calculate baseline 11-component point projections with Empirical Bayes prior shrinkage ($M_0 = 500.0$ mins) and discrete Poisson goals conceded deductions.
- Invokes `model/fixture_engine.py` to apply conjugate venue scaling, opponent difficulty multipliers, and DGW/BGW adjustments, saving `fixture_predictions.csv` and `fixture_predictions_gw<GW>.csv`.

### Stage 5: Live Matchday Solver & Multi-Channel Export
- Runs `model/live_manager.py` with multi-horizon lookahead (3–5 GWs), applying live status dampening (`'i'`, `'s'`, `'u'`, `'d'`), set-piece equities, matchup bonuses, and rotation hazard decays.
- Formulates and solves MILP starting XI, captaincy, and bench auto-sub priority.
- Writes formatted executive Excel workbook (`fpl_matchday_live_gw<GW>.xlsx`) and JSON state payload (`fpl_matchday_live_gw<GW>.json`).

---

## 3. Module Interface & CLI Specification

### Function Interface (`model/pipeline_automation.py`)

```python
def run_live_pipeline(
    season: str = "2026-27",
    gw: Optional[int] = None,
    mode: str = "sync",  # 'sync' | 'full' | 'predictions_only' | 'solver_only'
    bank: float = 0.0,
    free_transfers: int = 1,
    horizon: int = 3,
    strategy: str = "pure_xp",
    data_root: str = "data",
    offline: bool = False,
    export_excel: bool = True,
    export_json: bool = True,
) -> PipelineResult:
    """Execute end-to-end automated FPL data synchronization and model generation."""
```

### CLI Command Options

```bash
# 1. Fast Daily Sync (API + price velocity + live predictions + solver run):
python -m model.pipeline_automation --season 2026-27 --mode sync

# 2. Complete Post-Gameweek Rebuild (Player history + merged_gw + full dataset + predictions + solver):
python -m model.pipeline_automation --season 2026-27 --mode full

# 3. Solver & Export Only (Re-run tactical optimization without network fetching):
python -m model.pipeline_automation --season 2026-27 --mode solver_only --bank 1.5 --ft 2 --strategy rank_protect

# 4. Scheduled Autonomous Runner (Periodic background sync):
python -m model.pipeline_automation --season 2026-27 --daemon --interval-hours 6
```

---

## 4. Testing & Verification Plan

1. **Unit Tests (`model/test_pipeline_automation.py`)**:
   - `test_gameweek_detection`: Verifies automatic resolution of active and upcoming gameweek IDs from API events.
   - `test_price_velocity_snapshotting`: Verifies daily transfer delta tracking and alert generation.
   - `test_pipeline_sync_mode`: Verifies execution of sync mode with mock or cached API responses.
   - `test_pipeline_solver_only_mode`: Verifies local offline re-execution of predictions and solver without network calls.
   - `test_pipeline_error_recovery`: Verifies that pipeline handles partial network failures gracefully and falls back to existing local data.
2. **End-to-End Live Verification**:
   - Run `python -m model.pipeline_automation --season 2026-27 --mode sync` on real 2026-27 data.
   - Validate that `fixture_predictions_gw2.csv`, `fpl_matchday_live_gw2.json`, and `fpl_matchday_live_gw2.xlsx` are refreshed and consistent.
   - Verify 0 regressions across existing 134 unit tests.

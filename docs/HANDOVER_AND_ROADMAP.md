# FPL Analytics Platform: Handover & Roadmap Document

**Document Version:** 1.0.0  
**Status:** COMPLETED & READY FOR LIVE GW2 & FRONTEND DEVELOPMENT  
**Date:** 2026-08-25  

---

## 1. Executive Summary & Current Repository State

The Fantasy Premier League points-prediction model has been rebuilt from its legacy Excel roots into an **enterprise-grade, modular, fully-tested Python analytics and optimization ecosystem (`model/`)**.

### System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   END-TO-END FPL ANALYTICS ECOSYSTEM                             │
├─────────────────┬──────────────────┬──────────────────┬─────────────────────┬────────────────────┤
│ Phase 1:        │ Phase 2:         │ Phase 3:         │ Phase 4:            │ Phase 5:           │
│ Data Pipeline   │ Point-Prediction │ Fixture Engine   │ Squad Optimization  │ Multi-Tab Export   │
├─────────────────┼──────────────────┼──────────────────┼─────────────────────┼────────────────────┤
│ • rolling_form  │ • 11 Scoring     │ • 6-GW Rate      │ • solver.py (MILP)  │ • openpyxl Engine  │
│ • build_dataset │   Components     │   Blending       │ • Multi-GW Horizon  │ • 5 Themed Sheets  │
│ • FBref Starts  │ • Empirical      │ • Conjugate      │   (3-5 GWs)         │ • Dashboard, Pitch,│
│   & Understat   │   Bayes Shrink   │   Venue Scaling  │ • Chip Optimizer    │   Predictions,     │
│ • Minutes       │ • Exact Poisson  │ • DGW Fatigue    │ • Live Manager &    │   Fixtures, Stats  │
│   Proration     │   GC Penalty     │   Dampening      │   Injury Filtering  │ • Dynamic Formulas │
└─────────────────┴──────────────────┴──────────────────┴─────────────────────┴────────────────────┘
```

### Verified Test Suite Status
* **90 out of 90 unit tests passing** across `pytest`:
  * `test_prediction_engine.py` (25 tests): 11 components, Empirical Bayes shrinkage, Poisson clean sheets, discrete GC penalty, cold-start priors.
  * `test_solver.py` (13 tests): 15-man quotas, formation constraints, captaincy, bench priority, FPL 50% profit selling price, chips.
  * `test_fixture_engine.py` (12 tests): Form blending, venue conjugate factors ($1.08 / 0.9259$), GK save scaling, bonus scaling, DGW dampening.
  * `test_rolling_form.py` (13 tests): Dual-window rolling form, Understat xG/xA merging, calendar gameweek windowing.
  * `test_excel_exporter.py` (4 tests): 5 sheets creation, KPI cards, optimal squad formulas, predictions ranking.
  * `test_multi_horizon.py` (2 tests): Multi-GW lookahead, squad continuity, temporal discounting ($\gamma = 0.90$).
  * `test_chip_optimizer.py` (2 tests): DGW/BGW detection and seasonal chip roadmap.
  * `test_live_manager.py` (2 tests): Live matchday manager execution and injury dampening.
  * Standalone & scraper tests (17 tests).

---

## 2. Gameweek 2 Matchday Refresh Playbook

Since you missed the Gameweek 1 deadline, you have the strategic advantage of entering **Gameweek 2 with a clean slate**:
* **Fresh Squad Selection**: Select your full 15-man squad for Gameweek 2 within the full £100.0M starting budget with **0 transfer hit penalties**.
* **Live GW1 Match Intelligence**: The model incorporates live GW1 actuals, starting lineups, and tactical roles across all 20 Premier League clubs.

### Quick Refresh Commands for Gameweek 2

```powershell
# 1. Generate live matchday decision briefing and 3-gameweek lookahead for GW2:
python -m model.live_manager --season 2026-27 --gw 2 --horizon 3 --bank 0.0 --ft 1

# 2. Re-export formatted multi-tab Excel workbook for Gameweek 2:
python -m model.excel_exporter --season 2026-27 --gw 2 --budget 100.0

# 3. Check strategic chip opportunities across upcoming rounds:
python -m model.chip_optimizer --season 2026-27 --gw 2
```

### Generated Artifacts
* Excel Workbook: `data/2026-27/fpl_matchday_live_gw2.xlsx`
* JSON State Payload: `data/2026-27/fpl_matchday_live_gw2.json`

---

## 3. Elite Best Practices Roadmap (Top-1k FPL Strategies)

To elevate the engine from strong heuristic optimization to **elite top-1k decision-making**, we will integrate these five advanced dimensions:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ELITE FPL STRATEGIC ADVANTAGES (ROADMAP)                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Effective Ownership (EO) & Game Theory Engine:                                      │
│    • Tracks player ownership in top 10k vs overall to calculate Effective Ownership.  │
│    • Risk-Adjusted xP Formula: Balances high-floor rank protection on 150%+ EO         │
│      talismans (e.g. Haaland/Salah) vs high-upside differentials (<10% EO).           │
│                                                                                        │
│ 2. Price Change & Team Value Forecaster:                                               │
│    • Monitors daily net transfer balance velocity to predict +£0.1M rises and -£0.1M   │
│      falls before they occur.                                                          │
│    • Builds squad purchasing power from £100.0M to £103M–£105M by mid-season.          │
│                                                                                        │
│ 3. Set-Piece & Penalty Specialist Hierarchy:                                           │
│    • Explicit database of designated penalty takers (PK), direct free-kick specialists │
│      (FK), and corner crossers (CK) to award baseline goal/assist expectation.         │
│                                                                                        │
│ 4. Manager Press Conference & Rotation Intelligence:                                   │
│    • Models tactical rotation risks (Pep roulette, post-Champions League minutes       │
│      management, 60th-minute substitution vulnerability).                              │
│                                                                                        │
│ 5. Fixture Swing Clustering:                                                           │
│    • Multi-period transfer clustering targeting 4-to-6 gameweek fixture green runs     │
│      around international break pivot windows.                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Frontend Web Dashboard Architecture Blueprint

In our next session, we will build a **modern, high-performance web dashboard** that turns this backend analytics engine into your personal **FPL Command Cockpit**.

### Technology Stack
* **Framework**: React / Next.js or Vite.
* **Styling**: Vanilla CSS / Tailwind CSS with custom design tokens, dark mode, glassmorphism, and smooth micro-animations.
* **State & Data**: Consumes `fpl_matchday_live_gw<GW>.json` and Python REST/CLI endpoints.

### The 5 Core Views

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         FPL COMMAND COCKPIT — 5 CORE VIEWS                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ View 1: 🏟️ Tactical Pitch & Lineup Visualizer                                          │
│   • Glassmorphic 2D/3D pitch displaying player cards with photos/jerseys.              │
│   • Live expected points badges, opponent FDR indicators, and [C] / [V] badges.       │
│   • Interactive drag-and-drop substitutions with real-time xP and formation update.   │
│                                                                                        │
│ View 2: 🔄 Multi-Horizon Transfer Workbench                                            │
│   • 3-GW and 5-GW interactive transfer planner.                                       │
│   • Player search with price, position, and club filters.                              │
│   • Instant bank calculation, 50% profit retention selling price, and hit warnings.   │
│                                                                                        │
│ View 3: 🗺️ 38-Gameweek Fixture Difficulty Heatmap                                      │
│   • Color-coded matrix of all 20 teams across GW1–GW38.                                │
│   • Sortable by easiest upcoming attacking and defensive runs (3, 5, 8 GWs).           │
│                                                                                        │
│ View 4: 🔬 11-Component Player Deconstruction Explorer                                 │
│   • Interactive stacked bar and radar charts showing xP breakdown:                     │
│     C1-C2 (Mins), C3 (Saves), C6 (Bonus), C7 (xA), C8 (xG), C9 (CS), C11 (DC).        │
│                                                                                        │
│ View 5: ⚡ Live Action & Chip Control Center                                           │
│   • One-click pipeline refresh button.                                                 │
│   • Live injury & news alert banners.                                                  │
│   • Seasonal chip deployment timeline (3xC, BB, FH, WC1, WC2).                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Handover Summary: What I Understand & How I Will Help You

### What I Understand
1. **The Journey**: We rebuilt your legacy Excel system into a hardened, mathematically rigorous Python platform with 90 passing tests, multi-horizon lookahead, chip optimization, and live matchday management.
2. **Current Situation**: You missed GW1, which gives you a clean £100.0M slate to launch in **Gameweek 2** with real GW1 data.
3. **The Next Goal**: Transitioning smoothly into live Gameweek 2 management, layering in elite FPL manager advantages (EO, price changes, set-piece tiers), and creating a **stunning, interactive Web Dashboard**.

### How I Will Partner With You in the Next Session
1. **Gameweek 2 Squad Lock-In**:
   - Ingest live GW1 data, evaluate injury updates, run the multi-horizon solver, and lock in your optimal GW2 starting 15.
2. **Layering Elite Features**:
   - Add Effective Ownership (EO) tracking and penalty/set-piece hierarchy modules.
3. **Frontend Dashboard Construction**:
   - Scaffold and build the full web application with the tactical pitch, transfer workbench, fixture heatmap, and 11-component explorer.

*The codebase is in a stable, verified, and complete state. When you are ready for the next session, simply prompt me to proceed!*

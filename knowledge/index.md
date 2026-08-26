---
okf_version: "0.2"
---

# FPL Analytics Platform Knowledge Catalog

Welcome to the **Open Knowledge Format (OKF v0.2)** knowledge catalog for the Fantasy Premier League (FPL) analytics platform, points-prediction engine, and historical data repository.

This catalog provides human- and agent-friendly structured documentation, data schemas, mathematical specifications, and executable contracts across the codebase.

---

## 1. System Architecture

High-level design, data flow diagrams, daemon orchestration, and automated pipelines:

* [End-to-End Data Flow](/architecture/end-to-end-data-flow.md) - The 5-stage data processing graph from raw scraping to model predictions and UI cockpit.
* [Pipeline Automation & Daemons](/architecture/pipeline-automation.md) - Continuous execution loop, cron scheduling, and matchday live polling.

---

## 2. Datasets & Schemas

Canonical schemas, column definitions, data types, and join keys:

* [Players Raw Overview (`players_raw.csv`)](/datasets/players-raw.md) - Bootstrap-static player metadata, prices, positions, and current form.
* [Merged Gameweek History (`merged_gw.csv`)](/datasets/merged-gw.md) - Multi-season granular match-by-match performance metrics per player.
* [Model Training & Inference Dataset (`model_dataset.csv`)](/datasets/model-dataset.md) - Engineered feature matrix combining FPL, Understat (xG/xA), and FBref (starts/subs).
* [Baseline Predictions (`predictions.csv`)](/datasets/predictions.md) - Expected points breakdown across all 11 scoring components ($C_1 \dots C_{11}$).
* [Fixture-Adjusted Predictions (`fixture_predictions.csv`)](/datasets/fixture-predictions.md) - Predictions scaled by venue symmetry, opponent difficulty, form blending, and DGW factors.
* [Teams & Fixture Schedules (`teams.csv`, `fixtures.csv`)](/datasets/teams-and-fixtures.md) - Club attack/defense strength ratings and scheduled gameweek matchups.
* [Matchday Live State (`fpl_matchday_live_gw*.json`)](/datasets/matchday-live-state.md) - Real-time matchday state schema for live points, substitutions, and minutes.

---

## 3. Mathematical Models & Analytics

Mathematical formulas, statistical distributions, Empirical Bayes shrinkage, and MILP optimization:

* [Point-Prediction Engine](/models/point-prediction-engine.md) - 11 scoring components, Poisson clean sheet/goals conceded models, and Empirical Bayes shrinkage ($M_0 = 500$).
* [Fixture & Form Adjustment Engine](/models/fixture-and-form-engine.md) - 6-GW sample-size form blending, conjugate venue factors ($1.08 / 0.9259$), and promoted priors.
* [Squad Optimization Solver](/models/squad-optimization-solver.md) - Multi-gameweek lookahead Mixed-Integer Linear Programming (MILP) solver with 50% profit selling price mechanics and CVaR risk tuning.
* [Minutes & Playing Probability Model](/models/minutes-model.md) - Starter proration, active ratio modeling, and substitution cameo calculations.
* [Match Simulator & Rank Distribution](/models/match-simulator.md) - Monte Carlo matchday simulation for ceiling/floor outcomes and rank distributions.
* [Effective Ownership & Game Theory Engine](/models/ownership-engine.md) - Top-10k ownership modeling and rank protection mechanics.
* [Price Change Forecaster](/models/price-predictor.md) - Net transfer momentum forecasting for price rises and falls.
* [Set-Piece Specialist Hierarchies](/models/set-pieces.md) - Penalties, direct free-kicks, and corner taker priority modeling.
* [Live Auto-Substitutions & Captaincy Rollover](/models/auto-sub-and-captaincy.md) - Formation-safe bench auto-substitution engine and vice-captain promotion rules.

---

## 4. Attested Computations

Sanctioned execution contracts, parameters, and deterministic receipt attesters:

* [Build Modeling Dataset](/computations/build-dataset.md) - Attested computation contract for `model/build_dataset.py`.
* [Predict Player Points](/computations/predict-points.md) - Attested computation contract for `model/prediction_engine.py`.
* [Adjust Fixtures & Form](/computations/adjust-fixtures.md) - Attested computation contract for `model/fixture_engine.py`.
* [Solve Optimal Squad](/computations/solve-squad.md) - Attested computation contract for `model/solver.py`.
* [Optimize Strategic Chips](/computations/optimize-chips.md) - Attested computation contract for `model/chip_optimizer.py`.
* [Simulate Gameweek Matches](/computations/simulate-matches.md) - Attested computation contract for `model/match_simulator.py`.
* [Export Multi-Tab Excel Workbook](/computations/export-excel.md) - Attested computation contract for `model/excel_exporter.py`.
* [Sync Live Matchday Gameweek](/computations/sync-live-gameweek.md) - Attested computation contract for `model/live_sync.py`.

---

## 5. Scrapers & Ingestion Pipelines

Data extraction pipelines, API clients, and external source scrapers:

* [FPL API Pipeline](/scrapers/fpl-api-pipeline.md) - Scrapers for bootstrap-static, fixtures, and per-player history (`global_scraper.py`, `collector.py`, `getters.py`, `parsers.py`).
* [Understat xG Scraper](/scrapers/understat-scraper.md) - Understat team/player xG and ID matching engine (`understat.py`).
* [FBref Match Log Scraper](/scrapers/fbref-scraper.md) - FBref player match logs, starts, and substitution extraction (`fbref.py`).

---

## 6. Operational Playbooks

Standard Operating Procedures (SOPs) for maintenance and matchday execution:

* [Weekly Gameweek Transition Workflow](/playbooks/weekly-gameweek-workflow.md) - End-to-end operational guide from pre-deadline team selection to live tracking and post-GW rollover.
* [Troubleshooting Data Drift & ID Reconciliation](/playbooks/troubleshooting-data-drift.md) - Diagnosing and resolving missing player IDs, unmapped FBref names, and schema shifts.

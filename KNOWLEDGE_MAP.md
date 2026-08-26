# Repository Knowledge Map & Cross-Reference Matrix

This matrix provides instant bidirectional cross-referencing between source code modules, output datasets, mathematical specifications, test suites, and OKF concept documents.

---

## 1. End-to-End Analytics & Prediction Engine Matrix

| Subsystem | Source Code | Output Dataset / Schema | OKF Concept Specification | Unit Test File | Primary CLI Command |
|---|---|---|---|---|---|
| **Data Ingestion** | [`global_scraper.py`](file:///e:/Fantasy-Premier-League/global_scraper.py), [`collector.py`](file:///e:/Fantasy-Premier-League/collector.py) | [`data/<season>/players_raw.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/players-raw.md), [`gws/merged_gw.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/merged-gw.md) | [`scrapers/fpl-api-pipeline.md`](file:///e:/Fantasy-Premier-League/knowledge/scrapers/fpl-api-pipeline.md) | [`test_global_scraper.py`](file:///e:/Fantasy-Premier-League/test_global_scraper.py) | `python global_scraper.py` |
| **Understat xG** | [`understat.py`](file:///e:/Fantasy-Premier-League/understat.py) | Understat player/team match logs | [`scrapers/understat-scraper.md`](file:///e:/Fantasy-Premier-League/knowledge/scrapers/understat-scraper.md) | [`model/test_understat.py`](file:///e:/Fantasy-Premier-League/model/test_understat.py) | `python understat.py` |
| **FBref Lineups** | [`fbref.py`](file:///e:/Fantasy-Premier-League/fbref.py) | FBref team starts & sub logs | [`scrapers/fbref-scraper.md`](file:///e:/Fantasy-Premier-League/knowledge/scrapers/fbref-scraper.md) | [`model/test_build_dataset.py`](file:///e:/Fantasy-Premier-League/model/test_build_dataset.py) | `python fbref.py` |
| **Dataset Builder** | [`model/build_dataset.py`](file:///e:/Fantasy-Premier-League/model/build_dataset.py) | [`data/<season>/model_dataset.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/model-dataset.md) | [`computations/build-dataset.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/build-dataset.md) | [`model/test_build_dataset.py`](file:///e:/Fantasy-Premier-League/model/test_build_dataset.py), [`model/test_rolling_form.py`](file:///e:/Fantasy-Premier-League/model/test_rolling_form.py) | `python -m model.build_dataset --season 2026-27` |
| **Point Engine (11 Components)** | [`model/prediction_engine.py`](file:///e:/Fantasy-Premier-League/model/prediction_engine.py) | [`data/<season>/predictions.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/predictions.md) | [`models/point-prediction-engine.md`](file:///e:/Fantasy-Premier-League/knowledge/models/point-prediction-engine.md), [`computations/predict-points.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/predict-points.md) | [`model/test_prediction_engine.py`](file:///e:/Fantasy-Premier-League/model/test_prediction_engine.py) | `python -m model.prediction_engine --season 2026-27` |
| **Fixture Engine** | [`model/fixture_engine.py`](file:///e:/Fantasy-Premier-League/model/fixture_engine.py) | [`data/<season>/fixture_predictions.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/fixture-predictions.md) | [`models/fixture-and-form-engine.md`](file:///e:/Fantasy-Premier-League/knowledge/models/fixture-and-form-engine.md), [`computations/adjust-fixtures.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/adjust-fixtures.md) | [`model/test_fixture_engine.py`](file:///e:/Fantasy-Premier-League/model/test_fixture_engine.py) | `python -m model.fixture_engine --season 2026-27 --gw 2` |
| **MILP Squad Solver** | [`model/solver.py`](file:///e:/Fantasy-Premier-League/model/solver.py) | Optimal 15-man squad, starting XI, transfers, Captain | [`models/squad-optimization-solver.md`](file:///e:/Fantasy-Premier-League/knowledge/models/squad-optimization-solver.md), [`computations/solve-squad.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/solve-squad.md) | [`model/test_solver.py`](file:///e:/Fantasy-Premier-League/model/test_solver.py), [`model/test_solver_cvar.py`](file:///e:/Fantasy-Premier-League/model/test_solver_cvar.py), [`model/test_multi_horizon.py`](file:///e:/Fantasy-Premier-League/model/test_multi_horizon.py) | `python -m model.solver --season 2026-27 --gw 2 --budget 100.0 --horizon 3` |
| **Chip Optimizer** | [`model/chip_optimizer.py`](file:///e:/Fantasy-Premier-League/model/chip_optimizer.py) | Seasonal chip roadmap (BB, TC, FH, WC) | [`computations/optimize-chips.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/optimize-chips.md) | [`model/test_chip_optimizer.py`](file:///e:/Fantasy-Premier-League/model/test_chip_optimizer.py) | `python -m model.chip_optimizer --season 2026-27 --gw 2` |
| **Match Simulator** | [`model/match_simulator.py`](file:///e:/Fantasy-Premier-League/model/match_simulator.py) | 10,000 Monte Carlo match simulations, p10/p50/p90 percentiles | [`models/match-simulator.md`](file:///e:/Fantasy-Premier-League/knowledge/models/match-simulator.md), [`computations/simulate-matches.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/simulate-matches.md) | [`model/test_match_simulator.py`](file:///e:/Fantasy-Premier-League/model/test_match_simulator.py) | `python -m model.match_simulator --season 2026-27 --gw 2` |
| **Excel Exporter** | [`model/excel_exporter.py`](file:///e:/Fantasy-Premier-League/model/excel_exporter.py) | [`data/<season>/fpl_matchday_live_gw*.xlsx`](file:///e:/Fantasy-Premier-League/knowledge/computations/export-excel.md) | [`computations/export-excel.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/export-excel.md) | [`model/test_excel_exporter.py`](file:///e:/Fantasy-Premier-League/model/test_excel_exporter.py) | `python -m model.excel_exporter --season 2026-27 --gw 2 --budget 100.0` |
| **Live Matchday Sync** | [`model/live_sync.py`](file:///e:/Fantasy-Premier-League/model/live_sync.py), [`model/live_manager.py`](file:///e:/Fantasy-Premier-League/model/live_manager.py) | [`data/<season>/fpl_matchday_live_gw*.json`](file:///e:/Fantasy-Premier-League/knowledge/datasets/matchday-live-state.md) | [`architecture/pipeline-automation.md`](file:///e:/Fantasy-Premier-League/knowledge/architecture/pipeline-automation.md), [`computations/sync-live-gameweek.md`](file:///e:/Fantasy-Premier-League/knowledge/computations/sync-live-gameweek.md) | [`model/test_live_sync.py`](file:///e:/Fantasy-Premier-League/model/test_live_sync.py), [`model/test_live_manager.py`](file:///e:/Fantasy-Premier-League/model/test_live_manager.py) | `python -m model.live_sync --season 2026-27 --gw 2 --poll 60` |
| **Automation Daemon** | [`model/pipeline_automation.py`](file:///e:/Fantasy-Premier-League/model/pipeline_automation.py) | Automated daily refresh and matchday scheduling | [`architecture/pipeline-automation.md`](file:///e:/Fantasy-Premier-League/knowledge/architecture/pipeline-automation.md) | [`model/test_pipeline_automation.py`](file:///e:/Fantasy-Premier-League/model/test_pipeline_automation.py) | `python -m model.pipeline_automation --season 2026-27 --gw 2` |

---

## 2. Mathematical Invariant Quick-Reference

* **Empirical Bayes Shrinkage**: $M_0 = 500.0\text{ mins}$ towards positional priors (FWD $0.35$, MID $0.15$, DEF $0.05$, GK $0.00$).
* **Exact Discrete Poisson $GC \ge 2$ Penalty**: $-\sum_{m=1}^5 m (P(2m) + P(2m+1))$.
* **Conjugate Venue Factors**: $1.08 \longleftrightarrow 0.9259$ ($\mathbb{E}[\text{Scored}] \equiv \mathbb{E}[\text{Conceded}]$).
* **FPL 50% Profit Retention Rule**: $\text{selling} = \text{purchase} + \lfloor (\text{current} - \text{purchase})/2 \rfloor$.
* **Lookahead Temporal Discount**: $\gamma = 0.90$ across horizon $H = 3 \dots 5$.

---

## 3. Verification & Conformance Commands

* **OKF v0.2 Bundle Linter**: `python scripts/validate_okf.py`
* **Schema Invariant Attester**: `python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2`
* **Solver Invariant Attester**: `python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2`
* **Unit Test Regression Suite**: `pytest`

# Architecture & Codebase Boundaries

This document defines the strict 3-tier boundary of the repository to prevent architectural confusion between active production engines, historical archives, and legacy one-offs.

---

## 1. Tier 1: Active Core Production Pipeline (Primary Execution Engine)

This is the **only** tier that should be used for ongoing predictions, solver optimizations, live matchday data feeds, and frontend components.

| Module / Path | Role & Responsibility | Interface Pattern |
| :--- | :--- | :--- |
| [`model/prediction_engine.py`](file:///e:/Fantasy-Premier-League/model/prediction_engine.py) | 11-Component Point Prediction Model ($C_1 \dots C_{11}$) | `predict_player_points(player_dict)` |
| [`model/fixture_engine.py`](file:///e:/Fantasy-Premier-League/model/fixture_engine.py) | Dixon-Coles Poisson Goals & Away Defcon Engine | `compute_fixture_multipliers(home, away)` |
| [`model/solver.py`](file:///e:/Fantasy-Premier-League/model/solver.py) | PuLP MILP 15-Man Squad & Multi-Horizon Lookahead Solver | `solve_initial_squad(...)`, `solve_weekly_transfers(...)` |
| [`model/minutes_model.py`](file:///e:/Fantasy-Premier-League/model/minutes_model.py) | Continuous Minutes Survival Hazard & Hook Hazard Model | `compute_player_minutes_hazard(...)` |
| [`model/rotation_intelligence.py`](file:///e:/Fantasy-Premier-League/model/rotation_intelligence.py) | Midweek European Congestion & Press News Dampening | `compute_news_dampening(...)` |
| [`model/set_pieces.py`](file:///e:/Fantasy-Premier-League/model/set_pieces.py) | Team-Specific Penalty Frequencies & Set-Piece Hierarchy | `compute_set_piece_equity(...)` |
| [`model/accuracy_tracker.py`](file:///e:/Fantasy-Premier-League/model/accuracy_tracker.py) | Post-Gameweek Calibration & Accuracy Metric Logger | `evaluate_gameweek_accuracy(...)` |
| [`model/pipeline_automation.py`](file:///e:/Fantasy-Premier-League/model/pipeline_automation.py) | End-to-End Daily / Weekly Pipeline Orchestrator | CLI entry point |
| [`data/2026-27/`](file:///e:/Fantasy-Premier-League/data/2026-27/) | Active Season Dataset (`players_raw.csv`, live matchday JSONs) | Single Source of Truth for 2026-27 |
| [`frontend/`](file:///e:/Fantasy-Premier-League/frontend/) | React + Vite Production Matchday Cockpit (Vercel Deployed) | User Interface & Client-Side Solver |
| [`knowledge/`](file:///e:/Fantasy-Premier-League/knowledge/) | Open Knowledge Format (OKF v0.2) Specifications | Mathematical & Schema Source of Truth |
| [`.github/workflows/`](file:///e:/Fantasy-Premier-League/.github/workflows/) | Daily (06:00 UTC) & Friday Post-Press (16:00 UTC) Actions | Cloud Automation |

---

## 2. Tier 2: Historical Archives & Backtest Datasets (Read-Only)

These files are used strictly for model backtesting, historical validation, and machine learning training:

| Path | Purpose | Constraint |
| :--- | :--- | :--- |
| [`data/2025-26/`](file:///e:/Fantasy-Premier-League/data/2025-26/) | Complete 38-GW historical season dataset | Read-only for `model/backtester.py` validation |
| `data/2016-17/` to `data/2024-25/` | Multi-season historical training data | Read-only historical archive |
| [`reference/original_excel/`](file:///e:/Fantasy-Premier-League/reference/original_excel/) | Original Excel spreadsheets and mathematical prototypes | Preserved reference archive |

---

## 3. Tier 3: Extinct / Legacy Scrapers (Quarantined)

These files originated from the 2016–2020 `vaastav/Fantasy-Premier-League` public dataset scraper era. They are preserved in [`archive/legacy_scrapers_2016_2020/`](file:///e:/Fantasy-Premier-League/archive/legacy_scrapers_2016_2020/) and **must never be imported or executed by the points-prediction engine**:

* `analysis/analyze.py` (2018 SQLite combination search)
* `deprecated_script.py`, `schedule.py`, `gameweek.py`
* `top_managers.py`, `top_players.py`, `world_cup26_data.py`
* `aggregated_points_goals.py`, `global_merger.py`, `utility.py`, `new_position_checker.py`
* `team_4582_data18_19/`, `lateriser_report_1920.pdf`, `magnus_report_1920.pdf`, `vaastav_report_1920.pdf`

---

## 4. Operational Guardrails

1. **Never read legacy files for active gameweek predictions**: Always query `data/2026-27/players_raw.csv` and `data/2026-27/fixtures.csv`.
2. **Never import from `archive/`**: All algorithmic modules reside inside `model/`.
3. **Always validate with OKF**: Run `python scripts/validate_okf.py` whenever documentation or mathematical formulas are modified.

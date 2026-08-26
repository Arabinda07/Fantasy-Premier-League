# Attested Computations Catalog

This section defines the sanctioned execution contracts, parameters, CLI recipes, receipts, and deterministic attestation checkers for all executable modules across the analytics platform.

## Contracts

* [Build Modeling Dataset (`build_dataset.py`)](/computations/build-dataset.md) - Generates `model_dataset.csv` from raw FPL, Understat, and FBref data.
* [Predict Player Points (`prediction_engine.py`)](/computations/predict-points.md) - Computes baseline points ($xP$) and the 11 component breakdowns into `predictions.csv`.
* [Adjust Fixtures & Form (`fixture_engine.py`)](/computations/adjust-fixtures.md) - Applies venue multipliers and opponent ratings to output `fixture_predictions.csv`.
* [Solve Optimal Squad (`solver.py`)](/computations/solve-squad.md) - MILP optimization for 15-man squad, starting XI, captaincy, and transfers.
* [Optimize Strategic Chips (`chip_optimizer.py`)](/computations/optimize-chips.md) - Solves seasonal chip deployment roadmap (BB, TC, FH, WC).
* [Simulate Gameweek Matches (`match_simulator.py`)](/computations/simulate-matches.md) - Runs 10,000 Monte Carlo match simulations for ceiling/floor rank percentiles.
* [Export Multi-Tab Excel Workbook (`excel_exporter.py`)](/computations/export-excel.md) - Generates professional `.xlsx` workbooks with dashboards and pitch visuals.
* [Sync Live Matchday Gameweek (`live_sync.py`)](/computations/sync-live-gameweek.md) - Live polling daemon for real-time points, BPS, and auto-subs.

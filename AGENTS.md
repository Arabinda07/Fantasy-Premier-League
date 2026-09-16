# AGENTS.md

Instructions for coding agents working in this repository.

## System Architecture & Codebase Tiers
This repository houses two coexisting systems governed by the ratified [Project Constitution](file:///e:/Fantasy-Premier-League/CONSTITUTION.md):
1. **Tier 1 — FPL Dugout Production Engine**:
   - [`model/`](file:///e:/Fantasy-Premier-League/model/): 11-component point-prediction engine ($C_1 \dots C_{11}$), Bayesian shrinkage, fixture modeling, and MILP squad solver.
   - [`frontend/`](file:///e:/Fantasy-Premier-League/frontend/): React + Vite matchday cockpit and interactive workbench.
   - [`knowledge/`](file:///e:/Fantasy-Premier-League/knowledge/): Open Knowledge Format (OKF v0.2) specifications, dataset schemas, and computation contracts.
2. **Tier 2 & 3 — Archives & Legacy Scrapers (Quarantined)**:
   - Root scripts (`collector.py`, `global_scraper.py`, `getters.py`, `parsers.py`, `teams_scraper.py`): Historical data collectors. Do not refactor or modernize unless explicitly tasked.
   - [`positions.py`](file:///e:/Fantasy-Premier-League/positions.py): The single source of truth for `element_type` mapping (`'1' -> 'GK'`). Import from here; never redeclare.
   - `data/2016-17/` through `data/2025-26/`: Read-only backtesting vaults. Active runs consume only `data/2026-27/`.

## Context On-Demand (Read When Applicable)
Do not read all project documentation upfront. Consult relevant reference documents contextually based on the area you are touching:
- **Schema changes or data pipelines**: Consult verified schemas in [`knowledge/datasets/`](file:///e:/Fantasy-Premier-League/knowledge/datasets/index.md) (`players_raw.md`, `merged_gw.md`, `model-dataset.md`, `predictions.md`, `fixture-predictions.md`).
- **Statistical models or solver invariants**: Consult [`knowledge/models/`](file:///e:/Fantasy-Premier-League/knowledge/models/index.md) (empirical Bayes $M_0=500$, Poisson clean sheet formulations, conjugate venue symmetry, FPL 50% profit retention formula).
- **Frontend UI components or styling**: Consult [`DESIGN.md`](file:///e:/Fantasy-Premier-League/DESIGN.md) for surface scopes, tokenized CSS variables, and the repeatable component catalog.
- **Copy, tooltips, chip advice, or error states**: Consult [`docs/voice-and-tone-guide.md`](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md) and import shared tokens from [`frontend/src/constants/copyTokens.js`](file:///e:/Fantasy-Premier-League/frontend/src/constants/copyTokens.js). Ban corporate jargon and raw math names.

## Autonomy, Permissions & Definition of Done
You are fully authorized to run safe local verification commands, inspect the output, and fix failures without seeking approval at every intermediate step:
- **Python / Model tasks**: Run `pytest` or targeted tests (`pytest model/test_<feature>.py`).
- **Frontend changes**: Run `npm run check-copy` and `npm run build` (inside `frontend/`).
- **Knowledge / Spec changes**: Run `python scripts/validate_okf.py`.

**Definition of Done**: A task is complete only when the implementation is in place, relevant local verification passes, and any regressions caused by your changes have been resolved. Do not stop halfway after writing code if verification has not been performed.

## Engineering Standards

### 1. Model Code (`model/`)
- Mandatory type annotations on all new functions.
- Docstrings for non-trivial formulas or branching logic.
- Unit tests (`pytest`) covering non-trivial math, edge cases, or data transformations.
- Prefer `pandas` for multi-season tabular datasets.

### 2. Frontend Code (`frontend/`)
- Strict compliance with [`DESIGN.md`](file:///e:/Fantasy-Premier-League/DESIGN.md): reuse existing CSS custom properties and surface scopes (`.surface-scope-*`).
- Typography: Use `--font-mono` (`JetBrains Mono`, `font-feature-settings: 'tnum' 1`) for all telemetry, predictions, and metrics; use `--font-sans` (`Plus Jakarta Sans`) for interface chrome.
- Reciprocal Registration: When creating a new repeatable UI component or variant, document it in [`DESIGN.md`](file:///e:/Fantasy-Premier-League/DESIGN.md) and register it in [`frontend/src/components/ComponentStudio.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/ComponentStudio.jsx) in the same change.
- Never introduce hardcoded hex colors or arbitrary bubble pills.

### 3. Legacy Scrapers & Root Scripts
- Surgical changes only. Respect existing style without introducing wildcard imports or unilateral refactoring.

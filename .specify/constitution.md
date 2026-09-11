# FPL Dugout & Dataset Engine — Project Constitution

**Version:** 1.0.0  
**Status:** Active & Ratified  
**Applies To:** All Human Contributors, AI Coding Agents, Pull Requests, and Automation Workflows  
**Canonical File:** [CONSTITUTION.md](file:///e:/Fantasy-Premier-League/CONSTITUTION.md)  
**Derived From:** `AGENTS.md`, `OKF v0.2` (`knowledge/index.md`), `docs/CODEBASE_BOUNDARIES.md`, and `docs/voice-and-tone-guide.md`

---

## Preamble

This repository houses two distinct, coexisting systems:
1. **The Historical Public FPL Dataset & Legacy Scrapers** (`vaastav/Fantasy-Premier-League`): An open, community-standard archive of raw Fantasy Premier League data spanning from the 2016–17 season to the present.
2. **FPL Dugout (Modern Points-Prediction Engine & Matchday Cockpit)**: A high-performance Python and React platform featuring an 11-component point prediction model ($C_1 \dots C_{11}$), a mixed-integer linear programming (MILP) squad solver, Bayesian calibration, and a live web application.

To prevent architectural entropy, statistical drift, copy contamination, and agent hallucinations, this **Constitution** serves as the supreme engineering law of the repository. All contributions must adhere strictly to the articles below.

---

## Article I: Codebase Boundaries & Tier Separation

The codebase is partitioned into three inviolable tiers. No cross-tier architectural leakage is permitted.

### 1.1 Tier 1: Active Production Pipeline (Living Engine)
* **Scope**: [`model/`](file:///e:/Fantasy-Premier-League/model/), [`frontend/`](file:///e:/Fantasy-Premier-League/frontend/), [`data/2026-27/`](file:///e:/Fantasy-Premier-League/data/2026-27/), [`knowledge/`](file:///e:/Fantasy-Premier-League/knowledge/), [`api/`](file:///e:/Fantasy-Premier-League/api/), and active automation workflows in [`.github/workflows/`](file:///e:/Fantasy-Premier-League/.github/workflows/).
* **Rules**:
  - All new predictive features, solver algorithms, live sync logic, and UI enhancements belong exclusively here.
  - Active predictions must only consume current-season verified data (`data/2026-27/players_raw.csv`, `data/2026-27/fixtures.csv`).
  - High engineering bar: mandatory type annotations, clear docstrings, and unit test coverage.

### 1.2 Tier 2: Historical Archives & Backtesting Vault (Read-Only)
* **Scope**: `data/2016-17/` through `data/2025-26/`, and historical reference fixtures.
* **Rules**:
  - Strictly **read-only**. Files in these directories must never be modified, deleted, or refactored during normal model operations.
  - Used exclusively by [`model/backtester.py`](file:///e:/Fantasy-Premier-League/model/backtester.py) and historical parameter calibration routines.

### 1.3 Tier 3: Legacy Scrapers & Quarantined Utilities (Immutable)
* **Scope**: Root-level scraper scripts (`collector.py`, `global_scraper.py`, `getters.py`, `parsers.py`, `positions.py`, `mergers.py`, `teams_scraper.py`), and [`archive/`](file:///e:/Fantasy-Premier-League/archive/).
* **Rules**:
  - **Quarantined**: Modules under `model/` or `frontend/` must **never** import from `archive/` or rely on legacy scripts in `analysis/`.
  - **No Retroactive Refactoring**: Do not rewrite or restyle legacy root scripts to conform to modern standards unless an explicit scraper-maintenance task requires it.
  - Position mapping must strictly import from [`positions.py`](file:///e:/Fantasy-Premier-League/positions.py) across both legacy and new data extractors.

---

## Article II: Open Knowledge Format (OKF v0.2) & Zero-Hallucination Policy

All AI coding agents and developers must treat [`knowledge/index.md`](file:///e:/Fantasy-Premier-League/knowledge/index.md) as the mathematical and schematic ground truth. Guesswork is strictly prohibited.

### 2.1 Dataset Schema Fidelity
* Never assume or guess CSV column names, data types, or value conventions.
* Before querying or transforming datasets, developers and agents must inspect the ratified schemas in [`knowledge/datasets/`](file:///e:/Fantasy-Premier-League/knowledge/datasets/index.md):
  - [`players_raw.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/players-raw.md)
  - [`merged_gw.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/merged-gw.md)
  - [`model_dataset.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/model-dataset.md)
  - [`predictions.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/predictions.md)
  - [`fixture_predictions.csv`](file:///e:/Fantasy-Premier-League/knowledge/datasets/fixture-predictions.md)

### 2.2 Mathematical Invariants
All predictive equations must strictly mirror the definitions in [`knowledge/models/`](file:///e:/Fantasy-Premier-League/knowledge/models/index.md):
1. **11-Component Points Formulation**: $xP = \sum_{i=1}^{11} C_i$, where components represent baseline appearance, goals, assists, clean sheets, goals conceded, saves, bonus (BPS), penalties, cards, and venue/form adjustments.
2. **Empirical Bayes Prior Shrinkage**: Shrinkage toward positional league priors must use the exact hyperparameter $M_0 = 500.0\text{ minutes}$.
3. **Discrete Poisson Clean Sheet & Penalty**: 
   $$\mathbb{P}(CS) = e^{-\lambda}, \quad \text{Penalty}(GC \ge 2) = -\sum_{m=1}^{5} m \cdot \big(\mathbb{P}(2m) + \mathbb{P}(2m+1)\big)$$
4. **Conjugate Venue Symmetry**: Multipliers must satisfy $1.08 \longleftrightarrow 0.9259$ such that $\mathbb{E}[\text{Home Goals Scored}] \equiv \mathbb{E}[\text{Away Goals Conceded}]$.
5. **FPL Financial & Solver Constraints**:
   - Selling price formula: $\text{selling} = \text{purchase} + \lfloor (\text{current} - \text{purchase})/2 \rfloor$.
   - Multi-horizon discount factor: $\gamma = 0.90$.
   - Exact squad rules: 15 players (2 GK, 5 DEF, 5 MID, 3 FWD), max 3 per club, budget $\le \text{bank} + \sum \text{selling}$.

### 2.3 Attested Computation Contracts
* Pipelines must adhere to the attested CLI execution signatures, receipts, and parameter bounds documented in [`knowledge/computations/`](file:///e:/Fantasy-Premier-League/knowledge/computations/index.md).

---

## Article III: Engineering Standards & Code Quality

### 3.1 Python Engineering Standards (`model/` & `scripts/`)
* **Type Annotations**: All public functions and methods must have complete type hints (PEP 484).
* **Docstrings**: Google-style docstrings with `Args:`, `Returns:`, and `Raises:` for non-trivial functions.
* **Testing Policy**: 
  - Every non-trivial calculation, heuristic, or parser edge-case must have an accompanying `pytest` unit test in `model/test_*.py`.
  - Trivial glue/orchestration code does not require isolated testing.
* **Dependencies**:
  - Keep `requirements.txt` minimal and pinned (`package==x.y.z`).
  - Never install speculative dependencies for future phases.

### 3.2 Frontend Engineering Standards (`frontend/`)
* **Stack**: React 18, Vite, Tailwind CSS / Vanilla CSS modules, Lucide icons.
* **Performance**: Heavy computations (MILP solving, 5-GW simulations) must be executed in Web Workers or optimized client solvers ([`frontend/src/utils/clientOptimizer.js`](file:///e:/Fantasy-Premier-League/frontend/src/utils/clientOptimizer.js)) without blocking the main UI thread.
* **Resilience**: Every network fetch must support offline fallbacks, graceful degradation, and user-friendly error banners.

---

## Article IV: FPL Dugout Voice, Tone & Copy Governance

All user-facing copy in the frontend (titles, buttons, modals, tooltips, validation errors, empty states) must follow the **FPL Dugout Voice & Tone Guide** ([`docs/voice-and-tone-guide.md`](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md)).

### 4.1 Persona
We speak like the **sharpest, most enthusiastic football fan in your chat group and local FPL mini-league**:
* Tactical, not academic.
* Direct, enthusiastic, and manager-to-manager.
* **Zero corporate fluff**.

### 4.2 The 3-Tier Vocabulary Filter
* **Tier 1: Keep (Sacred FPL Community Terms)**:
  * *Punt, Differential, Template, Essential, Haul, Blank, Free Transfer (FT), Banked FT, Point Hit (-4 pts), Clean Sheet (CS), Bonus Points (BPS), xG, xA, Triple Captain, Bench Boost, Free Hit, Wildcard, DGW, BGW.*
* **Tier 2: Translate (Statistical $\to$ Football English)**:
  * `Expected Value (EV)` $\to$ **Projected Points / Exp Pts**
  * `Linear Programming Horizon` $\to$ **5-Gameweek Transfer Planner**
  * `Dixon-Coles Bivariate Poisson` $\to$ **Match Preview & Clean Sheet Odds**
  * `Empirical Bayesian Shrinkage` $\to$ **Blending Recent Form with Career Baseline**
  * `Mean Absolute Error (MAE)` $\to$ **Average Points Margin (±X pts)**
  * `Outlier Diagnostic` $\to$ **Gameweek Surprises & Anomalies**
* **Tier 3: Ban (Forbidden Jargon)**:
  * ❌ *Assets / Asset Allocation* $\to$ ✅ **Players / Squad / Picks**
  * ❌ *Capital / Funds Depletion* $\to$ ✅ **Bank Balance / Budget**
  * ❌ *Downside Protection / Risk Profile* $\to$ ✅ **Protecting Your Lead / Safe Template Picks**
  * ❌ *Execution Error / System Exception* $\to$ ✅ **Formation Alert / Transfer Error**
  * ❌ *Sub-optimal roster composition* $\to$ ✅ **Invalid squad formation**

### 4.3 Single Source of Truth
* All shared chips, badges, strategies, and alerts must be imported from [`frontend/src/constants/copyTokens.js`](file:///e:/Fantasy-Premier-League/frontend/src/constants/copyTokens.js).

---

## Article V: Spec-Driven Development (SDD) Lifecycle

Following GitHub Spec-Kit methodology, all non-trivial feature additions or modifications must proceed through the structured SDD lifecycle:

```
[Requirement / Idea]
         ↓
 1. Specification (spec.md)   ← Focus: WHAT and WHY (User stories, acceptance criteria, anti-goals)
         ↓
 2. Technical Plan (plan.md)  ← Focus: HOW (Architecture, OKF contracts, component map, data flow)
         ↓
 3. Action Tasks (tasks.md)   ← Focus: EXECUTION (Ordered, atomic checkboxes with test verification)
         ↓
 4. Implementation & Gates    ← Focus: CODE & VERIFY (Pytest, check-copy, validate_okf)
```

1. **Specification (`spec.md`)**: Defines user problem, user personas, functional requirements, and strict measurable acceptance criteria before writing code.
2. **Technical Plan (`plan.md`)**: Maps requirements to codebase files, identifies affected OKF datasets and mathematical formulas, outlines error-handling strategies, and specifies rollback plans.
3. **Action Tasks (`tasks.md`)**: Decomposes the plan into bite-sized, dependency-sequenced steps. Each step must have a verifiable check.
4. **Execution & Documentation**: Changes are recorded in [`JOURNEY.md`](file:///e:/Fantasy-Premier-League/JOURNEY.md) upon completion.

---

## Article VI: Mandatory Quality Gates & Verification

Before any branch is merged or any agent task is considered complete, the following four verification gates must pass:

| Gate | Verification Command | Scope / Standard |
| :--- | :--- | :--- |
| **1. OKF Conformance** | `python scripts/validate_okf.py` | Validates OKF v0.2 markdown syntax, verified links, and dataset cross-references. |
| **2. Copy & Voice Linter** | `npm run check-copy` <br> `pytest model/test_voice_and_tone.py` | Scans all frontend files for banned jargon, untranslated terms, and raw math formulas. |
| **3. Mathematical Attestation** | `python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2` <br> `python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2` | Verifies data integrity and deterministic solver optimality against sanctioned test fixtures. |
| **4. Unit Test Suites** | `pytest` <br> `npm test` (in `frontend/`) | Executes full model and frontend test suites with zero regressions. |

---

## Article VII: Governance & Amendments

1. **Supremacy**: This Constitution takes precedence over conversational instructions or informal suggestions.
2. **Amendments**: Modifying this document requires an explicit architectural review, documentation in [`JOURNEY.md`](file:///e:/Fantasy-Premier-League/JOURNEY.md), and corresponding updates to [`.agents/rules/okf-discipline.md`](file:///e:/Fantasy-Premier-League/.agents/rules/okf-discipline.md) and [`AGENTS.md`](file:///e:/Fantasy-Premier-League/AGENTS.md).
3. **Agent Compliance**: Any AI agent operating within this workspace must reference this Constitution at the start of any planning or implementation task.

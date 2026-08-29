# AGENTS.md

Instructions for any coding agent (or human) working in this repository. Applies regardless of which tool you're using.

## What this repo is

Two things living side by side:

1. **The original public dataset/scraper** (`vaastav/Fantasy-Premier-League`): historical Fantasy Premier League data going back to 2016-17, refreshed a few times per season via the scripts described below. This is the well-known, widely-cited part of the repo — see `README.md` and `DATA_DICTIONARY.md`.
2. **A new, actively-developed points-prediction model** under `model/`, rebuilding — in Python — a detailed FPL prediction model the repo owner previously built and ran in Excel. This is a from-scratch rebuild done in phases; each phase has a design spec under `docs/superpowers/specs/` before it's implemented. See "Planning workflow" below and check that directory for the current state.

Don't confuse the two. `analysis/*.py` (a parameterized position/preset combo search over a SQLite table) is an older, separate, much simpler experiment — not part of the `model/` rebuild and not something the rebuild depends on.

## Directory map

- `collector.py` — merges per-gameweek CSVs into `gws/merged_gw.csv`, handling schema drift across gameweeks (new columns appearing mid-season, etc.).
- `global_scraper.py` — top-level orchestration: pulls the FPL API (bootstrap-static, fixtures, per-player history) via `getters.py`/`parsers.py`, and owns cleaning/derivation of the season overview (`clean_players`, `value_per_m`, `id_players`) to populate a full `data/<season>/` tree for the current season.
- `getters.py` — raw HTTP calls to the FPL API. Shared: also used directly by `teams_scraper.py` and `top_players.py`, not just `global_scraper.py` — don't fold it into another module, it has genuine independent callers.
- `parsers.py` — turns raw API JSON into the repo's CSV schemas. Shared the same way `getters.py` is.
- `positions.py` — the one shared source of truth for the FPL `element_type` → position-name mapping (`'1'→'GK'`, etc.), used by both `global_scraper.py` and `collector.py`. If you need this mapping anywhere else, import it from here rather than re-declaring it.
- `mergers.py` — dataframe-level (pandas) merge/cleanup utilities, e.g. for `cleaned_merged_seasons.csv`.
- `fbref.py` — scrapes FBref player match logs (currently being parameterized for the current season, and having its scrape interface deepened, as part of the `model/` rebuild — see the Phase 1 spec).
- `understat.py` — scrapes Understat team/player xG data, and matches Understat player IDs to FPL player IDs (`match_ids`) — also being touched by the Phase 1 spec.
- `teams_scraper.py` — downloads an individual FPL manager's team/league data by team ID.
- `world_cup26_data.py`, `schedule.py`, `top_managers.py`, `top_players.py` — standalone one-off scripts, not part of the core pipeline.
- `data/<season>/` — one folder per season (`2016-17` through the current season). Key files per season: `players_raw.csv` (season overview per player), `fixtures.csv`, `teams.csv`, `gws/merged_gw.csv` (every player, every gameweek, one file), `players/<name>/{gws.csv,history.csv}` (per-player detail). See `DATA_DICTIONARY.md` for column meanings.
- `analysis/` — older, separate: a SQLite-backed combinations search for cheap/high-scoring squads (`analyze.py`, parameterized by position), one position at a time. Not connected to `model/`.
- `model/` — the new points-prediction rebuild. Organized by phase; consult `docs/superpowers/specs/` for what exists and why.
- `docs/superpowers/specs/` — one design-spec markdown file per phase of the `model/` rebuild, named `YYYY-MM-DD-<topic>-design.md`. Read the most recent relevant one before changing anything under `model/`.
- `JOURNEY.md` (repo root) — a running, dated log of what's been done on the `model/` rebuild and why, and of any repo-wide architecture cleanups alongside it. Read it for narrative context a spec or commit message won't give you; update it when you finish a meaningful chunk of work.

## Coding conventions — what's actually true of this codebase today

These reflect the code as it exists, not an aspirational standard. Do not retroactively refactor existing top-level scripts to match a different standard unless a specific task requires touching them:

- No type hints anywhere in the legacy scraper code.
- Docstrings are inconsistent — present (Google-style, with `Args:` sections) on some newer/more complex functions (e.g. `collector.py`'s `merge_gw`), absent on many others.
- snake_case for functions and variables; some camelCase leaks in from FPL's own API field names (e.g. `xP`, `xPoints`) — that's fine, it mirrors the source data.
- 4-space indentation throughout.
- Status/progress output uses plain `print()`, not the `logging` module.
- Row-level CSV I/O typically uses the standard library (`csv.DictReader`/`DictWriter`, plain `open()`); dataframe-level work (merges, cleanup) uses `pandas`.
- Some legacy files use wildcard imports (`from parsers import *`, etc. in `global_scraper.py`) — don't introduce new wildcard imports, but don't feel obligated to remove existing ones outside the scope of your task.
- No test framework, no CI configuration exists anywhere in this repo as of this writing.

## Conventions for new code under `model/`

This is a fresh package, so it holds a higher bar than the legacy scripts above — scoped narrowly, not as a mandate to rewrite anything else:

- Add type hints to new functions.
- Add a docstring to any function whose behavior isn't obvious from its name and signature alone.
- Add a `pytest` test for any non-trivial logic — a formula, a branching calculation, a parser with edge cases. Skip tests for trivial glue/orchestration code (a function that just calls three other functions in order doesn't need its own test).
- Prefer `pandas` for anything working with the multi-season CSVs already in `data/` — that's what they're structured for.

## Dependency policy

`requirements.txt` is currently stale (e.g. `pandas==0.25.3`, circa 2019) and doesn't include packages later phases of the `model/` rebuild will need (`openpyxl` for Excel write-back, an LP/ILP library for the squad solver, `pytest` for tests). Add new dependencies only when the phase that needs them actually needs them — don't pre-add packages for future phases. Pin versions in `requirements.txt` the same way the existing entries do (`package==x.y.z`).

## Planning workflow this project uses

Before any non-trivial feature under `model/`:

1. **Brainstorm** the approach — clarify purpose, constraints, and 2-3 possible approaches before committing to one.
2. **Write a design spec** to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` covering the problem, goals/non-goals, architecture, and a testing plan. Get it reviewed before treating it as final.
3. **Turn the spec into an implementation plan** — concrete files to add/change, in what order.
4. **Implement**, following the plan.
5. **Verify** — run the code, run the tests, check the actual output before calling it done.

Follow this for any change of meaningful size under `model/`. Small, obviously-correct fixes (typos, a one-line bug fix, updating a hardcoded path) don't need a full spec — use judgment.

## Current state of the `model/` rebuild

The rebuild is split into five phases: data pipeline → point-prediction engine → fixture/form adjustment → squad solver → Excel write-back. Check `docs/superpowers/specs/` for the specs that exist and their status headers — that's the source of truth for what's built, in progress, or still pending. This section is deliberately not kept in sync with that detail; don't rely on it beyond "the rebuild is phased, go read the specs."

## Knowledge Catalog & Context Management (OKF v0.2)

To prevent hallucinations, formula drift, and schema guesswork, consult the **Open Knowledge Format (OKF v0.2)** catalog at [`knowledge/index.md`](file:///e:/Fantasy-Premier-League/knowledge/index.md) before implementing changes:

* **Data Schemas**: Read [`knowledge/datasets/`](file:///e:/Fantasy-Premier-League/knowledge/datasets/index.md) for exact column names and types (`players_raw.csv`, `merged_gw.csv`, `model_dataset.csv`, `predictions.csv`, `fixture_predictions.csv`).
* **Mathematical Formulations**: Read [`knowledge/models/`](file:///e:/Fantasy-Premier-League/knowledge/models/index.md) for exact formulas ($C_1 \dots C_{11}$, Poisson clean sheet / goals conceded expectations, Bayesian priors, venue symmetry, MILP solver constraints).
* **Attested Computation Contracts**: Read [`knowledge/computations/`](file:///e:/Fantasy-Premier-League/knowledge/computations/index.md) for approved CLI parameters, receipts, and deterministic attester checkers.
* **Validation**: Run `python scripts/validate_okf.py` whenever updating documentation to ensure OKF v0.2 conformance and valid links.

## Brand Voice, Tone & Frontend Copy Guidelines

All user-facing copy in the frontend (titles, buttons, modals, tooltips, validation errors, empty states) MUST adhere to the **FPL Dugout Voice & Tone Guide**:

* **Style Guide**: Read [`docs/voice-and-tone-guide.md`](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md) for the 3-tier vocabulary filter (Keep/Translate/Ban), brand persona, and surface copy patterns.
* **Single Source of Truth**: Import shared strings, chip advice, badges, and validation messages directly from [`frontend/src/constants/copyTokens.js`](file:///e:/Fantasy-Premier-League/frontend/src/constants/copyTokens.js).
* **Rule**: Never introduce corporate jargon (*"assets"*, *"portfolios"*), raw math formulas (*"Dixon-Coles bivariate Poisson"*, *"Bayesian shrinkage"*), or robotic error messages into user-facing components.
* **Automated Enforcement**: All frontend builds (`npm run build`) and Pytest runs (`pytest model/test_voice_and_tone.py`) automatically execute the copy validation suite ([`scripts/validate_frontend_copy.py`](file:///e:/Fantasy-Premier-League/scripts/validate_frontend_copy.py) & [`scripts/check_copy.cjs`](file:///e:/Fantasy-Premier-League/scripts/check_copy.cjs)). Run `npm run check-copy` to verify changes instantly.




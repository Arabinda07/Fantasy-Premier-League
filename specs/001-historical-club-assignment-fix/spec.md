# Feature Specification: Historical Campaign Club Assignment Fix

**Feature ID:** `001-historical-club-assignment-fix`  
**Status:** `Completed`  
**Author:** Antigravity (AI Assistant)  
**Created:** 2026-09-11  
**Architectural Tier:** `Tier 2: Historical Archives & Backtesting Vault` (Compiler & Vault UI)  
**Target Delivery:** Immediate Hotfix  

---

## 1. Executive Summary & Problem Statement

### 1.1 Problem Statement
In the **Historical Vault** (10 Seasons Archive, `frontend/src/components/HistoricalVault.jsx`), several historical Premier League campaigns display players assigned to completely incorrect clubs on the tactical pitch, bench, and All-Time Hall of Fame:
- **2018–19 Season**: All Liverpool players (Alisson, Robertson, van Dijk, Alexander-Arnold, Salah, Mané) are labeled as **Middlesbrough** (Middlesbrough was not even in the Premier League in 2018–19). Eden Hazard is labeled as **Everton** (played for Chelsea), Raheem Sterling and Sergio Agüero are labeled as **Southampton** (played for Manchester City), and Gylfi Sigurdsson is labeled as **Leicester** (played for Everton).
- **2017–18 Season**: Mohamed Salah is labeled as **Manchester City**, Raheem Sterling as **Manchester United**, Romelu Lukaku as **Middlesbrough**, and Eden Hazard as **Crystal Palace**.

### 1.2 Root Cause
In [`scripts/compile_pl_history.py`](file:///e:/Fantasy-Premier-League/scripts/compile_pl_history.py), the compiler looks for `teams.csv` in each season directory (`data/<season>/teams.csv`). While modern seasons (`2019-20` through `2026-27`) contain `teams.csv`, the three earliest seasons (**`2016-17`**, **`2017-18`**, and **`2018-19`**) do not.

When `teams.csv` is missing, `compile_pl_history.py` falls back to `HISTORICAL_TEAM_CODES`, a single hardcoded dictionary that represents **only the 2016–17 alphabetical team IDs**. Because promoted and relegated clubs shift the alphabetical $1 \dots 20$ team IDs every year, team IDs in 2017–18 and 2018–19 were mapped to the wrong clubs, corrupting [`data/pl_history.db`](file:///e:/Fantasy-Premier-League/data/pl_history.db) and [`frontend/src/data/historical_vault.json`](file:///e:/Fantasy-Premier-League/frontend/src/data/historical_vault.json).

### 1.3 Proposed Solution
1. Generate verified `teams.csv` files for `2016-17`, `2017-18`, and `2018-19` matching official FPL team IDs and permanent global `team_code`s.
2. Upgrade [`scripts/compile_pl_history.py`](file:///e:/Fantasy-Premier-League/scripts/compile_pl_history.py) with a resilient multi-season resolver that maps via `teams.csv` and falls back to FPL's permanent global `team_code` table.
3. Add an automated export routine in `compile_pl_history.py` to refresh [`frontend/src/data/historical_vault.json`](file:///e:/Fantasy-Premier-League/frontend/src/data/historical_vault.json) in lockstep with the database.
4. Add unit test assertions in [`tests/test_compile_pl_history.py`](file:///e:/Fantasy-Premier-League/tests/test_compile_pl_history.py) to prevent future regressions.

---

## 2. User Personas & User Stories

### 2.1 Target Personas
- **The FPL Historian / Mini-League Manager**: Explores 10 seasons of Dream Teams and records to analyze historic tactical trends and benchmark active squads against all-time greats.

### 2.2 User Stories
- **US-1**: As an FPL manager viewing the 2018–19 Dream Team, I want to see Alisson, Robertson, van Dijk, Alexander-Arnold, Salah, and Mané accurately badged under **Liverpool**, so that tactical retrospectives and club filters are completely accurate.
- **US-2**: As an FPL manager inspecting the 2017–18 Dream Team, I want to see Salah badged as **Liverpool**, Sterling as **Man City**, and Hazard as **Chelsea**, so that all-time scoring records reflect true club history.
- **US-3**: As an engineer, I want `compile_pl_history.py` to automatically update `historical_vault.json` whenever the SQLite database is recompiled, so that data drift between the database and the frontend is permanently eliminated.

---

## 3. Functional Requirements

- **FR-1**: Synthesize canonical `teams.csv` files for seasons `2016-17`, `2017-18`, and `2018-19` containing columns: `id,code,name,short_name`.
- **FR-2**: In `scripts/compile_pl_history.py`, resolve team names first from season `teams.csv`, second from season `raw.json` (if present), and third via FPL's permanent global `team_code` table (`14` $\to$ Liverpool, `8` $\to$ Chelsea, `43` $\to$ Man City, `1` $\to$ Man Utd, `3` $\to$ Arsenal, etc.).
- **FR-3**: Recompile `data/pl_history.db` so that all rows in `players_seasons` and `season_dream_teams` have correct `team_name`s.
- **FR-4**: Export the refreshed dataset into `frontend/src/data/historical_vault.json` (updating `seasons`, `dream_teams`, `hall_of_fame_points`, and `hall_of_fame_goals`).
- **FR-5**: Add unit test coverage in `tests/test_compile_pl_history.py` asserting exact club verification for key historic players across 2016–17, 2017–18, and 2018–19.

---

## 4. Acceptance Criteria

- [ ] **AC-1**: `data/2016-17/teams.csv`, `data/2017-18/teams.csv`, and `data/2018-19/teams.csv` exist and contain verified club definitions.
- [ ] **AC-2**: Querying `season_dream_teams` in `data/pl_history.db` returns:
  - 2018–19: Salah = Liverpool, Hazard = Chelsea, Sterling = Man City, Agüero = Man City, Alisson = Liverpool.
  - 2017–18: Salah = Liverpool, Sterling = Man City, Hazard = Chelsea, De Bruyne = Man City.
- [ ] **AC-3**: `frontend/src/data/historical_vault.json` contains 0 instances of Middlesbrough in 2017–18 or 2018–19 Dream Teams or Hall of Fame.
- [ ] **AC-4**: `pytest tests/test_compile_pl_history.py` passes with 100% success.
- [ ] **AC-5 (Constitutional Gates)**: All 4 quality gates pass (`validate_okf.py`, `check-copy`, attesters, frontend build).

---

## 5. Anti-Goals & Out of Scope

- **Anti-Goal 1**: Will not alter points, minutes, goals, or financial cost data from historical seasons.
- **Anti-Goal 2**: Will not touch modern prediction models ($C_1 \dots C_{11}$) or live matchday state in `data/2026-27/`.

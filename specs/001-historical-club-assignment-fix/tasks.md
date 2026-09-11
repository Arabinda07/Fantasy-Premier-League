# Implementation Tasks: Historical Club Assignment Fix

**Feature ID:** `001-historical-club-assignment-fix`  
**Specification Reference:** [`spec.md`](spec.md)  
**Plan Reference:** [`plan.md`](plan.md)  
**Status:** `Completed`  
**Assigned Implementer:** AI Coding Agent / Contributor  

---

## Task Checklist & Execution Sequence

### Phase 1: Canonical Datasets & Ground Truth
- [x] **T-101**: Create canonical `data/2016-17/teams.csv` with the 20 official clubs and codes.
  - **Target**: `[NEW] data/2016-17/teams.csv`
  - **Verify**: File exists and has 20 rows + header.
- [x] **T-102**: Create canonical `data/2017-18/teams.csv` with Brighton, Huddersfield, Newcastle included.
  - **Target**: `[NEW] data/2017-18/teams.csv`
  - **Verify**: Team 10 is Liverpool, Team 11 is Man City, Team 12 is Man Utd, Team 5 is Chelsea.
- [x] **T-103**: Create canonical `data/2018-19/teams.csv` matching `data/2018-19/raw.json`.
  - **Target**: `[NEW] data/2018-19/teams.csv`
  - **Verify**: Team 12 is Liverpool, Team 6 is Chelsea, Team 13 is Man City, Team 8 is Everton, Team 20 is Wolves.

---

### Phase 2: Compiler Enhancement & Automation
- [x] **T-201**: Update `get_teams_map(season_dir)` in `scripts/compile_pl_history.py`:
  - Support `teams.csv` reading.
  - Parse `raw.json` as secondary fallback if `teams.csv` is absent.
  - Provide multi-season dictionary lookup + FPL global `team_code` fallback table.
  - **Target**: `[MODIFY] scripts/compile_pl_history.py`
  - **Verify**: Test `get_teams_map(Path('data/2018-19'))[12] == 'Liverpool'`.
- [x] **T-202**: Add `export_vault_json(conn, json_path)` to `scripts/compile_pl_history.py`:
  - Extract `seasons` summary, `dream_teams` with full player profiles (including `goals_scored`, `assists`, `clean_sheets`, `bonus`, `minutes`), `hall_of_fame_points`, and `hall_of_fame_goals`.
  - Export atomic JSON to `frontend/src/data/historical_vault.json`.
  - **Target**: `[MODIFY] scripts/compile_pl_history.py`
  - **Verify**: Script runs without errors and updates `historical_vault.json`.

---

### Phase 3: Database Recompilation & Frontend Refresh
- [x] **T-301**: Execute compiler to rebuild database and export clean vault JSON.
  - **Command**: `python scripts/compile_pl_history.py`
  - **Verify**:
    - `data/pl_history.db` recompiled.
    - Check 2018–19 Dream Team in JSON: Alisson, Robertson, van Dijk, Alexander-Arnold, Salah, Mané mapped to Liverpool.
    - Check 2017–18 Dream Team in JSON: Salah mapped to Liverpool.

---

### Phase 4: Unit Testing & Constitutional Verification Gates
- [x] **T-401**: Add regression assertions in `tests/test_compile_pl_history.py`:
  - Assert Salah (2017–18 & 2018–19) has `team_name == 'Liverpool'`.
  - Assert Hazard (2018–19) has `team_name == 'Chelsea'`.
  - Assert Sterling (2017–18 & 2018–19) has `team_name == 'Man City'`.
  - Assert no Middlesbrough in 2018–19 dream team.
  - **Target**: `[MODIFY] tests/test_compile_pl_history.py`
  - **Verify**: `pytest tests/test_compile_pl_history.py` passes 100%.
- [x] **T-402 (Gate 1 - OKF Conformance)**:
  - **Command**: `python scripts/validate_okf.py`
  - **Expected**: 0 errors.
- [x] **T-403 (Gate 2 - Copy & Voice Check)**:
  - **Command**: `npm run check-copy --prefix frontend` and `pytest model/test_voice_and_tone.py`
  - **Expected**: 0 violations.
- [x] **T-404 (Gate 3 - Mathematical Attestation)**:
  - **Command**:
    ```bash
    python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2
    python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2
    ```
  - **Expected**: Attestation successful.
- [x] **T-405 (Gate 4 - Test Suites & Build)**:
  - **Command**: `pytest` and `npm run build --prefix frontend`
  - **Expected**: All unit tests pass and Vite builds cleanly.

---

### Phase 5: Journey Documentation & Handover Sign-Off
- [x] **T-501**: Update [JOURNEY.md](file:///e:/Fantasy-Premier-League/JOURNEY.md) with narrative log of the fix.
- [x] **T-502**: Mark `spec.md`, `plan.md`, and `tasks.md` status to `Completed`.

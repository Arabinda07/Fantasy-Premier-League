---
type: Playbook
title: Troubleshooting Data Drift & ID Reconciliation
description: Diagnostic procedures for resolving unmapped player names, Understat ID sync mismatches, FBref text variations, and schema column drift.
tags: [playbook, troubleshooting, debugging, data-drift, reconciliation]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:24:00Z }
sources:
  - id: journey-log
    resource: JOURNEY.md
    title: Engineering Journey & Lessons Learned Log
---

# Playbook: Troubleshooting Data Drift & ID Reconciliation

Guide to diagnosing and resolving data discrepancies across FPL, Understat, and FBref.

---

## 1. Symptom: Player Missing from `model_dataset.csv`

### Root Cause
Player name in FBref or Understat has special Unicode characters (e.g. `Gabriel Martinelli Silva`, `Son Heung-Min`, accents) that failed exact match against FPL `first_name + ' ' + second_name`.

### Resolution Steps
1. Check [model/build_dataset.py](/computations/build-dataset.md) `normalize_name()` function.
2. Verify player exists in `data/<season>/players_raw.csv` and has a valid `code` or `element_type`.
3. Add alias mapping in `model/build_dataset.py` if name differs substantially between providers.

---

## 2. Symptom: Promoted Team Has 0 historical xG90

### Root Cause
Newly promoted Premier League clubs have 0 games in historical Premier League CSVs.

### Resolution Steps
The [Fixture Engine](/models/fixture-and-form-engine.md) automatically assigns promoted baseline priors:
* Attack: $1.050\text{ xG90}$
* Defense: $1.800\text{ xGC90}$
Ensure team names in `teams.csv` are matched to the promoted prior dictionary in `model/fixture_engine.py`.

---

## 3. Symptom: Schema Validation Failure (`verify_schema.py`)

### Root Cause
FPL API added a new column or renamed an existing field in `players_raw.csv` or `merged_gw.csv`.

### Resolution Steps
1. Run `python scripts/validate_okf.py` to identify which dataset schema is out of sync.
2. Update the corresponding schema document in [knowledge/datasets/](/datasets/index.md).
3. If new columns require feature transformation, update `model/build_dataset.py` without modifying legacy `collector.py` schemas.

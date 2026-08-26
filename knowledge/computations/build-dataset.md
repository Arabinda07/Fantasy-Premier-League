---
type: Attested Computation
title: Build Modeling Dataset Contract
description: Sanctioned execution contract to merge FPL raw data, Understat metrics, and FBref starting lineups into model_dataset.csv.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: false }
computation: model/build_dataset.py
executor:
  resource: references/skills/run_pipeline.md
  receipt: [status, row_count, output_file]
attester:
  resource: references/attesters/verify_schema.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: build-dataset-src
    resource: model/build_dataset.py
    title: Build Dataset Module
---

# Contract & Execution

The dataset builder extracts and reconciles player data from [players_raw.csv](/datasets/players-raw.md), [merged_gw.csv](/datasets/merged-gw.md), Understat, and FBref match logs.

## CLI Execution Command

```powershell
python -m model.build_dataset --season 2026-27
```

## Generated Output Receipt
* Output File: [data/2026-27/model_dataset.csv](/datasets/model-dataset.md)
* Invariants: Must contain columns `player_id`, `name`, `team`, `position`, `cost`, `xg90`, `xa90`, `p_start`, `mins_per_start`.

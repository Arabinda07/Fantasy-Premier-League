---
type: Attested Computation
title: Adjust Fixtures & Form Contract
description: Sanctioned execution contract for scaling predictions by venue factors, opponent ratings, form blending, and DGW via model/fixture_engine.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: true, default: 2 }
computation: model/fixture_engine.py
executor:
  resource: references/skills/run_pipeline.md
  receipt: [status, gw, output_file]
attester:
  resource: references/attesters/verify_schema.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: fixture-engine-src
    resource: model/fixture_engine.py
    title: Fixture Engine Subsystem
---

# Contract & Execution

Executes the [Fixture & Form Engine](/models/fixture-and-form-engine.md) over `predictions.csv`.

## CLI Execution Command

```powershell
python -m model.fixture_engine --season 2026-27 --gw 2
```

## Generated Output Receipt
* Output File: [data/2026-27/fixture_predictions.csv](/datasets/fixture-predictions.md) (or `fixture_predictions_gw2.csv`)
* Invariants: Valid opponent ratings, venue factors, `fdr`, and adjusted expected points `xP`.

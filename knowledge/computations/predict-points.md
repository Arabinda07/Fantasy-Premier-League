---
type: Attested Computation
title: Predict Player Points Contract
description: Sanctioned execution contract for computing baseline expected points and the 11 component breakdowns via model/prediction_engine.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
computation: model/prediction_engine.py
executor:
  resource: references/skills/run_pipeline.md
  receipt: [status, players_ranked, output_file]
attester:
  resource: references/attesters/verify_schema.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: pred-engine-src
    resource: model/prediction_engine.py
    title: Point Prediction Engine Subsystem
---

# Contract & Execution

Executes the [Point-Prediction Engine](/models/point-prediction-engine.md) over `model_dataset.csv`.

## CLI Execution Command

```powershell
python -m model.prediction_engine --season 2026-27
```

## Generated Output Receipt
* Output File: [data/2026-27/predictions.csv](/datasets/predictions.md)
* Invariants: Exactly 11 component columns ($C_1 \dots C_{11}$) and total `xP`.

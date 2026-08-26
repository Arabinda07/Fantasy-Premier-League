---
type: Reference
title: Run Full Modeling Pipeline Recipe
description: Execution steps for building dataset, computing predictions, and applying fixture adjustments.
tags: [reference, skill, pipeline, execution]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:25:00Z }
---

# Skill Recipe: Run Full Modeling Pipeline

Standard recipe to execute the full data scraping, dataset building, points prediction, and fixture adjustment pipeline.

## Execution Sequence

```powershell
# 1. Build master dataset from FPL, Understat, and FBref
python -m model.build_dataset --season 2026-27

# 2. Compute 11-component baseline expected points
python -m model.prediction_engine --season 2026-27

# 3. Apply opponent ratings, venue factors, and form blending for target gameweek
python -m model.fixture_engine --season 2026-27 --gw 2
```

## Verification

```powershell
python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2
```

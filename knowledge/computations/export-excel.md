---
type: Attested Computation
title: Export Multi-Tab Excel Workbook Contract
description: Sanctioned execution contract for generating themed 5-sheet Excel workbooks via model/excel_exporter.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: true, default: 2 }
  - { name: budget, type: float, required: false, default: 100.0 }
computation: model/excel_exporter.py
executor:
  resource: references/skills/run_solver.md
  receipt: [status, output_xlsx]
attester:
  resource: references/attesters/verify_schema.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: excel-exporter-src
    resource: model/excel_exporter.py
    title: Excel Exporter Subsystem
---

# Contract & Execution

Generates the professional 5-sheet workbook:
1. `Summary Dashboard`: Executive KPI cards, starting XI pitch view, ordered bench.
2. `Optimal Squad`: Detailed 15-player table with costs, FDR, expected points.
3. `GW Predictions`: Full player rankings with 11 component point breakdowns.
4. `Fixtures & Ratings`: Team attack/defense metrics and matchups.
5. `Form & Underlying Stats`: Short vs long form and Understat metrics.

## CLI Execution Command

```powershell
python -m model.excel_exporter --season 2026-27 --gw 2 --budget 100.0
```

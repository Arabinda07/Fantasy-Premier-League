---
type: Reference
title: Run Squad Optimization Solver Recipe
description: Execution steps for solving 15-man squad, starting XI, captaincy, and multi-horizon transfers.
tags: [reference, skill, solver, execution]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:25:00Z }
---

# Skill Recipe: Run Squad Optimization Solver

Standard recipe to optimize 15-man squad selection, starting XI formation, captaincy, and multi-horizon transfers.

## Execution Sequence

```powershell
# 1. Single-gameweek / Multi-gameweek optimal squad solve
python -m model.solver --season 2026-27 --gw 2 --budget 100.0 --horizon 3

# 2. Multi-tab Excel workbook generation
python -m model.excel_exporter --season 2026-27 --gw 2 --budget 100.0
```

## Verification

```powershell
python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2 --budget 100.0
```

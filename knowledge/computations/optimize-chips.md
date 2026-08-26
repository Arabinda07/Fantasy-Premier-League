---
type: Attested Computation
title: Optimize Strategic Chips Contract
description: Sanctioned execution contract for solving the seasonal roadmap for Bench Boost, Triple Captain, Free Hit, and Wildcard via model/chip_optimizer.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: true, default: 2 }
computation: model/chip_optimizer.py
executor:
  resource: references/skills/run_solver.md
  receipt: [status, chip_recommendations]
attester:
  resource: references/attesters/verify_solver.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: chip-opt-src
    resource: model/chip_optimizer.py
    title: Chip Optimizer Subsystem
---

# Contract & Execution

Identifies high-value Double and Blank Gameweeks across the season schedule and assigns optimal chip timings.

## CLI Execution Command

```powershell
python -m model.chip_optimizer --season 2026-27 --gw 2
```

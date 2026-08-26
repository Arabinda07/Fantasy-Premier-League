---
type: Attested Computation
title: Solve Optimal Squad Contract
description: Sanctioned execution contract for solving the optimal 15-man squad, starting XI, captaincy, and multi-horizon transfers via model/solver.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: true, default: 2 }
  - { name: budget, type: float, required: false, default: 100.0 }
  - { name: horizon, type: integer, required: false, default: 3 }
  - { name: chip, type: string, required: false, default: "none" }
  - { name: bank, type: float, required: false, default: 0.0 }
  - { name: ft, type: integer, required: false, default: 1 }
computation: model/solver.py
executor:
  resource: references/skills/run_solver.md
  receipt: [status, starting_xi, captain, vice_captain, bench_order, transfers_in, transfers_out, total_xp]
attester:
  resource: references/attesters/verify_solver.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: solver-src
    resource: model/solver.py
    title: Squad Solver Subsystem
---

# Contract & Execution

Executes the [Squad Optimization Solver](/models/squad-optimization-solver.md) (MILP) to find the mathematically optimal starting XI and bench.

## CLI Execution Command

```powershell
python -m model.solver --season 2026-27 --gw 2 --budget 100.0 --horizon 3
```

## Generated Output Receipt
* Invariants:
  * Exactly 15 squad players (2 GK, 5 DEF, 5 MID, 3 FWD).
  * Exactly 11 starting XI players with valid formation (min 3 DEF, min 2 MID, min 1 FWD).
  * Exactly 1 Captain and 1 Vice-Captain.
  * Maximum 3 players per Premier League club.
  * Squad spend $\le \text{budget} + \text{bank}$.

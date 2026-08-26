---
type: Attested Computation
title: Simulate Gameweek Matches Contract
description: Sanctioned execution contract for executing 10,000 Monte Carlo matchday simulations via model/match_simulator.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: true, default: 2 }
  - { name: simulations, type: integer, required: false, default: 10000 }
computation: model/match_simulator.py
executor:
  resource: references/skills/run_pipeline.md
  receipt: [status, p10_floor, p50_median, p90_ceiling]
attester:
  resource: references/attesters/verify_solver.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: match-sim-src
    resource: model/match_simulator.py
    title: Match Simulator Subsystem
---

# Contract & Execution

Simulates Poisson match events and produces ceiling/floor percentiles for squad selection and captaincy decisions.

## CLI Execution Command

```powershell
python -m model.match_simulator --season 2026-27 --gw 2 --simulations 10000
```

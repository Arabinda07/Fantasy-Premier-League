---
type: Attested Computation
title: Sync Live Matchday Gameweek Contract
description: Sanctioned execution contract for streaming live matchday points, provisional BPS bonus, and auto-substitutions via model/live_sync.py.
status: stable
runtime: python
parameters:
  - { name: season, type: string, required: true, default: "2026-27" }
  - { name: gw, type: integer, required: true, default: 2 }
  - { name: poll_interval, type: integer, required: false, default: 60 }
computation: model/live_sync.py
executor:
  resource: references/skills/run_pipeline.md
  receipt: [status, live_points, json_state]
attester:
  resource: references/attesters/verify_solver.py
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:22:00Z }
sources:
  - id: live-sync-src
    resource: model/live_sync.py
    title: Live Matchday Synchronization Subsystem
---

# Contract & Execution

Polls official FPL live match endpoints to update player scores, recalculate bonus points, and simulate bench auto-substitutions.

## CLI Execution Command

```powershell
python -m model.live_sync --season 2026-27 --gw 2 --poll 60
```

---
type: Dataset
title: Manager Squad Ground Truth and Recommendation Schema
description: Schema and invariants governing authoritative manager squad persistence (actual_squad.json) versus solver recommendations (recommended_squad_gw*.json).
resource: data/2026-27/actual_squad.json
tags: [dataset, schema, json, manager-squad, ground-truth, okf]
generated: { by: antigravity/gemini-3.8-flash, at: 2026-10-10T05:55:00Z }
sources:
  - id: live-sync-src
    resource: model/live_sync.py
    title: Live Matchday Synchronization Subsystem
  - id: live-manager-src
    resource: model/live_manager.py
    title: Live Matchday Manager
  - id: sync-script-src
    resource: scripts/sync_live_squad.py
    title: Live Squad Synchronization CLI
---

# Schema: Manager Squad Snapshots

Authoritative data contract distinguishing the manager's real, verified account state on the official Fantasy Premier League servers from ephemeral solver transfer simulations.

## File Roles & Invariants

| File Path | Role | Mutation Authority | Contract Guarantee |
| :--- | :--- | :--- | :--- |
| `data/<season>/actual_squad.json` | **Immutable Ground Truth** | Official FPL API (`/entry/{id}/picks/` + `/transfers/`) or explicit human confirmation (`EXECUTED`) | Reflects the 15 players actually owned. **Never** overwritten by solver recommendations. |
| `data/<season>/manager_squad_<entry_id>_actual.json` | **Per-Team Ground Truth Mirror** | Same as above | Team-partitioned copy of `actual_squad.json`. |
| `data/<season>/recommended_squad_gw<gw>.json` | **Solver Proposal Artifact** | MILP Squad Solver (`model/solver.py`, `model/live_manager.py`) | Contains proposed transfers in/out, proposed starting XI, and projected xP for the target gameweek. |
| `data/<season>/current_squad.json` | **Continuity Compatibility Layer** | Synchronized with `actual_squad.json` | Backwards-compatible snapshot. When `squad_status != 'EXECUTED'`, baseline codes take absolute precedence over hypothetical proposals. |

## JSON Structure (`actual_squad.json`)

```json
{
  "entry_id": 9500404,
  "manager_name": "Arabinda Saha",
  "team_name": "Fuljhore Giants",
  "season": "2026-27",
  "last_updated_gw": 6,
  "squad_status": "EXECUTED",
  "overall_rank": 7007180,
  "overall_points": 270,
  "bank": 2.1,
  "free_transfers": 0,
  "squad_codes": [
    154561, 80201, 226597, 169528, 122798,
    466075, 465730, 222531, 201658, 424876,
    244851, 141746, 586309, 177815, 216646
  ],
  "baseline_squad_codes": [ ... ],
  "starter_codes": [ ... ],
  "bench_codes": [ ... ],
  "captain_code": 141746,
  "vice_captain_code": 154561,
  "updated_at": "2026-10-10 05:52:00 UTC"
}
```

## Computation & Synchronization Contracts

1. **Anti-Drift Invariant**: The live MILP solver (`manage_gameweek`) must never overwrite `actual_squad.json` with unexecuted simulated transfers.
2. **Pre-Flight Attestation**: Before proposing weekly transfers or lineups, agents and pipelines must inspect `actual_squad.json` or query the live FPL API via `scripts/sync_live_squad.py` to ensure bank balance, free transfers, and hits taken reflect the real manager state.
3. **Pre-Deadline Reconciliation**: In-progress transfers executed by the manager prior to deadline (which appear in `/entry/{id}/transfers/` with `event == current_gw`) must be applied to the squad baseline.

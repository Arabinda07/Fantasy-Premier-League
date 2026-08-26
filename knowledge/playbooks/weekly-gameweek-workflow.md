---
type: Playbook
title: Weekly Gameweek Transition Workflow
description: Step-by-step Standard Operating Procedure for running weekly FPL data updates, model predictions, MILP squad solves, and live matchday tracking.
tags: [playbook, workflow, gameweek, operations, sops]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:24:00Z }
sources:
  - id: handover-doc
    resource: docs/HANDOVER_AND_ROADMAP.md
    title: Handover and Roadmap Document
  - id: journey-log
    resource: JOURNEY.md
    title: Engineering Journey & Lessons Learned Log
---

# Playbook: Weekly Gameweek Transition Workflow

Follow this step-by-step workflow every gameweek to ensure reliable predictions and optimal squad management.

---

## 1. Pre-Deadline Phase (T-24h to T-1h)

### Step 1: Ingest Latest FPL & External Data
```powershell
# Scrape latest FPL bootstrap, player status, prices, and Understat metrics
python -m model.pipeline_automation --season 2026-27 --gw <TARGET_GW> --run-once
```

### Step 2: Run Full Predictive Engine
```powershell
# Build dataset, compute predictions, and apply fixture multipliers
python -m model.build_dataset --season 2026-27
python -m model.prediction_engine --season 2026-27
python -m model.fixture_engine --season 2026-27 --gw <TARGET_GW>
```

### Step 3: Solve Optimal Squad & Strategy
```powershell
# Run MILP solver with 3-GW lookahead
python -m model.solver --season 2026-27 --gw <TARGET_GW> --budget 100.0 --horizon 3

# Export multi-tab Excel workbook
python -m model.excel_exporter --season 2026-27 --gw <TARGET_GW>
```

---

## 2. Matchday Live Phase (During Matches)

```powershell
# Start live matchday sync daemon (polls every 60s for BPS bonus and auto-subs)
python -m model.live_sync --season 2026-27 --gw <TARGET_GW> --poll 60
```

---

## 3. Post-Gameweek Rollover Phase

1. **Verify Actuals**: Ensure all match fixtures in [merged_gw.csv](/datasets/merged-gw.md) are completed.
2. **Archive Workbooks**: Excel output saved in `data/<season>/fpl_matchday_live_gw<GW>.xlsx`.
3. **Transition to Next Gameweek**: Run [gameweek_transition.py](/architecture/pipeline-automation.md) to advance target gameweek.

---
type: Dataset
title: Model Training & Inference Dataset Schema
description: Canonical feature dataset combining FPL history, Understat expected metrics, and FBref starting lineups.
resource: data/2026-27/model_dataset.csv
tags: [dataset, schema, features, model-input]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:26:00Z }
sources:
  - id: build-dataset-src
    resource: model/build_dataset.py
    title: Model Dataset Builder
  - id: phase1-spec
    resource: docs/superpowers/specs/2026-08-24-fpl-data-pipeline-design.md
    title: Phase 1 Data Pipeline Design Spec
---

# Schema: `model_dataset.csv`

The master feature matrix constructed by [model/build_dataset.py](/computations/build-dataset.md) used as the direct input into [model/prediction_engine.py](/models/point-prediction-engine.md).

## Core Player Identifiers & Position

| Column | Type | Description |
|---|---|---|
| `player_code` | `INTEGER` | Permanent FPL player code across seasons. |
| `web_name` | `STRING` | Player standard FPL display name. |
| `team` | `STRING` | Club name (e.g. `'Arsenal'`, `'Liverpool'`). |
| `position` | `STRING` | Standardized position string: `'GK'`, `'DEF'`, `'MID'`, `'FWD'`. |
| `now_cost` | `INTEGER` | Current FPL price in tenths of millions (e.g. `60` = £6.0M). |
| `status` | `STRING` | Availability status code (`'a'`, `'d'`, `'i'`, `'s'`). |

## Playing Time & Lineup Probabilities (FBref + FPL)

| Column | Type | Description |
|---|---|---|
| `season_minutes` | `INTEGER` | Total minutes played in the current season. |
| `season_starts` | `INTEGER` | Total Premier League starts in current season. |
| `fbref_starts` | `INTEGER` | Total official team sheet starts (reconciled via FBref). |
| `fbref_subs` | `INTEGER` | Matches brought on as a substitute. |
| `fbref_unused_subs` | `INTEGER` | Matches included on bench but did not play. |
| `fbref_squads_made` | `INTEGER` | Total matchday squads made ($Starts + Subs + Unused\_Subs$). |

## Long-Form Rolling Performance Metrics (Full Evaluation Window)

| Column | Type | Description |
|---|---|---|
| `long_form_minutes` | `FLOAT` | Total minutes played in long-form window. |
| `long_form_expected_goals_90` | `FLOAT` | Long-form expected goals per 90 ($xG90$). |
| `long_form_expected_assists_90` | `FLOAT` | Long-form expected assists per 90 ($xA90$). |
| `long_form_expected_goals_conceded_90` | `FLOAT` | Long-form expected goals conceded per 90 ($xGC90$). |
| `long_form_defensive_contribution_90` | `FLOAT` | Long-form defensive contributions per 90. |
| `long_form_bonus_90` | `FLOAT` | Long-form bonus points awarded per 90. |
| `team_long_form_xg90` | `FLOAT` | Team attacking $xG90$ over long window. |
| `team_long_form_xgc90` | `FLOAT` | Team defensive $xGC90$ over long window. |

## Short-Form Blending Fields (Last 6 Calendar Gameweeks)

| Column | Type | Description |
|---|---|---|
| `short_form_minutes` | `FLOAT` | Minutes played across the last 6 calendar gameweeks. |
| `short_form_expected_goals_90` | `FLOAT` | Short-window expected goals per 90. |
| `short_form_expected_assists_90` | `FLOAT` | Short-window expected assists per 90. |
| `short_form_expected_goals_conceded_90` | `FLOAT` | Short-window expected goals conceded per 90. |
| `short_form_defensive_contribution_90` | `FLOAT` | Short-window defensive contributions per 90. |
| `short_form_bonus_90` | `FLOAT` | Short-window bonus points per 90. |
| `team_short_form_xg90` | `FLOAT` | Team attacking $xG90$ over short window. |
| `team_short_form_xgc90` | `FLOAT` | Team defensive $xGC90$ over short window. |

## Joins & Downstream Dependencies

- Direct input into [model/prediction_engine.py](/computations/predict-points.md).
- Processed into [predictions.csv](/datasets/predictions.md).

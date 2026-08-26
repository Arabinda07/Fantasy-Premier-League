---
type: Dataset
title: Players Raw Overview Schema
description: Canonical schema and column definitions for players_raw.csv generated from FPL bootstrap-static API.
resource: data/2026-27/players_raw.csv
tags: [dataset, schema, fpl-api, players]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:20:00Z }
sources:
  - id: fpl-api-bootstrap
    resource: https://fantasy.premierleague.com/api/bootstrap-static/
    title: FPL Bootstrap-Static API Endpoint
  - id: repo-data-dict
    resource: DATA_DICTIONARY.md
    title: Repository Data Dictionary
---

# Schema: `players_raw.csv`

The primary season overview dataset extracted directly from the official FPL `bootstrap-static` endpoint via [global_scraper.py](/scrapers/fpl-api-pipeline.md).

## Key Identifier Columns

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` | Unique FPL player identifier for the current season (1-indexed). |
| `code` | `INTEGER` | Permanent FPL player code across seasons. |
| `first_name` | `STRING` | Player's official first name. |
| `second_name` | `STRING` | Player's official surname. |
| `web_name` | `STRING` | Standard display name shown in the FPL UI. |
| `team` | `INTEGER` | Team ID (1 to 20), foreign key into [teams.csv](/datasets/teams-and-fixtures.md). |
| `element_type` | `INTEGER` | Player position code: `1`=GK, `2`=DEF, `3`=MID, `4`=FWD.[^repo-data-dict] |

## Price & Market Columns

| Column | Type | Description |
|---|---|---|
| `now_cost` | `INTEGER` | Current FPL price in tenths of millions (e.g. `100` = £10.0M). |
| `cost_change_event` | `INTEGER` | Price change in current gameweek in tenths. |
| `selected_by_percent` | `FLOAT` | Overall game ownership percentage (e.g. `45.2`). |
| `transfers_in_event` | `INTEGER` | Net transfers into the team for the current round. |
| `transfers_out_event` | `INTEGER` | Net transfers out of the team for the current round. |

## Availability & Status

| Column | Type | Description |
|---|---|---|
| `status` | `STRING` | Player status: `'a'` (available), `'d'` (doubtful/25-75%), `'i'` (injured), `'s'` (suspended), `'u'` (unavailable). |
| `chance_of_playing_next_round` | `INTEGER` | Official percentage probability of playing next round (`0`, `25`, `50`, `75`, `100`). |
| `news` | `STRING` | Official injury / suspension text update from FPL. |

## Joins & Downstream Dependencies

- Joined with [merged_gw.csv](/datasets/merged-gw.md) on `element` (which matches `id`).
- Joined with Understat and FBref data via normalized `first_name + ' ' + second_name` in [model_dataset.csv](/datasets/model-dataset.md).

[^repo-data-dict]: Repository Data Dictionary
[^fpl-api-bootstrap]: FPL Official Bootstrap-Static API Endpoint

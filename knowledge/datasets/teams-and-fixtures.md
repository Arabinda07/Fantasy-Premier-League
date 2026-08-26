---
type: Dataset
title: Teams & Fixtures Schema
description: Canonical schemas for teams.csv, fixtures.csv, and team-level attacking and defensive power ratings.
resource: data/2026-27/teams.csv
tags: [dataset, schema, teams, fixtures]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:20:00Z }
sources:
  - id: global-scraper-src
    resource: global_scraper.py
    title: Global Scraper Pipeline
  - id: repo-data-dict
    resource: DATA_DICTIONARY.md
    title: Repository Data Dictionary
---

# Schema: `teams.csv` & `fixtures.csv`

Official team metadata, attack/defense power ratings, and season fixture schedules.

## 1. `teams.csv` Schema

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` | Unique Team ID (1 to 20). |
| `name` | `STRING` | Full club name (e.g. `'Arsenal'`, `'Manchester City'`). |
| `short_name` | `STRING` | 3-letter abbreviation (e.g. `'ARS'`, `'MCI'`). |
| `strength` | `INTEGER` | FPL overall strength rating (1-5). |
| `strength_attack_home` | `INTEGER` | FPL home attacking strength metric. |
| `strength_attack_away` | `INTEGER` | FPL away attacking strength metric. |
| `strength_defence_home` | `INTEGER` | FPL home defensive strength metric. |
| `strength_defence_away` | `INTEGER` | FPL away defensive strength metric. |
| `xg90` | `FLOAT` | Modeled expected goals scored per 90 (promoted default $1.05$). |
| `xgc90` | `FLOAT` | Modeled expected goals conceded per 90 (promoted default $1.80$). |

---

## 2. `fixtures.csv` Schema

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` | Unique fixture identifier. |
| `event` | `INTEGER` | Gameweek number (1 to 38, or `null` if unscheduled). |
| `team_h` | `INTEGER` | Home Team ID (1 to 20). |
| `team_a` | `INTEGER` | Away Team ID (1 to 20). |
| `team_h_difficulty` | `INTEGER` | Official FDR for the home team. |
| `team_a_difficulty` | `INTEGER` | Official FDR for the away team. |
| `kickoff_time` | `TIMESTAMP` | Scheduled kickoff time (ISO-8601 UTC). |
| `finished` | `BOOLEAN` | `True` if the match has concluded. |
| `team_h_score` | `INTEGER` | Final home team score (if finished). |
| `team_a_score` | `INTEGER` | Final away team score (if finished). |

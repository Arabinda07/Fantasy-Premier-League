---
type: Data Pipeline
title: FBref Match Log Scraper
description: Scrapes Premier League official match sheets to extract actual player starts, substitution appearances, and bench inclusions.
tags: [scrapers, fbref, starts, subs, lineups]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:23:00Z }
sources:
  - id: fbref-src
    resource: fbref.py
    title: FBref Scraper Module
---

# Pipeline: FBref Match Logs

[`fbref.py`](../../fbref.py) extracts match lineups from FBref to determine:
1. **Starts ($S$)**: Outfield and GK starts on the official team sheet.
2. **Subs ($Sub$)**: Appearances brought on from the bench.
3. **Unused Subs ($UB$)**: Included in matchday squad but remained on bench.

## ID & Name Reconciliation
Normalized via `first_name + ' ' + second_name` with Unicode stripping to match Opta player IDs in [model_dataset.csv](/datasets/model-dataset.md).

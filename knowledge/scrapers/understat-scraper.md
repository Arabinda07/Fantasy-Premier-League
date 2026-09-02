---
type: Data Pipeline
title: Understat xG Scraper & Player ID Matching
description: Scrapes match-level expected goals (xG) and expected assists (xA) from Understat and matches player IDs to official FPL element IDs.
tags: [scrapers, understat, xg, xa, id-matching]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:23:00Z }
sources:
  - id: understat-src
    resource: understat.py
    title: Understat Scraper Module
---

# Pipeline: Understat xG Scraper

[`understat.py`](../../understat.py) scrapes shot-level and match-level expected metrics ($xG, xA$) from Understat.

## Key Features
1. **Player Matching (`match_ids`)**: Matches Understat player names to FPL IDs using fuzzy string matching and team alignment.
2. **Team Attack/Defense Power**: Computes historical rolling $xG90$ and $xGC90$ per team for [teams.csv](/datasets/teams-and-fixtures.md).
3. **Player Per-90 Rates**: Computes rolling $xG90$ and $xA90$ for [model_dataset.csv](/datasets/model-dataset.md).

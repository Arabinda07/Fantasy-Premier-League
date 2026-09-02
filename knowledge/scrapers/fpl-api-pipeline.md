---
type: Data Pipeline
title: Official FPL API Ingestion Pipeline
description: Architectural documentation for scraping, parsing, and merging official Fantasy Premier League API endpoints.
tags: [scrapers, fpl-api, pipeline, ingestion]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:23:00Z }
sources:
  - id: global-scraper-src
    resource: global_scraper.py
    title: Global Scraper Script
  - id: getters-src
    resource: getters.py
    title: FPL HTTP Getters
  - id: parsers-src
    resource: parsers.py
    title: FPL JSON Parsers
  - id: collector-src
    resource: collector.py
    title: Gameweek Merger Collector
---

# Pipeline: Official FPL API Ingestion

The platform extracts data from official FPL JSON endpoints via four decoupled modules:

```mermaid
flowchart LR
    API[FPL Official API] --> Getters[getters.py]
    Getters --> Parsers[parsers.py]
    Parsers --> GlobalScraper[global_scraper.py]
    GlobalScraper --> RawCSV[players_raw.csv & fixtures.csv]
    GlobalScraper --> Collector[collector.py]
    Collector --> MergedGW[gws/merged_gw.csv]
```

## 1. Module Responsibilities

* **[`getters.py`](../../getters.py)**: Raw HTTP calls to official FPL endpoints (`/api/bootstrap-static/`, `/api/fixtures/`, `/api/element-summary/{id}/`).
* **[`parsers.py`](../../parsers.py)**: Converts JSON payloads into standard tabular dictionaries.
* **[`global_scraper.py`](../../global_scraper.py)**: Top-level orchestration for season overview files ([players_raw.csv](/datasets/players-raw.md), [teams.csv](/datasets/teams-and-fixtures.md), [fixtures.csv](/datasets/teams-and-fixtures.md)).
* **[`collector.py`](../../collector.py)**: Merges weekly gameweek CSVs into [merged_gw.csv](/datasets/merged-gw.md).

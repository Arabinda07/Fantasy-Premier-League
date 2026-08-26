# Scrapers & External Data Ingestion

This section documents the scrapers, HTTP clients, and data ingestion pipelines connecting to official and third-party data providers.

## Documents

* [FPL API Ingestion Pipeline](/scrapers/fpl-api-pipeline.md) - Architecture of the official FPL scraper modules (`global_scraper.py`, `collector.py`, `getters.py`, `parsers.py`).
* [Understat xG Scraper](/scrapers/understat-scraper.md) - Expected goals ($xG$) and assists ($xA$) scraper and player ID matcher (`understat.py`).
* [FBref Match Log Scraper](/scrapers/fbref-scraper.md) - Premier League team sheets, starts, and substitution logs scraper (`fbref.py`).

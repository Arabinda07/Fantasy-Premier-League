# Datasets & Schema Catalog

This section defines the canonical schemas, column names, data types, and join keys for all raw datasets and engineered feature tables across the platform.

## Documents

* [Players Raw Overview (`players_raw.csv`)](/datasets/players-raw.md) - Official FPL bootstrap-static player overview and status metadata.
* [Merged Gameweek History (`merged_gw.csv`)](/datasets/merged-gw.md) - Historical match-by-match player performance and scoring breakdown.
* [Model Training & Inference Dataset (`model_dataset.csv`)](/datasets/model-dataset.md) - Merged feature set containing rolling form, Understat xG/xA, and FBref starts/subs.
* [Baseline Predictions (`predictions.csv`)](/datasets/predictions.md) - Expected points breakdown across all 11 scoring components ($C_1 \dots C_{11}$) and playing probabilities.
* [Fixture-Adjusted Predictions (`fixture_predictions.csv`)](/datasets/fixture-predictions.md) - Venue- and opponent-scaled point predictions for upcoming gameweeks.
* [Teams & Fixture Schedules (`teams.csv`, `fixtures.csv`)](/datasets/teams-and-fixtures.md) - Premier League team ratings, venue strengths, and match schedules.
* [Matchday Live State (`fpl_matchday_live_gw*.json`)](/datasets/matchday-live-state.md) - Real-time matchday state schema for live points, auto-subs, and minutes.

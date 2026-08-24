# Phase 1 Design: FPL Model Data Pipeline

Status: proposed, awaiting review
Author: Claude Code, in collaboration with the repo owner
Date: 2026-08-24
Phase: 1 of 5 (Data pipeline → Point-prediction engine → Fixture/form adjustment → Squad solver → Excel write-back)

## Problem statement

The repo owner has, separately from this repository, built a detailed FPL points-prediction model in Excel (`MODEL.xlsx`) that produces a probability-weighted predicted score for every player, gameweek by gameweek, and feeds a squad-optimization solver. The model's maths is sound — reviewed in detail as part of this project — but three structural problems make it fragile and slow to maintain:

1. **Manual, error-prone data collection.** Every gameweek, three separate data sources are pulled by hand into the spreadsheet: the FPL API (via a Google Apps Script that exposes `writePlayers`/`writeTeams`/`writeFixtures` custom functions), FBref's "Playing Time" tables (copy-pasted, since FBref no longer offers a CSV export), and Understat's league table (downloaded as CSV). Each step is manual, and the Apps Script in particular is a black box even to its owner ("I don't know how it works, I hope it never breaks").
2. **A season-spanning "data bank" that's hard to reason about.** To let form metrics (long-form: this season and further back; short-form: last 6 gameweeks) survive the close-season gap, the model maintains a flat table of roughly 76,000 rows (up to ~1,000 player-slots × up to two seasons of gameweeks), queried via pivot tables and range-based `SUMIFS`-style lookups. The owner has already lost track of exactly how parts of this work ("I can't remember what I've done here... you'd have to have a look at the sums again").
3. **This repo already has the scrapers needed, but they're disconnected.** `fbref.py` and `understat.py` already exist in this codebase and already do most of what's needed — but `fbref.py` is hardcoded to write into `data/2021-22/` and has never been pointed at the current season, and `understat.py`'s season is hardcoded to `"2024"` in its URL, with its main data-parsing call (`parse_epl_data`) commented out. Neither is part of the current `global_scraper.py` / `collector.py` pipeline that already correctly produces `data/2026-27/players_raw.csv` and `data/2026-27/gws/merged_gw.csv` each gameweek.

This phase fixes all three: it turns three manual/half-working data sources into one script that produces a single, clean, current dataset — without touching the point-prediction maths itself (that's Phase 2).

**Related architecture review.** An `/improve-codebase-architecture` pass over this repo separately flagged `fbref.py` and `understat.py` as modules with real hidden complexity (HTML-comment-hidden tables; a fragile JS-variable JSON-extraction trick) that's currently exposed to callers rather than hidden behind a clean interface. Since this phase already has to edit both files for season-parameterization, Components 1 and 2 below fold that interface work in directly rather than treating it as a separate later task.

## Goals

- One command produces a single output CSV containing, for every current-season player: identity (player code, name, team, position), season-to-date totals, and long-form/short-form rolling rates (minutes, xG, xA, xGC, defensive contributions, bonus, BPS — per-90 where applicable), plus FBref-derived season totals for squads-made/starts/subs/unused-subs.
- `fbref.py` and `understat.py` work against the current season without manual URL/path edits.
- The long-form/short-form windowing logic is computed programmatically from data already on disk (`data/*/gws/merged_gw.csv` across seasons), replacing the Excel data-bank/pivot-table/SUMIFS mechanism entirely.
- The new logic is testable: at least one non-trivial calculation is covered by an automated test with hand-checked expected values.

## Non-goals (explicitly out of scope for this phase)

- **Transfermarkt / squad-position scraping.** The owner currently pastes Transfermarkt squad-by-position tables into `SQUADS.xlsm` by hand. Positions change only at transfer windows, not weekly, so automating this has low value relative to effort right now. Out of scope until a later phase, if ever.
- **The point-prediction formulas** (appearance probability, goals/assists, clean sheets via Poisson, defensive contributions, bonus, fixture multipliers, home/away adjustment, start-vs-true-total blending). These are Phase 2's job. This phase only produces the *inputs* those formulas will need.
- **The squad solver** (Phase 4) and **Excel write-back** (Phase 5).
- **Scheduling/automation.** The repo owner wants a script he runs manually when he wants fresh data before setting his team — not a scheduled job. No GitHub Actions workflow, cron job, or similar is part of this phase.

## Current state (what already exists and will be reused)

- `global_scraper.py` (via `parsers.py`, `getters.py`, `cleaners.py`) and `collector.py` already scrape the FPL API (`bootstrap-static`, fixtures, per-player `element-summary` history) into `data/2026-27/players_raw.csv`, `data/2026-27/fixtures.csv`, `data/2026-27/teams.csv`, `data/2026-27/gws/merged_gw.csv`, and `data/2026-27/players/<name>/{gws.csv,history.csv}`. This is already correct, already targets the current season, and needs **no changes** for this phase — it is called as-is.
- `fbref.py`'s `get_epl_players()` and `get_matches_data()` scrape every Premier League player's full match log from FBref, including rows classed `unused_sub` (rows are kept if they have no class, i.e. a normal match entry, or if their class is `unused_sub` — every other classed row, e.g. `dnp`/injury rows, is dropped). This is exactly the raw signal needed for appearance-point probability (squads-made / starts / subs / unused-subs), but:
  - `main()` hardcodes the output path to `data/2021-22/fbref/`.
  - There is no aggregation step — it writes one CSV of raw match rows per player, not a season summary.
- `understat.py`'s `get_epl_data()` hardcodes the URL `https://understat.com/league/EPL/2024`, and `parse_epl_data()` writes one CSV per team (`understat_<Team_Name>.csv`, from each team's `history` list — per-match xG/xGA/npxG/deep/ppda/date/result) plus a combined player-level CSV. `main()` has `parse_epl_data(...)` commented out; only `match_ids(...)` (which matches Understat and FPL player IDs into `data/2026-27/id_dict.csv`) currently runs.

## Target architecture

```
                 ┌─────────────────────┐
                 │  global_scraper.py   │  (unchanged, already current-season)
                 │  + collector.py      │
                 └──────────┬───────────┘
                             │ data/2026-27/players_raw.csv
                             │ data/2026-27/gws/merged_gw.csv
                             │ data/2026-27/fixtures.csv, teams.csv
                             ▼
┌───────────────┐   ┌───────────────────┐   ┌──────────────────────┐
│  fbref.py      │   │  understat.py      │   │  (existing multi-    │
│  fetch_*(),    │   │  _extract_js_json,  │   │   season merged_gw   │
│  summarize_    │   │  season param,      │   │   files already on   │
│  season()      │   │  parse_epl_data on  │   │   disk, unchanged)   │
└───────┬────────┘   └─────────┬──────────┘   └───────────┬──────────┘
        │ season summary        │ per-team per-match         │
        │ (starts/subs/         │ xG/xGA history              │
        │  unused-subs)         │                              │
        ▼                       ▼                              ▼
                 ┌──────────────────────────────────┐
                 │      model/rolling_form.py         │
                 │  long-form + short-form rates,      │
                 │  player- and team-level, computed    │
                 │  fresh for "as of now"               │
                 └──────────────┬───────────────────┘
                                 ▼
                 ┌──────────────────────────────────┐
                 │      model/build_dataset.py         │
                 │  orchestrates all of the above,      │
                 │  joins on player code, writes one    │
                 │  output CSV                          │
                 └──────────────┬───────────────────┘
                                 ▼
                 data/2026-27/model_dataset.csv
```

### Component 1: `fbref.py` — season parameterization + a deepened scrape interface

Beyond the original scope (season parameterization), this component now also deepens `fbref.py`'s interface per the architecture review: today, using this file safely requires a caller to already know that FBref hides its tables inside HTML comments and to understand the long `data-stat`-driven if/elif dispatch inside `get_matches_data` — that knowledge is exposed, not hidden. Target shape:

- **`fetch_season_overview(season, session=None) -> pd.DataFrame`** — replaces the scrape half of `get_epl_players()`. Takes the season and an optional `requests.Session` (defaulting to a new one if not given, so callers/tests can inject a mock or a shared session with retry policy already attached — this also fixes the current `get_data()`/`get_table_data()` inconsistency, where one has a retry loop and the other doesn't). Returns one row per player with the overview stats, instead of the current `PlayerData` struct-mutation approach.
- **`fetch_player_match_log(player_id, season, session=None) -> pd.DataFrame`** — replaces `get_matches_data()`. Takes a player id and season explicitly (not a mutable `PlayerData` object reached into and set on), and returns the match-log rows as a DataFrame. The HTML-comment unwrapping and `data-stat` column dispatch move entirely behind this call — a caller doesn't need to know either quirk exists.
- **`summarize_season(match_log_df) -> pd.Series`** (or equivalent) — the new aggregation step from the original scope, now defined in terms of `fetch_player_match_log`'s output rather than reaching into `PlayerData` internals: counts squads-made / starts / subs / unused-subs for the season, per player. **Implementation note carried over unchanged**: getting the precise start/sub/unused_sub three-way split needs one more signal from the row data than the current "kept vs. dropped" class check alone provides (e.g. a `game_started` field or minutes-played inference) — verify against 2-3 known players by hand before trusting it.
- Output paths change from the hardcoded `data/2021-22/fbref/` to `data/<season>/fbref/`, and the season summary is written to `data/<season>/fbref/season_summary.csv` alongside the existing per-player raw match CSVs.
- Fix while touching this file: write CSV columns from a **sorted** list of field names, not the current raw `set` (`player.match_stat_set`) — column order is currently nondeterministic run-to-run.
- `main()` becomes a thin CLI wrapper calling the two fetch functions plus `summarize_season`, not itself containing scrape logic.

### Component 2: `understat.py` — season parameterization + a shared JSON-extraction seam

Beyond the original scope (season parameterization, re-enabling `parse_epl_data`), this component also deepens the interface per the architecture review: `get_epl_data()` and `get_player_data()` each independently repeat the same fragile parse (split the script tag's content on `=`, regex out a `JSON.parse('...')` payload, hex-decode it, then `json.loads`) once per JS variable (`teamsData`, `playersData`, `matchesData`, `shotsData`, `groupsData`) — four copies of the same undocumented-format knowledge. Target shape:

- Factor a single **`_extract_js_json(scripts, var_name) -> dict`** helper out of the four duplicated blocks. `get_epl_data`/`get_player_data` become thin callers of this one function, one call per variable they need.
- Change the hardcoded `"2024"` in `get_epl_data()`'s URL to a `season` parameter (confirm whether Understat's URL uses the season's start year or end year against the live site before finalizing the mapping from this repo's `data/<season>/` folder naming, e.g. `"2026-27"`, to Understat's URL parameter — same open question as before, unchanged).
- Re-enable `parse_epl_data(...)` in `main()`, pointed at `data/2026-27/understat/`.
- `match_ids()` stays a separate concern (ID reconciliation is a different problem from scraping, not something to merge into the extraction seam) but gets two fixes while it's being touched: accept an injectable matching function/strategy instead of the current hardcoded exact-string equality (`if k in fpl_players`), and write `id_dict.csv` via `csv.writer` instead of hand-joined comma strings (the current approach breaks silently if any player name contains a comma).

### Component 3: `model/rolling_form.py` (new)

Given:
- a target "as of" point (current season + current gameweek number),
- a long-form window (default: current season to date, plus up to N prior full seasons — start with N=1, i.e. up to 2 seasons total, matching the owner's stated ceiling),
- a short-form window (default: last 6 gameweeks, allowed to reach back into the prior season the way the owner's model does),

compute, per player:
- minutes, xG, xA, xGC, defensive contributions, bonus, BPS — summed over the window, and per-90 rates — by reading `data/<season>/gws/merged_gw.csv` for the relevant season(s) and filtering/summing by gameweek range.

And per team:
- xG and xGC per-90 — by reading the corresponding Understat per-team match-history CSVs and mapping each match to a gameweek number via `data/<season>/fixtures.csv` (match date/opponent → fixture → gameweek).

This is a pure function of the CSVs already on disk plus the parameters above — it does not persist a historical table. Unlike the Excel data-bank, which stores every gameweek's rolling window because spreadsheet formulas need somewhere to point, this only ever needs to answer "what are the rates right now," so nothing is precomputed for gameweeks that aren't the current one. If a future need arises for a full historical time series (e.g. to reproduce the owner's old `FORM CHARTS.xlsx`), that is a separate, explicitly scoped addition — not something this function should try to anticipate.

### Component 4: `model/build_dataset.py` (new)

Orchestrates, in order:
1. Call `global_scraper.parse_data()` (already exists, unchanged) to refresh `data/2026-27/*`.
2. Call the updated `fbref.py` season-summary step.
3. Call the updated `understat.py` step.
4. Call `model/rolling_form.py` for the current gameweek.
5. Join everything on player code (FPL's own player `code` field, per the owner's own observation that it's stabler across seasons than player names — confirmed sound practice, keep it) and write `data/2026-27/model_dataset.csv`.

Output columns (final list to be confirmed during implementation, but at minimum):
`player_code, web_name, team, position, season_minutes, season_starts, season_subs, season_unused_subs, long_form_minutes, long_form_xg90, long_form_xa90, long_form_xgc90, long_form_dc90, long_form_bonus90, short_form_minutes, short_form_xg90, short_form_xa90, short_form_xgc90, short_form_dc90, short_form_bonus90, team_long_form_xg90, team_long_form_xgc90, team_short_form_xg90, team_short_form_xgc90`

## Testing plan

This repository currently has no test infrastructure at all (no `tests/` directory, no `pytest.ini`, no existing `test_*.py` files) — this phase establishes the first convention, scoped narrowly to the one genuinely new piece of logic:

- Add `pytest` to `requirements.txt` (new dependency — nothing here to conflict with; already added as part of the `analysis/analyze.py` consolidation, so this phase reuses that addition rather than re-adding it).
- Add `model/test_rolling_form.py` with 2-3 cases where the expected long-form/short-form rate for a specific known player or team is computed by hand from `data/2025-26/gws/merged_gw.csv` (a season that's already complete and stable) and asserted against `rolling_form`'s output.
- Add a test for `understat._extract_js_json` — a pure function, testable against a small canned string fixture shaped like Understat's actual script-tag format (no network needed). This is the one piece of the Understat deepening that's non-trivial parsing logic rather than mechanical scraping.
- No test is required for `build_dataset.py` itself (thin orchestration/glue), for the `fbref.py`/`understat.py` season-parameterization changes themselves, or for `fetch_season_overview`/`fetch_player_match_log`/`fetch_*` network calls (mechanical, network-dependent scraping) — per this project's stated policy of testing non-trivial logic, not everything.

## Open questions / risks

1. **`pandas` version.** `requirements.txt` pins `pandas==0.25.3` (circa 2019). Recommendation: implement `rolling_form.py` against this pin first, since the operations needed (`groupby`, `concat`, basic CSV I/O) have been stable across pandas versions for a long time. Only bump the pin if a specific needed feature is actually missing — and if bumped, spot-check that `mergers.py` (the other pandas consumer in this repo) still runs correctly afterward.
2. **FBref start/sub/unused-sub split.** As noted in Component 1, `get_matches_data`'s existing row-keeping logic distinguishes "kept" from "dropped" rows, but the precise three-way split (started / came on as sub / unused sub) needs one more signal from the row data than is currently extracted. Verify by hand against 2-3 known players (e.g. a nailed starter, a rotation player, a fringe player) before trusting the aggregation.
3. **Understat season URL convention.** Confirm whether Understat's season parameter for `https://understat.com/league/EPL/<year>` uses the season's start year or end year before hardcoding the mapping from `data/<season>/` folder names (e.g. `"2026-27"`) to Understat's URL parameter.
4. **Player-identity matching across sources.** `understat.py` already has `match_ids()`, matching by exact full-name string against `data/2026-27/player_idlist.csv`. FBref names may differ from both (the owner's Excel model already handles this with a 4-alias fuzzy-match scheme). This phase should reuse/extend `match_ids`-style matching rather than re-inventing the owner's alias system; if FBref name mismatches turn out to be common, that's worth a short follow-up note rather than silently dropping unmatched players from the output.
5. **FBref scrape performance.** `get_matches_data` makes one HTTP request per player (with a 5-second retry backoff on non-200 responses) to build the full match-log scrape. With ~500-700 Premier League players, this could take a while run on-demand. Measure actual wall-clock time during implementation; if it's too slow for a "run before I set my team" workflow, consider a simple on-disk cache keyed by season+gameweek rather than pre-optimizing now.

## Rollout

This phase is purely additive: new files (`model/rolling_form.py`, `model/build_dataset.py`) and parameterization fixes to two existing-but-disconnected scripts (`fbref.py`, `understat.py`). It does not touch `MODEL.xlsx`, `SOLVER.xlsx`, or any of the owner's live Excel files, and nothing downstream depends on this output yet (Phase 2 will). No cutover or migration step is needed — this can be built, tested, and left dormant until Phase 2 is ready to consume `model_dataset.csv`.

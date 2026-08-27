# Engineering Journey & Lessons Learned Log

This document tracks the phased rebuild of the Fantasy Premier League (FPL) points-prediction model from Excel into Python, along with an explicit log of architectural decisions, mistakes, gotchas, and guidelines to ensure errors are never repeated in future phases.

---

## Roadmap & Phase Status

| Phase | Description | Status | Key Deliverables |
|---|---|---|---|
| **Phase 1** | **Data Pipeline** | **COMPLETE** | `understat.py`, `fbref.py`, `model/rolling_form.py`, `model/build_dataset.py`, test suite (19 unit tests), `model_dataset.csv` |
| **Phase 2** | **Point-Prediction Engine** | **COMPLETE** | `model/prediction_engine.py`, `model/test_prediction_engine.py` (12 unit tests, 31 total passing tests), `predictions.csv` with full 11-component breakdown |
| **Phase 3** | **Fixture & Form Adjustment** | **COMPLETE** | `model/fixture_engine.py`, `model/test_fixture_engine.py` (11 unit tests, 63 total passing tests across repo), `fixture_predictions.csv` with opponent & venue multipliers, form blending, and DGW/BGW support |
| **Phase 4** | **Squad Optimization Solver** | *Next* | Linear Programming (ILP) solver for 15-man squad, captaincy, bench order, weekly transfers under budget constraints |
| **Phase 5** | **Excel Sync / Output** | *Pending* | Automated export to `.xlsx` / `.xlsm` formats via `openpyxl` |

---

## Milestone 1: Adversarial Remediations Summary (Completed)

1. **Empirical Bayes Prior Shrinkage (`model/prediction_engine.py`)**:
   - Small sample size players (e.g. Max Dowman, 152 mins) shrank raw per-90 rates toward positional league priors ($M_0 = 500.0$ mins).
   - Formula: $\text{rate}_{\text{adj}} = \frac{M}{M + M_0} \text{rate}_{\text{raw}} + \frac{M_0}{M + M_0} \text{Prior}(\text{POS})$.
   - Positional baselines: FWD (xG 0.35, xA 0.15, DC 2.0), MID (xG 0.15, xA 0.15, DC 4.0), DEF (xG 0.05, xA 0.05, DC 8.0), GK (xG 0.0, xA 0.0, DC 1.0).
   - Dowman's raw $xG90$ dropped from $0.7046 \to 0.2793$, dropping projected baseline $xP$ from $7.07 \to \sim 4.2$ (and $4.06\text{ xP}$ fixture-adjusted).

2. **Exact Discrete $C_{10}$ Goals Conceded Expectation (`model/prediction_engine.py`)**:
   - Replaced binary approximation for $GC \ge 2$ with exact Poisson expectation:
     $$\mathbb{E}[\text{Penalty}] = -\sum_{m=1}^5 m \left(P(X = 2m) + P(X = 2m + 1)\right)$$
   - Correctly accounts for multiple points lost in heavy defeats (4 GC = -2 pts, 6 GC = -3 pts).

3. **Robust Full-Name Reconciliation for FBref (`model/build_dataset.py`)**:
   - Added unicode text normalization (`normalize_name`) and mapping via `players_raw.csv` and `player_idlist.csv` (`first_name + ' ' + second_name`).
   - Ensures FBref starts, subs, and unused subs match to Opta/FPL player codes without dropping rows.

4. **Starter Minutes Proration (`model/prediction_engine.py`)**:
   - Estimated average minutes per start: $\text{mins\_per\_start} = \min(90.0, \max(45.0, \text{total\_minutes} / \text{starts}))$.
   - Scaled attacking active ratio: $\text{active\_ratio} = P(\text{Start}) \times \frac{\text{mins\_per\_start}}{90.0} + P(\text{Sub}) \times \frac{20.0}{90.0}$.

---

## Phase 3 Implementation & Hardening Summary (Completed)

1. **`model/fixture_engine.py`**:
   - **Form Blending with Sample-Size Shrinkage**: Short-form rates (last 6 GWs) blended via $\alpha_{\text{eff}} = \alpha \times \frac{M_{\text{short}}}{M_{\text{short}} + 270.0}$ preventing noisy substitute cameos from inflating projections.
   - **Promoted Team Baseline Priors**: Defaults to $1.05\text{ xG90}$ and $1.80\text{ xGC90}$ for promoted sides lacking historical PL data, accurately valuing captaincies against promoted defenses.
   - **Conjugate Symmetric Venue Factors**: Enforces exact mathematical goal conservation ($\mathbb{E}[\text{Scored}] \equiv \mathbb{E}[\text{Conceded}]$) with conjugate pairs $1.08 \longleftrightarrow 0.9259$.
   - **Dynamic Goalkeeper Save Scaling**: Scales $C_3$ expected saves by $(\text{Opp\_xG90} / \text{League\_Avg\_xG})^{0.65} \times \text{Venue\_Defense}$ so budget goalkeepers facing high-shot volume are accurately valued.
   - **Fixture-Scaled Bonus ($C_6$) and DC ($C_{11}$)**: Attack multipliers scale bonus point probability ($\text{Attack\_Mult}^{0.75}$), while opponent attacking pressure scales defensive contribution volume.
   - **DGW Rotation Dampening**: Applies $0.90\times$ fatigue/rotation decay on Match 2 for outfield players and accurately reports total expected starts.
   - Output: `data/<season>/fixture_predictions.csv` with full 11-component breakdowns and fixture metadata.

2. **Automated Unit Tests**:
   - 12 unit tests in `model/test_fixture_engine.py` covering blending weights, promoted priors, goal conservation, GK save scaling, bonus/DC scaling, and DGW handling.
## Phase 4 Implementation & Cross-Phase Hardening (Completed)

1. **`model/solver.py`**:
   - **Integer Linear Programming (MILP / ILP)** engine powered by `pulp` (CBC solver).
   - **15-Man Squad Selection**: Enforces exact positional quotas (2 GK, 5 DEF, 5 MID, 3 FWD), £100.0M budget constraint, and maximum 3 players per Premier League club.
   - **11-Man Starting XI & Formation Optimization**: Dynamically selects the highest expected points lineup satisfying all valid formations (min 3 DEF, min 2 MID, min 1 FWD).
   - **Captain ($2\times \text{xP}$) & Vice-Captaincy**: Optimizes captain and vice-captain selection from starting XI.
   - **FPL Strategic Chips**: Full mathematical modeling of Bench Boost (`'bboost'`), Triple Captain (`'3xc'`), Free Hit (`'freehit'`), and Wildcard (`'wildcard'`).
   - **FPL Selling Price Mechanics**: 50% profit retention formula ($\text{purchase} + \lfloor (\text{current} - \text{purchase})/2 \rfloor$) prevents phantom cash distortions.
   - **Bench Ordering**: Standard FPL order with backup GK in slot 1 and outfield bench players ordered descending by expected points for auto-substitutions.
   - **Weekly Transfer Optimizer**: Solves transfer in/out decisions factoring in Free Transfers ($1\dots 5$) and $-4\text{ pt}$ hit penalties.
   - **Terminal ASCII Pitch Layout**: Visualizes starting XI formation and bench layout.

2. **Cross-Phase Remediations in `model/prediction_engine.py`**:
   - **Cold-Start Playing Priors**: Assigns price-based starting probabilities ($0.85$ for $\ge \pounds 9.0\text{M}$, $0.70$ for $\ge \pounds 7.0\text{M}$, $0.45$ for $\ge \pounds 5.5\text{M}$) for new transfers with 0 historical PL minutes.
   - **Disciplinary Yellow/Red Correction**: Corrected yellow card expectation $\max(0, \text{yc90} - 2 \times \text{rc90})$ to eliminate double penalties on 2-yellow red cards.

## Phase 5 Implementation Summary (Completed)

1. **`model/excel_exporter.py`**:
   - **Multi-Tab Excel Workbook Generator** powered by `openpyxl`.
   - **5 Dedicated Sheets**:
     - `Summary Dashboard`: Executive KPI cards (Total Projected xP, Squad Spend, Remaining Bank, Formation), starting XI pitch layout with Captain/Vice badges, and ordered bench table.
     - `Optimal Squad`: 15-player squad table with role, position, name, team, cost, opponent, venue, FDR, expected points, and key scoring component contributions ($C_3, C_6, C_7, C_8, C_9$).
     - `GW Predictions`: Full league player ranking with all 11 component point breakdowns ($C_1 \dots C_{11}$) and playing probabilities ($P(\text{Start}), P(\text{App}), P(60+)$).
     - `Fixtures & Ratings`: Team attack/defense strengths (xG90, xGC90) and gameweek fixture matchups with difficulty ratings.
     - `Form & Underlying Stats`: Short-form vs long-form comparison and underlying Understat/FBref metrics.
   - **Professional Formatting**:
     - Dark Navy (`#1E293B`) headers with bold white text.
     - Emerald pitch accents (`#0F766E`), soft green starter highlights (`#F0FDF4`), and amber captain badges (`#FEF3C7`).
     - Number formatting: Currency as `£#,##0.0"M"`, xP as `0.00`, rates as `0.000`, probabilities as `0.0%`.
     - Frozen panes and auto-fitted column dimensions across all sheets.
   - Output: `data/<season>/fpl_model_output_<season>_gw<GW>.xlsx`.

2. **Automated Unit Tests**:
   - 4 unit tests in `model/test_excel_exporter.py` verifying sheet generation, KPI metrics, optimal squad sum formulas, and player prediction rankings.
   - **84 total unit tests** passing across the entire repository.

## Advanced Strategy & Live Matchday Management Layer (Completed)

1. **`model/solver.py` (Multi-Gameweek Horizon Lookahead)**:
   - **Time-Expanded MILP Formulation**: Replaces single-gameweek myopia with a 3-to-5 gameweek lookahead optimization using temporal discounting ($\gamma = 0.90$).
   - **Inter-Temporal Constraints**: Enforces squad continuity ($x_{i,t} = x_{i,t-1} + u_{i,t} - v_{i,t}$), free transfer evolution ($1 \dots 5$), selling price profit mechanics, and bank balance conservation across time.
   - Eliminates transfer churn into short-term enablers.

2. **`model/chip_optimizer.py` (Strategic Chip Timing Optimizer)**:
   - **DGW & BGW Schedule Scanner**: Detects double and blank gameweeks across all 38 fixture rounds.
   - **Chip Value Deltas**: Computes expected value gains for Triple Captain ($\Delta_{\text{3xC}}$), Bench Boost ($\Delta_{\text{BB}}$), Free Hit ($\Delta_{\text{FH}}$), and Wildcards 1 & 2 ($\Delta_{\text{WC}}$).
   - Generates season-long chip deployment roadmap.

3. **`model/live_manager.py` (Live Matchday Manager & Decision Cockpit)**:
   - Ingests current squad codes, bank balance, and free transfers.
   - Filters live injury/status flags (`'a'`, `'d'`, `'i'`, `'s'`) from `players_raw.csv`.
   - Generates immediate action recommendations (Roll vs Free Transfer vs Hit), Starting XI lineup, captaincy, vice-captaincy, ordered bench, and multi-GW transfer roadmap.
   - Writes out live Excel workbook (`fpl_matchday_live_gw<GW>.xlsx`) and JSON state (`fpl_matchday_live_gw<GW>.json`).

4. **Automated Unit Tests**:
   - `model/test_multi_horizon.py`: Verifies multi-GW squad continuity and time-discounted optimization.
   - `model/test_chip_optimizer.py`: Verifies DGW/BGW detection and chip schedule profiles.
   - `model/test_live_manager.py`: Verifies live manager execution and injury dampening.
   - **90 total unit tests** passing across the entire repository.

---


## Mistakes, Failures & Lessons Learned Log (DO NOT REPEAT)

### 1. Cross-Season ID Drift (`element` vs `code`)
* **Mistake**: When combining `merged_gw.csv` rows across two seasons (e.g. 2024-25 and 2025-26), grouping was initially done by `element`.
* **Why it failed**: In FPL, the `element` ID is season-specific and reassigned every summer. `element=3` was Karl Hein in 2025-26, but a different player in 2024-25. This caused cross-season stats to silently contaminate different players.
* **Resolution**: In `_load_merged_gw_with_code`, always join each season's `merged_gw.csv` to that season's `players_raw.csv` on `element == id` to attach the permanent Opta/FPL `code`. All cross-season grouping must be keyed on `player_code`.

### 2. Double Gameweeks & Row Count vs. Calendar Gameweek Window
* **Mistake**: Assuming a player has at most 1 row per gameweek number and slicing by row count (e.g. `tail(6)`).
* **Why it failed**: In official FPL, postponed matches are rescheduled into Double Gameweeks (DGW). In DGW33 and DGW36 of 2025-26, Manchester City played 2 fixtures in a single gameweek, producing 2 fixture rows with `GW=33` in `merged_gw.csv`. Slicing by row count took 6 match rows instead of 6 calendar gameweeks (450 mins over 7 fixtures vs 6 GWs).
* **Resolution**: Windowing must always use unique calendar gameweek sets (`GW.isin(cutoff_gws)`), and all rates must normalize by exact minutes played (`rate = stat / (minutes / 90.0)`). In Phase 2/3, point prediction treats fixture count per gameweek explicitly.

### 3. Player-Level Minutes Proration in Team Stats (`xGC`)
* **Mistake**: Assuming `expected_goals_conceded` in player match rows was an identical team-wide constant per match and taking `first()`.
* **Why it failed**: FPL prorates `expected_goals_conceded` according to the minutes a player was on the pitch. A substitute playing 18 minutes had `xGC = 0.21`, while the 90-minute starter had `xGC = 1.70`. Taking `first()` selected whichever player appeared first in the file (often a bench player with 0.0 or 0.21).
* **Resolution**: To extract the full match-level team xGC from player data, take `max()` across players on that team for that fixture (the 90-minute player reflects the full match xGC).

### 4. JavaScript Variable Parsing in Scrapers
* **Mistake**: In `understat.py`, splitting raw script contents on `=` directly without line-by-line isolation.
* **Why it failed**: When multiple JavaScript assignments existed inside the same `<script>` block, splitting on all `=` broke subsequent variables.
* **Resolution**: Split script text by `\n` lines first, then use `split('=', 1)` to only split on the first assignment operator per line.

### 5. `NaN` Poisoning in Pandas Series `.get()` Lookups
* **Mistake**: Using `float(player.get(key, 0.0) or 0.0)` to read values from a pandas Series.
* **Why it failed**: In pandas, if a key exists in the Series index with a missing value (`np.nan`), `player.get(key, default)` returns `np.nan`, not the default. In Python, `bool(np.nan)` is `True`, so `np.nan or 0.0` evaluates to `np.nan`. When passed into mathematical expressions, `nan` poisoned the entire sum, and `max(0.0, nan)` evaluated to `0.0`.
* **Resolution**: Use a dedicated `_safe_float(val, default=0.0)` helper that checks `math.isnan(f)` on all converted numbers.

### 6. Division by Zero on Inactive Players
* **Mistake**: Inactive players (reserve goalkeepers, unselected youth) with 0 minutes played produce `ZeroDivisionError` or `NaN` when calculating per-90 rates.
* **Resolution**: Guard all rate calculations with `if minutes > 0 else 0.0`. Add dedicated test cases (e.g., `TestZeroMinutesPlayer`) verifying that 0-minute players cleanly return `0.0` for all per-90 metrics.

### 7. Small-Sample Over-Projection (The Dowman Anomaly)
* **Mistake**: Applying linear raw rates on players with minimal minutes (e.g. 152 mins, 1 start) resulting in unrealistically inflated projections ($7.07\text{ xP}$).
* **Why it failed**: Without sample size shrinkage, outlier performances over 1 or 2 matches project as unsustainable season-long superstars.
* **Resolution**: Apply Empirical Bayes prior shrinkage with $M_0 = 500.0$ minutes toward positional league baselines (`POSITIONAL_PRIORS`), and scale active ratios by average minutes per start.

### 8. Lookahead Horizon CSV Overwrite Race Condition
* **Mistake**: When `live_manager.py` looped through lookahead horizon steps ($t = 0 \dots H-1$), `predict_gameweek_fixtures` was invoked with default `save_csv=True` on every step.
* **Why it failed**: Step $t=0$ wrote GW2 to `fixture_predictions.csv`, but step $t=2$ subsequently overwrote the file on disk with GW4 fixtures (e.g. Man Utd vs Man City in GW4). Any subsequent script reading `fixture_predictions.csv` from disk saw GW4 matchups instead of GW2.
* **Resolution**: In `live_manager.py`, pass `save_csv=(step == 0)` so only the active target gameweek writes to disk. In `fixture_engine.py`, also save versioned `fixture_predictions_gw{gw}.csv` to isolate gameweeks permanently.

### 9. Missing Live Injury / Availability Filter in Core Solver (`prepare_solver_dataframe`)
* **Mistake**: `prepare_solver_dataframe` in `model/solver.py` was evaluating raw historical per-90 rates without applying live FPL injury status flags (`status = 'i'`, `'s'`, `'u'`).
* **Why it failed**: Injured players (e.g., Ekitiké with Achilles injury, Kroupi.Jr with Foot injury, Timber with Groin injury) had positive historical xP and were selected into the optimal squad despite being unavailable.
* **Resolution**: Wire `apply_rotation_dampening` directly into `prepare_solver_dataframe()` in `model/solver.py`, automatically mapping any player with `status in ('i', 's', 'u')` or `chance_of_playing == 0` to $\text{xP} = 0.0$ so they can never enter any optimal solution.

### 10. Web Name Identifier Collisions (Duplicate Player Names in FPL)
* **Mistake**: Resolving player locks by bare string `web_name` (e.g., `'Palmer'`, `'Davies'`) when multiple active players in the league share the exact same surname.
* **Why it failed**: `'Palmer'` matched both Cole Palmer (£9.5M, Chelsea) and Palmer (£4.0M, Ipswich); `'Davies'` matched Ben Davies (£4.0M, Spurs) and Davies (£4.0M, Liverpool), causing constraint binding errors.
* **Resolution**: Always resolve player locks using unique permanent Opta/FPL integer `code` (`player_code`) or explicitly disambiguate via `(team, web_name)`.

### 11. Fixture Cannibalization Blindness in Independent Solvers
* **Mistake**: Selecting multiple defensive assets from opposing teams in the exact same match (e.g., 5 players across Sunderland vs. Fulham).
* **Why it failed**: Standard expected points models treat player match distributions independently, ignoring that opposing clean sheets are mutually exclusive events.
* **Resolution**: Enforce an automated cross-fixture correlation check and cap total squad exposure to any single fixture to a maximum of 2–3 players.

---

## Elite Enhancements Layer Implementation (Completed)

1. **`model/set_pieces.py` (Set-Piece & Penalty Specialist Hierarchy)**:
   - Ingests official FPL PK, Direct FK, and Corner/Indirect FK taker orders (1/2/3).
   - Computes baseline penalty goal equity ($\Delta \text{xG}_{\text{PK}} = 0.79 \times 0.78 \times \lambda_{\text{PK}}$) added to $C_8$ and corner/FK assist equity added to $C_7$.

2. **`model/ownership_engine.py` (Effective Ownership & Game Theory Engine)**:
   - Models top-10k Effective Ownership ($\text{EO} = \text{Ownership} + \text{Captaincy} + \text{3xC}$).
   - Implements configurable strategy utility functions:
     - `'pure_xp'`: Raw expected points (neutral).
     - `'rank_protect'`: Shields against high-EO talismans ($\text{EO} > 100\%$).
     - `'differential_chase'`: Rewards high-ceiling differentials ($\text{EO} < 20\%$).

3. **`model/price_predictor.py` (Price Change & Team Value Forecaster)**:
   - Tracks net transfer velocity $\Delta T = \text{transfers\_in\_event} - \text{transfers\_out\_event}$.
   - Classifies market movement into 5 discrete alert tiers: `RISING_LOCK`, `RISING_ALERT`, `STABLE`, `FALLING_ALERT`, `FALLING_LOCK`.

4. **`model/rotation_intelligence.py` (Rotation & Tactical Hazard Engine)**:
   - Models midweek European turnaround congestion decay ($\le 3\text{ days rest} \to 0.82\times$ hazard for rotation-heavy clubs like Man City/Liverpool).
   - Evaluates sub-60-minute hook vulnerability and news availability dampening ($75\% \to 0.75, 50\% \to 0.40$).

5. **`model/matchup_intelligence.py` (Matchup Intelligence & Tactical Archetypes)**:
   - Formulates Empirical Bayesian Head-to-Head attacking multipliers with $M_{\text{H2H}, 0} = 270.0\text{ mins}$ shrinkage.
   - Evaluates opponent defensive line depth and transition vulnerability (High-Line $1.15\times$ for transition playmakers like Palmer vs Brighton).
   - Enriches point predictions dynamically across all solvers and live matchday tools.

6. **Manager Locks, Exclusions & Captaincy Overrides Infrastructure**:
   - Added `--lock-players`, `--exclude-players`, `--captain`, and `--vice-captain` CLI arguments to `model/solver.py` and `model/live_manager.py`.
   - Formulates hard ILP binary constraints for exact tactical customization without breaking global optimality.
   - Automated unit tests in `model/test_matchup_intelligence.py` and `model/test_solver.py`.
   - **134 total unit tests** passing across the entire repository with 0 regressions.

---

## Live Data Pipeline Automation Engine (Completed)

1. **`model/pipeline_automation.py` (Unified Multi-Stage Orchestrator)**:
   - **5-Stage Automated Pipeline**: Connects API sync, price velocity tracking, historical data rebuild, 11-component point predictions, fixture scaling, and multi-horizon MILP solving into a single executable workflow.
   - **4 Execution Modes**:
     - `sync`: Fast daily sync — API fetch + price delta + dataset rebuild + predictions + solver (~30s).
     - `full`: Complete post-gameweek rebuild — player histories + `merged_gw.csv` + dataset + predictions + solver.
     - `predictions_only`: Re-run projections and fixture engine without network calls or solver.
     - `solver_only`: Re-run MILP solver and export without re-predicting.
   - **Automatic Gameweek Detection**: Resolves current/next GW and deadline from FPL API events, with offline fallback to local `fixtures.csv`.
   - **Daily Price Velocity Tracker**: Records timestamped snapshots to `data/<season>/price_history/<date>.csv` with net transfer delta ($\Delta T$) and 5-tier alert classification (`RISING_LOCK`, `RISING_ALERT`, `STABLE`, `FALLING_ALERT`, `FALLING_LOCK`).
   - **Offline Resilience**: Graceful fallback to local cached data when FPL API is unavailable.
   - **Scheduler Daemon**: `--daemon --interval-hours 6` for autonomous background execution with configurable iteration limits.
   - **Rich CLI Interface**: Full argparse CLI with `--season`, `--gw`, `--mode`, `--bank`, `--ft`, `--horizon`, `--strategy`, `--offline`, `--daemon`, `--interval-hours`, `--max-iterations`.

2. **Automated Unit Tests (`model/test_pipeline_automation.py`)**:
   - 14 unit tests covering gameweek detection, price velocity snapshotting, sync mode execution, solver-only mode, predictions-only mode, error handling, and data structure validation.
   - **148 total unit tests** passing across the entire repository with 0 regressions.

---

## Next-Gen Alpha Engine: Dixon-Coles Match Simulator & Phase B Live Sync (Completed)

1. **`model/match_simulator.py` (Bivariate Dixon-Coles & Monte Carlo Match Engine)**:
   - **Dixon-Coles Low-Scoring Dependency Formulation**:
     $$\tau_{\lambda, \mu}(x, y) = \begin{cases}
     1 - \lambda \mu \rho & x=0, y=0 \\
     1 + \lambda \rho & x=0, y=1 \\
     1 + \mu \rho & x=1, y=0 \\
     1 - \rho & x=1, y=1 \\
     1 & \text{otherwise}
     \end{cases}$$
     with $\rho = -0.05$, capturing joint scoreline dependencies and low-draw empirical distributions.
   - **Exact Discrete $(11 \times 11)$ Matrix Analytics**: Generates normalized joint probability grids for Home Win, Draw, Away Win, Home Clean Sheet, Away Clean Sheet, Both Teams To Score (BTTS), Over/Under 2.5 goals, and ranked top scorelines.
   - **Vectorized 10,000-Run Monte Carlo Simulation**: Attributes simulated goals and assists via multinomial softmax sampling over player $xG90$ and $xA90$ active ratios.
   - **True BPS Allocation**: Simulates match event BPS scores (goals, assists, clean sheets, saves, DC, yellow/red cards) and allocates official 3, 2, 1 bonus points.
   - **Player Probability Distributions**: Calculates Mean ($\mathbb{E}[\text{xP}]$), Standard Deviation ($\sigma$), Floor (p10), Median (p50), Ceiling (p90), and Haul Probability ($P(\text{Points} \ge 10)$).
   - Automated unit tests: `model/test_match_simulator.py` (7 unit tests).

2. **`model/live_sync.py` (Phase B Direct Ingestion & Live Sync)**:
   - **1-Click FPL Entry ID & Mini-League Ingestion**: Ingests manager profile, overall rank, bank balance, team value, 15-player picks, captaincy, and active chip directly from FPL REST API.
   - **Opta/FPL Permanent Code Reconciliation**: Automatically maps season-specific FPL `element` IDs to permanent `player_code` values using `data/<season>/players_raw.csv`.
   - **Transfer History & Dynamic FT Calculation**: Tracks rolling free transfers ($1\dots 5$).
   - **Mini-League Rival Threat Matrix**: Ingests mini-league standings and competitor squads for direct differential analysis.
   - **Offline Resilience & Disk Caching**: Stores JSON snapshots in `data/<season>/cache/` with graceful fallback when offline.
   - Automated unit tests: `model/test_live_sync.py` (7 unit tests).

3. **`model/live_manager.py` Integration**:
   - Added `--team-id` and `--league-id` parameters for automated 1-click live decision cockpit execution.
   - Verified end-to-end live sync on Entry ID 12345 with automatic formation solve, multi-horizon transfer trajectory, and live briefing.
   - **173 total unit tests** passing across the entire repository with 0 regressions.

---

## Next-Gen Alpha Engine: Milestone 2 & Milestone 3 (Completed)

1. **`model/minutes_model.py` (Continuous Minutes Hazard & Survival Engine - Milestone 2)**:
   - **Three-Regime Survival Decomposition**: Deconstructs playing time into Starter ($T_{\text{start}} \in [1, 95]$), Substitute ($T_{\text{sub}} \in [5, 35]$), and DNP ($T = 0$) regimes.
   - **Continuous Probability Outputs**:
     - $\mathbb{P}(\text{Mins} \ge 60)$: Clean Sheet & 2-appearance-point qualification probability.
     - $\mathbb{P}(\text{Pre-60 Hook Hazard})$: Calibrated logistic hazard function for tactical substitutions prior to minute 60.
     - $\mathbb{P}(\text{Mins} = 0)$: DNP probability driving auto-sub bench activation.
     - $\mathbb{E}[\text{Mins}]$: Overall expected playing minutes.
   - **Hazard Adjustment Features**: Recent 6-GW start rate, European congestion ($\le 3$ days rest $\to 0.82\times - 0.88\times$ starter multiplier), manager tactical hook propensities (Arteta, Pep, Slot), FPL status flags, and price-tier priors for new transfers.
   - Automated unit tests: `model/test_minutes_model.py` (6 unit tests).

2. **`model/solver.py` Enhancements (Risk-Adjusted CVaR & Auto-Sub Solver - Milestone 3)**:
   - **CVaR Tail-Risk Objective Formulation**:
     $$\max \quad \sum_{t=1}^H \gamma^{t-1} \left( \mathbb{E}[R_t] - \lambda_{\text{risk}} \cdot \text{TailRisk}_t + \lambda_{\text{FT}} \cdot \text{FT}_t - 4 \cdot \text{Hits}_t \right)$$
     - $\lambda_{\text{risk}} > 0$ (`rank_protect`): Penalizes downside tail variance ($\text{xP} - \text{Floor}_{p10}$), targeting reliable, high-floor assets.
     - $\lambda_{\text{risk}} < 0$ (`differential_chase`): Rewards upside potential ($\text{Ceiling}_{p90} - \text{xP}$), targeting explosive haul differentials.
   - **Dynamic Bench Auto-Sub Valuation**: Weights bench slots ($w_{\text{bench}} \approx 0.10$, $1.0$ for Bench Boost) according to starter DNP probabilities.
   - **Free Transfer Banking Shadow Price**: $\lambda_{\text{FT}} = 1.75\text{ pts}$ encourages rolling transfers over low-delta sideways moves.
   - Automated unit tests: `model/test_solver_cvar.py` (3 unit tests).

3. **Continuous Minutes Hazard Integration into Core Prediction Pipeline (`model/prediction_engine.py`)**:
   - Wired `calculate_pre60_hook_probability` directly into `estimate_playing_probabilities` and `predict_player_points`.
   - Replaced linear approximations with continuous logistic hazard functions, accurately calculating $P(\text{Mins} \ge 60)$, appearance points ($C_1, C_2$), clean sheet expectations ($C_9$), and disciplinary penalties ($C_{10}$).

4. **`model/backtester.py` (Historical Backtest Engine with Automated Chip Strategy)**:
   - **Autonomous 38-Gameweek Simulator**: Simulates full historical season playthroughs (e.g. 2024-25) with dynamic free transfers ($1\dots 5$), bank tracking, selling prices, and official auto-substitution rules.
   - **Strategic Chip Automation**: Integrates `model/chip_optimizer.py` to trigger Wildcard 1, Wildcard 2, Free Hit (with post-FH squad restoration), Bench Boost (15-player scoring), and Triple Captain (3x multiplier).
   - Automated unit tests: `model/test_backtester.py` (3 unit tests).

---

## Frontend Next-Gen Cockpit & Repeatable Elements System (Completed)

1. **Next-Gen Frontend Cockpit Architecture & Ingestion**:
   - Integrated live matchday and 5-Gameweek multi-horizon planning state (`live_matchday_gw2.json`).
   - Integrated Dixon-Coles Poisson joint scoreline matrices ($\rho = -0.05$), clean sheet probabilities, and continuous minutes hazard indicators (`ShieldCheck`, `Warning`).
   - Built 1-Click FPL Team ID & Mini-League live sync modal with `localStorage` persistence.
   - Built Rival Radar threat matrix with differential tracking and competitor rank analysis.

2. **Repeatable Element System & Anti-Slop Design Architecture**:
   - Formalized and implemented the **5 Repeatable Element Rules**:
     1. **Concentric Mathematical Radius Scale**: $8\text{px}$ canvas $\rightarrow$ $6\text{px}$ card $\rightarrow$ $4\text{px}$ rail $\rightarrow$ $3\text{px}$ chip; completely banned $9999\text{px}$ bubble pills and $50\%$ circles.
     2. **Precision Data Chips & Micro-Flags**: Monospace squircle badges (`[GK]`, `[DEF]`, `[MID]`, `[FWD]`, `[C]`, `[V]`) and left-bordered gauge flags (`HAUL 28%`, `PK1`).
     3. **Segmented Hardware Switcher Rails**: Unified scenario switcher track replacing floating lozenge buttons.
     4. **Integrated Matchday Strategy Bars**: Machined status indicator bar with clean executive strategy copy.
     5. **Structured Tabular Asset Ledgers**: Two-column tabular rows replacing chaotic differential pill clouds.
   - Codified de-slopped FPL fan vocabulary across all views (*Matchday XI*, *5-Week Planner*, *Rival Radar*, *Danger Men*, *Clean Sheet Odds*, *Roll Free Transfer*).
   - Codified and updated the root specification in `DESIGN.md`.
   - Verified production build: `npm run build` in **862ms**, 0 errors.

---

---

## Operational Pipeline Overhaul & Live Gameweek Transition Engine (Completed)

### 1. Dynamic Frontend Data Discovery & Gameweek Switcher
- **Root Problem**: The React frontend was hardcoded to import `live_matchday_gw2.json`, meaning that as new gameweeks were solved, the UI remained locked to GW2 without manual code alterations.
- **Architectural Solution**:
  - Implemented `frontend/src/utils/loadLatestMatchday.js` utilizing Vite's `import.meta.glob('../data/live_matchday_gw*.json', { eager: true })` to dynamically discover and bundle all available gameweek datasets at build and runtime.
  - Updated `frontend/src/App.jsx` to statefully manage `selectedGw` and auto-default to the highest available gameweek index.
  - Added an institutional gameweek `<select>` switcher to `frontend/src/components/Header.jsx` aligned with `DESIGN.md` tokens.
  - Parameterized `model/enrich_frontend_data.py` to auto-detect current gameweek and dual-export Dixon-Coles matrices and continuous minutes hazard indicators to both `frontend/src/data/` and `data/<season>/`.

### 2. Live Team & Mini-League Auto-Sync Integration
- **Root Problem**: CLI pipeline executions and scheduled batch workflows were running without user identity context, defaulting to generic template rosters.
- **Architectural Solution**:
  - Parameterized `model/pipeline_automation.py` with `--team-id` and `--league-id` across CLI parsing and pipeline orchestration.
  - Wired manager profile extraction (`sync_manager_profile`) through `run_live_pipeline` -> `run_live_solver` -> `manage_gameweek` -> `fetch_fpl_entry_picks`.
  - Added **Stage 6: Frontend Enrichment** directly into `pipeline_automation.py` so solver JSON outputs are automatically enriched with Poisson scoreline distributions and minutes hazard indicators upon solver completion.
  - Updated `scripts/run_daily_sync.bat` and `.github/workflows/daily_fpl_sync.yml` with default production flags: `--team-id 9500404 --league-id 1305495`.

### 3. Live Scraping Resilience & Diagnostic Documentation
- **FBref Scraping Diagnostic**:
  - `https://fbref.com/en/comps/9/` enforces Cloudflare Bot Management returning `HTTP 403 Forbidden` on automated scripts.
  - Remediated `fbref.py`'s retry loop with immediate fail-fast error handling on 403 status codes instead of hanging in infinite exponential backoff.
  - Configured `model/build_dataset.py` to catch 403 exceptions cleanly and fall back to official FPL API appearance counts (`season_starts`, `season_minutes`) in `players_raw.csv`.
- **Understat Scraping Diagnostic & Historical Fallback**:
  - Understat transitioned to a client-side rendered Single Page Application (SPA), deprecating static HTML JavaScript variable scraping (`var teamsData = ...`).
  - Added `fallback_historical_understat()` in `understat.py` to automatically populate current season directory (`data/2026-27/understat/`) with 789 baseline team and player files from historical season `2024-25` whenever live scraping yields 0 records.
- **Windows Encoding Hardening**:
  - Resolved `charmap UnicodeEncodeError` and `UnicodeDecodeError` across `understat.py`, `global_scraper.py`, `pipeline_automation.py`, `accuracy_tracker.py`, and `gameweek_transition.py` by strictly enforcing `encoding='utf-8', errors='replace'` and ASCII-safe terminal logging.

### 4. Post-Gameweek Quantitative Accuracy Tracker (`model/accuracy_tracker.py`)
- Built autonomous evaluation engine reconciling pre-gameweek projections (`fixture_predictions_gw{N}.csv`) against actual gameweek scores (`merged_gw.csv` or `players_raw.csv`).
- Computes:
  - Overall MAE and RMSE across all rostered players.
  - Active Starters MAE and RMSE (minutes > 0).
  - Positional Breakdown (GK, DEF, MID, FWD) with directional model bias metrics.
  - Pure-Pandas Spearman rank correlation ($r_s = \text{corr}(\text{rank}(x), \text{rank}(y))$) with zero external `scipy` dependency.
  - Haul and outlier identification (top under-predictions and over-predictions).
  - Appends historical calibration log to `data/<season>/accuracy_log.csv`.
- Verified with unit tests in `model/test_accuracy_tracker.py`.

### 5. Unified One-Command Gameweek Transition Orchestrator (`model/gameweek_transition.py`)
- Created end-to-end executive orchestrator combining:
  1. Automated gameweek state detection & deadline countdown.
  2. Completed gameweek model accuracy evaluation.
  3. Live FPL API sync & price change momentum snapshot.
  4. Unified 612-player feature dataset rebuild.
  5. 11-component point projections & fixture difficulty scaling.
  6. Live manager squad sync (`9500404`), mini-league rival threat matrix (`1305495`), and multi-horizon MILP solver.
  7. Frontend JSON enrichment with Dixon-Coles matrices & continuous minutes hazard.
  8. Professional Excel report generation (`fpl_matchday_live_gw{N}.xlsx`).
  9. Executive terminal decision briefing.

### 6. Native FPL Opta Data Engine (Eliminating Understat & FBref Scraping)
- **Architectural Motivation**: Understat SPA migration and FBref Cloudflare bot blocking created brittle failure points and required historical season fallbacks.
- **Implementation**:
  - Replaced external web scraping in `model/build_dataset.py` with 100% native FPL Opta metrics.
  - Built `compute_native_participation()` to derive exact starts, substitute appearances, and squads-made counts directly from `players_raw.csv` and `merged_gw.csv`.
  - Maintained full backward compatibility by populating `fbref_starts`, `fbref_subs`, `fbref_unused_subs` aliases natively from FPL data so all downstream modules (`prediction_engine.py`, `fixture_engine.py`, `solver.py`, `excel_exporter.py`) function without breaking changes.
  - Added unit test suite in `model/test_build_dataset.py` (7 tests).
- **Test Suite Results**:
  - `python -m pytest model/ -v`: **182 passed, 0 failed** in 70.32s.
- **Live Transition Results**:
  - `python -m model.gameweek_transition --season 2026-27 --team-id 9500404 --league-id 1305495 --mode sync`: Completed in **16.9s** with 100% stage success.

### 7. Strategic 4-Chip Scenario Simulations & Frontend Reactive Lineup Solvers
- **Problem**: When selecting chip scenario buttons (Wildcard, Free Hit) on the tactical pitch, the squad on display did not change because `chip_simulations` was not being generated or preserved by the live data pipeline, and the frontend lacked client-side fallback solvers for unconstrained £100M squad optimization.
- **Implementation**:
  - Integrated full 4-chip scenario optimization (`wildcard`, `freehit`, `bboost`, `3xc`) into `model/enrich_frontend_data.py` and `model/live_manager.py`.
  - Enriched all chip squad players with Dixon-Coles matchup intelligence, home/away fixture details, and probability percentiles (`floor_p10`, `median_p50`, `ceiling_p90`, `haul_prob`).
  - Added in-browser client-side fallback heuristic in `frontend/src/components/TacticalPitch.jsx` using `allPlayers` for live squad syncs.
  - Standardized status directive banner labels and updated substitutes sidebar headers (`WILDCARD BENCH`, `FREE HIT BENCH`, `BENCH BOOST ACTIVE`).
  - Enriched both `live_matchday_gw1.json` and `live_matchday_gw2.json` with fully solved 4-chip scenario payloads.
- **Verification**:
  - `python -m pytest`: **203 passed** across all model tests.
  - `npm run build`: Frontend production build succeeded in 1.02s.

### 8. Unified Transfer Studio, Dynamic Price Velocity & Interactive Heatmap Wiring
- **Implementation**:
  - **Unified Transfer Studio**: Integrated [`TransferWorkbench.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/TransferWorkbench.jsx) into [`MultiGwPlanner.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/MultiGwPlanner.jsx) with a 3-mode segmented switcher (`5-Week Strategy Roadmap`, `Interactive Transfer Scout & H2H Bench`, `Unified Canvas`).
  - **Dynamic Price Velocity Radars**: Refactored [`MarketVelocityTicker.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/MarketVelocityTicker.jsx) to dynamically derive rising and falling assets from `allPlayersData` using real net transfer velocities, alert thresholds, and discrete trend states.
  - **Interactive Fixture Heatmap**: Connected [`FixtureHeatmap.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/FixtureHeatmap.jsx) to dynamic `selectedGw` lookahead windows and wired 1-click tile inspection to slide open the Dixon-Coles Poisson Drawer.
  - **Rival Differentials DNA Inspection**: Wired `allPlayers` and `onInspectPlayer` into [`RivalThreatMatrix.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/RivalThreatMatrix.jsx) so all mini-league differential threats and shared assets can be inspected in 1 click.
  - **Model Calibration Scorecards**: Embedded historical empirical Spearman correlation ($r_s = +0.684$) and active starters MAE benchmarks into [`ComponentStudio.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/ComponentStudio.jsx).
- **Verification**:
  - `npm run build`: Production bundle generated in 985ms.
  - `python scripts/validate_okf.py`: 0 errors verified across 43 catalog documents.

### 9. Multi-User Live Platform Phase 1: Vercel Serverless Sync & Client Solver Engine
- **Problem**: Direct browser requests to the official FPL REST API (`fantasy.premierleague.com/api/*`) are blocked by CORS policies. Running a heavy Python MILP backend on every visitor request would require paid hosting and introduce latency, conflicting with the $0/mo Vercel Hobby hosting requirement.
- **Implementation**:
  - **Vercel Serverless Sync Endpoint ([`api/sync.js`](file:///e:/Fantasy-Premier-League/api/sync.js))**: High-performance Node.js function concurrently fetching manager summary, picks, rolling transfer history (calculating 1..5 Free Transfers), and mini-league rival standings with full CORS support (`Access-Control-Allow-Origin: *`) and HTTP 503/404/400 resilience.
  - **General FPL CORS Proxy ([`api/fpl.js`](file:///e:/Fantasy-Premier-League/api/fpl.js))**: Transparent proxy route for ad-hoc FPL REST resources.
  - **Priority API Rewrites ([`vercel.json`](file:///e:/Fantasy-Premier-League/vercel.json))**: Explicit `/api/(.*)` mapping guaranteeing serverless functions precede SPA catch-all routing.
  - **Player ID Enrichment ([`scripts/enrich_player_costs.py`](file:///e:/Fantasy-Premier-League/scripts/enrich_player_costs.py))**: Attached both `id` (FPL element ID) and `player_code` (Opta code) to all 610 players in [`frontend/src/data/players_full.json`](file:///e:/Fantasy-Premier-League/frontend/src/data/players_full.json) for $O(1)$ client lookup.
  - **Client-Side Optimization Engine ([`frontend/src/utils/clientOptimizer.js`](file:///e:/Fantasy-Premier-League/frontend/src/utils/clientOptimizer.js))**: In-browser formation solver across 8 legal templates (3-5-2, 3-4-3, 4-4-2, etc.), captain/vice-captain selector, 4-strategy generator (`pure_xp`, `ceiling_p90`, `floor_p10`, `differential`), budget-constrained transfer evaluator (enforcing 3-per-club limits), chip simulator, and rival threat matrix analyzer.
  - **Unit & Contract Test Suites**: Built [`frontend/src/utils/clientOptimizer.test.js`](file:///e:/Fantasy-Premier-League/frontend/src/utils/clientOptimizer.test.js) (9 comprehensive test suites) and [`tests/test_api_sync.js`](file:///e:/Fantasy-Premier-League/tests/test_api_sync.js).
- **Verification**:
  - `node frontend/src/utils/clientOptimizer.test.js`: All 9 test suites passed cleanly.
  - `node tests/test_api_sync.js`: All serverless API contract tests passed.
  - `npm run build`: Frontend compiled cleanly in 464ms.
  - `python scripts/validate_okf.py`: 0 errors verified across 43 catalog documents.

### 10. Multi-User Live Platform Phase 2: Client-Side Optimization Engine Deepening
- **Problem**: Live squads require formation-safe mutation validation during interactive substitutions, combinatorial 2-transfer upgrades under joint budget constraints, and greedy 15-player £100.0M Free Hit/Wildcard knapsack solvers executing in $<50\text{ms}$ on the client.
- **Implementation**:
  - **Formation Invariant Validator (`validateFormation`)**: Validates 11-player lineups against all official FPL formation limits (1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD).
  - **Formation-Safe Substitution Mutator (`swapStarterBench`)**: Manages starter $\leftrightarrow$ bench swaps while enforcing formation legality and preserving captaincy.
  - **Squad Transfer Mutator (`applyTransferToSquad`)**: Applies individual player swaps with joint budget updates and strict team quota validation ($\le 3$ per Premier League club).
  - **Combinatorial Pairwise 2-Transfer Search (`evaluateTransfers`)**: Evaluates 2-FT trade pairs ($P_{out1}, P_{out2} \to P_{in1}, P_{in2}$) subject to joint budget ($\text{Cost}_1 + \text{Cost}_2 \le \text{bank} + \text{Sell}_1 + \text{Sell}_2$) and club constraints.
  - **Greedy Knapsack 15-Man Squad Solver (`solveOptimal15Squad`)**: Assembles optimal 15-player £100.0M rosters using marginal loss-per-pound downgrade optimization.
  - **Auto-Sub Bench Prioritization**: Orders outfield bench slots using auto-sub expectation $S_i = xP_i \times P(\text{App}_i) \times (1 - \text{Hook\_Hazard}_i)$.
- **Verification**:
  - `node frontend/src/utils/clientOptimizer.test.js`: **11 / 11 test suites passed cleanly**.
  - `node tests/test_api_sync.js`: **3 / 3 serverless contract tests passed**.
### 11. Multi-User Live Platform Phase 3: Frontend UI & State Wiring
- **Problem**: First-time visitors need a zero-friction, high-converting onboarding experience tailored to football fan psychology, with solid institutional styling adhering strictly to [`DESIGN.md`](file:///e:/Fantasy-Premier-League/DESIGN.md) (no glassmorphism, no emojis, concentric squircles, fixed-width tabular monospace typography), instant 1-click fallback to demo squads, and seamless live state hydration.
- **Implementation**:
  - **Onboarding Gateway Screen ([`OnboardingModal.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/OnboardingModal.jsx))**:
    - High-density institutional first-visit modal on solid `var(--bg-surface-1, #111726)` with hairline borders and concentric squircle radiuses.
    - Integrated 10-second visual Team ID Discovery Guide (`fantasy.premierleague.com/entry/[ID]/history`).
    - Optional Classic Mini-League ID input for instant Rival Radar hydration.
    - Dual CTA path: Primary live sync (`Sync My Squad & Optimize Lineup`) and 1-click instant demo fallback (`Explore Demo Squad (GW2 Top-10k Template)`).
  - **Upgraded Live Team Sync Cockpit ([`LiveTeamSyncModal.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/LiveTeamSyncModal.jsx))**:
    - Connected live sync to `/api/sync` serverless endpoint with kinetic step ticker (`[1/3] Connecting to FPL...` $\to$ `[2/3] Reconciling player DNA...` $\to$ `[3/3] Solving optimal XI...`).
    - Active squad summary card displaying live manager name, bank balance, and rolling Free Transfers.
  - **Header Manager Status Pill ([`Header.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/Header.jsx))**:
    - Active manager indicator (`👤 Arabinda (#9500404)`) with live sync status dot and 1-click trigger to open settings/sync cockpit.
  - **React State & LocalStorage Wiring ([`App.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/App.jsx))**:
    - First-visit detection via `localStorage.getItem('fpl_has_onboarded')`.
    - Live hydration pipeline: `/api/sync` payload $\to$ `buildLiveMatchdayPayload` $\to$ instant update of all 6 analytical views.
- **Verification**:
  - `npm run build`: Production bundle compiled in **504ms**.
  - `node frontend/src/utils/clientOptimizer.test.js`: **11 / 11 test suites passed**.
  - `node tests/test_api_sync.js`: **3 / 3 serverless contract tests passed**.
### 12. Multi-User Live Platform Phase 4: Automated Weekly GitHub Action Pipeline
- **Problem**: Model predictions, Dixon-Coles Poisson parameters, continuous hazard rates, and player costs must be refreshed automatically every gameweek with zero ongoing server maintenance or hosting costs ($0.00/mo operations).
- **Implementation**:
  - **Weekly Production Pipeline Workflow ([`.github/workflows/weekly_pipeline.yml`](file:///e:/Fantasy-Premier-League/.github/workflows/weekly_pipeline.yml))**:
    - Scheduled cron execution (`0 4 * * 2` — Tuesdays at 04:00 UTC, after Monday night PL fixtures) + `workflow_dispatch` for manual triggers.
    - Python 3.11 + Node.js 20 dual-runtime environment with pip and npm dependency caching.
    - Data scraping, mathematical model computation, element ID and cost reconciliation (`enrich_player_costs.py`), matchday payload compilation (`enrich_frontend_data.py`), OKF v0.2 validation, test suite execution, and automatic commit/push to `master` with `[skip ci]` to trigger Vercel deployment.
  - **Local CI & Quality Gate Orchestrator ([`scripts/run_pipeline_local.py`](file:///e:/Fantasy-Premier-League/scripts/run_pipeline_local.py))**:
    - Cross-platform CLI runner replicating the exact CI pipeline steps locally for one-command dry-run verification.
  - **Enriched Player Cost & ID Mapper ([`scripts/enrich_player_costs.py`](file:///e:/Fantasy-Premier-League/scripts/enrich_player_costs.py))**:
    - Robust multi-key matching (Opta code and web name fallback) guaranteeing 100% element ID and cost mapping for client-side solver lookups.
- **Verification**:
  - `python scripts/run_pipeline_local.py --skip-pipeline`: **All 7 pipeline & quality gate stages passed cleanly**.
  - `node frontend/src/utils/clientOptimizer.test.js`: **11 / 11 test suites passed**.
  - `node tests/test_api_sync.js`: **3 / 3 serverless contract tests passed**.
  - `python scripts/validate_okf.py`: 0 errors verified across 43 catalog documents.
  - `npm run build`: Production bundle compiled in **1.24s**.

### 13. FPL Dugout Rebranding & Complete 6-Surface Indian English Language Transformation
- **Problem**: The frontend UI suffered from technical AI slop, corporate finance terminology (*"assets"*, *"portfolios"*, *"capital allocation"*), and intimidating statistical formula notations (*"Dixon-Coles bivariate Poisson"*, *"Empirical Bayesian Shrinkage"*, *"Linear programming horizon"*). The app name *"FPL Analytics Terminal"* felt cold and unapproachable.
- **Implementation**:
  - **Rebranding**: Rebranded app to **FPL Dugout** *(Smart Squad & Matchday Planner)* with short mobile badge **Dugout**.
  - **Voice & Tone Style Guide ([`docs/voice-and-tone-guide.md`](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md))**:
    - Defined brand persona (the sharpest manager in your WhatsApp group & local EPL fan club).
    - Established 3-tier vocabulary filter (Keep sacred FPL slang, Translate stats to fan English, Ban corporate jargon).
  - **Single Source of Truth Copy Tokens ([`frontend/src/constants/copyTokens.js`](file:///e:/Fantasy-Premier-League/frontend/src/constants/copyTokens.js))**:
    - Centralized copy tokens for chip advice, tactical goals, strategy badges, metric labels, and validation messages.
  - **Comprehensive 6-Surface Transformation**:
    - *Surface 1 (My Lineup & Pitch)*: Direct chip tooltips, clear tactical directives (*"Max Points"*, *"Protect Lead"*, *"Climb Rank"*), friendly swap instructions, and plain English badges (`⚡ DIFF`, `🛡️ TEMPLATE`, `🚀 BB`).
    - *Surface 2 (Transfer Planner & Scout)*: `5-Gameweek Transfer Planner & Bank Strategy`, `5-Week Expected Total`, `Point Hits Planned (-4 pts)`, H2H workbench cards (`SELLING (OUT)` vs `BUYING (IN)`), and `Goal Threat (xG / 90 mins)`.
    - *Surface 3 (Mini-Leagues & Rivals)*: `Mini-League Head-to-Head`, `Your Captain`, `Your Differentials`, `Biggest Threat to Your Rank`, `Squad Overlap`, and `Your Points Advantage (+X pts projected lead)`.
    - *Surface 4 (Fixture Ticker & Matchups)*: `Fixture Difficulty & Schedule Ticker`, `Avg Difficulty`, `MATCH PREVIEW & PROBABILITY FORECAST`, `Win / Draw / Loss Chances`, `Most Likely Match Scorelines (Probability Grid)`, and clean sheet chances.
    - *Surface 5 (Price Trends)*: `Players Set to Rise Tonight (+£0.1m)`, `Players Set to Fall Tonight (-£0.1m)`, and `Season Chip Strategy & Double Gameweek Guide`.
    - *Surface 6 (Points Forecaster)*: `How Points Projections Work`, `Recent Form vs Long-Term Track Record`, `League Averages by Position`, and `How Accurate Are Our Points Projections?`.
  - **Mobile Responsive Polish**:
    - Fixed hero padding, chip switcher touch scroll, slider card typography, and table scrollers for mobile devices.
- **Verification**:
  - `npm run build`: Production bundle compiled in **662ms** with **0 errors**.
  - Automated browser test suite verified all 6 main tabs, interactive matchup drawer, and live state modals.

---

## Current Status & Next Horizon

All core phases, the Advanced Strategy Layer, the **Elite Enhancements Layer**, the **Matchup Intelligence Engine**, the **Live Data Pipeline Automation Engine**, the **Dixon-Coles Match Simulator**, the **Continuous Minutes Hazard Engine**, the **Risk-Adjusted CVaR & Auto-Sub Solver**, **Historical Backtesting with Chip Automation**, the **Next-Gen Frontend Cockpit with Reactive 4-Chip Projections**, the **Autonomous Gameweek Transition Orchestrator**, the **100% Native FPL Opta Data Engine**, **Phases 1–4 of the Multi-User Live Platform Rebuild**, and the **FPL Dugout Rebranding & Complete 6-Surface Fan-Friendly Copy Transformation** are **complete, robust, and production-verified**.

For complete operational playbooks and design standards:
- 👉 **[DESIGN.md](file:///E:/Fantasy-Premier-League/DESIGN.md)**
- 👉 **[docs/voice-and-tone-guide.md](file:///E:/Fantasy-Premier-League/docs/voice-and-tone-guide.md)**
- 👉 **[docs/HANDOVER_AND_ROADMAP.md](file:///E:/Fantasy-Premier-League/docs/HANDOVER_AND_ROADMAP.md)**







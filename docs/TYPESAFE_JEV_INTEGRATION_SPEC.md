# TypeSafe Jev Integration Specification: FPL Dugout

> **Document Status**: Ratified Architecture & Use-Case Specification  
> **Target Engine**: FPL Dugout Production Engine (`model/`, `frontend/`, `knowledge/`)  
> **Model Provider**: TypeSafe AI — System One Flagship Model (`jev-1.13`)  
> **Governing Standards**: [CONSTITUTION.md](file:///e:/Fantasy-Premier-League/CONSTITUTION.md), [AGENTS.md](file:///e:/Fantasy-Premier-League/AGENTS.md), [DESIGN.md](file:///e:/Fantasy-Premier-League/DESIGN.md)

---

## 1. Executive Summary & Philosophy

### 1.1 What Jev Is (and Is Not)
* **System One (S1) vs. System Two (S2)**: Traditional LLMs (Claude 3.7, GPT-4o) are S2 models designed for slow, multi-step generation, long reasoning chains, and freeform text output. Jev is an S1 model designed for **fast, intuitive, bounded semantic evaluations** that a human expert could make in a few seconds.
* **Operational Characteristics**:
  * **Latency**: 50–150ms roundtrip (enables 8–10 serial or parallel decisions per second).
  * **Cost**: ~$42 per billion input tokens (100–200× cheaper than frontier generative models).
  * **Typed Primitives**: Outputs structured primitives—**`Choice`** (categorical selection with confidence distribution), **`Score`** (ordinal rating on descriptive rubrics), and **`Noul`** (calibrated binary probability)—never markdown essays.

### 1.2 Non-Duplication Covenant (Zero Architectural Redundancy)
In accordance with the repository Constitution:
1. **Mathematical Invariants Belong to Python/Pandas**: Point prediction formulas ($C_1 \dots C_{11}$ in `model/prediction_engine.py`), Dixon-Coles Poisson goal distributions, Empirical Bayes shrinkage ($M_0 = 500$), EWMA form filters, and FPL profit retention (50%) remain purely deterministic. Jev never generates numbers that calculus or linear regression already calculate.
2. **Squad Optimization Belongs to MILP**: 15-man squad selection, formation rules, £100m budget caps, and 3-per-club quotas remain strictly solved by PuLP / HiGHS in `model/solver.py` or the client-side WebAssembly solver. Jev never picks squads from scratch.
3. **Jev's Role**: Jev acts as **programmable semantic common sense**, converting unstructured world signals (pressers, injury ambiguity, match narratives, tactical role shifts) into calibrated coefficients, typed parameter routing, and error attribution.

---

## 2. Exhaustive Use-Case Catalog

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                  UNSTRUCTURED WORLD                                │
│          Press Conferences · Match Commentary · Injury Notes · Social Rumors       │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       TypeSafe System One Engine (Jev)        │
                 │   - Choice: Categorical taxonomy & routing    │
                 │   - Score:  Descriptive ordinal calibration   │
                 │   - Noul:   Binary probability [0.0, 1.0]     │
                 └───────────────────────┬───────────────────────┘
                                         │
    ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
    ▼                  ▼                 ▼                 ▼                  ▼
[1. Feedback &     [2. Squad &       [3. Dynamic       [4. Pipeline &    [5. Matchday
 Calibration]      Tie-Breaking]     Knowledge]        Ingestion]         Cockpit UI]
 - Error Taxon.    - Captain Tie     - Defensive Line  - Presser P(start) - Rumor Gate
 - Noise Filter    - Cameo Risk      - Rotation Prior  - Rehab Duration   - Sub Context
 - Autoresearch    - Intent Router   - Set-Piece Role  - Jet-Lag Risk     - Copy Badges
```

---

### Area 1: Post-Gameweek Feedback Alignment & Continuous Learning

*Target Modules*: [`model/accuracy_tracker.py`](file:///e:/Fantasy-Premier-League/model/accuracy_tracker.py), [`model/fixture_engine.py`](file:///e:/Fantasy-Premier-League/model/fixture_engine.py), [`model/calibration.py`](file:///e:/Fantasy-Premier-League/model/calibration.py)

#### Use-Case 1.1: Semantic Error Attribution (Noise vs. Structural Failure)
* **Current State**: `accuracy_tracker.py` identifies top prediction misses (hauls and busts). `fixture_engine.py` applies blanket positional bias corrections (`load_positional_bias_corrections`). It cannot distinguish between bad luck and tactical disruption.
* **The Gap**: If Haaland has $xG = 1.6$, hits the woodwork twice, and scores 2 points, the quantitative error is $+6.0$ points. Applying a downward bias correction here is mathematically destructive. Conversely, if a winger was shifted to defensive fullback, the error is structural.
* **Jev Primitive**: `Choice`
* **Inputs (State)**:
  ```json
  {
    "player": "Erling Haaland",
    "gw": 27,
    "projected_xp": 8.4,
    "actual_points": 2,
    "match_stats": {"mins": 90, "shots": 6, "xg": 1.62, "xa": 0.15, "hit_woodwork": 2},
    "tactical_summary": "Man City dominated possession (74%). Haaland had 4 big chances saved or deflected."
  }
  ```
* **Question**:
  * *Instruction*: "Identify the primary driver behind the divergence between projected expected points and actual return."
  * *Options*:
    * `STOCHASTIC_FINISHING_NOISE`: High underlying xGI/involvement, variance in finishing/goalkeeping.
    * `SYSTEMIC_ROLE_CHANGE`: Player deployed deeper, tactical shift in team structure.
    * `EARLY_INJURY_OR_TACTICAL_SUB`: Minutes severely curtailed due to injury or game-state emergency.
    * `EXTERNAL_GAME_STATE_COLLAPSE`: Early red card or penalty conceded destroying team baseline.
* **Pipeline Action**:
  * If `STOCHASTIC_FINISHING_NOISE`: Set error weight to 0.0 in `accuracy_log.csv` so historical Bayes priors are not diluted.
  * If `SYSTEMIC_ROLE_CHANGE`: Trigger immediate prior decay for the player's role in `model/matchup_intelligence.py`.

#### Use-Case 1.2: Continuous Autoresearch Feature Discovery
* **Current State**: The 11 components ($C_1 \dots C_{11}$) are fixed. New tactical trends (e.g., transition pressing against high-line fullbacks) must be hand-coded.
* **The Gap**: TypeSafe's *Autoresearch* pattern allows an automated loop to test whether semantic questions over match summaries uncover unexplained residual variance across historical gameweeks.
* **Jev Primitive**: Batched `Score` & `Noul`
* **Implementation**:
  * Run Jev over past 5 Gameweeks of Understat/match summaries to score dimensions such as:
    * `box_congestion_level`: Score (1: Wide open to 4: Low-block bunker).
    * `opposing_fullback_press_intensity`: Score (1: Passive to 4: Relentless).
  * Check correlation with player prediction residuals. If significant ($p < 0.01$), incorporate as an empirical coefficient into $C_5$ (Fixture Difficulty Multiplier).

#### Use-Case 1.3: Clean Sheet Defeat Taxonomy
* **Current State**: Dixon-Coles Poisson model projects clean sheet probability $P(\text{CS})$. When a 65% $P(\text{CS})$ team concedes 3 goals, calibration treats it as standard variance.
* **Jev Primitive**: `Noul`
* **Question**: "Did the defensive concession stem from an individual anomaly (e.g. goalkeeping howler, freak deflection) rather than a systemic defensive collapse?"
* **Pipeline Action**: Adjusts the team defensive rating decay rate. Freak individual errors don't trigger a downgrade of the entire backline's defensive baseline.

---

### Area 2: Squad Selection, Bench Priority & Captaincy Optimization

*Target Modules*: [`model/solver.py`](file:///e:/Fantasy-Premier-League/model/solver.py), `frontend/src/components/TransferWorkbench.jsx`, client-side WebAssembly solver

#### Use-Case 2.1: High-Stakes Captaincy Dilemma Decoupler (Re-ranking)
* **Current State**: Top captain picks frequently project within $0.05 - 0.20\ xP$ of each other (e.g., Salah $6.45\ xP$ vs. Palmer $6.38\ xP$). The solver picks the higher number strictly on float precision.
* **The Gap**: FPL captaincy doubles points. When mathematical projections are effectively tied, contextual factors (tactical space, rest interval, penalty record, psychological derby intensity) dictate explosive upside.
* **Jev Primitive**: `Choice` (with confidence distribution)
* **Inputs (State)**:
  ```json
  {
    "candidate_a": {"name": "Mohamed Salah", "opponent": "EVE", "venue": "A", "xp": 6.45, "rest_days": 6},
    "candidate_b": {"name": "Cole Palmer", "opponent": "SOU", "venue": "H", "xp": 6.38, "rest_days": 3},
    "matchup_notes": "Everton playing deep compact 5-4-1 low block; Southampton deploying high line with vulnerability on transitions."
  }
  ```
* **Question**:
  * *Instruction*: "Evaluate which player has a higher probability of an explosive return (10+ points) considering opposing defensive architecture."
  * *Options*: `["CANDIDATE_A", "CANDIDATE_B", "NEUTRAL_SPLIT"]`
* **Solver Action**: If Jev selects with `confidence > 0.75`, apply a $+0.25\ xP$ tactical bonus to the winner before finalizing the captain designation in `solver.py`.

#### Use-Case 2.2: Bench Auto-Sub Cameo Hazard Scoring
* **Current State**: `solver.py` orders bench slots 2–4 strictly by descending $xP$.
* **The Gap**: A £5.0m attacker with $2.4\ xP$ might have an 80% chance of a 5-minute cameo (1 point) if benched, effectively blocking a £4.0m defender on the bench who scored 6 points.
* **Jev Primitive**: `Score`
* **Rubric Levels**:
  * `1_CLEAN_BINARY`: Player either starts 90m or is an unused sub (ideal for bench slot 1).
  * `2_OCCASIONAL_SUB`: Brings low probability of late cameo (< 20%).
  * `3_CHRONIC_CAMEO`: Regularly introduced for 10–15 minute cameo appearances (toxic for bench ordering).
* **Solver Action**: Enforce bench ordering constraint: Players with Level 3 Cameo Hazard are demoted behind Level 1 Clean Binary assets, safeguarding auto-sub utility.

#### Use-Case 2.3: Natural Language Strategy Routing to MILP Solver Parameters
* **Current State**: Users in the frontend workbench must manually set budget overrides, transfer hit tolerances, excluded teams, and variance weights via multiple dropdowns.
* **The Gap**: Managers think strategically: *"I'm chasing a 40-point deficit in my mini-league, bench Haaland, prioritize explosive differentials under 10% ownership."*
* **Jev Primitive**: `Choice` + Argument Extraction (`cookbooks/function_calling.md`)
* **Output Specification**:
  ```json
  {
    "solver_strategy": "DIFFERENTIAL_CHASE",
    "risk_profile": "HIGH_VARIANCE",
    "locked_bench": ["Erling Haaland"],
    "max_ownership_pct": 12.0,
    "min_transfer_horizon_gws": 3
  }
  ```
* **Action**: Dispatches directly to the browser solver parameters without requiring multi-second LLM reasoning.

#### Use-Case 2.4: Pareto Frontier Squad Recommendation
* **Current State**: Solver computes a single optimal squad for a fixed objective function.
* **The Gap**: Often 3 squads exist on the Pareto frontier:
  1. *The Conservative Template* (high floor, high effective ownership protection).
  2. *The Chasing Differential* (low ownership, high variance).
  3. *The Roll-Transfer Preserver* (saves 1 transfer for the upcoming double gameweek).
* **Jev Primitive**: `Choice`
* **Inputs**: User's current rank, points behind mini-league leader, remaining gameweeks.
* **Action**: Evaluates user context and selects which Pareto lineup to recommend in the UI with calibrated confidence.

---

### Area 3: Dynamic Knowledge Prior Refreshing (Eliminating Stale Dictionaries)

*Target Modules*: [`model/matchup_intelligence.py`](file:///e:/Fantasy-Premier-League/model/matchup_intelligence.py), [`model/rotation_intelligence.py`](file:///e:/Fantasy-Premier-League/model/rotation_intelligence.py), [`model/set_pieces.py`](file:///e:/Fantasy-Premier-League/model/set_pieces.py)

#### Use-Case 3.1: Automated `TACTICAL_ARCHETYPES` Refresh
* **Current State**: In `matchup_intelligence.py`, `TACTICAL_ARCHETYPES` contains hardcoded dictionary values (`Spurs: {'defensive_line': 1.20, 'transition_vulnerability': 1.18}`). When a manager tweaks their system or suffers center-back injuries, this static table drifts.
* **Jev Primitive**: Two parallel `Score` questions executed weekly on post-match reports:
  1. *Defensive Line Height*: Scale 1 (Ultra Low Block / Deep Box) to 5 (Ultra High Line / Aggressive Offside Trap).
  2. *Transition Vulnerability*: Scale 1 (Impervious Counter-Press) to 5 (High Space Exploitation on Turnover).
* **Engine Action**: Automatically calculates a rolling 3-week EWMA of tactical archetypes and writes to `knowledge/datasets/tactical_archetypes.json`.

#### Use-Case 3.2: Dynamic Manager Rotation Propensity
* **Current State**: In `rotation_intelligence.py`, `ROTATION_HEAVY_MANAGERS = ['Man City', 'Liverpool']` is hardcoded.
* **The Gap**: Managers adapt based on squad depth and cup eliminations.
* **Jev Primitive**: `Score`
* **Question**: "Evaluate manager's tactical willingness to rotate key starters during congested 3-match weeks (1: Rigid Starting XI to 5: Constant Extreme Rotation)."
* **Engine Action**: Replaces binary list membership with a continuous penalty multiplier in `compute_rotation_hazard()`.

#### Use-Case 3.3: Set-Piece Hierarchy Usurpation Tracking
* **Current State**: `model/set_pieces.py` tracks penalty and corner takers. When a new player signs or a designated taker misses a penalty, manual intervention is needed.
* **Jev Primitive**: `Choice`
* **Question**: "Based on match events and manager post-match comments, what is the status of the primary penalty taker role?"
* **Options**: `["SECURE_INCUMBENT", "SHARED_DUAL_DUTY", "USURPED_BY_CONTENDER", "TACTICAL_ROTATION"]`
* **Engine Action**: Dynamically scales penalty xG share in `model/prediction_engine.py` component $C_2$.

---

### Area 4: Weekly Pipeline Ingestion & Pre-Deadline Signals

*Target Modules*: [`model/pipeline_automation.py`](file:///e:/Fantasy-Premier-League/model/pipeline_automation.py), [`.github/workflows/weekly_pipeline.yml`](file:///e:/Fantasy-Premier-League/.github/workflows/weekly_pipeline.yml), [`model/minutes_model.py`](file:///e:/Fantasy-Premier-League/model/minutes_model.py)

#### Use-Case 4.1: Thursday/Friday Press Conference Minutes Calibrator
* **Current State**: FPL API provides coarse status codes (`75%`, `50%`, `25%`, `0%`). Managers routinely use deceit ("mind games") or cautious phrasing.
* **The Gap**: Static mapping (`75% -> 0.75`) in `rotation_intelligence.py` fails on nuance:
  * *"He trained lightly, we'll make a decision tomorrow"* vs. *"He's fit, available, and ready to go."*
* **Jev Primitive**: `Noul` + `Score`
* **Input (State)**:
  ```json
  {
    "player": "Bukayo Saka",
    "manager": "Mikel Arteta",
    "quote": "Bukayo was able to complete part of the session yesterday. We have another session today and we will see how he responds.",
    "historical_arteta_veracity_score": 0.45
  }
  ```
* **Questions**:
  * *Noul*: "Probability that player is included in the matchday squad (starts or bench)?"
  * *Score*: "Expected starting capacity: [1: Sub cameo only (<30m), 2: Managed start (60m sub), 3: Full unconstrained 90m]."
* **Engine Action**: Directly updates `p_start` and expected minutes in `model/minutes_model.py`.

#### Use-Case 4.2: Return-from-Injury Ramp-Up Curve
* **Current State**: Once marked fit, players are often modeled at their full historical average minutes ($~85$ mins), ignoring gradual rehabilitation ramps.
* **Jev Primitive**: `Score`
* **Question**: "Rate the re-integration stage following multi-week layoff (1: Precautionary 20-30 min cameo, 2: 60-min substitution ceiling, 3: Full match fitness)."
* **Engine Action**: Caps maximum minutes ceiling in `model/minutes_model.py` for Gameweek $N$.

#### Use-Case 4.3: International Break Jet-Lag & Travel Congestion Hazard
* **Current State**: Standard rest interval calculation (`days_rest`).
* **The Gap**: A South American player playing in La Paz or Buenos Aires on Wednesday night and arriving in London on Friday midday suffers acute travel fatigue even if technically resting 48h+.
* **Jev Primitive**: `Noul`
* **Question**: "Is there elevated rotational or minutes restriction risk due to intercontinental travel and late arrival?"
* **Engine Action**: Multiplies minutes hazard by $0.85\times$ for the immediate weekend fixture.

---

### Area 5: Frontend Cockpit & Live Matchday Intelligence

*Target Modules*: [`frontend/src/components/MarketVelocityTicker.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/MarketVelocityTicker.jsx), [`frontend/src/components/TacticalPitch.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/TacticalPitch.jsx), [`frontend/src/components/PlayerDNAInspector.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/PlayerDNAInspector.jsx)

#### Use-Case 5.1: Transfer Market Rumor & Panic Gate
* **Current State**: `MarketVelocityTicker.jsx` displays net transfer velocity. When 50,000 managers panic-sell an asset, the ticker sounds an alarm.
* **The Gap**: Often selling is triggered by domestic cup suspensions (which do not affect PL) or unverified social media claims.
* **Jev Primitive**: `Noul`
* **Question**: "Does this reported development legally or physically impair the player's eligibility for the upcoming Premier League gameweek?"
* **Frontend Action**: If `False`, displays a subtle reassurance pill (`SURFACE_SCOPE_INFO`: "False Alarm: Carabao Cup suspension does not apply to PL") to stop the user taking panic hits.

#### Use-Case 5.2: Live Matchday Substitution Taxonomy
* **Current State**: Live feeds broadcast substitutions with minute timestamps (e.g. "58' Sub: Isak OFF, Wilson ON").
* **The Gap**: FPL managers need to know instantly if they should hold or sell ahead of the next deadline.
* **Jev Primitive**: `Choice` (executed in <100ms via Edge serverless function)
* **Taxonomy Options**:
  * `TACTICAL_PRESERVATION`: Team leading comfortably, protecting key asset. (Hold).
  * `PERFORMANCE_HOOK`: Poor display, tactical failure. (Watchlist risk).
  * `ACUTE_MUSCLE_INJURY`: Grabbed hamstring/groin, went straight down tunnel. (Immediate Sell Trigger).
* **Frontend Action**: Tags the live player node in `TacticalPitch.jsx` with real-time actionable color telemetry.

#### Use-Case 5.3: Strict-Copy Tactical Badge Assignment
* **Current State**: Player cards need concise badges ("Target Man", "High Ceiling", "Rotation Risk") aligned with [`frontend/src/constants/copyTokens.js`](file:///e:/Fantasy-Premier-League/frontend/src/constants/copyTokens.js) and [`docs/voice-and-tone-guide.md`](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md).
* **The Gap**: Traditional LLMs generate long adjectives or corporate jargon violating repo rules.
* **Jev Primitive**: `Choice` constrained strictly to the pre-registered enum tokens in `copyTokens.js`.
* **Action**: 100% compliant badge assignment with zero risk of copy drift or forbidden terms.

---

## 3. Comparative Architecture: Current vs. Jev-Enhanced

| Dimension | Current System | Jev-Enhanced System | Benefit |
| :--- | :--- | :--- | :--- |
| **Weekly Accuracy Audit** | Calculates numerical MAE/RMSE; uniform positional bias. | Classifies errors into Noise vs. Structural Role Changes. | Prevents damaging Bayesian priors due to bad finishing luck. |
| **Tactical Archetypes** | Hardcoded static dictionaries in `matchup_intelligence.py`. | Rolling weekly S1 `Score` ratings (1–5) on match reports. | Adapts to manager sackings and tactical pivots instantly. |
| **Captaincy Ties** | Arbitrary floating point tie-break ($6.45$ vs $6.44$). | Calibrated S1 pairwise `Choice` on explosive upside. | Higher double-point ($2\times$) conversion rate. |
| **Press Conference Nuance** | Static FPL API flags ($75\% \to 0.75$, $50\% \to 0.40$). | S1 `Noul` + `Score` on raw press conference quotes. | Catches manager mind games and accurate starting probabilities. |
| **Bench Auto-Sub Ordering** | Strictly ordered by descending $xP$. | Evaluates Cameo Risk to demote 5-minute cameo blockers. | Unlocks maximum utility from auto-substitutions. |
| **Transfer Panic Ticker** | Displays raw selling velocity. | S1 `Noul` gate on rumor validity & league eligibility. | Prevents unnecessary $-4$ transfer hits. |

---

## 4. Technical Implementation & Bridge Architecture

To maintain the architectural standards in [`AGENTS.md`](file:///e:/Fantasy-Premier-League/AGENTS.md), all TypeSafe interactions are encapsulated in a single bridge module:

```
model/
├── typesafe_bridge.py        <-- [NEW] Singleton client, caching, retries, mock fallbacks
├── feedback_aligner.py       <-- [NEW] Post-GW Error Attribution Loop (Use-Case 1.1)
├── presser_intelligence.py   <-- [NEW] Press conference parser & minutes scaler (Use-Case 4.1)
├── solver.py                 <-- [MODIFIED] Captaincy tie-break & bench cameo hazard hook
└── matchup_intelligence.py   <-- [MODIFIED] Consumes dynamic tactical archetype scores
```

### 4.1 The Bridge Implementation Pattern (`model/typesafe_bridge.py`)
```python
"""TypeSafe AI System One Bridge for FPL Dugout.

Encapsulates all Jev-1.13 API interactions with automatic offline fallbacks,
retry policies, and local JSON disk caching.
"""
import os
from typing import Dict, Any, Optional
from typesafe_sdk import TypeSafeClient, Choice, Score, Noul

class FPLTypeSafeBridge:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        self.model = "jev-1.13"
        self._client = TypeSafeClient(api_key=self.api_key) if self.api_key else None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def evaluate_failure_mode(self, player_context: Dict[str, Any]) -> Dict[str, Any]:
        """Categorizes prediction misses into variance vs structural shifts."""
        if not self.is_available:
            return {"failure_mode": "STOCHASTIC_FINISHING_NOISE", "confidence": 0.5}
        
        response = self._client.questions.ask(
            model=self.model,
            state=player_context,
            questions={
                "failure_mode": Choice(
                    instruction="Classify root cause of divergence between projected xP and actual return.",
                    options={
                        "STOCHASTIC_FINISHING_NOISE": "High xG/xA, normal minutes, finishing variance.",
                        "SYSTEMIC_ROLE_CHANGE": "Player deployed in different tactical role/deeper position.",
                        "EARLY_SUB_OR_INJURY": "Minutes cut short (<60m) by tactical substitution or knock.",
                        "EXTERNAL_GAME_STATE": "Team red card or abnormal match collapse."
                    }
                ),
                "structural_shift": Noul(
                    instruction="Is this divergence likely to persist into the next 3 gameweeks?"
                )
            }
        )
        return {
            "failure_mode": response.answers["failure_mode"].value,
            "confidence": response.answers["failure_mode"].confidence,
            "structural_shift_prob": response.answers["structural_shift"].probability
        }
```

---

## 5. Execution Budgets, Latency & Reliability Guardrails

1. **GitHub Actions Workflow Integration**:
   * Runs in `.github/workflows/weekly_pipeline.yml` during Tuesday 04:00 UTC pipeline execution.
   * Batch evaluates top 15 outliers + 20 press conferences in under **4 seconds total** (leveraging parallel HTTP pipelining).
   * Token cost per weekly run: ~15,000 tokens = **$0.00063 per week** ($0.024 for an entire 38-game season).
2. **Serverless & Frontend Latency Guardrails**:
   * As mandated by [ADR 0001](file:///e:/Fantasy-Premier-League/docs/adr/0001-serverless-cors-proxy-and-client-side-solver.md), all global predictions are compiled into static JSON (`players_full.json`).
   * Live client-side queries (natural language solver router, live substitution tagger) run through the lightweight `/api/sync` proxy with a hard 250ms timeout.
3. **Graceful Degradation (Offline Fallback Guarantee)**:
   * If `TYPESAFE_API_KEY` is missing or the endpoint is unreachable, all methods in `FPLTypeSafeBridge` gracefully return neutral deterministic defaults (e.g. treat errors as standard variance, order bench purely by mathematical $xP$). The core model and MILP solver never crash.

---

## 6. Implementation Roadmap

- [ ] **Phase 1: Bridge & Feedback Alignment**
  - Implement `model/typesafe_bridge.py` with full offline fallback.
  - Connect `model/accuracy_tracker.py` to `evaluate_failure_mode` to filter noise out of `accuracy_log.csv`.
- [ ] **Phase 2: Solver Enhancements (Captaincy & Bench Cameo)**
  - Add captaincy tie-breaking hook in `model/solver.py` for $|\Delta xP| \le 0.20$.
  - Add bench cameo hazard scoring to prevent auto-sub blockages.
- [ ] **Phase 3: Dynamic Knowledge Prior Automation**
  - Replace static `TACTICAL_ARCHETYPES` in `matchup_intelligence.py` with weekly rolling S1 evaluations.
  - Automate manager press conference quote calibration for Friday deadline runs.

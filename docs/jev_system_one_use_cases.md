# TypeSafe Jev (System One) Use Cases in FPL Dugout

This document is the master architectural reference catalog of **TypeSafe AI's Jev (System One)** integrations within FPL Dugout. It defines the core philosophy, current implementations, and future roadmap for embedding calibrated decision primitives into the modeling and software development lifecycle.

---

## 1. Core Philosophy: System 1 vs System 2 Architecture

Inspired by Daniel Kahneman's *Thinking, Fast and Slow*, AI workflows in FPL Dugout are partitioned into two complementary tiers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              SYSTEM 2: DELIBERATE, STRATEGIC REASONING & OPTIMIZATION       │
│  • Multi-Gameweek Horizon Linear Programming (model/solver.py)              │
│  • Macro Chip Deployment Timing (Wildcard, Free Hit, Bench Boost)           │
│  • Weekly Reflection Loop: Auditing prediction errors & revising rubrics    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Sets boundaries, objectives, and
                                       │ risk tolerances
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 SYSTEM 1: FAST, CALIBRATED DECISIONS (JEV)                  │
│  • Response Latency: ~150–250 ms | Cost: ~20×–200× cheaper than LLMs        │
│  • Zero text generation, no stream parsing; outputs strictly typed JSON     │
│  • Atomic Primitives: Choice (Categorical), Score (Rubric), Noul (Prob)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Calibrated probabilities & scores
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DETERMINISTIC MATHEMATICAL ENGINE                       │
│  • 11-Component Point Prediction Engine (C1 … C11 in prediction_engine.py)  │
│  • Empirical Bayes Shrinkage (M0 = 500.0)                                   │
│  • Poisson Clean Sheet & Goal Expectancy Formulations                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Three Atomic Primitives of Jev

1. **`Noul` (Condition Probability)**: Evaluates the calibrated probability ($0.0 \dots 1.0$) that a proposition is true (e.g., $P(\text{Start})$, $P(\text{Sub 60 Hook})$, $P(\text{Data Corruption})$).
2. **`Score` (Continuous Degree on Ordered Rubric)**: Grades an observation against an ordered spectrum of $2 \dots 11$ criteria (e.g., Defensive Line Depth $1 \dots 5$, On-Call Pipeline Severity $0 \dots 3$, Manager Candor Level $0 \dots 3$).
3. **`Choice` (Categorical Classification)**: Selects one option among up to 255 discrete possibilities, returning probability distributions across all choices (e.g., Tactical Profile, Injury Severity Category, Strategic Intent Posture).

---

## 2. Catalog of Jev Use Cases

### Summary Matrix

| # | Use Case Area | Target Module | Primitive(s) | Status | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Dynamic Tactical Archetypes** | [`model/tactical_prior_updater.py`](file:///e:/Fantasy-Premier-League/model/tactical_prior_updater.py) | `Score` (1–5), `Choice` | **Implemented** | Replaces static defensive line dictionaries with dynamic scouting evaluations. |
| **2** | **Press Conference & Injury Triage** | [`model/press_conference_intelligence.py`](file:///e:/Fantasy-Premier-League/model/press_conference_intelligence.py) | `Noul`, `Choice`, `Score` | **Implemented** | Decodes manager quotes, injury flags, and sub-60 hook hazards into starter probabilities. |
| **3** | **Pipeline Automated Guardrail** | [`model/pipeline_guardrail.py`](file:///e:/Fantasy-Premier-League/model/pipeline_guardrail.py), [`model/pipeline_automation.py`](file:///e:/Fantasy-Premier-League/model/pipeline_automation.py) | `Score` (0–3), `Noul`, `Choice` | **Implemented** | Pre-deadline on-call severity grader that halts automated transfers on data corruption or solver anomalies. |
| **4** | **Qualitative Constitution Linter** | [`scripts/jev_constitution_linter.py`](file:///e:/Fantasy-Premier-League/scripts/jev_constitution_linter.py) | `Score` (0–3), `Noul`, `Choice` | **Implemented** | Audits git diffs for tokenized CSS compliance, voice-and-tone rules, and zero-hex invariants with AX self-healing hints. |
| **5** | **Set-Piece Succession Deduction** | [`model/set_pieces.py`](file:///e:/Fantasy-Premier-League/model/set_pieces.py) | `Choice`, `Score` | **Planned (Phase 3)** | Elects secondary penalty/corner takers when primary talismans are benched or injured. |
| **6** | **Strategic Posture Router** | [`model/live_manager.py`](file:///e:/Fantasy-Premier-League/model/live_manager.py), `frontend/` | `Choice`, `Score` | **Planned (Phase 3)** | Maps natural language manager queries to typed MILP solver hyperparams (`--strategy`, $\lambda_{\text{EO}}$). |
| **7** | **Context & OKF Spec Router** | Agent / CI tooling | `Choice` | **Planned (Phase 3)** | Prunes 10k+ context tokens by selecting the exact OKF dataset spec needed for a task. |
| **8** | **Adversarial Stress Testing** | [`model/match_simulator.py`](file:///e:/Fantasy-Premier-League/model/match_simulator.py) | `Noul` | **Planned (Phase 4)** | Runs 1,000 parallel matchday scenarios to detect edge-case solver bugs (e.g. invalid bench orders). |
| **9** | **Price Momentum Velocity Classifier**| [`model/price_predictor.py`](file:///e:/Fantasy-Premier-League/model/price_predictor.py) | `Choice`, `Score` | **Planned (Phase 4)** | Classifies community transfer cascades (`viral_surge`, `panic_dump`) for early transfer warnings. |

---

## 3. Detailed Specifications

### 1. Dynamic Tactical Archetypes & Player Affinities
- **Module**: [`model/tactical_prior_updater.py`](file:///e:/Fantasy-Premier-League/model/tactical_prior_updater.py)
- **Integration**: Feeds into [`model/matchup_intelligence.py`](file:///e:/Fantasy-Premier-League/model/matchup_intelligence.py).
- **Description**: Evaluates scouting observations to rate a team's defensive line height ($1 \dots 5$) and transition vulnerability ($1 \dots 5$), then applies Exponential Weighted Moving Average (EWMA, $\alpha = 0.30$) smoothing. Also categorizes player profiles (`transition_playmaker`, `poacher`, `cross_specialist`).
- **Primitives**:
  - `defensive_line_depth`: `Score` (1 = Deep Low-Block, 5 = Suicidal High Line).
  - `transition_vulnerability`: `Score` (1 = Impervious, 5 = Severe Concession).
  - `player_affinity`: `Choice` across attacking archetype profiles.

### 2. Press Conference & Injury NLP Triage ("The Roulette Decoder")
- **Module**: [`model/press_conference_intelligence.py`](file:///e:/Fantasy-Premier-League/model/press_conference_intelligence.py)
- **Integration**: Feeds into [`model/rotation_intelligence.py`](file:///e:/Fantasy-Premier-League/model/rotation_intelligence.py) (`compute_rotation_hazard` and `apply_rotation_dampening`).
- **Description**: Replaces coarse discrete FPL API flags (75% $\to$ 0.75, 50% $\to$ 0.40) with continuous calibrated probabilities by analyzing manager quotes, injury news, turnaround rest days, and manager candor history.
- **Primitives**:
  - `p_start`: `Noul` (probability of starting the upcoming match).
  - `sub_60_hook_risk`: `Noul` (probability of substitution before minute 60).
  - `cameo_risk`: `Noul` (probability of being benched and making a 10–25 min cameo).
  - `injury_severity`: `Choice` (`fit_to_start`, `minor_doubt_likely_start`, `managed_minutes_risk`, `bench_cameo_only`, `unfit_ruled_out`).
  - `manager_candor_score`: `Score` (0 = transparent like Postecoglou, 3 = extreme mind games like Arteta or Guardiola).

### 3. Automated Pipeline Sanity Guardrail & On-Call Severity
- **Module**: [`model/pipeline_automation.py`](file:///e:/Fantasy-Premier-League/model/pipeline_automation.py)
- **Integration**: Matchday unattended execution pipeline.
- **Description**: Before committing transfers to the official FPL account or generating production outputs, Jev grades the proposed transfer plan. If an anomalous transfer (e.g. selling an uninjured £14M asset for an inactive £4.0M sub) is detected, Jev halts the pipeline and alerts the manager.
- **Primitives**:
  - `pipeline_severity_score`: `Score` (0 = Routine healthy run, 1 = Minor warning, 2 = Suspicious anomaly, 3 = Fatal corruption / emergency abort).
  - `abort_execution`: `Noul` (true if pipeline should halt execution immediately).

### 4. Qualitative Constitution & DESIGN.md Linter
- **Module**: `scripts/jev_constitution_linter.py`
- **Integration**: Pre-commit hook & CI verification step.
- **Description**: Verifies that new code changes comply with [`CONSTITUTION.md`](file:///e:/Fantasy-Premier-League/CONSTITUTION.md), [`DESIGN.md`](file:///e:/Fantasy-Premier-League/DESIGN.md), and [`docs/voice-and-tone-guide.md`](file:///e:/Fantasy-Premier-League/docs/voice-and-tone-guide.md). Catches hardcoded hex colors, arbitrary pill styles, unregistered UI components, and corporate/mathematical jargon.
- **Primitives**:
  - `has_untokenized_styles`: `Noul` (flags hardcoded hex/rgb colors).
  - `voice_and_tone_grade`: `Score` (0–3 rating of matchday tone).
  - `constitution_verdict`: `Choice` (`clean`, `warning`, `blocked`).

### 5. Set-Piece & Penalty Succession Deduction
- **Module**: [`model/set_pieces.py`](file:///e:/Fantasy-Premier-League/model/set_pieces.py)
- **Integration**: Points prediction engine ($\Delta C_8$ Goal xP, $\Delta C_7$ Assist xP).
- **Description**: Dynamically elects the active designated penalty, direct free-kick, and corner takers from the starting XI when the primary taker (e.g. Saka, Palmer, Fernandes) is injured or benched, preserving $+0.79 \text{ xG}$ equity.
- **Primitives**:
  - `active_penalty_taker`: `Choice` selecting among starting outfield players.
  - `corner_share_estimate`: `Score` (0 = no deliveries, 3 = primary crosser on both wings).

### 6. Strategic Posture & Chip Semantic Router
- **Module**: [`model/live_manager.py`](file:///e:/Fantasy-Premier-League/model/live_manager.py) & `frontend/`
- **Integration**: Matchday Cockpit & Transfer Workbench natural language interface.
- **Description**: Translates natural language user prompts (e.g. *"Trailing by 40 pts in my mini-league, rival owns Haaland"*) into typed mathematical solver hyperparams (`strategy="differential_chase"`, `eo_weight=1.5`, `chip="hold"`).
- **Primitives**:
  - `strategic_posture`: `Choice` (`pure_xp`, `rank_protect`, `differential_chase`, `crisis_repair`).
  - `risk_tolerance`: `Score` (1 = ultra-conservative, 5 = high-variance differential chase).
  - `recommended_chip`: `Choice` (`none`, `wildcard`, `free_hit`, `triple_captain`, `bench_boost`).

### 7. Dynamic Skill & Spec Router (Context Optimization)
- **Module**: Agent tool selector / development tooling.
- **Integration**: Workspace agent workflows.
- **Description**: Sits in front of coding agents to select the exact 1–2 OKF specifications or skills needed for a task from the 50+ available options, cutting 10,000+ unnecessary tokens from the prompt window and preventing misrouting.
- **Primitives**:
  - `selected_spec`: `Choice` among OKF dataset markdown files.
  - `requires_skill`: `Noul` indicating whether a specialized skill file must be loaded.

### 8. Adversarial Simulation & Matchday Stress Tester
- **Module**: [`model/match_simulator.py`](file:///e:/Fantasy-Premier-League/model/match_simulator.py)
- **Integration**: Pre-deployment solver verification suite.
- **Description**: Runs 1,000 parallel matchday edge-case scenarios (early red card, goalkeeper injury, triple clean-sheet wipeout) and uses Jev to verify solver sanity and auto-sub prioritization across all simulated permutations.
- **Primitives**:
  - `solver_validity`: `Noul` (verifies valid squad, budget, and bench ordering).
  - `sub_priority_sane`: `Noul` (verifies auto-subs reflect expected minutes).

### 9. Price Momentum & Panic Dump Velocity Classifier
- **Module**: [`model/price_predictor.py`](file:///e:/Fantasy-Premier-League/model/price_predictor.py)
- **Integration**: Team value optimizer & transfer timing advisory.
- **Description**: Analyzes net transfer velocity alongside social/influencer momentum to classify transfer waves and forecast midnight price rises/falls with calibrated confidence.
- **Primitives**:
  - `transfer_momentum`: `Choice` (`viral_surge`, `steady_accumulation`, `panic_dump`, `stagnant`).
  - `price_change_imminent`: `Noul` (probability of rise/fall within 24 hours).

---

## 4. Engineering Standards for Jev Integrations

All current and future Jev modules in this repository must comply with the following standards:

1. **Bridge Encapsulation**: All network calls must pass through [`model/typesafe_bridge.py`](file:///e:/Fantasy-Premier-League/model/typesafe_bridge.py). No direct HTTP requests or SDK imports outside this bridge.
2. **Local Disk Caching**: Requests are SHA-256 hashed and cached in `data/.cache/typesafe/` to guarantee zero redundant token costs or duplicate network roundtrips.
3. **Safe Offline Fallback (Mock Mode)**: Every Jev integration must provide deterministic fallback values so that tests and automated pipelines run safely without requiring an active API key or internet access.
4. **Strict Output Typing**: Raw responses must be parsed into dataclasses (`NoulResult`, `ScoreResult`, `ChoiceResult`) before entering mathematical modeling layers.

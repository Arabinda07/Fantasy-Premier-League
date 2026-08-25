# Design Specification: Elite FPL Enhancements Engine

**Document Type:** Technical Architecture & Implementation Spec  
**Target Modules:** `model/set_pieces.py`, `model/ownership_engine.py`, `model/price_predictor.py`, `model/rotation_intelligence.py`  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  
**Date:** 2026-08-25  

---

## 1. Executive Summary & Strategic Rationale

While the core prediction engine ($C_1 \dots C_{11}$) and Multi-Horizon MILP solver optimize for theoretical expected points ($\text{xP}$), competitive top-1k / top-10k FPL performance requires modeling the **game-theoretic, market, and tactical micro-mechanics** of Fantasy Premier League:

1. **Set-Piece & Penalty Specialist Equity**:
   - Penalties ($+0.79\text{ xG}$ per kick) and corners/indirect free kicks are high-value point sources that take weeks for historical rolling form to adjust to when taker hierarchies change.
2. **Effective Ownership (EO) & Game Theory Optimization**:
   - In competitive ranks, raw xP ignores rank variance. High-EO talismans ($\text{EO} > 150\%$) act as essential rank shields, while low-EO differentials ($\text{EO} < 10\%$) provide explosive rank climbing potential.
3. **Price Change & Team Value Forecaster**:
   - Growing team budget from £100.0M to £103.0M–£105.0M allows fielding 3+ premium players later in the season; avoiding -£0.1M drops preserves transfer flexibility.
4. **Tactical Rotation & Press Conference Hazard Intelligence**:
   - Sub-60-minute substitutions, short rest between midweek European fixtures (UCL/UEL), and manager press conference injury flags significantly impact $P(\text{Start})$ and $P(60+)$.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               ELITE ENHANCEMENTS ENGINE ARCHITECTURE                             │
├─────────────────────┬──────────────────────┬──────────────────────┬──────────────────────────────┤
│ 1. Set-Pieces       │ 2. Ownership & EO    │ 3. Price Predictor   │ 4. Rotation Hazard           │
│   (set_pieces.py)   │   (ownership.py)     │   (price_predictor.py│   (rotation.py)              │
├─────────────────────┼──────────────────────┼──────────────────────┼──────────────────────────────┤
│ • PK / FK / CK Taker│ • Top-10k EO Model   │ • Net Transfer       │ • European Rest Days Decay   │
│   Hierarchies (1/2/3│ • Rank-Adjusted      │   Velocity Tracker   │ • Sub-60 Min Hook Hazard     │
│ • Non-Penalty xG    │   Utility Function   │ • ±£0.1M Rise/Fall   │ • Live Press Conference &    │
│   Decomposition     │ • Shield vs Upside   │   Threshold Warning  │   News NLP Probability Damp  │
│ • Direct xG/xA add  │   Differential Mode  │ • Team Value Builder │ • Starter Minutes Correction │
└─────────────────────┴──────────────────────┴──────────────────────┴──────────────────────────────┘
```

---

## 2. Mathematical Formulation of the 4 Elite Modules

### Module 1: Set-Piece & Penalty Hierarchy (`model/set_pieces.py`)

#### 1. Data Ingestion & Role Matrices
FPL `players_raw.csv` provides official set-piece indicators:
- `penalties_order` (1.0 = first choice, 2.0 = second choice)
- `direct_freekicks_order` (1.0 = primary direct shooter)
- `corners_and_indirect_freekicks_order` (1.0 = primary crosser)

#### 2. Baseline Penalty Equity Formula
Premier League teams average $\lambda_{\text{PK}} \approx 0.18$ to $0.22$ penalties awarded per 90 minutes. A penalty has an average conversion rate $\kappa_{\text{PK}} \approx 0.78$ and expected goals $\text{xG}_{\text{PK}} = 0.79$.
If a player is the primary penalty taker ($\text{order} = 1$) with playing time on pitch:
$$\Delta \text{xG}_{\text{PK}} = P(\text{on pitch}) \cdot \lambda_{\text{PK}}(\text{Team}) \cdot 0.79$$
$$\Delta C_8(\text{Goal xP}) = \Delta \text{xG}_{\text{PK}} \cdot \text{Goal\_Points}(\text{Position}) \cdot \kappa_{\text{PK}}$$

If a player is secondary taker ($\text{order} = 2$), equity applies conditioned on the primary taker being absent ($1 - P(\text{Primary on pitch})$).

#### 3. Corner & Free-Kick Assist Equity
Primary corner takers ($\text{order} = 1$) on high set-piece volume teams receive:
$$\Delta \text{xA}_{\text{SetPiece}} = P(\text{on pitch}) \cdot \text{Team\_CK\_per\_90} \cdot \text{xA\_per\_Corner} \approx 0.08\text{ to }0.14\text{ xA90}$$
$$\Delta C_7(\text{Assist xP}) = \Delta \text{xA}_{\text{SetPiece}} \cdot 3.0$$

---

### Module 2: Effective Ownership (EO) & Game Theory (`model/ownership_engine.py`)

#### 1. Effective Ownership Definition
$$\text{EO}_i = \text{Ownership}_i + \text{Captaincy\_Share}_i + \text{Triple\_Captaincy\_Share}_i$$
In top-tier leagues and top-10k ranks, captaincy heavily concentrates on top 2–3 assets (e.g. 60–80% captaincy share), driving talisman EO above $150\%–180\%$.

#### 2. Rank-Adjusted Utility for Solver & Live Manager
We define a configurable objective utility:
$$\text{Utility}_i = \text{xP}_i + \lambda_{\text{strategy}} \cdot \Phi(\text{EO}_i, \text{RiskProfile})$$

Where:
- **`'rank_protect'` (Protect High Rank / Leaderboard Defense)**:
  $$\Phi(\text{EO}_i) = \begin{cases} +0.5 \times (\text{EO}_i - 1.0) & \text{if } \text{EO}_i > 1.0 \\ 0 & \text{otherwise} \end{cases}$$
  Penalizes fading high-EO captains to minimize rank drawdowns.
- **`'differential_chase'` (Rank Climbing / Chasing Mini-League)**:
  $$\Phi(\text{EO}_i) = \begin{cases} +1.2 \times (0.20 - \text{EO}_i) & \text{if } \text{EO}_i < 0.20 \\ -0.5 \times (\text{EO}_i - 1.0) & \text{if } \text{EO}_i > 1.0 \end{cases}$$
  Rewards low-owned differentials with comparable xP ceilings.
- **`'pure_xP'` (Default / Mathematical Neutral)**:
  $\lambda_{\text{strategy}} = 0.0$.

---

### Module 3: Price Change & Team Value Forecaster (`model/price_predictor.py`)

#### 1. Price Momentum Tracking
Tracks the net transfer velocity during the active gameweek event:
$$\text{Net\_Transfers}_i = \text{transfers\_in\_event}_i - \text{transfers\_out\_event}_i$$
$$\text{Transfer\_Velocity\_Ratio}_i = \frac{\text{Net\_Transfers}_i}{\text{Threshold}(\text{Ownership}_i, \text{Total\_Players})}$$

#### 2. Price Change Alert Classifications
- `RISING_LOCK` ($\ge 100\%$ threshold): Price rise $+£0.1\text{M}$ expected within 24 hours.
- `RISING_ALERT` ($\ge 75\%$ threshold): Price rise imminent before next deadline.
- `FALLING_ALERT` ($\le -75\%$ threshold): Price fall $-£0.1\text{M}$ imminent.
- `FALLING_LOCK` ($\le -100\%$ threshold): Price fall expected within 24 hours.
- `STABLE`: Low transfer momentum.

#### 3. Strategic Integration with Live Manager
- Recommends early transfer execution when a target is in `RISING_LOCK` and current squad asset is in `FALLING_LOCK`, saving £0.2M in purchasing power.

---

### Module 4: Manager Rotation & Tactical Hazard Engine (`model/rotation_intelligence.py`)

#### 1. Midweek Congestion & European Rest Hazard
For teams participating in European competitions (UCL / UEL / UECL) or domestic cups with $<72\text{ hours}$ turnaround:
$$\text{Hazard}_{\text{Midweek}} = \begin{cases} 0.82 & \text{if days\_rest } \le 3 \text{ and rotation-heavy manager} \\ 0.90 & \text{if days\_rest } \le 4 \\ 1.00 & \text{if days\_rest } \ge 5 \end{cases}$$
Adjusted probability of starting:
$$P(\text{Start})_{\text{adj}} = P(\text{Start}) \times \text{Hazard}_{\text{Midweek}}$$

#### 2. Early Sub-60-Minute Substitution Dampener
Certain tactical positions (e.g. explosive wingers subbed at min 55–58) suffer reduced clean sheet bonus and 60+ appearance probability:
$$P(60+\text{ mins} \mid \text{Start}) = \min\left(1.0, \frac{\text{Historical 60+ Starts}}{\text{Total Starts}}\right)$$

#### 3. Live News & Status NLP Dampener
Evaluates `chance_of_playing_this_round` and news tags:
- `chance = 75%` $\longrightarrow P(\text{Start}) \times 0.75$, $P(\text{App}) \times 0.85$
- `chance = 50%` $\longrightarrow P(\text{Start}) \times 0.40$, $P(\text{App}) \times 0.60$
- `chance = 25%` $\longrightarrow P(\text{Start}) \times 0.15$, $P(\text{App}) \times 0.30$
- `chance = 0%` or status `'i'`, `'s'`, `'u'` $\longrightarrow P(\text{Start}) = 0.0, P(\text{App}) = 0.0$.

---

## 3. Integration Points with Existing Architecture

1. **`model/prediction_engine.py`**:
   - Incorporates Set-Piece Equity ($\Delta C_7, \Delta C_8$) and Rotation/News Dampening into base player point predictions.
2. **`model/fixture_engine.py`**:
   - Integrates opponent penalty-conceding rate and European fixture turnaround schedules.
3. **`model/solver.py` & `model/live_manager.py`**:
   - Adds `--strategy` parameter (`'pure_xp'`, `'rank_protect'`, `'differential_chase'`) utilizing EO utilities.
   - Outputs price rise/fall warnings in the matchday terminal report.
4. **`model/excel_exporter.py`**:
   - Adds Set-Piece roles (PK, FK, CK), EO%, and Price Trend badges into the `Optimal Squad` and `GW Predictions` sheets.

---

## 4. Verification & Testing Plan

1. **Unit Tests (`model/test_elite_enhancements.py`)**:
   - Verify penalty equity calculation and role hierarchies.
   - Verify corner/free-kick assist additions.
   - Verify EO computation and strategy objective utilities (`rank_protect` vs `differential_chase`).
   - Verify price rise/fall threshold detection and velocity calculations.
   - Verify midweek fatigue decay and sub-60 proration.
2. **End-to-End Test Suite**:
   - Ensure all 79 existing tests + new unit tests pass with 0 regressions.

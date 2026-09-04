# M-04 Design Spec: Order-Statistic Tournament Modeling for BPS ($C_6$)

**Document Type:** Design Specification  
**Topic:** M-04 Bonus Points Order-Statistic Tournament  
**Author:** AI Agent (Antigravity)  
**Date:** 2026-09-04  
**Status:** In Review & Planning  

---

## 1. Problem Statement & Motivation

In official Fantasy Premier League (FPL), bonus points are a **strictly zero-sum match competition**:
- Exactly **6 bonus points** (3 for 1st place in BPS, 2 for 2nd, 1 for 3rd) are distributed per fixture.
- Ties expand this slightly (e.g. ties for 1st yield 3, 3, 1 = 7 pts; ties for 2nd yield 3, 2, 2 = 7 pts), producing an empirical league average of $\approx 6.15$ bonus points per match.

### Current Limitations:
1. **Unconstrained Individual Product**:
   In [`prediction_engine.py`](file:///e:/Fantasy-Premier-League/model/prediction_engine.py) and [`fixture_engine.py`](file:///e:/Fantasy-Premier-League/model/fixture_engine.py), $C_6$ is modeled as:
   $$C_6 = \text{bonus90} \times P(\text{Start}) \times (\text{Attack\_Mult})^{0.75}$$
   Because players are evaluated independently in isolation, the sum of predicted bonus points in a single match can wildly exceed or fall short of the physical fixture limit:
   - In lopsided matches (e.g. Man City vs Southampton), 5 different City attackers can accumulate $1.5 + 1.2 + 1.0 + 0.8 + 0.6 = 5.1$ bonus points, plus Southampton contributors, predicting $> 6.5$ bonus points.
   - In defensive 0-0 grinds, low attack multipliers depress everyone's bonus points, predicting as little as $2.5$ points for the match—even though in reality **6 bonus points are guaranteed to be awarded**!
2. **Game-State Dynamics Blindness**:
   - In a 0-0 draw or 1-0 win, defenders keeping clean sheets receive +12 BPS and almost invariably sweep the 3, 2, and 1 bonus points.
   - In high-scoring shootouts (e.g. 4-2), defenders lose clean sheets and suffer goals-conceded BPS deductions, while goalscorers (+24/+18 BPS) and assisters (+9 BPS) capture 100% of the bonus pool.
   - Current independent multipliers scale bonus solely on attack strength, failing to reallocate bonus points to defenders in low-scoring fixtures.

---

## 2. Mathematical Formulation

### 2.1 Latent Match BPS Propensity ($\theta_i$)

For each player $i$ in a scheduled fixture between Home team $H$ and Away team $A$, we compute their expected BPS generation:
$$\theta_i = \mathbb{E}[\text{BPS}_i] = \text{BPS}_{\text{base}} + \text{BPS}_{\text{attack}} + \text{BPS}_{\text{defense}} + \text{BPS}_{\text{discipline}}$$

Where:
1. **Base BPS Generation**:
   $$\text{BPS}_{\text{base}} = \text{bps90}_{\text{adj}} \times \frac{\mathbb{E}[M_i]}{90.0} + 6.0 \cdot P(M_i \ge 60) + 3.0 \cdot P(1 \le M_i < 60)$$
2. **Attacking Returns**:
   $$\text{BPS}_{\text{attack}} = \text{BPS}_{\text{goal}}(\text{POS}_i) \cdot \lambda_{\text{goal}, i} + 9.0 \cdot \lambda_{\text{assist}, i}$$
   with $\text{BPS}_{\text{goal}}(\text{FWD}) = 24.0$, $\text{BPS}_{\text{goal}}(\text{MID}) = 18.0$, $\text{BPS}_{\text{goal}}(\text{DEF/GK}) = 12.0$.
3. **Defensive Returns & Deductions**:
   $$\text{BPS}_{\text{defense}} = \begin{cases}
   12.0 \cdot P(\text{CS}_{\text{team}}) \cdot P(M_i \ge 60) - 4.0 \cdot \mathbb{E}[\text{GC} \ge 2] \cdot P(M_i \ge 60) + 2.0 \cdot \mathbb{E}[\text{Saves}_i] & \text{if } \text{POS}_i = \text{GK} \\
   12.0 \cdot P(\text{CS}_{\text{team}}) \cdot P(M_i \ge 60) - 4.0 \cdot \mathbb{E}[\text{GC} \ge 2] \cdot P(M_i \ge 60) + 1.0 \cdot \mathbb{E}[\text{DC}_i] & \text{if } \text{POS}_i = \text{DEF} \\
   0.0 & \text{otherwise}
   \end{cases}$$
4. **Discipline Deductions**:
   $$\text{BPS}_{\text{discipline}} = -(3.0 \cdot \lambda_{\text{YC}, i} + 9.0 \cdot \lambda_{\text{RC}, i})$$

### 2.2 Plackett-Luce Ranking Tournament

Let $S = H \cup A$ be the set of active players in the match with participation probability $P(\text{App}_i) > 0$.
The latent ranking strength $s_i$ is parameterized via a calibrated softmax temperature $\tau \approx 6.0$:
$$s_i = \exp\left(\frac{\theta_i}{\tau}\right) \cdot P(\text{App}_i)$$

Under the Plackett-Luce model:
1. **Probability of 1st Place (3 Bonus Points)**:
   $$P_1(i) = \frac{s_i}{\sum_{j \in S} s_j}$$
2. **Probability of 2nd Place (2 Bonus Points)**:
   $$P_2(i) = \sum_{j \in S \setminus \{i\}} P_1(j) \cdot \frac{s_i}{\sum_{k \in S \setminus \{j\}} s_k}$$
3. **Probability of 3rd Place (1 Bonus Point)**:
   $$P_3(i) = \sum_{j \in S \setminus \{i\}} \sum_{k \in S \setminus \{i, j\}} P_1(j) \cdot \frac{s_k}{\sum_{l \in S \setminus \{j\}} s_l} \cdot \frac{s_i}{\sum_{m \in S \setminus \{j, k\}} s_m}$$

### 2.3 Exact Match Conservation & Tie Inflation

The expected bonus points for player $i$ in this match is:
$$\mathbb{E}[\text{Bonus}_i] = \kappa_{\text{tie}} \cdot \left(3 \cdot P_1(i) + 2 \cdot P_2(i) + 1 \cdot P_3(i)\right)$$

Where $\kappa_{\text{tie}} = 1.025$ accounts for the empirical $+2.5\%$ bonus point expansion from tied BPS scores in historical Premier League matches.

#### Mathematical Conservation Theorem:
$$\sum_{i \in S} \mathbb{E}[\text{Bonus}_i] = \kappa_{\text{tie}} \cdot \left(3 \sum_{i} P_1(i) + 2 \sum_i P_2(i) + 1 \sum_i P_3(i)\right) = 6.0 \cdot \kappa_{\text{tie}} \approx 6.15\text{ pts}$$
This enforces exact mathematical bonus conservation across every simulated and predicted Premier League fixture!

---

## 3. Architecture & Integration Plan

### 3.1 New Module: `model/bps_tournament.py`
A dedicated, highly-optimized module implementing:
1. `compute_player_bps_propensity(player_fixture_pred: Dict[str, Any]) -> float`
2. `solve_plackett_luce_tournament(players: List[Dict[str, Any]], tau: float = 6.0, tie_inflation: float = 1.025) -> Dict[int, float]`
   - Vectorized computation returning `{player_code: expected_bonus_pts}`.
3. `calibrate_fixture_bonus_points(predictions_df: pd.DataFrame, fixtures: List[Dict[str, Any]]) -> pd.DataFrame`
   - Groups gameweek predictions by fixture, runs the tournament, updates `c6_bonus`, and recalibrates `expected_points`.

### 3.2 Pipeline Wiring in `fixture_engine.py`
- In `predict_gameweek_fixtures()`:
  - After computing fixture predictions for all players, call `calibrate_fixture_bonus_points(result_df, fixtures)`.
  - Enforces match conservation across all single-gameweek and double-gameweek matches.
- In `predict_player_fixture()`:
  - Retain existing fast heuristic as a single-player fallback when full match rosters are not available.

### 3.3 Monte Carlo Alignment in `match_simulator.py`
- Ensure `compute_true_bps_and_bonus` in `match_simulator.py` and `solve_plackett_luce_tournament` converge to identical expectations under identical match conditions.

---

## 4. Verification & Testing Plan

1. **Unit Test Suite (`model/test_bps_tournament.py`)**:
   - **Conservation Test**: Verify $\sum_{i \in \text{Match}} \mathbb{E}[\text{Bonus}_i] \approx 6.15 \pm 0.01$ across various fixture types.
   - **Game-State Invariance Test**:
     - In a projected 0-0 match, verify that $\ge 70\%$ of bonus points are captured by defenders and goalkeepers.
     - In a projected 4-3 shootout, verify that $\ge 80\%$ of bonus points are captured by goalscorers and assisters.
   - **Monotonicity Test**: Increasing a player's xG or assist rate strictly increases their bonus point probability.
   - **Tournament Scalability**: Complete execution of 10 fixtures (300+ players) in $< 50\text{ ms}$.
2. **End-to-End Regression**:
   - All 79 existing tests must pass.
   - `python scripts/validate_okf.py`: 0 errors.
   - `node scripts/check_copy.cjs`: 0 errors.

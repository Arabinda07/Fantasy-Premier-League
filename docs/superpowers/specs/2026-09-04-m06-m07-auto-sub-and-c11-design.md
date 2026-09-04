# M-06 & M-07 Design Spec: Expected Auto-Substitution Valuation & $C_{11}$ Rate Normalization

**Document Type:** Design Specification  
**Topic:** M-06 Auto-Sub Solver Objective & M-07 Defensive Contribution Normalization  
**Author:** AI Agent (Antigravity)  
**Date:** 2026-09-04  
**Status:** Approved & Implemented  

---

## 1. Problem Statement & Motivation

### 1.1 M-06: Crude Bench Valuation in Solver Objective
In the FPL Squad Optimization Solver ([`model/solver.py`](file:///e:/Fantasy-Premier-League/model/solver.py)), the 15-player squad consists of 11 starters ($s_i = 1$) and 4 bench players ($x_i - s_i = 1$).
Historically, the solver evaluated bench players with an arbitrary static flat weight:
$$\text{bench\_weight} \cdot \sum_{i} \text{opt\_points}_i \cdot (x_i - s_i) \quad (\text{with } \text{bench\_weight} = 0.05 \text{ or } 0.10)$$

This formulation suffered from three major theoretical flaws:
1. **Uniformity Across Bench Slots**: In official FPL rules, bench players do not have equal exposure. The 1st outfield substitute ($\text{Bench}_1$) enters whenever *any* outfield starter does not play (DNP). The 2nd substitute ($\text{Bench}_2$) only enters if *at least two* starters DNP. The 3rd substitute ($\text{Bench}_3$) only enters if *at least three* starters DNP. Treating $\text{Bench}_1$ and $\text{Bench}_3$ identically as $0.05$ severely undervalues the 1st sub option while overvaluing 3rd bench fodder.
2. **Rotation & Congestion Blindness**: During periods of heavy congestion (e.g. 3 matches in 7 days, European midweek fatigue, manager rotation propensities), starter DNP risk surges from $\approx 5\%$ to $> 15\%$. The expected value of holding an active, scoring 1st bench substitute increases dramatically ($\approx 0.40 - 0.60 \times xP$), but a flat $0.05$ weight leaves the solver with zero incentive to protect against rotation risk.
3. **Goalkeeper Auto-Sub Disconnect**: A bench goalkeeper can only substitute for the starting goalkeeper. Since goalkeepers rarely DNP ($P(\text{App}) \approx 0.98$), their auto-sub probability is very low ($\approx 0.02 - 0.04$). A flat $0.05$ or $0.10$ weight over-allocates precious budget to backup goalkeepers instead of outfield starters or the 1st outfield sub.

### 1.2 M-07: $C_{11}$ Defensive Contributions Rate Normalization
Under official FPL scoring, players earn +1 point for $\ge 10$ defensive contributions (tackles, blocks, clearances, interceptions) and an additional +1 point for $\ge 15$ DC in a match.
In older scraper scripts, the expected rate was scaled as $\lambda = dc90 \times active\_ratio$ and subsequently multiplied by $P(60+)$ again:
$$C_{11} = (P(\text{DC}\ge 10) + P(\text{DC}\ge 15)) \times P(60+)$$
Because $active\_ratio$ already discounts for substitute appearances and early substitutions, multiplying by $P(60+)$ again was a **double-discounting** error.
M-07 formalizes the conditional rate normalization established during the continuous hazard integration (M-02) and verifies that the pipeline strictly avoids double discounting.

---

## 2. Mathematical Formulation

### 2.1 Binomial Starter DNP & Auto-Substitution Probabilities (M-06)
For each outfield starter $j \in \text{Outfield Starters}$, their probability of not playing (DNP) is:
$$q_j = 1.0 - P(\text{App}_j)$$
Across the 10 outfield starters, the mean DNP rate is:
$$q_{\text{avg}} = \text{clip}\left(\frac{1}{10} \sum_{j} q_j, \, 0.02, \, 0.15\right)$$

The cumulative auto-substitution activation probabilities are governed by the Binomial distribution $\text{Bin}(10, q_{\text{avg}})$:
1. **1st Outfield Sub Weight ($w_1$)**: Probability of $\ge 1$ outfield starter missing out:
   $$w_1 = P(N_{\text{DNP}} \ge 1) = 1.0 - (1.0 - q_{\text{avg}})^{10}$$
   *(Typically $0.30$ to $0.55$; rises to $> 0.65$ under heavy European congestion).*
2. **2nd Outfield Sub Weight ($w_2$)**: Probability of $\ge 2$ outfield starters missing out:
   $$w_2 = P(N_{\text{DNP}} \ge 2) = 1.0 - (1.0 - q_{\text{avg}})^{10} - 10 \cdot q_{\text{avg}} (1.0 - q_{\text{avg}})^9$$
   *(Typically $0.06$ to $0.18$).*
3. **3rd Outfield Sub Weight ($w_3$)**: Probability of $\ge 3$ outfield starters missing out:
   $$w_3 = P(N_{\text{DNP}} \ge 3) = w_2 - \binom{10}{2} q_{\text{avg}}^2 (1.0 - q_{\text{avg}})^8$$
   *(Typically $0.01$ to $0.05$).*
4. **Bench Goalkeeper Weight ($w_{\text{GK}}$)**: Probability of starting GK missing out:
   $$w_{\text{GK}} = q_{\text{GK}} = \text{clip}(1.0 - P(\text{App}_{\text{GK}}), \, 0.01, \, 0.05)$$

### 2.2 Special Chip Modifiers
- **Bench Boost (`bboost`)**: All 4 bench players are scored fully in Gameweek points:
  $$w_1 = 1.0, \quad w_2 = 1.0, \quad w_3 = 1.0, \quad w_{\text{GK}} = 1.0$$
- **Free Hit (`freehit`)**: Bench is temporary for 1 week only. Minimal auto-sub weights ($w_1 = 0.10, w_2 = 0.02, w_3 = 0.005, w_{\text{GK}} = 0.01$) prevent wasteful spending on a single-gameweek bench.

### 2.3 MILP Linear Formulation
To integrate tiered bench slots cleanly without non-linear complexity:
- For each outfield player $i \in \text{Outfield}$, define binary variables:
  - $b_{i, 1} \in \{0, 1\}$: 1st outfield bench slot.
  - $b_{i, 2} \in \{0, 1\}$: 2nd outfield bench slot.
  - $b_{i, 3} \in \{0, 1\}$: 3rd outfield bench slot.
- For each goalkeeper $i \in \text{GK}$, define binary variable:
  - $b_{i, \text{GK}} \in \{0, 1\}$: Bench goalkeeper slot.

**Exact Partition Constraints**:
$$s_i + b_{i, 1} + b_{i, 2} + b_{i, 3} = x_i \quad (\forall i \in \text{Outfield})$$
$$s_i + b_{i, \text{GK}} = x_i \quad (\forall i \in \text{GK})$$
$$\sum_{i \in \text{Outfield}} b_{i, 1} = 1, \quad \sum_{i \in \text{Outfield}} b_{i, 2} = 1, \quad \sum_{i \in \text{Outfield}} b_{i, 3} = 1, \quad \sum_{i \in \text{GK}} b_{i, \text{GK}} = 1$$

**Objective Function Term**:
$$\sum_{i} \text{opt\_points}_i \cdot \left( w_1 b_{i, 1} + w_2 b_{i, 2} + w_3 b_{i, 3} + w_{\text{GK}} b_{i, \text{GK}} \right)$$

Because $w_1 > w_2 > w_3$, the linear solver **naturally and automatically** assigns the highest-xP bench player to slot 1, matching FPL's `order_bench()` logic!

---

## 3. M-07 Defensive Contribution ($C_{11}$) Rate Normalization

In [`model/prediction_engine.py`](file:///e:/Fantasy-Premier-League/model/prediction_engine.py#L584-L592):
$$\text{exposure}_{60+} = \frac{\mathbb{E}[M \mid M \ge 60]}{90.0}$$
$$\lambda_{\text{DC} \mid 60+} = dc90_{\text{adj}} \cdot \text{exposure}_{60+}$$
$$C_{11} = \left( P(\text{DC} \ge 10 \mid \lambda_{\text{DC} \mid 60+}) + P(\text{DC} \ge 15 \mid \lambda_{\text{DC} \mid 60+}) \right) \cdot P(60+)$$

- **Eliminates double discounting**: The rate $\lambda_{\text{DC} \mid 60+}$ is strictly conditioned on qualifying for 60+ minutes.
- **Single Gating**: The qualification threshold probability $P(60+)$ is applied exactly once to the expected points.

---

## 4. Verification & Testing

1. `test_auto_sub_weights_monotonicity`: $w_1 > w_2 > w_3 > 0$ and $w_1$ increases with $q_{\text{avg}}$.
2. `test_bench_boost_weights`: Under `chip='bboost'`, all weights equal $1.0$.
3. `test_tier_1_bench_option_selected_under_rotation_risk`: When rotation risk is elevated, the solver invests in an active playing starter for $\text{Bench}_1$ instead of $0.0$ xP fodder.
4. `test_tier_3_bench_fodder_preserved`: Slot 3 maintains low weight ($\approx 0.02$), ensuring the solver does not waste budget on deep bench slots.
5. `test_c11_rate_normalization_audit`: Confirms $C_{11}$ conditions on 60+ minutes without double discounting.

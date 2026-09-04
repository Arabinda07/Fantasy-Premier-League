# M-05 Design Spec: Early-Season Captaincy Bayesian Confidence Calibration

**Document Type:** Design Specification  
**Topic:** M-05 Early-Season Captaincy Bayesian Confidence Calibration  
**Author:** AI Agent (Antigravity)  
**Date:** 2026-09-04  
**Status:** Approved & Implemented  

---

## 1. Problem Statement & Motivation

In official Fantasy Premier League (FPL), the team captain earns **double points** ($2\times$). In the squad optimization solver ([`model/solver.py`](file:///e:/Fantasy-Premier-League/model/solver.py)), this is formalized within the Mixed-Integer Linear Programming (MILP) objective:

$$\max \sum_{i \in \text{Squad}} \left( \text{opt\_points}_i \cdot s_i + \text{capt\_multiplier} \cdot \text{captain\_points}_i \cdot c_i + \text{bench\_w} \cdot \text{opt\_points}_i \cdot (x_i - s_i) \right)$$

where $s_i \in \{0, 1\}$ denotes starting XI membership and $c_i \in \{0, 1\}$ denotes the captaincy assignment.

### Current Limitation: Premature Early-Season Captaincy Penalty
To prevent low-minute fringe cameos (e.g. bench players with a lucky 20-minute goal haul) from usurping the captaincy armband from proven talismans, [`solver.py`](file:///e:/Fantasy-Premier-League/model/solver.py#L337) introduced a regularizer:

$$\text{capt\_conf} = \text{clip}\left( \frac{\text{season\_mins}}{720.0} \cdot P(\text{Start}) + \frac{\text{Cost}}{25.0}, \, 0.20, \, 1.0 \right)$$
$$\text{captain\_points} = \text{opt\_points} \cdot \text{capt\_conf}$$

The scale parameter $720.0$ minutes corresponds to approximately 8 full 90-minute fixtures. In early gameweeks (GW1–GW4), total elapsed minutes in the current season are strictly limited by calendar time:
- **Gameweek 1**: Prior to kickoff, $\text{season\_mins} = 0$.
  - Erling Haaland (£15.0M, $P(\text{Start})=1.0$): $\text{capt\_conf} = 0 + \frac{15.0}{25.0} = 0.60$ (**40% artificial penalty**).
  - Mohamed Salah (£12.5M, $P(\text{Start})=1.0$): $\text{capt\_conf} = 0 + \frac{12.5}{25.0} = 0.50$ (**50% artificial penalty**).
  - Cole Palmer (£10.5M, $P(\text{Start})=1.0$): $\text{capt\_conf} = 0 + \frac{10.5}{25.0} = 0.42$ (**58% artificial penalty**).
  - Bukayo Saka (£10.0M, $P(\text{Start})=1.0$): $\text{capt\_conf} = 0 + \frac{10.0}{25.0} = 0.40$ (**60% artificial penalty**).
- **Gameweek 2**: Maximum possible minutes $\le 90$. A nailed starter has $\text{capt\_conf} \le \frac{90}{720} + 0.40 = 0.525$ (**47.5% penalty**).
- **Gameweek 3**: Maximum possible minutes $\le 180$. A nailed starter has $\text{capt\_conf} \le \frac{180}{720} + 0.40 = 0.650$ (**35% penalty**).
- **Gameweek 4**: Maximum possible minutes $\le 270$. A nailed starter has $\text{capt\_conf} \le \frac{270}{720} + 0.40 = 0.775$ (**22.5% penalty**).

This artificially discounts captaincy bonus points relative to starting XI points in early gameweeks, distorting optimal formation and budget trade-offs.

---

## 2. Mathematical Formulation (M-05)

### 2.1 Bayesian Prior & Current-Season Evidence Blending
Instead of evaluating `season_mins` in isolation, M-05 introduces **Empirical Bayes sample-size blending** between current-season minutes ($M_{\text{season}}$) and historical long-form minutes ($M_{\text{long}}$).

Let:
- $M_{\text{season}}$: Minutes played in the current season (`season_minutes` or `minutes`).
- $M_{\text{long}}$: Historical minutes from the long-form window (`long_form_unweighted_minutes`, falling back to `long_form_minutes`, falling back to $0.0$).
- $M_{\text{target}} = 720.0$: Reference maturity threshold (8 matches $\times$ 90 mins).
- $M_{\text{long\_norm}} = 1800.0$: Benchmark long-form minutes for an established Premier League starter (20 full 90-minute matches). When using decayed EWMA minutes, $M_{\text{long\_norm}} = 1100.0$.
- $GW$: Upcoming or target gameweek number.

### 2.2 Season Horizon & Prior Weight
The calendar horizon of maximum completed minutes in the league is:
$$M_{\text{horizon}} = \min\left(M_{\text{target}}, \, \max\left(\max(M_{\text{season}}), \, 90.0 \times \max(0, GW - 1)\right)\right)$$

The Bayesian prior weight decays linearly with season progression:
$$w_{\text{prior}} = \max\left(0.0, \, 1.0 - \frac{M_{\text{horizon}}}{M_{\text{target}}}\right)$$

- At $GW = 1$ ($M_{\text{horizon}} = 0$): $w_{\text{prior}} = 1.0$ (100% prior reliance).
- At $GW = 5$ ($M_{\text{horizon}} = 360$): $w_{\text{prior}} = 0.50$ (50% prior / 50% current season).
- At $GW \ge 9$ ($M_{\text{horizon}} \ge 720$): $w_{\text{prior}} = 0.0$ (0% prior; current-season evidence completely governs).

### 2.3 Prior-Equivalent Minutes & Calibrated Minutes
A player's long-form baseline yields equivalent sample evidence:
$$M_{\text{prior\_equiv}} = \min\left(M_{\text{target}}, \, M_{\text{target}} \times \frac{M_{\text{long}}}{M_{\text{long\_norm}}}\right)$$

The calibrated effective minutes are then computed as:
$$M_{\text{calibrated}} = \begin{cases}
\min\left(M_{\text{target}}, \, M_{\text{season}} + w_{\text{prior}} \times M_{\text{prior\_equiv}}\right) & \text{if } w_{\text{prior}} > 0 \\
M_{\text{season}} & \text{if } w_{\text{prior}} = 0
\end{cases}$$

### 2.4 Calibrated Captaincy Confidence
The regularizer is evaluated on $M_{\text{calibrated}}$:
$$\text{capt\_conf} = \text{clip}\left( \frac{M_{\text{calibrated}}}{M_{\text{target}}} \cdot P(\text{Start}) + \frac{\text{Cost}}{25.0}, \, 0.20, \, 1.0 \right)$$
$$\text{captain\_points} = \text{opt\_points} \cdot \text{capt\_conf}$$

---

## 3. Boundary & Invariant Properties

1. **GW1 Proven Starters**:
   For Erling Haaland ($M_{\text{season}} = 0$, $M_{\text{long}} = 2800$, $P(\text{Start}) = 1.0$):
   $w_{\text{prior}} = 1.0 \implies M_{\text{calibrated}} = 720.0$.
   $\text{capt\_conf} = \min(1.0, 1.0 \times 1.0 + 15.0 / 25.0) = 1.0$. (No penalty).
2. **GW1 Cameo Protection Maintained**:
   For an unproven fringe reserve ($M_{\text{season}} = 0$, $M_{\text{long}} = 90$, $\text{Cost} = 4.5$, $P(\text{Start}) = 0.2$):
   $M_{\text{prior\_equiv}} = 720.0 \times (90 / 1800) = 36.0 \implies M_{\text{calibrated}} = 36.0$.
   $\text{capt\_conf} = \max(0.20, (36 / 720) \times 0.2 + 4.5 / 25) = \max(0.20, 0.01 + 0.18) = 0.20$. (Properly regularized).
3. **Smooth Monotonic Transition**:
   For an established starter who continues to start every match from GW1 through GW8, $M_{\text{calibrated}} \equiv 720.0$ and $\text{capt\_conf} \equiv 1.0$ across all gameweeks without discontinuity.
4. **Zero-Drift Late Season Convergence**:
   At $GW \ge 9$, $w_{\text{prior}} = 0.0$ identically, reducing $M_{\text{calibrated}} \equiv M_{\text{season}}$, matching the mature-season equation exactly.

---

## 4. Verification & Testing

- Unit tests in `model/test_captaincy_calibration.py` verifying all 4 boundary conditions, monotonicity, schema resilience, and full solver squad optimization.
- Integration tests ensuring `test_solver.py`, `test_solver_cvar.py`, and `test_creator_mechanics.py` pass with 100% backward compatibility.

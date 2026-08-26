---
type: Model Component
title: Effective Ownership & Game Theory Engine
description: Models overall and top-10k Effective Ownership (EO) to compute rank-adjusted utility for template protection and differential chasing.
resource: model/ownership_engine.py
tags: [math, model, game-theory, ownership, rank-protection]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: ownership-src
    resource: model/ownership_engine.py
    title: Ownership Engine Source Code
---

# Mathematical Specification: Ownership & Game Theory

The ownership engine ([model/ownership_engine.py](/models/index.md)) models Effective Ownership (EO) and applies game-theoretic utility adjustments:

$$\text{EO}_i = \text{ownership\_pct}_i + \text{captaincy\_share}_i + \text{triple\_captain\_share}_i$$

---

## 1. Captaincy Share Heuristic

Pre-deadline captaincy share is estimated from ownership fraction and relative $xP$ dominance:

$$\text{xp\_norm}_i = \min\left(1.0, \, \max\left(0.0, \, \frac{xP_i}{\max_{j} xP_j}\right)\right)$$

$$\text{captaincy\_share}_i = \text{clamp}\left(\text{ownership\_pct}_i \cdot \text{xp\_norm}_i \cdot 0.80, \, 0.0, \, 0.80\right)$$

---

## 2. Rank-Adjusted Utility Formulation

For player $i$, the solver and decision cockpit evaluate:

$$\text{Utility}_i = xP_i + \lambda \cdot \Phi(\text{EO}_i, \, \text{Strategy})$$
where $\lambda = 1.0$ by default.

### Strategy Modes:

1. **`'pure_xp'`** (Neutral / Expected Points Maximizer):
   $$\Phi(\text{EO}_i) = 0.0$$

2. **`'rank_protect'`** (Shielding Rank Lead / Template Defense):
   $$\Phi(\text{EO}_i) = \begin{cases}
   0.5 \cdot (\text{EO}_i - 1.0) & \text{if } \text{EO}_i > 1.0 \\
   0.0 & \text{otherwise}
   \end{cases}$$
   *Penalizes fading ultra-high EO players to protect against rank collapses.*

3. **`'differential_chase'`** (Climbing Ranks / High Risk-Reward):
   $$\Phi(\text{EO}_i) = \begin{cases}
   1.2 \cdot (0.20 - \text{EO}_i) & \text{if } \text{EO}_i < 0.20 \\
   -0.5 \cdot (\text{EO}_i - 1.0) & \text{if } \text{EO}_i > 1.0 \\
   0.0 & \text{otherwise}
   \end{cases}$$
   *Rewards low-owned differentials while actively penalizing template captains.*

[^ownership-src]: `model/ownership_engine.py`

---
type: Model Component
title: Point-Prediction Engine Formulation
description: Mathematical specifications for the 11 FPL scoring components (C1-C11), Empirical Bayes prior shrinkage, exact discrete Poisson goals conceded expectation, and cold-start playing priors.
resource: model/prediction_engine.py
tags: [math, model, poisson, bayes, prediction-engine]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:01:00Z }
sources:
  - id: pred-engine-src
    resource: model/prediction_engine.py
    title: Point Prediction Engine Source Code
  - id: journey-log
    resource: JOURNEY.md
    title: Engineering Journey & Lessons Learned Log
  - id: phase2-spec
    resource: docs/superpowers/specs/2026-08-24-fpl-point-prediction-engine-design.md
    title: Phase 2 Point Prediction Engine Design Spec
---

# Mathematical Specification: Point-Prediction Engine

The point-prediction engine ([model/prediction_engine.py](/computations/predict-points.md)) computes baseline expected points ($xP$) for every player across 11 discrete, mathematically orthogonal scoring components:

$$xP = \sum_{k=1}^{11} C_k$$

> **Reconciliation Note (2026-08-26)**: This specification was reconciled with the actual implementation during the adversarial audit. All component numbers, formulas, and multipliers below exactly match the code in `prediction_engine.py`.

---

## 1. Empirical Bayes Prior Shrinkage

To prevent small-sample distortions (e.g. young prospects or substitutes with high raw per-90 rates over $< 300\text{ mins}$), raw per-90 metrics are shrunk toward positional league priors with sample weight $M_0 = 500.0\text{ minutes}$:[^journey-log]

$$\text{rate}_{\text{adj}} = \frac{M}{M + M_0} \cdot \text{rate}_{\text{raw}} + \frac{M_0}{M + M_0} \cdot \text{Prior}(\text{Position})$$

### Positional Baseline Priors ($\text{Prior}(\text{Position})$)
* **FWD**: $xG = 0.35$, $xA = 0.15$, $DC = 2.0$, $\text{Bonus} = 0.60$
* **MID**: $xG = 0.15$, $xA = 0.15$, $DC = 4.0$, $\text{Bonus} = 0.50$
* **DEF**: $xG = 0.05$, $xA = 0.05$, $DC = 8.0$, $\text{Bonus} = 0.30$
* **GK**: $xG = 0.00$, $xA = 0.00$, $DC = 1.0$, $\text{Bonus} = 0.20$

Shrinkage is applied to: `xg90`, `xa90`, `dc90`, and `bonus90`.

---

## 2. Active Minutes Ratio & Playing Probabilities

Playing time expectation scales attacking and defensive contribution volumes:

$$\text{mins\_per\_start} = \min(90.0, \max(45.0, \text{total\_minutes} / \text{starts}))$$

$$\text{active\_ratio} = P(\text{Start}) \cdot \frac{\text{mins\_per\_start}}{90.0} + P(\text{Sub}) \cdot \frac{20.0}{90.0}$$

### Cold-Start Playing Priors (New Signings / 0 Historical PL Minutes)
* $\text{Cost} \ge \pounds 9.0\text{M} \implies P(\text{Start}) = 0.85$
* $\text{Cost} \ge \pounds 7.0\text{M} \implies P(\text{Start}) = 0.70$
* $\text{Cost} \ge \pounds 5.5\text{M} \implies P(\text{Start}) = 0.45$

Players with $\text{Cost} < \pounds 5.5\text{M}$ and 0 historical minutes receive $P(\text{Start}) = 0.0$ (no cold-start floor -- these are typically youth/reserve players not expected to start).

---

## 3. The 11 Scoring Components ($C_1 \dots C_{11}$)

> **Component Numbering**: The numbering below exactly matches the code's `c1` through `c11` variables and the output keys `c1_app_1_60`, `c2_app_60_plus`, etc.

### $C_1$: Appearance Points (1-60 mins)
$$C_1 = 1.0 \cdot P(\text{App})$$
where $P(\text{App}) = P(\text{Start}) + P(\text{Sub})$.

### $C_2$: Appearance Points (60+ mins)
$$C_2 = 1.0 \cdot P(60+)$$
where $P(60+) = P(\text{Start}) \cdot \frac{\max(0, \text{mins\_per\_start} - 60.0)}{30.0}$.

*A player appearing for 60+ minutes earns $C_1 + C_2 = 2$ appearance points (1 for any appearance + 1 bonus for 60+ mins).*

### $C_3$: Goalkeeper Saves (GK Only)
$$C_3 = \frac{1}{3} \cdot \text{saves}90_{\text{adj}} \cdot P(\text{Start})$$
$C_3 = 0$ for all non-GK positions.

### $C_4$: Yellow Cards Penalty
$$C_4 = -1.0 \cdot yc90 \cdot P(\text{App})$$

*Note: No correction is applied for 2-yellow reds. FPL awards both the second yellow card deduction ($-1$) and the red card deduction ($-3$) separately. The `yc90` rate includes all yellows.*

### $C_5$: Red Cards Penalty
$$C_5 = -3.0 \cdot rc90 \cdot P(\text{App})$$

### $C_6$: Bonus Points System (BPS) Expectation
$$C_6 = \text{bonus}90_{\text{adj}} \cdot P(\text{Start})$$

where $\text{bonus}90_{\text{adj}}$ is the historical bonus-per-90 rate, shrunk via Empirical Bayes with positional priors (FWD: 0.60, MID: 0.50, DEF: 0.30, GK: 0.20).

### $C_7$: Assists
$$C_7 = 3.0 \cdot xA90_{\text{adj}} \cdot \text{active\_ratio}$$

### $C_8$: Goals Scored
$$C_8 = \text{GoalPts}(\text{POS}) \cdot xG90_{\text{adj}} \cdot \text{active\_ratio}$$
where $\text{GoalPts}(\text{FWD}) = 4.0$, $\text{GoalPts}(\text{MID}) = 5.0$, $\text{GoalPts}(\text{DEF/GK}) = 6.0$.

### $C_9$: Clean Sheets
Under a Poisson distribution for opponent goals conceded with rate parameter $\lambda = xGC90$:
$$P(GC = 0) = e^{-\lambda}$$
$$C_9 = \text{CleanSheetPts}(\text{POS}) \cdot P(60+) \cdot e^{-\lambda}$$
where $\text{CleanSheetPts}(\text{GK/DEF}) = 4.0$, $\text{CleanSheetPts}(\text{MID}) = 1.0$, $\text{CleanSheetPts}(\text{FWD}) = 0.0$.

### $C_{10}$: Exact Discrete Poisson Goals Conceded Penalty (DEF / GK Only)
FPL deducts $-1\text{ pt}$ for every 2 goals conceded ($GC \in \{2, 3\} \implies -1$, $GC \in \{4, 5\} \implies -2$, etc.).
Exact expected deduction under Poisson distribution with parameter $\lambda = xGC90$:

$$\mathbb{E}[\text{Penalty}] = -\sum_{m=1}^5 m \cdot \left( P(X = 2m) + P(X = 2m + 1) \right)$$
$$C_{10} = P(60+) \cdot \mathbb{E}[\text{Penalty}]$$

### $C_{11}$: Defensive Contributions (DC)
FPL awards 1 pt for $\ge 10$ defensive contributions and an additional 1 pt for $\ge 15$ DC in a match. Under a Poisson distribution with rate $\lambda = dc90_{\text{adj}} \cdot \text{active\_ratio}$:

$$C_{11} = \left( P(\text{DC} \ge 10) + P(\text{DC} \ge 15) \right) \cdot P(60+)$$

*Note: Gated on $P(60+)$ because DC points are only awarded for 60+ minute appearances.*

---

## Reconciliation Changelog

| Date | Finding ID | Change |
|------|-----------|--------|
| 2026-08-26 | F-17 | Renumbered all components to match code (C1-C11 ordering: app -> 60+ -> saves -> YC -> RC -> bonus -> assists -> goals -> CS -> GC -> DC) |
| 2026-08-26 | F-18 | Updated C11 formula from linear `0.05 * dc90 * active_ratio` to Poisson threshold `P(DC>=10) + P(DC>=15)` |
| 2026-08-26 | F-02 | Updated C4 to remove `- 2.0 * rc90` correction (FPL awards both deductions) |
| 2026-08-26 | F-16 | Updated C6 to document Empirical Bayes shrinkage on `bonus90` |
| 2026-08-26 | F-01 | Updated C11 to document `P(60+)` gate |
| 2026-08-26 | F-19 | Removed `Cost < 5.5M -> P(Start) = 0.20` cold-start tier (not implemented in code) |
| 2026-08-26 | -- | Added `bonus90` to positional prior table |

[^pred-engine-src]: `model/prediction_engine.py`
[^journey-log]: `JOURNEY.md`
[^phase2-spec]: `docs/superpowers/specs/2026-08-24-fpl-point-prediction-engine-design.md`

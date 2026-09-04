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
where $P(\text{App}) = P(\text{Start}) + P(\text{Sub})$ is calculated canonically by the 3-regime continuous survival hazard engine ([`model/minutes_model.py`](file:///e:/Fantasy-Premier-League/model/minutes_model.py)).

### $C_2$: Appearance Points (60+ mins)
$$C_2 = 1.0 \cdot P(60+)$$
where $P(60+) = P(\text{Start}) \cdot (1.0 - P(\text{Hook} \mid \text{Start})) + P(\text{Sub}) \cdot 0.005$ incorporates manager tactical hook propensities and continuous substitution hazard.

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
Under a Negative Binomial distribution for opponent goals conceded with rate $\mu = xGC90$ and dispersion parameter $r = 6.0$ (calibrated via historical EPL fixtures):

$$P(GC = 0) = \left( 1 + \frac{\mu}{r} \right)^{-r}$$
$$C_9 = \text{CleanSheetPts}(\text{POS}) \cdot P(60+) \cdot \left( 1 + \frac{\mu}{r} \right)^{-r}$$

where $\text{CleanSheetPts}(\text{GK/DEF}) = 4.0$, $\text{CleanSheetPts}(\text{MID}) = 1.0$, $\text{CleanSheetPts}(\text{FWD}) = 0.0$.
When $r \to \infty$, this smoothly collapses to the classical Poisson model $P(GC=0) = e^{-\mu}$. The finite $r=6.0$ captures the observed zero-inflation (clean sheets occur ~2.5% more frequently than Poisson predicts for elite defenses).

### $C_{10}$: Exact Discrete Negative Binomial Goals Conceded Penalty (DEF / GK Only)
FPL deducts $-1\text{ pt}$ for every 2 goals conceded while the player is on the pitch ($GC \in \{2, 3\} \implies -1$, $GC \in \{4, 5\} \implies -2$, etc.).
Crucially, official FPL rules do NOT require 60 minutes on the pitch to receive a goals-conceded deduction. $C_{10}$ is therefore evaluated separately over starter duration and substitute cameo duration:

$$\mathbb{E}[\text{Penalty}(\mu)] = -\sum_{m=1}^5 m \cdot \left( P(X = 2m \mid \mu, r) + P(X = 2m + 1 \mid \mu, r) \right)$$
$$\mu_{\text{starter}} = \text{xGC90} \cdot \frac{\mathbb{E}[M_{\text{starter}}]}{90.0}, \quad \mu_{\text{sub}} = \text{xGC90} \cdot \frac{20.0}{90.0}$$
$$C_{10} = P(\text{Start}) \cdot \mathbb{E}[\text{Penalty}(\mu_{\text{starter}})] + P(\text{Sub}) \cdot \mathbb{E}[\text{Penalty}(\mu_{\text{sub}})]$$

*Note: Decoupling $C_{10}$ from the 60-minute gate eliminates the distortion where early-subbed defenders or late defensive substitutes falsely evaded goals conceded penalties.*

### $C_{11}$: Defensive Contributions (DC)
Modeled for draft leagues and custom rulesets awarding fantasy points for defensive volume ($\ge 10$ and $\ge 15$ DC). Under Poisson conditional distribution with rate $\lambda_{\text{DC} \mid 60+} = dc90_{\text{adj}} \cdot \frac{\mathbb{E}[M \mid 60+]}{90.0}$:

$$C_{11} = \left( P(\text{DC} \ge 10 \mid 60+) + P(\text{DC} \ge 15 \mid 60+) \right) \cdot P(60+)$$

*Official FPL Scoring Note: Under official FPL scoring, defensive actions feed the Bonus Points System (BPS) rather than awarding direct fantasy points. Hence, by default (`include_c11_in_xp=False`), $\text{xP} = \sum_{k=1}^{10} C_k$. Setting `--include-c11-in-xp` sums all 11 components for custom draft scoring.*

---

## Reconciliation Changelog

| Date | Finding ID | Change |
|------|-----------|--------|
| 2026-09-04 | M-01..M-07 P1 | Un-gated $C_{10}$ from $P(60+)$ and partitioned into starter duration and substitute cameo duration. Introduced explicit `include_c11_in_xp` flag defaulting to `False` to strictly match official FPL scoring ($C_1 \dots C_{10}$). Decontaminated substitute cameos from starter minutes in `minutes_model.py`. Preserved veteran rotation starter priors ($\ge 1800$ mins $\implies \pi_0 \ge 0.90$). Eliminated BPS event double-counting. Converted captaincy empirical Bayes decay to player-specific season minute evidence. |
| 2026-09-04 | M-02 | Formally integrated continuous minutes survival hazard engine (`minutes_model.py`) into $C_1$, $C_2$, and $C_{11}$. Eliminated DC double-discounting with conditional 60+ minute rate normalization. |
| 2026-09-04 | M-01 | Upgraded $C_9$ and $C_{10}$ from Poisson to Negative Binomial distribution with overdispersion $r=6.0$ to resolve zero-inflation and fat-tail blowout under-penalization. |
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


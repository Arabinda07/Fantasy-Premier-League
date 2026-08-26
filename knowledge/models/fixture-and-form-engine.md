---
type: Model Component
title: Fixture & Form Adjustment Engine
description: Mathematical formulation for short-form blending with shrinkage, conjugate venue factors, promoted team priors, dynamic GK save scaling, and Double Gameweek dampening.
resource: model/fixture_engine.py
tags: [math, model, fixtures, form, venue-symmetry]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: fixture-engine-src
    resource: model/fixture_engine.py
    title: Fixture Engine Source Code
  - id: phase3-spec
    resource: docs/superpowers/specs/2026-08-25-remediation-and-phase-3-design.md
    title: Phase 3 Fixture & Form Engine Design Spec
---

# Mathematical Specification: Fixture & Form Engine

The fixture & form engine ([model/fixture_engine.py](/computations/adjust-fixtures.md)) scales baseline player scoring expectations according to recent individual form, venue dynamics, and opponent strength.

---

## 1. Short-Form Blending with Sample-Size Shrinkage

Short-term form (last 6 calendar gameweeks) is blended into long-form baseline rates with sample-size shrinkage ($M_{\text{threshold}} = 450.0\text{ mins}$ / 5 full games) to prevent noisy cameos from distorting projections:[^phase3-spec]

$$\alpha_{\text{eff}} = \alpha \cdot \frac{M_{\text{short}}}{M_{\text{short}} + 450.0} \quad (\text{where } \alpha = 0.35)$$

$$\text{rate}_{\text{blended}} = \alpha_{\text{eff}} \cdot \text{rate}_{\text{short}} + (1 - \alpha_{\text{eff}}) \cdot \text{rate}_{\text{long}}$$

Blending is applied to `xg90`, `xa90`, `dc90`, and `bonus90`. If $M_{\text{short}} \le 0$, the long-form rate is used directly.

---

## 2. Conjugate Symmetric Venue Factors & Goal Conservation

To preserve mathematical goal conservation ($\mathbb{E}[\text{Scored}] \equiv \mathbb{E}[\text{Conceded}]$ across any fixture), venue multipliers use exact multiplicative inverses ($1.08 \longleftrightarrow 1 / 1.08 \approx 0.9259$):

* **Home Team Attack**: $\text{Venue}_{\text{Home\_Att}} = 1.0800$
* **Away Team Defense**: $\text{Venue}_{\text{Away\_Def}} = 0.9259$
* **Away Team Attack**: $\text{Venue}_{\text{Away\_Att}} = 0.9259$
* **Home Team Defense**: $\text{Venue}_{\text{Home\_Def}} = 1.0800$

---

## 3. Promoted Team Baseline Priors

For newly promoted sides without historical Premier League data in the evaluation window, the engine injects defensive and attacking league priors:
* $\text{Promoted } xG90 = 1.050$ (League baseline $\mu_{\text{league}} \approx 1.350$)
* $\text{Promoted } xGC90 = 1.800$ (League baseline $\mu_{\text{league}} \approx 1.350$)

---

## 4. Opponent Strength Multipliers

Given opponent expected goals conceded ($xGC_{\text{opp}}$) and expected goals scored ($xG_{\text{opp}}$) relative to the league averages ($\mu_{xG} \approx 1.350, \mu_{xGC} \approx 1.350$):

$$\text{Attack\_Mult} = \left( \frac{xGC_{\text{opp}}}{\mu_{xGC}} \right) \cdot \text{Venue}_{\text{Att}}$$

$$\text{Fixture\_xGC90} = \text{Team\_xGC90} \cdot \left( \frac{xG_{\text{opp}}}{\mu_{xG}} \right) \cdot \text{Venue}_{\text{Def}}$$

* Goals ($C_8$) and Assists ($C_7$) are scaled by $\text{Attack\_Mult}$:
  $$\text{adj\_xg90}_{\text{fixture}} = \text{adj\_xg90} \cdot \text{Attack\_Mult}$$
  $$\text{adj\_xa90}_{\text{fixture}} = \text{adj\_xa90} \cdot \text{Attack\_Mult}$$
* Clean Sheets ($C_9$) and Goals Conceded Penalty ($C_{10}$) use $\lambda_{\text{adj}} = \text{Fixture\_xGC90}$.

---

## 5. Dynamic Component Scaling

### Goalkeeper Save Scaling ($C_3$)
Budget goalkeepers facing high shot volume generate more save opportunities:

$$\text{Saves\_Mult} = \left( \frac{xG_{\text{opp}}}{\mu_{xG}} \right)^{0.65} \cdot \text{Venue}_{\text{Def}}$$
$$\text{saves}90_{\text{fixture}} = \text{clamp}\left( \text{raw\_saves}90 \cdot \text{Saves\_Mult}, \, 0.5, \, 7.5 \right)$$

### Bonus Points Scaling ($C_6$)
Teams scoring more goals capture a higher share of BPS:

$$\text{bonus}90_{\text{fixture}} = \text{blended\_bonus}90 \cdot \text{clamp}\left( \text{Attack\_Mult}^{0.75}, \, 0.3, \, 2.0 \right)$$

### Defensive Contribution Scaling ($C_{11}$)
Defenders facing heavier opponent pressure register more tackles, blocks, and clearances:

$$\text{dc}90_{\text{fixture}} = \text{adj\_dc}90 \cdot \text{clamp}\left( \left(\frac{xG_{\text{opp}}}{\mu_{xG}}\right)^{0.40}, \, 0.5, \, 1.8 \right)$$

---

## 6. Double & Blank Gameweeks (DGW / BGW)

* **Blank Gameweek (BGW)**: Player plays 0 fixtures $\implies xP = 0.0$.
* **Double Gameweek (DGW)**: Player plays 2 fixtures. Match 1 is evaluated normally. For outfield players, Match 2 applies a **$0.90\times$ fatigue/rotation decay** on expected starts:

$$P(\text{Start})_{\text{Match 2}} = 0.90 \cdot P(\text{Start})_{\text{Match 1}}$$
$$xP_{\text{DGW}} = xP_{\text{Match 1}} + xP_{\text{Match 2}}$$

All 11 component points ($C_1 \dots C_{11}$) are summed across both matches, while `fixture_attack_mult` and `fixture_xgc90` are averaged.

[^phase3-spec]: `docs/superpowers/specs/2026-08-25-remediation-and-phase-3-design.md`
[^fixture-engine-src]: `model/fixture_engine.py`

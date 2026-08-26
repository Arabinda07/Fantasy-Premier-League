---
type: Model Component
title: Continuous Minutes Hazard Engine & Playing Probability Model
description: Probabilistic modeling of three-regime survival decomposition, continuous minutes hazard, pre-60 hook hazard, European congestion rest decay, and FPL availability dampening.
resource: model/minutes_model.py
tags: [math, model, minutes, hazard, rotation, probabilities]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: minutes-src
    resource: model/minutes_model.py
    title: Minutes Model Source Code
  - id: rotation-src
    resource: model/rotation_intelligence.py
    title: Rotation Intelligence Subsystem
---

# Mathematical Specification: Continuous Minutes Hazard Engine

The minutes engine ([model/minutes_model.py](/models/index.md)) calculates continuous playing time distributions, availability hazard, and threshold probabilities for FPL qualification points.

---

## 1. Three-Regime Survival Decomposition

A player's playing status on any matchday belongs to one of three mutually exclusive regimes:

1. **Starter Regime**: $P(\text{Start})$ with conditional duration $f(t \mid \text{Start})$
2. **Substitute Regime**: $P(\text{Sub})$ with conditional duration $f(t \mid \text{Sub})$ ($\mu_{\text{sub}} = 20.0\text{ mins}$)
3. **Did Not Play (DNP) Regime**: $P(\text{DNP}) = 1.0 - P(\text{Start}) - P(\text{Sub})$

---

## 2. Baseline Start Rate & Cold-Start Priors

From short-form match logs ($N_{\text{matches}} > 0$):

$$\text{raw\_start\_rate} = \frac{S_{\text{short}}}{N_{\text{matches}}}, \quad \text{avg\_starter\_mins} = \text{clamp}\left(\frac{M_{\text{short}}}{S_{\text{short}}}, \, 45.0, \, 92.0\right)$$

For new signings or players without match logs in the current season, empirical price-tier priors are applied:
* $\text{Cost} \ge \pounds 10.0\text{M} \implies P(\text{Start}) = 0.92, \quad \text{avg\_starter\_mins} = 88.0$
* $\text{Cost} \ge \pounds 7.5\text{M} \implies P(\text{Start}) = 0.85, \quad \text{avg\_starter\_mins} = 82.0$
* $\text{Cost} \ge \pounds 5.5\text{M} \implies P(\text{Start}) = 0.65, \quad \text{avg\_starter\_mins} = 75.0$
* $\text{Cost} \ge \pounds 4.5\text{M} \implies P(\text{Start}) = 0.40, \quad \text{avg\_starter\_mins} = 70.0$
* $\text{Cost} < \pounds 4.5\text{M} \implies P(\text{Start}) = 0.10, \quad \text{avg\_starter\_mins} = 65.0$

---

## 3. European Congestion & Rest Hazard

For clubs competing in European competitions (UCL, UEL, UECL):

* **$\le 3$ Days Rest**: Multiplier $0.82\times$ for rotation-heavy managers (e.g. Man City, Arsenal, Chelsea, Liverpool), $0.88\times$ for standard clubs.
* **$4$ Days Rest**: Multiplier $0.92\times$.
* **$\ge 5$ Days Rest**: Multiplier $1.00\times$ (full recovery).

---

## 4. FPL News & Injury Status Dampening

Based on official FPL API status flags and `chance_of_playing_next_round`:

| Availability Status | FPL Chance % | $P(\text{Start})$ Multiplier | $P(\text{App})$ Multiplier |
|---|---|---|---|
| Available (`'a'`) | 100% | $1.00\times$ | $1.00\times$ |
| Doubtful (`'d'`) | 75% | $0.80\times$ | $0.85\times$ |
| Questionable (`'d'`) | 50% | $0.50\times$ | $0.55\times$ |
| Unlikely (`'d'`) | 25% | $0.20\times$ | $0.25\times$ |
| Injured / Suspended (`'i'`, `'s'`, `'u'`) | 0% | $0.00\times$ | $0.00\times$ |

$$P(\text{Start}) = \text{clamp}\left(\text{raw\_start\_rate} \cdot \text{Midweek\_Mult} \cdot \text{News\_Start\_Mult}, \, 0.0, \, 0.98\right)$$

$$P(\text{Sub}) = (1.0 - P(\text{Start})) \cdot P_{\text{sub\_base}} \cdot \text{News\_App\_Mult} \quad (P_{\text{sub\_base}} = 0.45\text{ outfield}, \, 0.01\text{ GK})$$

---

## 5. Pre-60 Hook Hazard & $P(60+)$ Qualification

Goalkeepers are rarely substituted ($P(\text{Hook} \mid \text{Start}) = 0.005$). For outfield players, hook probability follows a calibrated logistic sigmoid centered at 63.5 minutes:

$$z = \frac{63.5 - \text{eff\_mins}}{8.5}, \quad \text{raw\_p} = \frac{1}{1 + e^{-z}}$$

$$P(\text{Hook} \mid \text{Start}) = \text{clamp}\left(\text{raw\_p} \cdot \text{Manager\_Hook\_Mult} \cdot \text{Def\_Factor}, \, 0.005, \, 0.45\right)$$
where $\text{Def\_Factor} = 0.55$ for defenders and $1.00$ for midfielders/forwards.

### Exact 60+ Minute Probability ($P(60+)$)

$$P(60+) = P(\text{Start}) \cdot (1.0 - P(\text{Hook} \mid \text{Start})) + P(\text{Sub}) \cdot 0.005$$

### Expected Playing Minutes ($\mathbb{E}[M]$)

$$\mathbb{E}[M \mid \text{Start}] = (1 - P(\text{Hook} \mid \text{Start})) \cdot \text{avg\_starter\_mins} + P(\text{Hook} \mid \text{Start}) \cdot 52.0$$

$$\mathbb{E}[M] = P(\text{Start}) \cdot \mathbb{E}[M \mid \text{Start}] + P(\text{Sub}) \cdot 20.0$$

### Expected Appearance Points ($C_1 + C_2$)

$$C_1 = 1.0 \cdot P(\text{App}), \quad C_2 = 1.0 \cdot P(60+)$$

[^minutes-src]: `model/minutes_model.py`
[^rotation-src]: `model/rotation_intelligence.py`

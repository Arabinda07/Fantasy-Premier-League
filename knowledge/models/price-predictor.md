---
type: Model Component
title: Price Change Forecaster
description: Real-time monitoring of net transfer balances and ownership velocity to forecast overnight £0.1M price rises and falls.
resource: model/price_predictor.py
tags: [math, model, price-changes, transfer-velocity, market]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: price-pred-src
    resource: model/price_predictor.py
    title: Price Predictor Subsystem
---

# Mathematical Specification: Price Change Forecaster

The price predictor ([model/price_predictor.py](/models/index.md)) forecasts nightly price changes based on net transfer delta velocity:

$$\text{Net\_Velocity} = \text{transfers\_in\_event} - \text{transfers\_out\_event}$$

---

## 1. Dynamic Threshold Model

FPL price change thresholds scale with player ownership fraction:

$$\text{Threshold} = 100,000 \cdot \left( 1.0 + 2.0 \cdot \text{ownership\_pct} \right)$$

$$\text{Velocity\_Ratio} = \frac{\text{Net\_Velocity}}{\text{Threshold}}$$

---

## 2. Alert Tier Classifications

| Tier | Velocity Ratio ($\frac{\text{Net\_Velocity}}{\text{Threshold}}$) | Action Implication |
|---|---|---|
| **`RISING_LOCK`** | $\ge +1.0$ | Price rise $+£0.1\text{M}$ imminent within 24 hours. Buy before lockout. |
| **`RISING_ALERT`** | $\ge +0.75$ | Strong upward momentum ($\ge 75\%$ of threshold). Monitor closely. |
| **`STABLE`** | $(-0.75, \, +0.75)$ | Low price change momentum. Safe to hold. |
| **`FALLING_ALERT`** | $\le -0.75$ | Strong downward selling pressure ($\le -75\%$). Consider early sale. |
| **`FALLING_LOCK`** | $\le -1.0$ | Price drop $-£0.1\text{M}$ imminent within 24 hours. Sell before loss. |

[^price-pred-src]: `model/price_predictor.py`

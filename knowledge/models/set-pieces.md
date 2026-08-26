---
type: Model Component
title: Set-Piece Specialist Hierarchies
description: Designated penalty takers, direct free-kick specialists, and corner taker priority hierarchies across all 20 Premier League clubs.
resource: model/set_pieces.py
tags: [math, model, set-pieces, penalties, corners]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: set-pieces-src
    resource: model/set_pieces.py
    title: Set Pieces Subsystem
---

# Mathematical Specification: Set-Piece Specialists

The set-piece engine ([model/set_pieces.py](/models/index.md)) reads official FPL set-piece role hierarchies (`penalties_order`, `direct_freekicks_order`, `corners_and_indirect_freekicks_order`) and calculates additive equity for goals ($C_8$) and assists ($C_7$).

---

## 1. Penalty Kick (PK) Equity

* Team penalty frequency: $\text{rate}_{\text{pk}} = 0.12\text{ per 90}$
* Expected goals per penalty: $\text{xG}_{\text{pk}} = 0.79$
* Conversion rate: $78\%$

### Primary Taker ($\text{pk\_order} = 1$):
$$\Delta xG_{\text{pk}} = P(\text{Pitch}) \cdot \text{rate}_{\text{pk}} \cdot \text{xG}_{\text{pk}}$$
$$\Delta C_8 = \Delta xG_{\text{pk}} \cdot \text{GoalPts}(\text{POS}) \cdot 0.78$$

### Secondary Taker ($\text{pk\_order} = 2$):
Takes penalties only when the primary taker is absent ($P_{\text{primary\_on\_pitch}} \approx 0.90$):
$$\Delta xG_{\text{pk}} = P(\text{Pitch}) \cdot (1.0 - P_{\text{primary\_on\_pitch}}) \cdot \text{rate}_{\text{pk}} \cdot \text{xG}_{\text{pk}}$$

---

## 2. Corner & Direct Free-Kick Assist Equity

* Corner volume: $\text{CK}_{\text{team}} = 5.5\text{ per 90}$, Expected assist per corner: $xA_{\text{ck}} = 0.018$
* Direct free-kick volume: $\text{FK}_{\text{team}} = 1.2\text{ per 90}$, Expected assist per FK: $xA_{\text{fk}} = 0.020$

### Delivery Specialist ($\text{ck\_order} = 1, \text{fk\_order} = 1$):
$$\Delta xA_{\text{ck}} = P(\text{Pitch}) \cdot \text{CK}_{\text{team}} \cdot xA_{\text{ck}}$$
$$\Delta xA_{\text{fk}} = P(\text{Pitch}) \cdot \text{FK}_{\text{team}} \cdot xA_{\text{fk}}$$
$$\Delta C_7 = (\Delta xA_{\text{ck}} + \Delta xA_{\text{fk}}) \cdot 3.0$$

---

## 3. Total Expected Points Adjustment

$$\text{Adjusted } xP = xP_{\text{baseline}} + \Delta C_8 + \Delta C_7$$

[^set-pieces-src]: `model/set_pieces.py`

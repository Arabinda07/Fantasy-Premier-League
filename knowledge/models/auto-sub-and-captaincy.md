---
type: Model Component
title: Live Auto-Substitutions & Captaincy Rollover Invariants
description: Formal specification for live matchday formation-safe bench auto-substitutions, vice-captain promotion rules, and unplayed captaincy degradation.
resource: model/live_sync.py
tags: [math, model, auto-subs, captaincy-rollover, live-matchday]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T20:20:00Z }
sources:
  - id: live-sync-src
    resource: model/live_sync.py
    title: Live Sync Subsystem
---

# Mathematical Specification: Live Auto-Substitutions & Captaincy Rollover

The live matchday tracking engine ([model/live_sync.py](/models/index.md)) resolves in-progress and finalized matchday substitutions and captaincy promotions under official Premier League Fantasy rules.

---

## 1. Captaincy Rollover Invariant

For starting squad designated captain $C$ and vice-captain $VC$:

$$\text{Effective\_Captain} = \begin{cases}
C & \text{if } \text{Minutes}(C) > 0 \\
VC & \text{if } \text{Minutes}(C) = 0 \text{ and } \text{Minutes}(VC) > 0 \\
\text{None} & \text{if } \text{Minutes}(C) = 0 \text{ and } \text{Minutes}(VC) = 0
\end{cases}$$

$$\text{Multiplier}(\text{Effective\_Captain}) = 2\times$$

*If both $C$ and $VC$ fail to play ($\text{Minutes} = 0$), no $2\times$ multiplier is awarded to any player on the pitch; all active starting XI assets score $1\times$ baseline points.*

---

## 2. Formation-Safe Bench Auto-Substitution Engine

When a starter $p_{\text{starter}}$ plays 0 minutes ($\text{DNP}$):

### Goalkeeper Rule:
* An unplayed Goalkeeper can **only** be replaced by the bench Goalkeeper ($GK_{\text{bench}}$), provided $GK_{\text{bench}}$ played $> 0$ minutes.

### Outfield Priority & Legality Rules:
* Outfield bench players are evaluated sequentially in user-designated bench priority order ($B_1, B_2, B_3$).
* A candidate bench player $B_k$ is substituted for $p_{\text{starter}}$ **if and only if** the resulting 11-player formation $\mathcal{F}$ satisfies the fundamental FPL outfield bounds:

$$\mathcal{F} \text{ is legal} \iff \begin{cases}
N_{\text{GK}} = 1 \\
N_{\text{DEF}} \in \{3, 4, 5\} \\
N_{\text{MID}} \in \{2, 3, 4, 5\} \\
N_{\text{FWD}} \in \{1, 2, 3\}
\end{cases}$$

* **Skipping Rule**: If substituting $B_k$ would violate formation constraints (e.g. replacing a 3rd Defender with a 6th Midfielder, leaving only 2 Defenders on pitch), $B_k$ is skipped, and the engine tests $B_{k+1}$.

[^live-sync-src]: `model/live_sync.py`

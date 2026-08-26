---
type: Model Component
title: Squad Optimization Solver (MILP)
description: Mixed-Integer Linear Programming (MILP) formulation for optimal 15-man squad selection, Starting XI, captaincy, multi-gameweek lookahead, transfer penalties, 50% profit retention, and CVaR risk.
resource: model/solver.py
tags: [math, model, optimization, milp, solver, linear-programming]
generated: { by: reference_agent/gemini-3.7-flash, at: 2026-08-26T19:21:00Z }
reconciled: { by: adversarial_audit/gemini-3.7-flash, at: 2026-08-26T20:08:00Z }
sources:
  - id: solver-src
    resource: model/solver.py
    title: Squad Solver Subsystem
  - id: phase4-spec
    resource: docs/superpowers/specs/2026-08-25-fpl-squad-optimization-solver-design.md
    title: Phase 4 Squad Optimization Solver Design Spec
---

# Mathematical Specification: Squad Optimization Solver

The squad optimization solver ([model/solver.py](/computations/solve-squad.md)) uses **Mixed-Integer Linear Programming (MILP)** (powered by `PuLP` / CBC solver) to select the optimal 15-player squad, 11-player starting XI, captaincy, and weekly transfers.

---

## 1. Decision Variables (per player $i \in \mathcal{P}$ at horizon step $t \in \{0 \dots H-1\}$)

* $x_{i,t} \in \{0, 1\}$: $1$ if player $i$ is in the 15-man squad at horizon step $t$.
* $s_{i,t} \in \{0, 1\}$: $1$ if player $i$ is in the Starting XI at step $t$.
* $c_{i,t} \in \{0, 1\}$: $1$ if player $i$ is designated Captain ($2\times \text{points}$) at step $t$.
* $vcap_{i,t} \in \{0, 1\}$: $1$ if player $i$ is designated Vice-Captain at step $t$.
* $u_{i,t} \in \{0, 1\}$: $1$ if player $i$ is transferred IN at step $t$.
* $v_{i,t} \in \{0, 1\}$: $1$ if player $i$ is transferred OUT at step $t$.
* $\text{hits}_t \in \mathbb{Z}_{\ge 0}$: Integer number of 4-point transfer penalties taken at step $t$.

---

## 2. Objective Function (Multi-Gameweek Horizon Lookahead)

Maximizes discounted expected starting XI points minus transfer hit penalties over lookahead horizon $H$ with discount factor $\gamma = 0.90$:[^phase4-spec]

$$\max \sum_{t=0}^{H-1} \gamma^t \left( \sum_{i \in \mathcal{P}} xP_{i,t} \cdot (s_{i,t} + c_{i,t}) - 4.0 \cdot \text{hits}_t \right)$$

---

## 3. Structural FPL Constraints

### Positional Quotas (15-Man Squad)
$$\sum_{i \in \text{GK}} x_{i,t} = 2, \quad \sum_{i \in \text{DEF}} x_{i,t} = 5, \quad \sum_{i \in \text{MID}} x_{i,t} = 5, \quad \sum_{i \in \text{FWD}} x_{i,t} = 3$$

### Starting XI Formation Rules
* Total starters: $\sum_{i \in \mathcal{P}} s_{i,t} = 11$
* Starter subset of squad: $s_{i,t} \le x_{i,t} \quad \forall i$
* Starting Goalkeepers: $\sum_{i \in \text{GK}} s_{i,t} = 1$
* Valid outfield formations:
  * Defenders: $3 \le \sum_{i \in \text{DEF}} s_{i,t} \le 5$
  * Midfielders: $2 \le \sum_{i \in \text{MID}} s_{i,t} \le 5$
  * Forwards: $1 \le \sum_{i \in \text{FWD}} s_{i,t} \le 3$

### Club Limits
Maximum 3 players from any single Premier League club $k \in \{1 \dots 20\}$:
$$\sum_{i \in \text{Club}_k} x_{i,t} \le 3 \quad \forall k$$

### Captaincy Constraints
* Exactly one captain: $\sum_{i \in \mathcal{P}} c_{i,t} = 1$
* Captain must start: $c_{i,t} \le s_{i,t} \quad \forall i$
* Vice-Captain must start: $vcap_{i,t} \le s_{i,t}, \quad \sum_i vcap_{i,t} = 1, \quad c_{i,t} + vcap_{i,t} \le 1$

---

## 4. Transfer Continuity, FT Accumulation & Free Hit Reversion

### Inter-Temporal Continuity
For $t = 0$:
$$x_{i,0} = \text{initial}_i + u_{i,0} - v_{i,0}, \quad v_{i,0} \le \text{initial}_i$$
For $t \ge 1$ (standard):
$$x_{i,t} = x_{i,t-1} + u_{i,t} - v_{i,t}, \quad v_{i,t} \le x_{i,t-1}$$

### Free Hit Squad Reversion ($t = 1$)
When `chip == 'freehit'`, the squad at step $t=1$ reverts to the pre-FH initial squad:
$$x_{i,1} = \text{initial}_i + u_{i,1} - v_{i,1}, \quad v_{i,1} \le \text{initial}_i$$

### Hits & Free Transfer Balance
$$\text{hits}_t \ge \sum_{i \in \mathcal{P}} u_{i,t} - \text{FT}_t$$
where $\text{hits}_t \in \mathbb{Z}_{\ge 0}$ (integer variable).

---

## 5. Financial Constraints & 50% Profit Retention

FPL allows managers to realize only **50% of the profit** on player price rises, rounded down to the nearest £0.1M:

$$\text{profit\_tenths}_i = \text{round}\left( (\text{current\_price}_i - \text{purchase\_price}_i) \cdot 10 \right)$$
$$\text{share\_tenths}_i = \text{profit\_tenths}_i // 2$$
$$\text{Selling\_Price}_i = \text{purchase\_price}_i + \frac{\text{share\_tenths}_i}{10.0}$$

$$\text{Squad\_Cost}_t = \sum_{i \in \mathcal{P}} \text{Cost}_{i,t} \cdot x_{i,t} \le \text{Budget} + \text{Bank}_t$$

---

## 6. Strategic Chip Modeling

* **Bench Boost (`'bboost'`)**: Starters constraint relaxed to all 15 squad members: $s_{i,t} = x_{i,t} \quad \forall i$.
* **Triple Captain (`'3xc'`)**: Captain multiplier increased from $+1\times$ to $+2\times$ (total $3\times xP$).
* **Free Hit (`'freehit'`)**: Unlimited transfers at $t=0$ ($\text{hits}_0 = 0$); squad reverts to initial state at $t=1$.
* **Wildcard (`'wildcard'`)**: Unlimited transfers permitted with $\text{hits}_t = 0$.

---

## 7. CVaR Risk-Adjusted Optimization

To avoid fragile glass-cannon squads, the solver supports Conditional Value at Risk (CVaR) penalty tuning:

$$\text{Obj}_{\text{Risk}} = \mathbb{E}[\text{xP}] - \lambda \cdot \text{CVaR}_\alpha(\text{Squad})$$

[^solver-src]: `model/solver.py`
[^phase4-spec]: `docs/superpowers/specs/2026-08-25-fpl-squad-optimization-solver-design.md`

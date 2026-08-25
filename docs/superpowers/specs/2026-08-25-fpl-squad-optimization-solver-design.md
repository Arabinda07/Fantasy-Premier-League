# Phase 4 Design Specification: FPL Squad Optimization Solver

**Document Type:** Technical Architecture & Implementation Spec  
**Target Phase:** Phase 4 (Squad Optimization Solver)  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  

---

## 1. Executive Summary & Problem Formulation

In Fantasy Premier League, selecting an optimal squad and weekly transfer plan is a classical **Mixed Integer Linear Programming (MILP / ILP)** combinatorial optimization problem. Given fixture-adjusted expected points ($\text{xP}_i$) and player costs ($w_i$), the solver must find the binary decision variables that maximize total expected points subject to strict FPL rules.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Phase 4 Optimization Layer                      │
├────────────────────────────────────────────────────────────────────────┤
│ Inputs:                                                                │
│  - Fixture Predictions (xP_i) from Phase 3                             │
│  - Player Prices & Teams from players_raw.csv / cleaned_players.csv    │
│  - Budget (£100.0M / 1000 tenths) & Club limits (max 3 / team)        │
│                                                                        │
│ Optimization Problems Solved:                                          │
│  1. Best Initial 15-Man Squad Selection (£100.0M Budget)               │
│  2. Optimal Starting XI & Valid Formation Optimization                 │
│  3. Captain (2x) & Vice-Captain Optimization                           │
│  4. Optimal Bench Ordering & Auto-Sub Expectation                      │
│  5. Weekly Transfer Planner (Rolling FTs, Free Hit, Wildcard, Hits)    │
│                                                                        │
│ Output:                                                                │
│  - data/<season>/optimal_squad_gw<GW>.json & .csv                      │
│  - Formatted terminal report + structured data for Phase 5 Excel export│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical ILP Formulation

### 2.1 Decision Variables
For each candidate player $i \in \{1, \dots, N\}$:
- $x_i \in \{0, 1\}$: $1$ if player $i$ is selected in the 15-man squad, $0$ otherwise.
- $s_i \in \{0, 1\}$: $1$ if player $i$ is selected in the Starting XI, $0$ otherwise.
- $c_i \in \{0, 1\}$: $1$ if player $i$ is selected as Captain ($2\times \text{xP}$), $0$ otherwise.
- $v_i \in \{0, 1\}$: $1$ if player $i$ is selected as Vice-Captain, $0$ otherwise.
- $b_{i, k} \in \{0, 1\}$: $1$ if outfield player $i$ is placed in bench order slot $k \in \{1, 2, 3\}$.

---

### 2.2 Objective Function
Maximize total gameweek expected points (Starting XI + Captaincy bonus + Auto-sub expectation):
$$\max \sum_{i=1}^N \left( \text{xP}_i \cdot s_i + \text{xP}_i \cdot c_i + \text{xP}_i \cdot \text{Bench\_Weight}_i \cdot (x_i - s_i) \right)$$
where $\text{Bench\_Weight}_i \approx 0.10 \times (1 - P(\text{App}_{\text{starters}}))$ reflects the small but non-zero probability of bench auto-substitutions.

---

### 2.3 Mathematical Constraints

#### 1. Squad Size & Positional Quotas (15 Players)
$$\sum_{i \in \text{GK}} x_i = 2, \quad \sum_{i \in \text{DEF}} x_i = 5, \quad \sum_{i \in \text{MID}} x_i = 5, \quad \sum_{i \in \text{FWD}} x_i = 3, \quad \sum_{i=1}^N x_i = 15$$

#### 2. Starting XI Size & Valid Formation Quotas (11 Players)
$$s_i \le x_i \quad \forall i$$
$$\sum_{i=1}^N s_i = 11$$
$$\sum_{i \in \text{GK}} s_i = 1$$
$$3 \le \sum_{i \in \text{DEF}} s_i \le 5$$
$$2 \le \sum_{i \in \text{MID}} s_i \le 5$$
$$1 \le \sum_{i \in \text{FWD}} s_i \le 3$$
*(Valid formations automatically supported: 3-5-2, 3-4-3, 4-4-2, 4-3-3, 4-5-1, 5-3-2, 5-4-1, 5-2-3)*

#### 3. Budget Constraint
$$\sum_{i=1}^N \text{Cost}_i \cdot x_i \le \text{Budget} \quad (\text{default } 1000 \text{ in tenths of \pounds M})$$

#### 4. Team / Club Constraint
$$\sum_{i \in \text{Team } t} x_i \le 3 \quad \forall t \in \{1, \dots, 20\}$$

#### 5. Captaincy & Vice-Captaincy Constraints
$$c_i \le s_i \quad \forall i, \quad \sum_{i=1}^N c_i = 1$$
$$v_i \le s_i \quad \forall i, \quad \sum_{i=1}^N v_i = 1$$
$$c_i + v_i \le 1 \quad \forall i$$

---

### 2.4 Transfer Optimization & Rolling Horizon

Given an existing squad $S_0$, bank balance $B$, and available free transfers $FT \in \{1, \dots, 5\}$:
- $y_i^{\text{in}} \in \{0, 1\}$: $1$ if player $i$ is transferred IN.
- $y_i^{\text{out}} \in \{0, 1\}$: $1$ if player $i$ is transferred OUT.
- Conservation: $x_i = x_{i, 0} + y_i^{\text{in}} - y_i^{\text{out}}$.
- Transfers count: $N_{\text{transfers}} = \sum_{i=1}^N y_i^{\text{in}} = \sum_{i=1}^N y_i^{\text{out}}$.
- Transfer penalty: $\text{Penalty} = 4 \times \max(0, N_{\text{transfers}} - FT)$.
- Net transfer budget constraint: $\sum_{i=1}^N \text{SellPrice}_i \cdot y_i^{\text{out}} + B \ge \sum_{i=1}^N \text{BuyPrice}_i \cdot y_i^{\text{in}}$.

---

## 3. Module Architecture & File Layout

```
model/
├── __init__.py                # Exports solve_squad, solve_transfers
├── solver.py                  # Core PuLP ILP optimization engine
├── test_solver.py             # Pytest unit test suite (10+ tests)
```

### Core Classes & Functions in `model/solver.py`:
1. `class SquadSolution`: Dataclass holding squad, starting XI, bench order, captain, vice-captain, total xP, total cost, and formation string (e.g. `'3-4-3'`).
2. `solve_initial_squad(df, budget=100.0, max_team_players=3)`: Selects optimal 15-man squad, starting XI, and captaincy from scratch.
3. `solve_weekly_transfers(current_squad_ids, df, free_transfers=1, bank=0.0, max_transfers=3, hit_cost=4.0)`: Finds optimal transfers in/out and lineup.
4. `order_bench(bench_players, starting_xi)`: Determines exact bench priority (GK in slot 1, outfield ordered by xP).
5. `format_squad_output(solution)`: Beautiful terminal dashboard printing pitch formation, captaincy, bench, and totals.

---

## 4. Verification & Testing Plan

1. **Unit Tests in `model/test_solver.py`**:
   - Verify valid 15-player squad (2 GK, 5 DEF, 5 MID, 3 FWD).
   - Verify budget compliance ($\le \pounds 100.0\text{M}$).
   - Verify max 3 players per Premier League club.
   - Verify valid Starting XI formation (e.g. min 3 DEF, min 1 FWD, sum=11).
   - Verify Captain and Vice-Captain are distinct starters and captain has highest/top xP.
   - Verify Bench order: GK in bench slot 1, outfield ordered descending by xP.
   - Verify Transfer solver respects $FT$, penalizes $-4$ hits correctly, and abides by budget.
   - Verify solver handles infeasible/edge cases gracefully.
2. **Integration Verification**:
   - Run `python -m model.solver --season 2026-27 --gw 1` to generate the optimal GW1 squad.

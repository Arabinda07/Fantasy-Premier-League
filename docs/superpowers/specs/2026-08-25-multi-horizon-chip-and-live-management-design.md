# Design Specification: Multi-Gameweek Horizon Solver, Chip Timing Optimizer & Live Gameweek Manager

**Document Type:** Technical Architecture & Implementation Spec  
**Target Phase:** Advanced Strategy Layer (Multi-GW Horizon, Chip Timing, Live Matchday Manager)  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  

---

## 1. Executive Summary & Problem Formulation

While the single-gameweek solver and 11-component prediction engine successfully identify high-ceiling players, historical 38-gameweek backtesting revealed three critical strategic gaps separating the model from top-10k rank ($65+\text{ pts/GW}$):

1. **Single-Gameweek Myopia**: A 1-week optimizer purchases assets for immediate easy fixtures even when their 3-week schedule turns dreadful, burning free transfers and accumulating deadwood.
2. **Chip Timing Gap (+150 to +250 pts)**: Strategic FPL chips (Triple Captain, Bench Boost, Free Hit, 2x Wildcards) must be scheduled to exploit Double Gameweeks (DGWs) and navigate Blank Gameweeks (BGWs).
3. **Live Matchday Management**: Live seasons require real-time injury status awareness (`chance_of_playing_this_round`), transfer roll vs. hit decision logic, and automated matchday briefing generation.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             ADVANCED STRATEGY & LIVE MANAGEMENT LAYER                            │
├───────────────────────────────┬───────────────────────────────┬──────────────────────────────────┤
│ 1. Multi-GW Horizon Solver    │ 2. Chip Timing Optimizer      │ 3. Live Matchday Manager         │
│   (model/solver.py)           │   (model/chip_optimizer.py)   │   (model/live_manager.py)        │
├───────────────────────────────┼───────────────────────────────┼──────────────────────────────────┤
│ • 3-to-5 Gameweek Lookahead   │ • DGW & BGW Schedule Scanner  │ • User Team / Squad Ingestion    │
│ • Time-Discounted Objective   │ • Triple Captain DGW Peaks    │ • Real-time Injury & News Filter │
│ • Inter-Temporal Transfer &   │ • Bench Boost DGW Optimizer   │ • Roll vs Transfer vs Hit Logic  │
│   Bank Balance Constraints    │ • Blank GW Free Hit Trigger   │ • Live Matchday Briefing &       │
│ • Deadwood Churn Elimination  │ • Wildcard 1 & 2 Reset Windows│   Excel / JSON Export            │
└───────────────────────────────┴───────────────────────────────┴──────────────────────────────────┘
```

---

## 2. Multi-Gameweek Horizon Mathematical Formulation

For a lookahead horizon $H \in \{3, 4, 5\}$ and discount factor $\gamma \in [0.85, 0.95]$ (default $\gamma = 0.90$):

### Objective Function:
$$\max \sum_{t=1}^H \gamma^{t-1} \left( \sum_{i \in \text{Starters}_t} \text{xP}_{i,t} + \text{xP}_{\text{Capt},t} + w_{\text{bench}} \sum_{j \in \text{Bench}_t} \text{xP}_{j,t} - 4.0 \times \text{Hits}_t \right)$$

### Inter-Temporal Constraints across $t = 1 \dots H$:
1. **Squad Continuity**:
   $$x_{i,t} = x_{i,t-1} + u_{i,t} - v_{i,t} \quad \forall i, \forall t \ge 2$$
   where $x_{i,t} \in \{0, 1\}$ is squad membership, $u_{i,t} \in \{0, 1\}$ is transfer in, $v_{i,t} \in \{0, 1\}$ is transfer out.
2. **Transfer Counts**:
   $$T_t = \sum_i u_{i,t} = \sum_i v_{i,t}$$
3. **Free Transfer Dynamics (FPL 1 to 5 FT Rules)**:
   $$\text{FT}_1 = \text{Initial FT}$$
   $$\text{FT}_t = \min(5, \max(1, \text{FT}_{t-1} - T_{t-1} + 1)) \quad \forall t \ge 2$$
   $$\text{Hits}_t = \max(0, T_t - \text{FT}_t)$$
4. **Bank & Selling Price Balance**:
   $$\text{Bank}_t = \text{Bank}_{t-1} + \sum_i \text{SellPrice}_{i,t} v_{i,t} - \sum_j \text{BuyPrice}_{j,t} u_{j,t} \ge 0$$
5. **Positional Quotas & Club Limit**:
   $$\sum_{i \in \text{GK}} x_{i,t} = 2, \quad \sum_{i \in \text{DEF}} x_{i,t} = 5, \quad \sum_{i \in \text{MID}} x_{i,t} = 5, \quad \sum_{i \in \text{FWD}} x_{i,t} = 3$$
   $$\sum_{i \in \text{Club}_k} x_{i,t} \le 3 \quad \forall k \in \{1 \dots 20\}, \forall t$$

---

## 3. Chip Timing Optimizer (`model/chip_optimizer.py`)

Scans all remaining fixtures across the season (GW1–GW38) and computes the **Expected Value Delta** of activating each chip:

1. **Triple Captain ($\Delta_{\text{3xC}}(t)$)**:
   $$\Delta_{\text{3xC}}(t) = \max_{i} \text{xP}_{i,t}$$
   Identifies DGWs where a premium captain (e.g. Haaland/Salah) plays twice with low opponent FDR.
2. **Bench Boost ($\Delta_{\text{BB}}(t)$)**:
   $$\Delta_{\text{BB}}(t) = \sum_{j \in \text{Bench}_t} \text{xP}_{j,t}$$
   Identifies DGWs where all 4 bench players have guaranteed minutes and high expected points.
3. **Free Hit ($\Delta_{\text{FH}}(t)$)**:
   $$\Delta_{\text{FH}}(t) = \text{xP}(\text{Optimal Squad}_t) - \text{xP}(\text{Current Squad without transfers}_t)$$
   Triggers during severe Blank Gameweeks where the existing squad has 4+ blanks.
4. **Wildcard Windows ($\text{WC}_1$: GW2–GW19, $\text{WC}_2$: GW20–GW38)**:
   Recommends structural reset points when squad value can be reinvested into a massive long-term fixture swing or to prepare for a Bench Boost DGW.

---

## 4. Live Matchday Manager (`model/live_manager.py`)

A high-level command orchestrator providing live assistant capabilities:
- `plan_gameweek(season, gw, squad_codes, bank, free_transfers, horizon=3, chips_available=None)`:
  - Generates immediate GW transfer recommendation, rolling transfers path for GW+1 and GW+2, starting XI, captain, vice-captain, and bench order.
  - Formats an executive terminal matchday briefing.
  - Updates the Excel matchday report (`fpl_matchday_live_gw<GW>.xlsx`) and exports JSON state.

---

## 5. Verification Plan

1. **Unit Tests in `model/test_multi_horizon.py` and `model/test_chip_optimizer.py`**:
   - Verify multi-gameweek continuity, bank conservation, transfer count limits, and time-discounted trajectory.
   - Verify DGW/BGW detection and chip recommendations.
2. **Backtesting Validation**:
   - Re-run backtest on 2024-25 and 2025-26 with multi-gameweek lookahead to verify reduction in transfer churn and higher points baseline.

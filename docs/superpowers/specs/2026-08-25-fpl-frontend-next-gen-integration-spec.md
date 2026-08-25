# Technical Specification: Next-Gen Quantitative Frontend Cockpit & Backend Integration Architecture

**Date:** 2026-08-25  
**Author:** Antigravity (Principal Quantitative UI/UX Architect)  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  
**Target Directory:** `frontend/` (`frontend/src/components/`, `frontend/src/data/`, `frontend/src/styles/`)  
**Companion Backend Specs:**  
- `docs/superpowers/specs/2026-08-25-fpl-next-gen-alpha-architecture-design.md`  
- `docs/superpowers/specs/2026-08-25-fpl-frontend-cockpit-design.md`  

---

## 1. Executive Summary & Design Directive

### 1.1 Objective
To bridge the gap between our newly completed, high-performance quantitative backend (`model/`) and the user-facing web cockpit (`frontend/`). We transform the dashboard from a static scalar display into an **Institutional Quantitative Sports Terminal & Decision Cockpit** inspired by Bloomberg Terminal and StatsBomb, providing real-time probabilistic transparency, 1-click live FPL squad ingestion, mini-league game theory matrices, and interactive multi-horizon transfer roadmaps.

### 1.2 The "Absolute Zero" Anti-Slop Discipline
- ❌ **No generic AI marketing tropes**: No floating purple/cyan glowing orbs, blurry glass bubbles, or generic 3-column SaaS pricing cards.
- ❌ **No single-scalar opacity**: Never present a lone "$6.31\text{ xP}$" without displaying its underlying probabilistic uncertainty (Floor $p_{10}$, Median $p_{50}$, Ceiling $p_{90}$, and Haul Probability).
- ✅ **Double-Bezel Hardware Architecture**: Machine-edged concentric containers (outer shell `ring-1 ring-white/10` + inner core `shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)]`).
- ✅ **Tabular Typography**: `JetBrains Mono` and `Plus Jakarta Sans` with strict `font-variant-numeric: tabular-nums`.
- ✅ **Tactical Color Calibration**: Obsidian Base (`#0B0F17`), Elevated Surface (`#111827`), Turf Grass (`#064E3B`), Emerald Velocity (`#10B981`), Amber Captaincy (`#F59E0B`), and Crimson Risk (`#EF4444`).

---

## 2. System Architecture & End-to-End Data Flow

```mermaid
flowchart TD
    subgraph Backend_Engines [Backend Quantitative Architecture (model/)]
        A1[Dixon-Coles Match Simulator<br/>model/match_simulator.py] --> B[live_matchday_gwX.json]
        A2[Minutes Hazard & Survival Engine<br/>model/minutes_model.py] --> B
        A3[MILP Solver with CVaR & FT Shadow<br/>model/solver.py] --> B
        A4[Direct FPL API Live Sync<br/>model/live_sync.py] --> B
        A5[Set-Piece & Matchup Intelligence<br/>model/set_pieces.py] --> B
    end

    subgraph Frontend_App [Frontend React Cockpit (frontend/src/)]
        B --> C[App.jsx State Router & LocalStorage]
        C --> D1[Header.jsx & LiveTeamSyncModal.jsx]
        C --> D2[TacticalPitch.jsx & PlayerCard.jsx]
        C --> D3[MultiGwPlanner.jsx]
        C --> D4[RivalThreatMatrix.jsx]
        C --> D5[FixtureProbabilityDrawer.jsx]
        C --> D6[PlayerDNAInspector.jsx]
    end
```

---

## 3. Detailed Component Specifications & UI Contracts

### Component 1: `PlayerCard.jsx` & `TacticalPitch.jsx` (Probability Sparklines & Risk Indicators)

#### Capabilities:
1. **Three-Tier Probability Range Bar**:
   - Visual horizontal micro-bar embedded below the primary expected points badge:
     - **Floor ($p_{10}$)**: Soft muted slate gray (e.g. `2 pts`).
     - **Median ($p_{50}$)**: Standard tactical emerald (e.g. `6 pts`).
     - **Ceiling ($p_{90}$)**: Electric gold badge (e.g. `14 pts`).
2. **Haul Probability Badge**:
   - For explosive assets with $\mathbb{P}(\text{Points} \ge 10) \ge 0.20$, display an ambient micro-pill: `⚡ Haul 28%`.
3. **Continuous Minutes Security & Hook Hazard Warning**:
   - Display a visual security indicator based on $P(\text{Mins} \ge 60)$:
     - **High Security ($\ge 90\%$)**: Subtle green shield icon.
     - **Pre-60 Hook Hazard ($\ge 15\%$ hazard)**: Amber clock badge (`⚠️ Hook Risk`).
     - **Midweek Congestion Hazard ($\le 3$ days rest)**: Crimson flash badge (`⚡ 3-Day Turnaround`).
4. **Set-Piece Hierarchy Badges**:
   - Explicit micro-tags for primary dead-ball specialists: `[PK1]`, `[CK1]`, `[FK1]`.

#### UI Component State / Props:
```typescript
interface PlayerCardProps {
  player: {
    player_code: number;
    web_name: string;
    team: string;
    position: 'GK' | 'DEF' | 'MID' | 'FWD';
    cost: number;
    expected_points: number;
    floor_p10?: number;
    median_p50?: number;
    ceiling_p90?: number;
    haul_prob?: number;
    p_start?: number;
    p_mins_60?: number;
    hook_hazard?: number;
    rest_days?: number;
    sp_pk_order?: number;
    sp_ck_order?: number;
    sp_fk_order?: number;
    is_starter: boolean;
    is_captain: boolean;
    is_vice_captain: boolean;
    bench_order?: number | null;
  };
  isSelected?: boolean;
  onSelect?: (player: any) => void;
  onInspect?: (player: any) => void;
  onOpenMatchup?: (fixture: any) => void;
}
```

---

### Component 2: `LiveTeamSyncModal.jsx` (1-Click FPL API Sync)

#### Capabilities:
1. **Modal Trigger in `Header.jsx`**:
   - Prominent, machined button with `ArrowsClockwise` icon: `[Sync My Team]`.
2. **Entry ID & Mini-League Ingestion**:
   - Input field for official FPL Team ID (e.g., `9500404`).
   - Optional input field for Classic Mini-League ID.
3. **Client-Side Storage & API Dispatch**:
   - Persists the synced team ID and manager metadata to `localStorage`.
   - Dispatches fetch to `/api/sync?entry_id={id}&gw={gw}` or loads cached JSON profile.
   - Instantly updates global application state (`starters`, `bench`, `bank`, `free_transfers`, `active_chip`).

#### UI Layout & Wireframe:
```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 SYNC OFFICIAL FPL SQUAD & MINI-LEAGUE                    │
├─────────────────────────────────────────────────────────────┤
│ Enter your 7-digit FPL Entry ID:                            │
│ ┌──────────────────────────────────────────────┬──────────┐ │
│ │ 9500404                                      │ [Sync]   │ │
│ └──────────────────────────────────────────────┴──────────┘ │
│ Optional: Enter Classic Mini-League ID for Rival Analysis:  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 123456 (e.g. Work League / Friends Cup)                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ⚡ Synced Profile: Arabinda Saha (Fuljhore Giants)          │
│ • Bank: £0.0M | Team Value: £100.0M | Available FTs: 1     │
│ • Rank: #142,500 | Points: 65 pts                          │
└─────────────────────────────────────────────────────────────┘
```

---

### Component 3: `RivalThreatMatrix.jsx` (Mini-League Game Theory Matrix)

#### Capabilities:
1. **Top 5 Rival Standings Table**:
   - Ranks, manager names, team names, overall points, and Gameweek rank deltas.
2. **Player Overlap & Differential Analysis**:
   - **Differential Shields (Green)**: Players you own that rivals do not (Your rank climbing drivers).
   - **Rank Hazard Exposure (Red)**: High-EO template players owned by rivals but missing from your starting XI.
   - **Captaincy Threat Matrix**: Live swing delta scenarios comparing your captain vs rival captains.

---

### Component 4: `FixtureProbabilityDrawer.jsx` (Dixon-Coles Match Insights)

#### Capabilities:
1. **Interactive Fixture Selector**: Click any match on the pitch or heatmap to open detailed probabilities.
2. **Exact Dixon-Coles Probability Matrix**:
   - Normalized $(X, Y)$ joint scoreline probabilities with correlation parameter ($\rho = -0.05$).
   - Discrete Clean Sheet probabilities ($C_9$) for Home and Away.
   - Win/Draw/Away Win percentages, Both Teams to Score (BTTS), and Over/Under 2.5 goals.
3. **Simulated Match Events & BPS Leaderboard**:
   - Simulated top goalscorers, assisters, and projected True BPS bonus point distributions ($3, 2, 1$).

---

### Component 5: `MultiGwPlanner.jsx` (5-Gameweek Strategy Canvas)

#### Capabilities:
1. **5-Gameweek Matrix Layout**:
   - Columns for Gameweek deadlines (GW2, GW3, GW4, GW5, GW6) with FDR headers and free transfer counters.
   - Rows grouped by position (GK, DEF, MID, FWD).
2. **Interactive Transfer Modification**:
   - Ability to manually replace players or trigger the backend MILP Multi-Horizon optimizer.
   - Real-time floating KPI pill tracking:
     - Dynamic Bank (£M)
     - Cumulative Projected Horizon xP
     - Accumulated Free Transfers ($1\dots 5$)
     - Transfer Hits Penalty ($-4\text{ pts}$ each)

---

### Component 6: `PlayerDNAInspector.jsx` Enhancements

#### Capabilities:
1. **Continuous Minutes Hazard Curve Chart**:
   - Visual density plot of $f(t)$ for $t \in [0, 95]$ minutes.
   - Highlighted vertical threshold at Minute 60 (Appearance Point $C_2$ & Clean Sheet $C_9$ gate).
2. **Set-Piece Attribution Breakdown**:
   - Historical penalty conversion rate, corner delivery volume, and indirect free-kick target share.
3. **H2H & Tactical Archetype Multipliers**:
   - Display Head-to-Head opponent performance multiplier and tactical pace/low-block multipliers.

---

## 4. Frontend Data Schema Contracts

### 4.1 Extended `live_matchday_gw<GW>.json` Schema

```json
{
  "season": "2026-27",
  "gameweek": 2,
  "strategy": "rank_protect",
  "manager_profile": {
    "entry_id": 9500404,
    "manager_name": "Arabinda Saha",
    "team_name": "Fuljhore Giants",
    "overall_rank": 142500,
    "overall_points": 65,
    "bank": 0.0,
    "team_value": 100.0,
    "free_transfers": 1,
    "active_chip": null,
    "squad_codes": [154561, 466075, 198869, 201658, 466525, 177815, 424876, 223094, 141746, 446008, 223827, 80201, 173878, 539142, 230730],
    "starter_codes": [154561, 466075, 198869, 201658, 466525, 177815, 424876, 223094, 141746, 446008, 223827],
    "bench_codes": [80201, 173878, 539142, 230730],
    "captain_code": 223094,
    "vice_captain_code": 154561,
    "rivals": [
      {
        "entry_id": 1001,
        "manager_name": "Magnus Carlsen",
        "team_name": "Turing Test XI",
        "rank": 1,
        "total_points": 78,
        "captain_name": "Haaland",
        "differentials": ["Salah", "Isak"]
      }
    ]
  },
  "action_summary": "LOCKED GW2 INITIAL ENTRY SQUAD (Unlimited Transfers - Optimal 15-Man Draft)",
  "starting_xp": 58.41,
  "total_xp": 64.72,
  "captain": "Haaland",
  "vice_captain": "Raya",
  "starters": [
    {
      "player_code": 223094,
      "web_name": "Haaland",
      "team": "Man City",
      "position": "FWD",
      "cost": 15.5,
      "expected_points": 6.3129,
      "floor_p10": 2.1,
      "median_p50": 6.0,
      "ceiling_p90": 15.4,
      "haul_prob": 0.284,
      "p_start": 1.0,
      "p_mins_60": 0.94,
      "hook_hazard": 0.02,
      "rest_days": 7,
      "sp_pk_order": 1,
      "sp_ck_order": null,
      "sp_fk_order": null,
      "is_starter": true,
      "is_captain": true,
      "is_vice_captain": false,
      "bench_order": null
    }
  ],
  "bench": [],
  "multi_horizon_roadmap": [],
  "dixon_coles_fixtures": [
    {
      "fixture_id": 11,
      "home_team": "Aston Villa",
      "away_team": "Arsenal",
      "expected_home_goals": 1.38,
      "expected_away_goals": 1.06,
      "home_cs_prob": 0.345,
      "away_cs_prob": 0.252,
      "most_likely_scorelines": [
        {"score": "1-1", "prob": 0.128},
        {"score": "1-0", "prob": 0.114},
        {"score": "0-1", "prob": 0.098}
      ]
    }
  ]
}
```

---

## 5. Implementation Roadmap & Step-by-Step Task Breakdown

### Phase 1: Probability Range Bars & Set-Piece Badging in `PlayerCard.jsx`
- [ ] Add Floor ($p_{10}$), Median ($p_{50}$), and Ceiling ($p_{90}$) visual density range bar.
- [ ] Add `🔥 Haul XX%` pill for high-upside players.
- [ ] Add Set-Piece tags (`[PK1]`, `[CK1]`, `[FK1]`) and substitution hazard warnings.

### Phase 2: 1-Click FPL API Live Sync Modal & Header Integration
- [ ] Build `LiveTeamSyncModal.jsx` with FPL Entry ID and Mini-League ID inputs.
- [ ] Connect modal state to `Header.jsx` and synchronize with `localStorage`.
- [ ] Support instant dynamic reloading of starting XI, bench, bank, and chips.

### Phase 3: Mini-League Rival Threat Matrix (`RivalThreatMatrix.jsx`)
- [ ] Build dedicated Rival Threat Matrix component.
- [ ] Create Green Shield (Differential) and Red Flag (Rank Exposure) comparison widgets.
- [ ] Add Rival Threat tab to `Header.jsx` navigation.

### Phase 4: Dixon-Coles Matchup Probability Drawer (`FixtureProbabilityDrawer.jsx`)
- [ ] Implement slide-over drawer displaying exact Poisson joint scoreline matrices.
- [ ] Render discrete clean sheet odds, BTTS, and True BPS allocations per fixture.
- [ ] Attach click handlers from `TacticalPitch.jsx` and `FixtureHeatmap.jsx`.

### Phase 5: 5-Gameweek Interactive Strategy Canvas (`MultiGwPlanner.jsx`)
- [ ] Upgrade `TransferWorkbench.jsx` to interactive 5-GW canvas (`MultiGwPlanner.jsx`).
- [ ] Add dynamic Free Transfer counter ($1\dots 5$) and real-time hit penalty calculation.
- [ ] Add drag-and-drop / select substitution interface across lookahead weeks.

---

## 6. Verification & Quality Assurance Plan

1. **Vite Production Compilation**:
   - Execute `npm run build` in `frontend/` to ensure zero syntax, bundling, or chunk-splitting errors.
2. **Component Isolation & Accessibility Testing**:
   - Verify WCAG 2.4.1 Skip Links and keyboard tab order across all new modals and drawers.
   - Test color contrast ratios for dark mode obsidian surfaces ($\ge 4.5:1$ text contrast).
3. **Data Integrity & Fallback Verification**:
   - Verify that missing optional fields (`floor_p10`, `sp_pk_order`) fall back gracefully without rendering runtime errors.
   - Verify offline persistence and local storage cache handling.

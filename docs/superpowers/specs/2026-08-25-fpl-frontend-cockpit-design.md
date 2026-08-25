# Design Specification: FPL Quantitative Analytics Terminal (Frontend)

**Document Type:** Technical Architecture, Design System & Repeatable Elements Spec  
**Target Directory:** `frontend/`  
**Status:** IMPLEMENTED & RATIFIED  
**Date:** 2026-08-25  

---

## 0. Design Read & Anti-Slop Discipline

> **Design Read:** Institutional Quantitative Sports Terminal & Decision Cockpit for technical recruiters, engineering managers, and sports analytics professionals, with a high-density, editorial Bloomberg / StatsBomb-inspired visual language, powered by Vite + React + CSS Custom Properties + JetBrains Mono / Plus Jakarta Sans.

### The Three Dials:
- `DESIGN_VARIANCE: 6` — Disciplined, structured, data-first layout without chaotic novelty.
- `MOTION_INTENSITY: 4` — Restrained, instant 150ms state feedback, zero floating glowing orbs or jarring scroll-hijacking.
- `VISUAL_DENSITY: 8` — High information density, tactical pitch geometry, tabular monospace figures.

### Strict Anti-Slop Avoidance Rules:
- ❌ **NO capsule bubble pills (`border-radius: 9999px`) or floating circle badges** (Banned).
- ❌ **NO decorative consumer emojis (`⚡`, `⚠️`, `🎯`, `✨`) in metric labels** (Banned).
- ❌ **NO raw backend debug uppercase strings in UI strips** (Banned).
- ❌ **NO chaotic "pill clouds" for list comparisons** (Banned).
- ❌ **NO purple-and-black radial gradients or glowing floating orbs** (Banned).
- ❌ **NO generic 3-card marketing features, fake testimonials, or "$29/mo" pricing tiers** (Banned).
- ❌ **NO blurry, greasy "liquid glass" bubbles or soft corner radiuses** (Banned).
- ❌ **NO AI copy tropes** (*"It's not X, it's Y"* or overused em-dashes).
- ✅ **YES: Obsidian Slate (`#090D16`) & Deep Tactical Pitch (`#064030`)**.
- ✅ **YES: Tabular Numeral Monospace Typography** (`JetBrains Mono` / `Plus Jakarta Sans`).
- ✅ **YES: Concentric Squircles** (8px canvas ➔ 6px card ➔ 4px rail ➔ 3px chip).
- ✅ **YES: Structured Tabular Asset Ledgers** with precise differential deltas.
- ✅ **YES: Real-time dynamic state consumption** (`live_matchday_gw<GW>.json`).

---

## 1. The 5 Repeatable Element Rules (Design System Blueprint)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ REPEATABLE ELEMENT DESIGN SPECIFICATION                                                       │
├───────────────────┬──────────────────────────────┬────────────────────────────────────────────┤
│ Element Category  │ Anti-Pattern (To Avoid)      │ Best Practice Alternative (Institutional)  │
├───────────────────┼──────────────────────────────┼────────────────────────────────────────────┤
│ 1. Radius Scale   │ `border-radius: 9999px / 50%`│ Concentric Squircles (8px ➔ 6px ➔ 4px ➔ 3px)│
│ 2. Data Chips     │ Floating emoji bubble `⚡28%` │ Micro-Gauged Monospace Tag `HAUL 28%`      │
│ 3. Switchers/Tabs │ Rounded floating lozenges    │ Segmented Hardware Rail (Flush 4px radius) │
│ 4. Strategy Strip │ Clunky debug uppercase box   │ Integrated Machined Status Bar             │
│ 5. Differentials  │ Scattered "Pill Cloud"       │ Compact Tabular Asset Ledger               │
└───────────────────┴──────────────────────────────┴────────────────────────────────────────────┘
```

### Rule 1: Concentric Mathematical Radius Scale
All UI containers follow a concentric, nested mathematical hierarchy:
- **Outer Canvas / Panels**: `8px` (`--radius-lg`)
- **Player & KPI Cards**: `6px` (`--radius-md`)
- **Interactive Switchers / Inputs**: `4px` (`--radius-sm`)
- **Data Chips & Status Flags**: `3px` (`--radius-xs` with subtle inset highlights `inset 0 1px 0 rgba(255,255,255,0.06)`)

### Rule 2: Precision Data Chips & Badges
- **Position Tags**: Squircle tags (`[GK]`, `[DEF]`, `[MID]`, `[FWD]`) with $1\text{px}$ hairline borders and uppercase monospace typography.
- **Captaincy & Vice Badges**: Flush $18\text{px}$ square squircle tags (`[C]`, `[V]`) with inset top highlights.
- **Haul Potential**: Gauge micro-flags (`HAUL 28%`) with a $2\text{px}$ solid crimson left border.
- **Set-Piece Roles**: High-density monospace badges (`PK1`, `CK1`, `FK1`) with $1\text{px}$ borders.

### Rule 3: Segmented Hardware Switcher Rails
- Replace standalone floating buttons with unified segmented hardware tracks (`.segmented-chip-rail`):
  - Inactive segments are clean, flat monospace tabs.
  - Active segment is an elevated, tactile surface with subtle inset lighting and emerald contrast.

### Rule 4: Integrated Matchday Strategy Bars
- Strategy recommendations sit flush above the pitch container as an integrated hardware strip:
  - **Left**: `[MATCHDAY STRATEGY]` live status flag with green pulse dot.
  - **Center**: Executive human copy: `Optimal 15-man squad locked · 1 Free Transfer saved for GW3 · 0 hits taken` (or clean `[IN] ➔ [OUT]` pair).
  - **Right**: Horizon target projection indicator (`GW2 → GW4`).

### Rule 5: Structured Tabular Asset Ledgers
- Replace chaotic "pill clouds" with structured 2-column tabular rows (`.diff-ledger-row`):
  - Left: Position squircle + player name.
  - Right: Cost + exact differential point delta ($+5.8\text{ xP}$) or risk exposure level.

---

## 2. De-slopped FPL Fan Vocabulary Standard

| Robotic / Academic Term | De-slopped, Authentic FPL Vocabulary |
|---|---|
| "Algorithmic Lineup Optimizer" | **Matchday Starting XI** |
| "Multi-Horizon LP Transfer Engine" | **5-Week Transfer Planner** |
| "Bayesian Points Decomposition" | **Points Breakdown & DNA** |
| "Minimax Threat Exposure" | **Rival Radar & Danger Men** |
| "Dixon-Coles Poisson Match Modeler" | **Match Preview & Clean Sheet Odds** |
| "Net Asset Market Momentum" | **Price Riser / Faller Tracker** |
| "Rolling Invariant Decision" | **Roll Free Transfer (Bank FT)** |

---

## 3. System Architecture & Component Hierarchy

```
frontend/
├── src/
│   ├── assets/                      # Static assets & SVG club badges
│   ├── components/                  # Reusable UI primitives
│   │   ├── Header.jsx               # Top navigation & Gameweek metadata
│   │   ├── TacticalPitch.jsx        # 2D pitch with player cards, segmented chip rail & strategy bar
│   │   ├── PlayerCard.jsx           # Card with squircle position tags, [C] badges, haul flags & stats button
│   │   ├── OrderedBench.jsx         # Auto-sub priority bench slots 1-4
│   │   ├── MultiGwPlanner.jsx       # 5-GW interactive roadmap with transfer ledger
│   │   ├── RivalThreatMatrix.jsx    # Mini-league rank radar & structured differential ledgers
│   │   ├── FixtureProbabilityDrawer # Dixon-Coles Poisson match matrix & scoreline odds
│   │   ├── LiveTeamSyncModal.jsx    # 1-Click FPL ID & Mini-League ingestion modal
│   │   ├── PlayerDNAInspector.jsx   # 11-Component point ledger & underlying stats modal
│   │   ├── ComponentStudio.jsx      # Bayesian parameters studio & baseline tables
│   │   ├── FixtureHeatmap.jsx       # 38-GW FDR schedule matrix
│   │   └── MarketVelocityTicker.jsx # Net transfer velocity & price rise/fall alerts
│   ├── data/                        # Live JSON matchday & player payloads
│   │   ├── live_matchday_gw2.json   # Enriched GW2 matchday state
│   │   └── players_full.json        # Master player database with 40+ granular stats
│   ├── styles/
│   │   └── index.css                # Design system tokens, variables & pitch geometry
│   ├── App.jsx                      # Root container & tab routing
│   └── main.jsx                     # Vite entry point
├── package.json
└── vite.config.js
```

---

## 4. Verification & Testing Plan

1. **Build Verification**: Run `npm run build` to ensure zero compilation or bundle errors (Target: $<1000\text{ms}$).
2. **Data Integration Test**: Verify dynamic ingestion and rendering of `live_matchday_gw2.json` and master database `players_full.json`.
3. **Interactive Sub Test**: Verify swapping starters and bench players updates formation and starting XI $xP$ dynamically.
4. **Points Breakdown Test**: Verify single-click `[Stats]` button reliably opens the 11-component point ledger with zero blank container issues.
5. **Responsive Layout Check**: Verify layout integrity across desktop (1400px), tablet (1024px), and mobile (375px) without horizontal overflow.

# Design Specification: FPL Quantitative Analytics Terminal (Frontend)

**Document Type:** Technical Architecture & Implementation Spec  
**Target Directory:** `frontend/`  
**Status:** PROPOSED & READY FOR IMPLEMENTATION  
**Date:** 2026-08-25  

---

## 0. Design Read & Anti-Slop Discipline

> **Design Read:** Institutional Quantitative Sports Terminal & Decision Cockpit for technical recruiters, engineering managers, and sports analytics professionals, with a high-density, editorial Bloomberg / StatsBomb-inspired visual language, leaning toward Vite + React + CSS Custom Properties + JetBrains Mono / Plus Jakarta Sans.

### The Three Dials:
- `DESIGN_VARIANCE: 6` — Disciplined, structured, data-first layout without chaotic novelty.
- `MOTION_INTENSITY: 4` — Restrained, instant 150ms state feedback, zero floating glowing orbs or jarring scroll-hijacking.
- `VISUAL_DENSITY: 8` — High information density, tactical pitch geometry, tabular monospace figures.

### Strict Anti-Slop Avoidance Rules:
- ❌ **NO purple-and-black radial gradients or glowing floating orbs** (Banned).
- ❌ **NO generic Lucide sparkle icons or emojis as UI decoration** (Banned).
- ❌ **NO generic 3-card marketing features, fake testimonials, or "$29/mo" pricing tiers** (Banned).
- ❌ **NO blurry, greasy "liquid glass" bubbles or soft corner radiuses** (Banned).
- ❌ **NO AI copy tropes** (*"It's not X, it's Y"* or overused em-dashes).
- ✅ **YES: Obsidian Slate (`#0B0F17`) & Deep Turf Surface (`#111827`)**.
- ✅ **YES: Tabular Numeral Typography** (`JetBrains Mono` / `Plus Jakarta Sans`).
- ✅ **YES: Precise 1px contrast geometry with crisp 4px–6px radii**.
- ✅ **YES: Real-time dynamic state consumption** (`fpl_matchday_live_gw<GW>.json`).

---

## 1. System Architecture & Component Hierarchy

```
frontend/
├── src/
│   ├── assets/                      # Static assets & SVG club badges
│   ├── components/                  # Reusable UI primitives
│   │   ├── Header.jsx               # Top navigation & Gameweek metadata
│   │   ├── TacticalPitch.jsx        # 2D Glassmorphic football pitch with player cards
│   │   ├── PlayerCard.jsx           # Individual player card with xP, [C], FDR badges
│   │   ├── OrderedBench.jsx         # Auto-sub priority bench slots 1-4
│   │   ├── TransferWorkbench.jsx    # 3-5 GW lookahead transfer planner
│   │   ├── FixtureHeatmap.jsx       # 38-GW FDR matrix for all 20 clubs
│   │   ├── PlayerDNAInspector.jsx   # 11-Component stacked point deconstruction
│   │   ├── MarketVelocityTicker.jsx # Net transfer velocity & price rise/fall alerts
│   │   └── SkeletonLoader.jsx       # Zero-CLS layout shimmers
│   ├── data/                        # Sample & live JSON payloads
│   │   └── live_gw_data.json        # Synced state from data/2026-27/
│   ├── styles/
│   │   └── index.css                # Design system tokens, variables & pitch geometry
│   ├── App.jsx                      # Root container & tab routing
│   └── main.jsx                     # Vite entry point
├── package.json
└── vite.config.js
```

---

## 2. Design System Tokens & Color Calibration

```css
:root {
  /* Surface Layers */
  --bg-base: #0B0F17;        /* Obsidian Deep Slate */
  --bg-surface: #111827;     /* Elevated Card Surface */
  --bg-surface-subtle: #1F2937;
  --bg-pitch: #064E3B;       /* Deep Tactical Green */
  --bg-pitch-stripes: #04382A;

  /* Borders & Grid */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-active: rgba(16, 185, 129, 0.4);
  --border-radius-sm: 4px;
  --border-radius-md: 6px;

  /* Data Ink Accents */
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  
  /* Semantic Status Colors */
  --color-emerald: #10B981;   /* Starting XI & Positive Velocity */
  --color-amber: #F59E0B;     /* Captain [C] & Strategic Alerts */
  --color-crimson: #EF4444;   /* Tough FDR & Price Fall Alert */
  --color-blue: #3B82F6;      /* Defenders & Goalkeepers */
  
  /* Typography */
  --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'IBM Plex Mono', monospace;
}
```

---

## 3. The 5 Core Application Views

### View 1: 🏟️ Tactical Pitch & Lineup Visualizer
- **Formation Rendering**: Dynamic spatial layout based on optimal formation (3-4-3, 3-5-2, 4-4-2, 4-3-3).
- **Player Nodes**: Shows player name, position tag, club, cost (£M), expected points ($xP$), FDR difficulty badge, and captaincy badges (`[C]`, `[V]`).
- **Interactive Substitutions**: Click any starter to highlight valid bench swap targets with real-time recalculation of total projected $xP$.
- **Ordered Bench**: Fixed slots 1 (GK), 2 (Sub 1), 3 (Sub 2), 4 (Sub 3).

### View 2: 🔄 Multi-Horizon Transfer Planner & Strategy Workbench
- **Lookahead Timeline**: 3 to 5 gameweek horizontal horizon cards showing planned transfers, bank trajectory, and hit penalties.
- **Searchable Player Marketplace**: Fast client-side filtering by name, position, club, and max price slider, sortable by $xP$, value per million, and form.
- **Strategy Selector**: Toggle between `Pure xP` (neutral), `Rank Protect` (hedging high-EO talismans), and `Differential Chase` (low-EO high-upside picks).

### View 3: 🗺️ 38-Gameweek Fixture Difficulty Heatmap
- **Full 20-Team Matrix**: Visualizes all 38 fixture rounds with official FDR color-coding (1–5).
- **Sortable Filters**: Sort teams by easiest attacking runs (next 3/5/8 GWs) vs cleanest defensive schedules.

### View 4: 🔬 11-Component Player Deconstruction Studio
- **DNA Inspector Modal**: Click any player card to view their mathematical decomposition:
  - Stacked breakdown: $C_1–C_2$ (Mins), $C_3$ (Saves), $C_6$ (Bonus), $C_7$ (Assists), $C_8$ (Goals), $C_9$ (Clean Sheet), $C_{10}$ (Conceded Penalty), $C_{11}$ (Defensive Contribution).
  - Empirical Bayes shrinkage indicator comparing raw per-90 vs shrunken expectation.

### View 5: ⚡ Market Momentum & Price Velocity Tracker
- **Velocity Radar**: Daily net transfer velocity ($\Delta T$) metrics.
- **Price Movement Flags**: `RISING_LOCK`, `RISING_ALERT`, `STABLE`, `FALLING_ALERT`, `FALLING_LOCK`.
- **Seasonal Chip Timeline**: Recommended deployment windows for Triple Captain, Bench Boost, Free Hit, and Wildcards.

---

## 4. Verification & Testing Plan

1. **Build Verification**: Run `npm run build` to ensure zero compilation or bundle errors.
2. **Data Integration Test**: Verify dynamic ingestion and rendering of `data/2026-27/fpl_matchday_live_gw2.json`.
3. **Interactive Sub Test**: Verify swapping starters and bench players updates formation and starting XI $xP$ dynamically.
4. **Responsive Layout Check**: Verify layout integrity across desktop (1400px), tablet (1024px), and mobile (375px).

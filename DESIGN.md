# DESIGN.md — FPL Quantitative Analytics Terminal

This document is the permanent single source of truth for the visual design system, frontend architecture, component interfaces, and repeatable UI frameworks of the **FPL Quantitative Analytics Terminal**.

---

## 1. Design Philosophy & Register

### 1.1 The Register: Institutional Quantitative Sports Terminal
This interface is modeled after **institutional financial engineering and elite sports scouting tools** (*StatsBomb IQ*, *OptaPro*, *Bloomberg Terminal*), **not a B2B SaaS marketing site**. 

- **Primary User Audience**: Technical recruiters, quant researchers, data scientists, and competitive top-0.1% FPL managers.
- **Tone**: High data density, mathematical rigor, calm authority, zero marketing fluff.
- **Execution Style**: Dark obsidian slate canvas, precision 1px borders, tabular monospace data figures, realistic pitch geometry.

### 1.2 The Three Dials
- **`DESIGN_VARIANCE: 6`** — Structured, systematic, data-first grid alignment without chaotic novelty.
- **`MOTION_INTENSITY: 4`** — Restrained, instant 150ms state feedback; zero floating glowing orbs or scroll-hijacking.
- **`VISUAL_DENSITY: 8`** — High information density, compact tabular layouts, zero wasteful whitespace.

---

## 2. Anti-Slop Manifesto & Absolute Bans

Per the repository's strict anti-slop guidelines, the following elements are **permanently banned** from the codebase:

| Banned AI-Slop Pattern | Reason for Ban | Institutional Replacement |
|---|---|---|
| ❌ **Capsule Bubble Pills (`border-radius: 9999px`)** | Generic consumer bubble template trope | Concentric Squircles (`3px` to `8px`) with 1px hairline borders. |
| ❌ **Floating Circular Badges (`50%` circles)** | Disconnected floating elements | Flush square squircle tags (`[C]`, `[V]`) with top inset highlights. |
| ❌ **Decorative Emojis (`⚡`, `⚠️`, `🎯`, `✨`)** | Childish gimmicks undermining technical credibility | Precise Phosphor SVG icons and typographic tags (`HAUL 28%`, `[PK1]`). |
| ❌ **Raw Debug Uppercase Text in Strips** | Unfinished backend console log appearance | Executive, human strategy copy with status indicator tags. |
| ❌ **Chaotic "Pill Clouds" for Comparisons** | Disorganized, unaligned visual noise | Structured 2-column tabular asset ledgers with delta numbers. |
| ❌ **Purple/Black with Radial Glowing Orbs** | Generic "AI wrapper" template trope | Deep Slate (`#090D16`) & Elevated Navy (`#111726`) with 1px border contrast. |
| ❌ **Multi-Hue Decorative Gradients** | Saturated AI decorative fill trope | Solid token accents (`var(--accent-emerald)`, `var(--accent-amber)`, `var(--accent-crimson)`). |
| ❌ **Fake Testimonials & $29/mo Pricing Tiers** | Clueless marketing clutter | Pure functional workspace consuming live JSON payloads. |
| ❌ **Hardcoded Hex Colors in Components** | Bypasses design token hierarchy | Strict CSS custom property references (`var(--text-inverse)`, `var(--text-primary)`). |
| ❌ **"It's not X, it's Y" Copy Tropes** | Cliche AI copywriting | Direct, factual status labels and clear action summaries. |
| ❌ **Insanely Rounded Radii (>16px on cards)** | Codex-style over-rounding | Crisp geometric radii (`3px` to `8px`). |

---

## 3. The 5 Repeatable Element Rules (Design System Blueprint)

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
- **Outer Canvas / Bento Panels**: `8px` (`--radius-lg`)
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

## 4. De-slopped FPL Fan Vocabulary Standard

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

## 5. Design System Tokens (CSS Custom Properties)

```css
:root {
  /* Surface Layers (Obsidian Slate Theme) */
  --bg-canvas: #090D16;            /* Deep background */
  --bg-surface-1: #111726;         /* Elevated panel surface */
  --bg-surface-2: #182035;         /* Card / Table header surface */
  --bg-surface-subtle: #1E293B;    /* Hover / Active fill */
  --bg-pitch-base: #064030;        /* Tactical pitch green */
  --bg-pitch-stripe: #053326;      /* Alternating grass stripe */

  /* Text & Ink Hierarchy (All meet WCAG AA contrast >= 4.5:1) */
  --text-primary: #F8FAFC;         /* High-contrast titles & values */
  --text-secondary: #94A3B8;       /* Body labels & metrics */
  --text-muted: #8494A7;           /* Subtext & unit markers (4.8:1 contrast) */
  --text-inverse: #090D16;         /* Inverse dark text on emerald badges */

  /* Semantic Data Accents */
  --accent-emerald: #10B981;       /* Starting XI & Positive Net Velocity */
  --accent-emerald-subtle: rgba(16, 185, 129, 0.15);
  --accent-amber: #F59E0B;         /* Captaincy [C] & Moderate Warnings */
  --accent-amber-subtle: rgba(245, 158, 11, 0.15);
  --accent-crimson: #EF4444;       /* High Outflow & Price Fall Alerts */
  --accent-crimson-subtle: rgba(239, 68, 68, 0.15);
  --accent-cyan: #06B6D4;          /* Assist Threat / Cyan metric */
  --accent-blue: #3B82F6;          /* Defensive and GK Position Accents */

  /* Positional Roles */
  --pos-gk: #F59E0B;
  --pos-def: #3B82F6;
  --pos-mid: #10B981;
  --pos-fwd: #EF4444;

  /* Official FDR (Fixture Difficulty Rating 1-5) */
  --fdr-1: rgba(5, 150, 105, 0.25);   /* Very Easy (Green) */
  --fdr-2: rgba(16, 185, 129, 0.25);  /* Easy (Light Green) */
  --fdr-3: rgba(100, 116, 139, 0.25); /* Neutral (Slate Gray) */
  --fdr-4: rgba(245, 158, 11, 0.25);  /* Tough (Amber) */
  --fdr-5: rgba(220, 38, 38, 0.30);   /* Hard (Deep Crimson) */

  /* 1px Precision Borders */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-medium: rgba(255, 255, 255, 0.15);
  --border-active: rgba(16, 185, 129, 0.50);

  /* Geometry Radii (Concentric Squircles) */
  --radius-xs: 3px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;

  /* Typography */
  --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'IBM Plex Mono', monospace;
}
```

---

## 6. Mobile Responsive Architecture

To maintain high visual density and institutional elegance on small screens:

1. **Fluid App Container**: Max-width capped at `1600px` with fluid clamp padding (`clamp(16px, 2.5vw, 32px)`), scaling cleanly down to mobile viewports.
2. **2-Tier Mobile Header (`≤768px`)**:
   - **Tier 1**: Brand identity left, active Gameweek badge right.
   - **Tier 2**: Full-width segmented tab strip with horizontal snap and touch targets $\ge 40\text{px}$.
3. **Single-Line Institutional Footer**: Copyright on left, icon-only GitHub button on right across all screen widths.
4. **Responsive Table Strategy**:
   - All tabular grids wrapped in `.table-scroll-wrapper` with sticky left columns.
   - Fixture Heatmap automatically collapses team names to 3-letter acronyms (`BHA`, `MCI`, `ARS`) on screens $\le 480\text{px}$.
5. **Touch-Target Sizing**: Enforced via `@media (pointer: coarse)` ensuring all buttons, filters, and player cards meet $\ge 38\text{px}-42\text{px}$ minimum tap areas.

---

## 7. Codebase Architecture: Deep Module System

Applying the **Deep Module Principles** (*large amount of internal capability hidden behind a small, testable interface at a clean seam*):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               DEEP MODULE COMPONENT MAP                                │
├──────────────────────────┬──────────────────────────────┬──────────────────────────────┤
│ Deep Module              │ Minimal Public Interface     │ Encapsulated Logic           │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `TacticalPitch`          │ `starters`, `bench`,         │ • Dynamic formation parser   │
│                          │ `onSelectPlayer`,            │ • Spatial 2D row grouping    │
│                          │ `onInspectPlayer`,           │ • Field line CSS geometry    │
│                          │ `startingXp`, `totalXp`      │ • Bench swap validity        │
│                          │                              │ • Segmented chip switcher    │
│                          │                              │ • Integrated strategy bar    │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `MultiGwPlanner`         │ `roadmap`, `allPlayers`,     │ • 5-GW Transfer roadmap      │
│                          │ `onInspectPlayer`            │ • Multi-gameweek chip solver │
│                          │                              │ • Transfer transaction ledger│
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `RivalThreatMatrix`      │ `rivals`, `onInspectPlayer`  │ • Mini-league rank radar     │
│                          │                              │ • Tabular differential ledger│
│                          │                              │ • Danger men risk exposure   │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `FixtureHeatmap`         │ `fixtures`, `teams`          │ • 38-GW 20-team matrix map   │
│                          │                              │ • Home/Away FDR mapper       │
│                          │                              │ • Rolling average score      │
│                          │                              │ • Mobile short name switcher │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `PlayerDNAInspector`     │ `player`, `onClose`          │ • 11-Component decomposition │
│                          │                              │ • Fail-safe Point Ledger     │
│                          │                              │ • Underlying match metrics   │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `FixtureProbabilityDrawer│ `fixtureDetails`, `onClose`  │ • Dixon-Coles Poisson matrix │
│                          │                              │ • Joint scoreline odds       │
│                          │                              │ • Clean sheet percentages    │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `ComponentStudio`        │ `players`,                   │ • Bayesian shrinkage sandbox │
│                          │ `onInspectPlayer`            │ • Dynamic parameter sliders  │
│                          │                              │ • Multi-page paginated table │
└──────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

---

## 8. Interaction & Motion Rules

1. **State Feedback**: Interactive elements (player cards, table rows, tab buttons) use `transition: all 0.15s ease`.
2. **Tactile Push**: Active buttons and cards simulate an instant mechanical push with `transform: translateY(-2px)` on hover and `scale(0.98)` on click.
3. **Accessibility**: Full `@media (prefers-reduced-motion: reduce)` support:
   ```css
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
     }
   }
   ```
4. **Zero Layout Shifts (CLS)**: Dynamic data loading utilizes CSS shimmer skeleton loaders matching final layout shapes.

---

## 9. Pre-Flight Design Audit Checklist

Before releasing any new frontend view or feature:
- [ ] **Concentric Radius Scale**: All elements follow `8px` $\rightarrow$ `6px` $\rightarrow$ `4px` $\rightarrow$ `3px`. Zero $9999\text{px}$ bubble pills.
- [ ] **Data Tags**: Position tags, captaincy, haul probability, and set pieces use squircle monospace micro-flags.
- [ ] **Contrast Check**: All body text $\ge 4.5:1$, large labels $\ge 3:1$.
- [ ] **Typography**: All tabular numerical columns use `font-mono` (`JetBrains Mono`) with `font-feature-settings: "tnum" 1`.
- [ ] **No AI Slop Check**: Zero decorative multi-hue gradients, zero emojis in technical headers, zero hardcoded colors.
- [ ] **Keyboard Accessibility**: All clickable rows and cards have `tabIndex={0}`, `role="button"`, and `onKeyDown`.
- [ ] **Deep Module Seam**: Component props are minimal; complexity is encapsulated internally.
- [ ] **Responsive Breakpoints**: Layout renders without horizontal overflow across Desktop (1600px), Tablet (768px), and Mobile (375px).
- [ ] **Build Check**: `npm run build` compiles with 0 errors.

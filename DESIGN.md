---
name: FPL-Quantitative-Analytics-Terminal
version: alpha
description: Institutional sports analytics and decision cockpit for Fantasy Premier League management.
colors:
  primary: "#10B981"
  on-primary: "#090D16"
  secondary: "#94A3B8"
  background: "#090D16"
  surface-1: "#111726"
  surface-2: "#182035"
  surface-subtle: "#1E293B"
  text-primary: "#F8FAFC"
  text-secondary: "#94A3B8"
  text-muted: "#8494A7"
  text-inverse: "#090D16"
  accent-amber: "#F59E0B"
  accent-crimson: "#EF4444"
  accent-cyan: "#06B6D4"
  accent-blue: "#3B82F6"
  pos-gk: "#F59E0B"
  pos-def: "#3B82F6"
  pos-mid: "#10B981"
  pos-fwd: "#EF4444"
  pitch-base: "#064030"
  pitch-stripe: "#053326"
  border-subtle: "rgba(255, 255, 255, 0.08)"
  border-medium: "rgba(255, 255, 255, 0.15)"
  border-active: "rgba(16, 185, 129, 0.50)"
typography:
  display:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.75rem
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: -0.02em
  h1:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.5rem
    fontWeight: 800
    lineHeight: 1.2
  h2:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.125rem
    fontWeight: 700
    lineHeight: 1.3
  h3:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.875rem
    fontWeight: 700
    lineHeight: 1.4
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.8125rem
    fontWeight: 500
    lineHeight: 1.5
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.75rem
    fontWeight: 500
    lineHeight: 1.4
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: 700
    letterSpacing: -0.01em
    fontFeature: "'tnum' 1"
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 0.5625rem
    fontWeight: 800
    letterSpacing: 0.05em
rounded:
  xs: 3px
  sm: 4px
  md: 6px
  lg: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px
components:
  card-player:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 10px
  card-bench:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 12px
  panel-elevated:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: 18px
  button-chip:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.sm}"
    padding: 6px 10px
  badge-tag:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: 2px 5px
  badge-captain:
    backgroundColor: "{colors.accent-amber}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: 2px 4px
  badge-hazard:
    backgroundColor: "{colors.accent-crimson}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: 2px 4px
  badge-assist:
    backgroundColor: "{colors.accent-cyan}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: 2px 4px
  badge-def:
    backgroundColor: "{colors.accent-blue}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: 2px 4px
  tag-pos-gk:
    backgroundColor: "{colors.pos-gk}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: 1px 4px
  tag-pos-def:
    backgroundColor: "{colors.pos-def}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: 1px 4px
  tag-pos-mid:
    backgroundColor: "{colors.pos-mid}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: 1px 4px
  tag-pos-fwd:
    backgroundColor: "{colors.pos-fwd}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: 1px 4px
  pitch-surface:
    backgroundColor: "{colors.pitch-base}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.lg}"
    padding: 20px
  pitch-lines:
    backgroundColor: "{colors.pitch-stripe}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.xs}"
    padding: 0px
  border-hairline:
    backgroundColor: "{colors.border-subtle}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.xs}"
    padding: 1px
  border-interactive:
    backgroundColor: "{colors.border-medium}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: 1px
  border-selected:
    backgroundColor: "{colors.border-active}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.xs}"
    padding: 1px
---

## Overview

Architectural Rigor meets Quantitative Sports Scouting. The interface is modeled after institutional financial engineering and elite sports analytics terminals (*StatsBomb IQ*, *OptaPro*, *Bloomberg Terminal*), built specifically for competitive top-0.1% Fantasy Premier League managers and quantitative researchers.

The system is configured under the **Operate** mode:
- **`DESIGN_VARIANCE: 6`** — Structured, systematic, data-first grid alignment.
- **`MOTION_INTENSITY: 4`** — Instant 150ms state feedback; zero floating glowing orbs or scroll-hijacking.
- **`VISUAL_DENSITY: 8`** — High information density with compact tabular figures and strict alignment.

---

## Colors

The palette is rooted in deep obsidian slate foundations with 1px hairline border contrast and singular semantic role accents.

### Palette Definitions
- **Background (`#090D16`):** Deep canvas foundation for optimal eye comfort during long analytical sessions.
- **Surface Level 1 (`#111726`):** Elevated panel and container layer.
- **Surface Level 2 (`#182035`):** Interactive card and table row layer.
- **Surface Subtle (`#1E293B`):** Hover, selection, and interactive rail fill.
- **Primary Emerald (`#10B981`):** Core interactive accent, active projections, and positive market momentum.
- **Captaincy Amber (`#F59E0B`):** Captaincy indicators (`[C]`), GK positions, and warning thresholds.
- **Hazard Crimson (`#EF4444`):** Outflow velocity, high risk, and forward positions (`[FWD]`).
- **Defensive Blue (`#3B82F6`):** Defensive position accents (`[DEF]`) and clean sheet probability.
- **Assist Cyan (`#06B6D4`):** Expected assists (`xA`) and creative telemetry.

### Contrast Standards
All typography tokens strictly satisfy WCAG AA contrast ratios:
- `text-primary` (`#F8FAFC`) on `surface-2` (`#182035`): **14.2:1** (Passes AAA)
- `text-secondary` (`#94A3B8`) on `surface-1` (`#111726`): **6.8:1** (Passes AA)
- `text-muted` (`#8494A7`) on `surface-1` (`#111726`): **4.8:1** (Passes AA)

---

## Typography

Typography is clean, highly legible, and optimized for dense numerical evaluation.

### Font Families
- **Sans-Serif (`Plus Jakarta Sans`):** Clean, modern geometric grotesk for UI headers, buttons, and navigation.
- **Monospace (`JetBrains Mono` / `IBM Plex Mono`):** Tabular figures with `font-feature-settings: "tnum" 1` for all statistical metrics, prices, minutes, and probability percentages.

### Typographic Hierarchy Scale
1. **Display Titles ($24\text{px} - 28\text{px}$):** Bold page branding and active target readouts.
2. **Section Headers H2 ($18\text{px}$):** Modal titles and primary dashboard section headers.
3. **Card Headers H3 ($14\text{px}$):** Component sub-headers and table titles.
4. **Body Text ($12\text{px} - 13\text{px}$):** Player names, managerial directives, and table data.
5. **Metadata & Units ($10\text{px} - 11\text{px}$):** Team tags, cost readouts, and metric unit labels.
6. **Micro Tags ($8.5\text{px} - 9.5\text{px}$):** Positional squircle tags (`[MID]`), captain badges (`[C]`), and set-piece order tags (`PK1`).

---

## Layout

All layouts follow a strict 4px/8px base spatial grid to ensure consistent visual rhythm and zero layout drift.

### Spatial Scale
- **`xs (4px)`**: Tight internal element spacing (e.g. icon-to-text gap, badge padding).
- **`sm (8px)`**: Standard component gap (e.g. card elements, button group gaps).
- **`md (12px)`**: Grid gaps within panels (e.g. positional baselines grid, metrics rows).
- **`lg (16px)`**: Panel internal padding and section margins.
- **`xl (20px)`**: Bento grid gutter and major card margins.
- **`2xl (24px)`**: Outer workspace container padding and modal margins.

### Spatial Relativity & Nesting Math
- Parent container padding is always greater than child container padding:
  $$\text{Panel Padding } (16\text{px}-18\text{px}) > \text{Card Padding } (10\text{px}-12\text{px}) > \text{Badge Padding } (2\text{px}-4\text{px})$$
- Maximum workspace width is capped at `1600px` with fluid margin auto-centering.

### Matchday 2-Column Grid Architecture
Desktop Matchday Starting XI operates as a fixed 2-column split:
- **Left Column (`1fr`)**: Tactical football pitch surface (`.pitch-container`) with centered starter rows (GK $\to$ DEF $\to$ MID $\to$ FWD) and geometric line markings.
- **Right Column (`340px`)**: Substitutes Sidebar (`.pitch-sidebar`) with 4 vertical bench slots (`.bench-item`) and interactive swap feedback.

---

## Elevation & Depth

Surfaces are solid, opaque, and physical. Translucent "dark glass" or blurred fake layers are strictly banned.

### Surface Hierarchy
```
Level 0: Canvas Background      (--bg-canvas: #090D16)
  └── Level 1: Elevated Panels  (--bg-surface-1: #111726)  + 1px border-subtle
        └── Level 2: Cards      (--bg-surface-2: #182035)  + 1px border-subtle + inset highlight
              └── Level 3: Active (--bg-surface-subtle: #1E293B) + border-medium
```

### Inset Edge Lighting
Elevation is achieved via physical 1px hairline borders and inset highlights:
- Cards use: `border: 1px solid var(--border-subtle)` + `box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.35)`.
- Active/selected items illuminate with `border-color: var(--accent-emerald)` and `box-shadow: 0 0 12px rgba(16, 185, 129, 0.3)`.

---

## Shapes

Shapes utilize a concentric mathematical squircle scale. Arbitrary bubble pills (`9999px`) and unpadded 0px sharp boxes are avoided.

### Concentric Squircle Radius Hierarchy
- **Outer Bento Panels & Modals:** `8px` (`--radius-lg`)
- **Player & Telemetry Cards:** `6px` (`--radius-md`)
- **Interactive Switchers & Inputs:** `4px` (`--radius-sm`)
- **Data Chips, Status Tags & Role Badges:** `3px` (`--radius-xs`)

Concentric radius formula:
$$R_{\text{child}} = R_{\text{parent}} - \text{Padding}$$

---

## Components

Every interactive element follows a strict state machine (Default $\to$ Hover $\to$ Active $\to$ Focus $\to$ Disabled).

### 1. Minimalist Player Pitch Card (`.player-pitch-card`)
- **Surface**: Solid `#182035` with `6px` radius and 1px hairline border.
- **Top Row**: Concentric Squircle Badge (`[C]`, `[V]`, or `3XC`) + Position Tag (`[MID]`) + Cost (`£6.0m`).
- **Middle**: Bold high-contrast player name (`font-weight: 800`).
- **Matchup**: Clickable club and opponent link (`Bournemouth · vs EVE`) opening the Match Preview Drawer.
- **Points Banner**: Centered monospace expected score (`5.4 xP` or `18.9 3xP`).
- **Interaction**: Single or double click triggers the comprehensive Player DNA Inspector modal.

### 2. Substitutes Sidebar Panel (`.sidebar-panel`)
- **Container**: Solid `#111726` with `8px` radius.
- **Bench Item**: 4 vertical slots (`[GK Sub]`, `[Sub 1]`, `[Sub 2]`, `[Sub 3]`) on solid `#182035` with `6px` radius.
- **Bench Boost State**: When active, items illuminate with emerald border and display `ACTIVE` badge.

### 3. Positional Baselines Telemetry Grid (`.studio-baselines-panel`)
- **Container**: Solid `#111726` panel with `8px` radius and explanatory subtitle.
- **4-Card Grid**: 4 equal columns on desktop (`[GK]`, `[DEF]`, `[MID]`, `[FWD]`) on `#182035`.
- **Metrics**: Tabular monospace numbers with units (`xG`, `xA`, `Clean Sheet %`, `BPS`).

### 4. Segmented Hardware Switcher Rail (`.segmented-chip-rail`)
- Integrated track with flush `4px` radius.
- Inactive tabs: Flat monospace labels with icon.
- Active tab: Elevated `#1E293B` surface with emerald highlight and inset shadow.

### 5. Dixon-Coles 5×5 Scoreline Matrix (`.scoreline-matrix-table`)
- Bivariate Poisson grid with cell intensity heatmap shading.
- Neutral cell tinting: Blue tint for Home Win, Emerald for Away Win, Amber for Draw.
- Interactive hover cell displaying exact joint outcome probabilities.

---

## Do's and Don'ts

### Absolute Bans (Anti-Slop Directives)
| Anti-Pattern (To Avoid) | Institutional Requirement |
|---|---|
| ❌ Translucent "Dark Glass" or `backdrop-filter: blur()` | ✅ Solid, opaque tokenized surfaces (`#090D16`, `#111726`, `#182035`). |
| ❌ Capsule bubble pills (`border-radius: 9999px`) on cards | ✅ Concentric Squircles (`3px` to `8px`). |
| ❌ Floating circular 50% badges | ✅ Flush square squircle tags (`[C]`, `[V]`, `3XC`). |
| ❌ Decorative emojis (`⚡`, `🚀`, `🎯`, `✨`) in headers | ✅ Precise Phosphor SVG icons and typographic tags (`HAUL 28%`). |
| ❌ Multi-hue gradient decorative fills | ✅ Solid token accents (`var(--accent-emerald)`, `var(--accent-amber)`). |
| ❌ Raw unstyled HTML or missing CSS classes | ✅ 100% tokenized CSS rules in `index.css` matching `DESIGN.md`. |
| ❌ Proportional fonts for numerical statistics | ✅ Fixed-width tabular monospace typography (`JetBrains Mono`). |
| ❌ Hardcoded ad-hoc hex colors in components | ✅ Strict CSS custom property references (`var(--text-primary)`, `var(--bg-surface-2)`). |

### De-slopped FPL Fan Vocabulary Standard
| Robotic / Academic Slop | De-slopped, Authentic FPL Vocabulary |
|---|---|
| "Algorithmic Lineup Optimizer" | **Matchday Starting XI** |
| "Multi-Horizon LP Transfer Engine" | **5-Week Transfer Planner** |
| "Bayesian Points Decomposition" | **Points Breakdown & DNA** |
| "Minimax Threat Exposure" | **Rival Radar & Danger Men** |
| "Dixon-Coles Poisson Match Modeler" | **Match Preview & Clean Sheet Odds** |
| "Net Asset Market Momentum" | **Price Riser / Faller Tracker** |
| "Rolling Invariant Decision" | **Roll Free Transfer (Bank FT)** |

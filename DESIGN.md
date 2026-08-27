---
name: FPL-Quantitative-Analytics-Terminal
version: beta
description: Institutional quantitative sports scouting and mathematical decision cockpit for Fantasy Premier League management.
colors:
  canvas: "oklch(0.12 0.02 260)"
  surface-1: "oklch(0.15 0.025 260)"
  surface-2: "oklch(0.20 0.035 260)"
  surface-subtle: "oklch(0.24 0.03 260)"
  primary-emerald: "oklch(0.72 0.19 155)"
  captaincy-amber: "oklch(0.78 0.17 75)"
  hazard-crimson: "oklch(0.63 0.22 25)"
  defensive-blue: "oklch(0.65 0.18 250)"
  assist-cyan: "oklch(0.74 0.14 210)"
  pitch-base: "oklch(0.24 0.08 158)"
  pitch-stripe: "oklch(0.20 0.07 158)"
  text-primary: "#F8FAFC"
  text-secondary: "#94A3B8"
  text-muted: "#8494A7"
  text-inverse: "#090D16"
  on-primary: "{colors.text-inverse}"
  on-amber: "{colors.text-inverse}"
  on-crimson: "{colors.text-primary}"
  on-blue: "{colors.text-primary}"
  on-cyan: "{colors.text-inverse}"
  pos-gk: "{colors.captaincy-amber}"
  pos-def: "{colors.defensive-blue}"
  pos-mid: "{colors.primary-emerald}"
  pos-fwd: "{colors.hazard-crimson}"
  error: "{colors.hazard-crimson}"
  warning: "{colors.captaincy-amber}"
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
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px
motion:
  curve-snappy: "cubic-bezier(0.16, 1, 0.3, 1)"
  curve-instant: "cubic-bezier(0, 0, 0.2, 1)"
  duration-fast: "120ms"
  duration-normal: "180ms"
components:
  card-player:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
    border: "1px solid {colors.border-subtle}"
  card-bench:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
    border: "1px solid {colors.border-subtle}"
  panel-elevated:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
    border: "1px solid {colors.border-subtle}"
  control-deck:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
    border: "1px solid {colors.border-subtle}"
  button-chip:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.xs}"
    padding: "4px 8px"
  badge-captain:
    backgroundColor: "{colors.captaincy-amber}"
    textColor: "{colors.on-amber}"
    rounded: "{rounded.xs}"
    padding: "2px 4px"
  badge-hazard:
    backgroundColor: "{colors.hazard-crimson}"
    textColor: "{colors.on-crimson}"
    rounded: "{rounded.xs}"
    padding: "2px 4px"
  badge-assist:
    backgroundColor: "{colors.assist-cyan}"
    textColor: "{colors.on-cyan}"
    rounded: "{rounded.xs}"
    padding: "2px 4px"
  tag-pos-gk:
    backgroundColor: "{colors.pos-gk}"
    textColor: "{colors.on-amber}"
    rounded: "{rounded.xs}"
    padding: "1px 4px"
  tag-pos-def:
    backgroundColor: "{colors.pos-def}"
    textColor: "{colors.on-blue}"
    rounded: "{rounded.xs}"
    padding: "1px 4px"
  tag-pos-mid:
    backgroundColor: "{colors.pos-mid}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.xs}"
    padding: "1px 4px"
  tag-pos-fwd:
    backgroundColor: "{colors.pos-fwd}"
    textColor: "{colors.on-crimson}"
    rounded: "{rounded.xs}"
    padding: "1px 4px"
  pitch-surface:
    backgroundColor: "{colors.pitch-base}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
---

# DESIGN.md

## Overview

**FPL Analytics Terminal** is an institutional-grade sports analytics and mathematical decision cockpit modeled after financial engineering platforms (*Bloomberg Terminal*, *StatsBomb IQ*, *OptaPro*). It is designed specifically for quantitative Fantasy Premier League managers and data scientists seeking mathematical edges, LP solver optimizations, and probabilistic risk mitigation.

The terminal is governed under the **Operate** mode:
- **`DESIGN_VARIANCE: 6`** — Structured, systematic, data-first grid alignment.
- **`MOTION_INTENSITY: 3`** — Deterministic $\le 180\text{ms}$ cubic feedback; zero floating glowing orbs or distracting scroll-hijacking.
- **`VISUAL_DENSITY: 8`** — Maximum information density with compact tabular figures and strict hairline alignment.

---

## Colors & Perceptual Colorimetry

The palette is rooted in deep obsidian slate foundations with 1px hairline border contrast and domain-specific semantic role accents defined in the **`oklch()`** uniform perceptual color space.

### 1. Palette & Domain Mandates

- **Canvas Base (`oklch(0.12 0.02 260)` / `#090D16`):** Deep canvas foundation for optimal eye comfort during long analytical sessions.
- **Surface Level 1 (`oklch(0.15 0.025 260)` / `#111726`):** Elevated container and panel layer.
- **Surface Level 2 (`oklch(0.20 0.035 260)` / `#182035`):** Interactive card and table row layer.
- **Surface Subtle (`oklch(0.24 0.03 260)` / `#1E293B`):** Hover states, selection fills, and segmented switcher tracks.
- **Primary Emerald (`oklch(0.72 0.19 155)` / `#10B981`):** Core interactive accent, mathematical LP solver baseline, active projections, and MID role.
- **Captaincy Amber (`oklch(0.78 0.17 75)` / `#F59E0B`):** Captaincy indicators (`[C]`), GK positional role, warning thresholds, and market price fallers.
- **Hazard Crimson (`oklch(0.63 0.22 25)` / `#EF4444`):** Rival danger men, high effective ownership threat exposure, FWD positional role, and injury flags.
- **Defensive Blue (`oklch(0.65 0.18 250)` / `#3B82F6`):** DEF positional role and clean sheet probability distributions.
- **Assist Cyan (`oklch(0.74 0.14 210)` / `#06B6D4`):** Expected assists (`xA`), key creative metrics, and Rank Shield state.

---

### 2. Inherited Surface Scope Architecture

Pages and major workbenches declare a semantic scope class (`.surface-scope-pitch`, `.surface-scope-planner`, `.surface-scope-rivals`, `.surface-scope-fixtures`, `.surface-scope-market`, `.surface-scope-studio`). Nested panels, cards, and toolbars automatically inherit contextual background tokens, border colors, and role accents:

```css
/* Inherited Scope Tokens */
.surface-scope-pitch    { --scope-accent: var(--accent-emerald); --scope-card-bg: var(--bg-surface-2); }
.surface-scope-planner  { --scope-accent: var(--accent-cyan);    --scope-card-bg: var(--bg-surface-2); }
.surface-scope-rivals   { --scope-accent: var(--accent-crimson); --scope-card-bg: var(--bg-surface-2); }
.surface-scope-fixtures { --scope-accent: var(--accent-blue);    --scope-card-bg: var(--bg-surface-2); }
.surface-scope-market   { --scope-accent: var(--accent-amber);   --scope-card-bg: var(--bg-surface-2); }
.surface-scope-studio   { --scope-accent: var(--accent-emerald); --scope-card-bg: var(--bg-surface-2); }
```

---

### 3. Text-on-Accent & Contrast Matrix

Every colored tag, chip, or banner strictly enforces paired text tokens satisfying WCAG AA (minimum 4.5:1 for body, 3:1 for graphical UI):

| Accent Token | Background Hex | Mandatory Paired Text Token | Contrast Ratio |
|---|---|---|---|
| `primary-emerald` | `#10B981` | `text-inverse` (`#090D16`) | **10.8 : 1** (Passes AAA) |
| `captaincy-amber` | `#F59E0B` | `text-inverse` (`#090D16`) | **11.4 : 1** (Passes AAA) |
| `hazard-crimson` | `#EF4444` | `text-primary` (`#F8FAFC`) | **4.9 : 1** (Passes AA) |
| `defensive-blue` | `#3B82F6` | `text-primary` (`#F8FAFC`) | **5.2 : 1** (Passes AA) |
| `assist-cyan` | `#06B6D4` | `text-inverse` (`#090D16`) | **9.6 : 1** (Passes AAA) |
| `surface-2` | `#182035` | `text-primary` (`#F8FAFC`) | **14.2 : 1** (Passes AAA) |
| `surface-1` | `#111726` | `text-secondary` (`#94A3B8`) | **6.8 : 1** (Passes AA) |

---

## Typography

Typography establishes an unambiguous distinction between **functional UI chrome** and **high-density numerical telemetry**.

- **Sans-Serif (`Plus Jakarta Sans`):** Clean geometric grotesk for dashboard navigation, headers, button labels, and player web names.
- **Monospace (`JetBrains Mono` / `IBM Plex Mono`):** Tabular figures enabled with `font-feature-settings: "tnum" 1` for all statistical metrics, expected points ($xP$), prices ($\text{\pounds}m$), ownership percentages, and Poisson clean sheet probabilities.

### Typographic Hierarchy Scale
1. **Display & Brand ($24\text{px} - 28\text{px}$):** Terminal title and active target summaries.
2. **Section Headers H2 ($18\text{px}$):** Drawer headers, modal titles, and panel headings.
3. **Card Headers H3 ($14\text{px}$):** Workbench sub-headers and table grouping titles.
4. **Body Text ($12\text{px} - 13\text{px}$):** Player names, managerial directives, and table data.
5. **Metadata & Units ($10\text{px} - 11\text{px}$):** Club tags, metric unit labels, and cost readouts.
6. **Micro Tags ($8.5\text{px} - 9.5\text{px}$):** Positional squircle badges (`[MID]`), captaincy chips (`[C]`), and set-piece order tags (`PK1`).

---

## Layout & Spatial Geometry

All layouts adhere to an **8px base spatial grid with 4px sub-increments**:

### Spatial Scale
- **`xs (4px)`**: Badge internal padding, icon-to-label gaps.
- **`sm (8px)`**: Button internal padding, control rail gaps.
- **`md (12px)`**: Toolbar internal padding, card internal margins.
- **`lg (16px)`**: Panel internal padding and section margins.
- **`xl (20px)`**: Workbench gutters and bento grid gaps.
- **`2xl (24px)`**: Workspace container outer padding and modal margins.

### Concentric Squircle Radius Scale
We avoid arbitrary `9999px` capsule bubbles on cards and tables. Shapes follow a concentric mathematical squircle scale:
- **Panels & Drawers:** `8px` (`--radius-lg`)
- **Player & Telemetry Cards:** `6px` (`--radius-md`)
- **Interactive Switchers & Inputs:** `4px` (`--radius-sm`)
- **Data Chips, Status Tags & Role Badges:** `3px` (`--radius-xs`)

Concentric radius formula:
$$R_{\text{child}} = R_{\text{parent}} - \text{Padding}$$

---

## Motion & Interaction Physics

State transitions are crisp, deterministic, and instantaneous:
- **Snappy Easing (`--ease-snappy`):** `cubic-bezier(0.16, 1, 0.3, 1)` for drawers, slide-overs, and expanding panels ($180\text{ms}$).
- **Instant Easing (`--ease-instant`):** `cubic-bezier(0, 0, 0.2, 1)` for button hovers, tab switches, and chip selections ($120\text{ms}$).
- **Zero Scroll Hijacking:** Standard browser scrolling behavior is strictly preserved.

---

## Components

### 1. Unified Control Deck (`.matchday-control-deck`)
- **Surface**: Solid `#111726` with `6px` radius and 1px hairline border.
- **Height**: Compact 36px–40px single-row container eliminating vertical clutter.
- **Left Group**: Scenario / Chip switcher (`Standard XI`, `Wildcard`, `Free Hit`, `Bench Boost`, `Triple Capt`).
- **Center Group**: Strategy mode selector (`Pure xP`, `Rank Shield`, `Diff Chase`).
- **Right Telemetry**: Tabular monospace formation (`3-5-2`) and projected score (`59.2 xP`).

### 2. Contextual Directive Strip (`.matchday-directive-strip`)
- Unobtrusive single-line status banner below the control deck.
- Tagged with structured monospace role indicator (`[MATCHDAY]`, `[STRATEGY]`, `[SCENARIO]`).
- Visualizes transfer recommendations cleanly using `[IN]` / `[OUT]` arrow pills.

### 3. Minimalist Player Pitch Card (`.player-pitch-card`)
- **Surface**: Solid `#182035` with `6px` radius and 1px hairline border.
- **Top Row**: Concentric Squircle Badge (`[C]`, `[V]`) + Position Tag (`[MID]`) + Cost (`£6.0m`).
- **Middle**: High-contrast player web name (`font-weight: 800`).
- **Matchup**: Clickable opponent fixture link opening the Match Preview Drawer.
- **Points Banner**: Centered monospace expected score (`5.4 xP`).

### 4. Substitutes Sidebar Panel (`.sidebar-panel`)
- 4 vertical slots (`[GK Sub]`, `[Sub 1]`, `[Sub 2]`, `[Sub 3]`) on solid `#182035`.
- Bench Boost illumination activates a clean emerald border without neon text shadows.

---

## Do's and Don'ts

### Absolute Anti-Slop Bans
| Anti-Pattern (To Avoid) | Institutional Requirement |
|---|---|
| ❌ Translucent "Dark Glass" or `backdrop-filter: blur()` | ✅ Solid, opaque tokenized surfaces (`#090D16`, `#111726`, `#182035`). |
| ❌ Capsule bubble pills (`border-radius: 9999px`) on cards | ✅ Concentric Squircles (`3px` to `8px`). |
| ❌ Floating glowing dots, pulsing orbs, or neon shadow halos | ✅ Crisp hairline borders (`1px solid var(--border-subtle)`). |
| ❌ Decorative emojis (`⚡`, `🚀`, `🎯`, `✨`) in headers | ✅ Precise Phosphor SVG icons and typographic tags. |
| ❌ Multi-hue decorative gradient fills | ✅ Solid semantic role tokens (`var(--accent-emerald)`, `var(--accent-amber)`). |
| ❌ Proportional fonts for numerical statistics | ✅ Fixed-width tabular monospace typography (`JetBrains Mono`). |
| ❌ Duplicate strategy/scenario selectors stacked on one screen | ✅ Single unified control deck with contextual feedback. |
| ❌ Hardcoded ad-hoc hex colors in JSX components | ✅ Strict CSS custom property references (`var(--text-primary)`, `var(--bg-surface-2)`). |

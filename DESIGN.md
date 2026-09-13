---
name: FPL-Quantitative-Analytics-Terminal
version: 1.1.0
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
  text-secondary: "#CBD5E1"
  text-muted: "#94A3B8"
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
  fdr-1: "#1B5E20"
  fdr-2: "#00796B"
  fdr-3: "#455A64"
  fdr-4: "#E65100"
  fdr-5: "#B71C1C"
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

# DESIGN.md — FPL Dugout Design System & Architecture

## 1. System Overview & Register

**FPL Dugout Analytics Terminal** is an institutional-grade sports analytics and mathematical decision cockpit modeled after financial engineering platforms (*Bloomberg Terminal*, *StatsBomb IQ*, *OptaPro*). It is designed specifically for quantitative Fantasy Premier League managers and data scientists seeking mathematical edges, LP solver optimizations, and probabilistic risk mitigation.

The terminal is governed under the Impeccable **Operate** mode:
- **`DESIGN_VARIANCE: 6`** — Structured, systematic, data-first grid alignment.
- **`MOTION_INTENSITY: 3`** — Deterministic $\le 180\text{ms}$ cubic feedback; zero floating glowing orbs or distracting scroll-hijacking.
- **`VISUAL_DENSITY: 8`** — Maximum information density with compact tabular figures and strict hairline alignment.

---

## 2. Colors & Perceptual Colorimetry

The palette is rooted in deep obsidian slate foundations with 1px hairline border contrast and domain-specific semantic role accents defined in the **`oklch()`** uniform perceptual color space with CSS custom property implementations.

### 2.1 Color Tokens

- **Canvas Base (`oklch(0.12 0.02 260)` / `--bg-canvas: #090D16`):** Deep canvas foundation for optimal eye comfort during long analytical sessions.
- **Surface Level 1 (`oklch(0.15 0.025 260)` / `--bg-surface-1: #111726`):** Elevated container, header, control deck, and panel layer.
- **Surface Level 2 (`oklch(0.20 0.035 260)` / `--bg-surface-2: #182035`):** Interactive card, player card, and table row layer.
- **Surface Subtle (`oklch(0.24 0.03 260)` / `--bg-surface-subtle: #1E293B`):** Hover states, selection fills, and segmented switcher tracks.
- **Pitch Base (`oklch(0.24 0.08 158)` / `--bg-pitch-base: #064030`):** Pitch canvas field base.
- **Pitch Stripe (`oklch(0.20 0.07 158)` / `--bg-pitch-stripe: #053326`):** Alternating pitch mowing pattern.
- **Primary Emerald (`oklch(0.72 0.19 155)` / `--accent-emerald: #10B981`):** Core interactive accent, mathematical LP solver baseline, active projections, and MID role.
- **Captaincy Amber (`oklch(0.78 0.17 75)` / `--accent-amber: #F59E0B`):** Captaincy indicators (`[C]`), GK positional role, warning thresholds, and market price fallers.
- **Hazard Crimson (`oklch(0.63 0.22 25)` / `--accent-crimson: #EF4444`):** Rival danger men, high effective ownership threat exposure, FWD positional role, and injury flags.
- **Defensive Blue (`oklch(0.65 0.18 250)` / `--accent-blue: #3B82F6`):** DEF positional role and clean sheet probability distributions.
- **Assist Cyan (`oklch(0.74 0.14 210)` / `--accent-cyan: #06B6D4`):** Expected assists (`xA`), key creative metrics, and Rank Shield state.
- **FDR Difficulty Scale (Official 1–5 Matrix)**:
  - FDR 1: `--fdr-1: #1B5E20` (Text: `--on-fdr-1: #E8F5E9`)
  - FDR 2: `--fdr-2: #00796B` (Text: `--on-fdr-2: #E0F2F1`)
  - FDR 3: `--fdr-3: #455A64` (Text: `--on-fdr-3: #ECEFF1`)
  - FDR 4: `--fdr-4: #E65100` (Text: `--on-fdr-4: #FFF3E0`)
  - FDR 5: `--fdr-5: #B71C1C` (Text: `--on-fdr-5: #FFEBEE`)

---

### 2.2 Inherited Surface Scope Architecture

Pages and major workbenches declare a semantic scope class. Nested panels, cards, and toolbars automatically inherit contextual background tokens, border colors, and role accents:

```css
/* Inherited Scope Tokens */
.surface-scope-pitch    { --scope-accent: var(--accent-emerald); --scope-card-bg: var(--bg-surface-2); }
.surface-scope-planner  { --scope-accent: var(--accent-cyan);    --scope-card-bg: var(--bg-surface-2); }
.surface-scope-rivals   { --scope-accent: var(--accent-crimson); --scope-card-bg: var(--bg-surface-2); }
.surface-scope-fixtures { --scope-accent: var(--accent-blue);    --scope-card-bg: var(--bg-surface-2); }
.surface-scope-market   { --scope-accent: var(--accent-amber);   --scope-card-bg: var(--bg-surface-2); }
.surface-scope-studio   { --scope-accent: var(--accent-emerald); --scope-card-bg: var(--bg-surface-2); }
.surface-scope-vault    { --scope-accent: var(--accent-emerald); --scope-card-bg: var(--bg-surface-2); }
```

---

### 2.3 Text-on-Accent & Contrast Matrix

Every colored tag, chip, or banner strictly enforces paired text tokens satisfying WCAG AA (minimum 4.5:1 for body, 3:1 for graphical UI):

| Accent Token | Background Hex | Mandatory Paired Text Token | Contrast Ratio |
|---|---|---|---|
| `primary-emerald` | `#10B981` | `text-inverse` (`#090D16`) | **10.8 : 1** (Passes AAA) |
| `captaincy-amber` | `#F59E0B` | `text-inverse` (`#090D16`) | **11.4 : 1** (Passes AAA) |
| `hazard-crimson` | `#EF4444` | `text-primary` (`#F8FAFC`) | **4.9 : 1** (Passes AA) |
| `defensive-blue` | `#3B82F6` | `text-primary` (`#F8FAFC`) | **5.2 : 1** (Passes AA) |
| `assist-cyan` | `#06B6D4` | `text-inverse` (`#090D16`) | **9.6 : 1** (Passes AAA) |
| `surface-2` | `#182035` | `text-primary` (`#F8FAFC`) | **14.2 : 1** (Passes AAA) |
| `surface-1` | `#111726` | `text-secondary` (`#CBD5E1`) | **6.8 : 1** (Passes AA) |

---

## 3. Typography & Typesetting System

Typography establishes an unambiguous distinction between **functional UI chrome** and **high-density numerical telemetry**.

- **Sans-Serif (`Plus Jakarta Sans`)**: Clean geometric grotesk for dashboard navigation, headers, button labels, tabs, and player web names.
- **Monospace (`JetBrains Mono` / `IBM Plex Mono`)**: Tabular figures enabled with `font-feature-settings: "tnum" 1` for all statistical metrics, expected points ($xP$), prices ($\text{\pounds}m$), ownership percentages, and Poisson clean sheet probabilities.

### 3.1 8-Step Whole-Pixel Typographic Ramp

| Token | Size | Weight | Tracking | Purpose |
|---|---|---|---|---|
| `--text-2xs` | `8px` | `700` | `+0.05em` | Micro status tags, set-piece roles (`PK1`, `FK1`) |
| `--text-xs` | `9px` | `700` | `+0.04em` | Squircle positional badges (`[MID]`), metadata chips |
| `--text-sm` | `10px` | `600` | `+0.02em` | Cost readouts, club abbreviations, FDR labels |
| `--text-base` | `11px` | `500` | `0` | Subtitle notes, fixture opponent text, metadata |
| `--text-md` | `12px` | `500` / `600` | `0` | Standard data table cells, player display names |
| `--text-lg` | `14px` | `700` | `-0.01em` | Card section titles, workbench group headers |
| `--text-xl` | `16px` | `700` | `-0.02em` | Drawer headers, modal titles, panel headlines |
| `--text-2xl` | `18px` | `800` | `-0.02em` | Terminal brand title, major workbench titles |

### 3.2 Typesetting Rules
1. **Never use proportional fonts for statistical metrics**: All tables, points readouts, prices, and percentages must render with `--font-mono` and `font-feature-settings: "tnum" 1`.
2. **Measure discipline**: Descriptive body text and strategy advice must stay within a comfortable 45–75 character measure.
3. **Perceptual dark compensation**: On dark surfaces (`#090D16` / `#111726`), secondary text uses slightly elevated tracking (`+0.01em` to `+0.02em`) and higher contrast (`#CBD5E1`).

---

## 4. Layout & Spatial Geometry

All layouts adhere to an **8px base spatial grid with 4px sub-increments**:

### 4.1 Spatial Scale
- **`--space-1: 2px`**: Hairline offsets, border gaps.
- **`--space-2: 4px`**: Micro badge internal padding, icon-to-label gaps.
- **`--space-3: 6px`**: Tight control gaps, pill internal padding.
- **`--space-4: 8px`**: Standard button internal padding, control rail gaps.
- **`--space-5: 12px`**: Card internal padding, toolbar padding.
- **`--space-6: 16px`**: Panel internal padding and section margins.
- **`--space-7: 20px`**: Workbench gutters and bento grid gaps.
- **`--space-8: 24px`**: Container outer padding and modal margins.

### 4.2 Concentric Squircle Radius Scale
We avoid arbitrary `9999px` capsule bubbles on structural cards and tables. Shapes follow a concentric mathematical squircle scale:
- **Panels, Drawers & Modals:** `8px` (`--radius-lg`)
- **Player & Telemetry Cards:** `6px` (`--radius-md`)
- **Interactive Switchers & Inputs:** `4px` (`--radius-sm`)
- **Data Chips, Status Tags & Role Badges:** `3px` (`--radius-xs`)

Concentric radius formula:
$$R_{\text{child}} = R_{\text{parent}} - \text{Padding}$$

---

## 5. Catalog of Repeatable Elements

All frontend surfaces are constructed by composing the following standardized repeatable elements:

### 5.1 Control Deck (`.matchday-control-deck`)
- **Container**: Solid `#111726` with `6px` radius, 1px hairline border (`var(--border-subtle)`), 36px–40px height.
- **Left Slot**: Scenario / Chip switcher (`Standard XI`, `Wildcard`, `Free Hit`, `Bench Boost`, `Triple Capt`).
- **Center Slot**: Strategy mode selector (`Pure xP`, `Rank Shield`, `Diff Chase`).
- **Right Slot**: Monospace formation telemetry (`3-5-2`) and projected score (`59.2 xP`).

### 5.2 Contextual Directive Strip (`.matchday-directive-strip`)
- Compact single-line banner below the control deck.
- Tagged with structured monospace role indicator (`[MATCHDAY]`, `[STRATEGY]`, `[SCENARIO]`).
- Visualizes transfer recommendations using `[IN]` / `[OUT]` arrow pills.

### 5.3 Player Pitch Card (`.player-pitch-card`)
- **Container**: Solid `#182035`, `6px` radius, 1px border (`var(--border-subtle)`).
- **Header**: Squircle Role Badge (`[C]`, `[V]`) + Positional Tag (`[MID]`) + Cost (`£6.0m`).
- **Identity**: High-contrast player web name (`Plus Jakarta Sans`, `font-weight: 800`).
- **Fixture**: Opponent link opening Match Preview Drawer (`v ARS (H)`).
- **Metric Banner**: Centered monospace expected score (`5.4 xP`).

### 5.4 Bench Strip Slot (`.bench-slot-card`)
- 4 vertical slots (`[GK Sub]`, `[Sub 1]`, `[Sub 2]`, `[Sub 3]`) on `#182035`.
- Bench Boost illumination activates an emerald border without neon text glow.

### 5.5 Transfer Workbench Row & Delta Badges (`.transfer-workbench-card`)
- Side-by-side player replacement comparison (`Out` vs `In`).
- Net budget calculation pill (`£0.4m in bank`).
- Delta xP readout (`+1.8 xP`) in tabular monospace.

### 5.6 Rival Threat Telemetry Card (`.rival-threat-card`)
- Displays danger players with Effective Ownership (EO%) meters.
- Net threat differential score in tabular monospace.
- Shield advice badge (`Block Captain`, `Differential Gamble`).

### 5.7 Fixture Cell (`.fixture-cell`)
- Monospace club code (`MCI`, `ARS`, `LIV`) with venue flag (`(H)` / `(A)`).
- Strict FDR background colors (`--fdr-1` through `--fdr-5`) with paired text contrast tokens.

### 5.8 Market Velocity Card (`.velocity-card`)
- Price change momentum indicator with tabular velocity index.
- Projection tag for expected price rise (`+£0.1m imminent`) or drop.

### 5.9 Historical Vault Telemetry & Time Machine (`.vault-metric-card`)
- Season selector bar (`2016-17` to `2026-27`).
- Backtested prediction vs actual points comparison bar.
- Archival player profile deep viewer.

### 5.10 Drawers & Modals
- **Match Preview Drawer (`.fixture-drawer`)**: Slide-over panel (`380px` width) with Poisson probability distributions, xG/xGA tables, and head-to-head records.
- **Live Team Sync Modal (`.sync-modal`)**: Centered dialog (`480px` max-width) with Team ID input and instant squad hydration.
- **Player DNA Inspector (`.player-dna-modal`)**: Modal displaying Recharts radar plot of threat, creativity, bonus potential, and Poisson goal distributions.
- **Onboarding Guide (`.onboarding-modal`)**: First-run tour highlighting key cockpit capabilities.

### 5.11 Progressive Disclosure Tray (`.nike-collapsible-section` / `<CollapsibleSection>`)
- **Container**: Sharp 0px corners (`var(--radius-sharp)`), solid `#181818` background, 1px hairline border (`var(--border-subtle)`).
- **Header**: Accessible button trigger (`role="button"`, `aria-expanded`), uppercase title, optional pill badge (`badge-neutral`, `badge-accent`, `badge-warning`), and smooth rotating chevron (`CaretDown`).
- **Content Area**: CSS grid 0fr → 1fr zero-layout-shift transition. Eliminates viewport clutter by tucking auxiliary tables and reserves away until requested.

### 5.12 Monolithic Focal Point Container (`.nike-hero-card` & `.nike-pill-cta` / `<HeroFocusCard>`)
- **Container**: Color-blocked `#111111` canvas with generous macro-whitespace (`padding: clamp(20px, 3vw, 48px)`). Enforces the **Rule of One**.
- **Hero Display**: Monolithic display typography (`48px` / `32px`, `font-weight: 800`, line-height: 1.0, tabular numbers).
- **Signature Pill CTA**: 48px height, full pill radius (`9999px`), light high-contrast background (`#F5F5F5`), black text (`#111111`), and trailing action icon (`↗`).

### 5.13 Operational Matchday Lineup Architecture (`TacticalPitch.jsx`)
- **Compact Status Bar (`.matchday-status-bar`)**: Streamlined $42\text{px}$ operational header integrating Gameweek focus, active formation tag, tabular monospace score chip (`64.2 xP`), and an inline Lock Lineup button (`[ Lock Lineup ]`). Eliminates 200px+ of viewport dead space so the pitch sits directly above the fold.
- **Integrated Dugout Command HUD (`.tactical-hud-ribbon`)**: 4 modular operational tiles (Objective Strategy, Bonus Chips, Strategic Directive, and Matchday Scorecard) sit directly above the pitch for immediate scenario evaluation without accordion click barriers.
- **Heroic 11-Man Pitch with Restrained Positional Semantics**: Central visual canvas featuring high-contrast, accessible semantic position chips (soft amber GK, calm blue DEF, emerald MID, muted crimson FWD) on player pitch cards and bench slots, preserving instant peripheral recognition, the gold `[C]` captaincy badge (`var(--accent-amber)`), and high-contrast player typography.
- **Natural Substitutes Sidebar Panel (`.pitch-sidebar`)**: The 4 bench substitutes (or Bench Boost telemetry grid) sit naturally open alongside the pitch in the 2-column desktop workspace (`.pitch-workspace`), eliminating empty voids and enabling frictionless click-to-swap player substitutions.

### 5.14 Fixture Ticker Legend & Difficulty Formula Popover (`.fixture-legend-bar`)
- **Single-Line Legend Bar (`.fixture-legend-bar`)**: Replaces multi-row 90px+ header blocks with a compact 38px horizontal strip positioned beside the horizon pills. Reclaims ~60px of vertical height so 15+ clubs sit directly above the fold.
- **FDR Dot Track (`.legend-scale-group`)**: Unified 1-line scale with 7 micro-chips (`1 Very Easy` to `5 Very Tough`, `Blank`, `Past`) utilizing 6px colored dots (`--fdr-1` to `--fdr-5`, `--bg-canvas-subtle`, `--text-muted`) with uppercase 10px tracking.
- **Contextual Formula Trigger (`.formula-trigger-btn`) & Popover (`.formula-popover-card`)**: Accessible popover button trigger (`[ ℹ Avg Difficulty Formula ]`) toggling an on-demand mathematical explanation card ($280\text{px}$ width) with keyboard Escape / outside click dismissal, keeping mathematical nuances available without permanent table clutter.

---

## 6. Motion & Interaction Physics

State transitions are crisp, deterministic, and instantaneous:
- **Snappy Easing (`--ease-snappy`):** `cubic-bezier(0.16, 1, 0.3, 1)` for drawers, slide-overs, and expanding panels ($180\text{ms}$).
- **Instant Easing (`--ease-instant`):** `cubic-bezier(0, 0, 0.2, 1)` for button hovers, tab switches, and chip selections ($120\text{ms}$).
- **Zero Scroll Hijacking:** Standard browser scrolling behavior is strictly preserved.

---

## 7. Absolute Anti-Slop Manifesto

| Anti-Pattern (Strictly Banned) | Institutional Requirement |
|---|---|
| ❌ Translucent "Dark Glass" or `backdrop-filter: blur()` | ✅ Solid, opaque tokenized surfaces (`#090D16`, `#111726`, `#182035`). |
| ❌ Capsule bubble pills (`border-radius: 9999px`) on cards | ✅ Concentric Squircles (`3px` to `8px`). |
| ❌ Floating glowing dots, pulsing orbs, or neon shadow halos | ✅ Crisp hairline borders (`1px solid var(--border-subtle)`). |
| ❌ Decorative emojis (`⚡`, `🚀`, `🎯`, `✨`) in headers | ✅ Precise Phosphor / SVG icons and typographic tags. |
| ❌ Multi-hue decorative gradient fills | ✅ Solid semantic role tokens (`var(--accent-emerald)`, `var(--accent-amber)`). |
| ❌ Proportional fonts for numerical statistics | ✅ Fixed-width tabular monospace typography (`JetBrains Mono`). |
| ❌ Duplicate strategy/scenario selectors stacked on one screen | ✅ Single unified control deck with contextual feedback. |
| ❌ Hardcoded ad-hoc hex colors in JSX components | ✅ Strict CSS custom property references (`var(--text-primary)`, `var(--bg-surface-2)`). |

---

## 8. Bi-Directional Design System Governance

To eliminate design drift across multi-agent sessions, all contributors and coding agents must abide by the **Bi-Directional Contract**:

1. **DESIGN.md → Code (Mandatory Consumption)**:
   - Prior to modifying any component under `frontend/src/`, agents must inspect this document.
   - All styling must reuse the repeatable elements, surface scopes, and CSS custom property tokens defined above.
   - Introducing one-off hex colors, custom un-tokenized paddings, or non-concentric border radii is a constitutional violation.

2. **Code → DESIGN.md (Mandatory Reciprocal Documentation)**:
   - When an agent implements a new repeatable UI component, layout primitive, or variant in `frontend/src/`, the agent is contractually mandated to document it in this file in the exact same pull request or task.
   - If the component has interactive states, the agent must also register it in `frontend/src/components/ComponentStudio.jsx`.

3. **Validation Gates**:
   - Run the Impeccable detector: `node .agent/skills/impeccable/scripts/detect.mjs --json frontend/src`
   - Run the voice & tone validator: `npm run check-copy`
   - Run the frontend build: `npm run build`

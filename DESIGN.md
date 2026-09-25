---
name: FPL-Quantitative-Analytics-Terminal
version: 2.0.0
description: Matchday radio-wire decision cockpit for Fantasy Premier League management (Direction J, locked 2026-09-21).
colors:
  canvas: "#18181B"
  surface-1: "#1C1C20"
  surface-2: "#232328"
  surface-subtle: "#2A2A30"
  primary-emerald: "oklch(0.72 0.19 155)"
  captaincy-amber: "oklch(0.78 0.17 75)"
  hazard-crimson: "oklch(0.63 0.22 25)"
  defensive-blue: "oklch(0.65 0.18 250)"
  assist-cyan: "oklch(0.74 0.14 210)"
  pitch-base: "oklch(0.24 0.08 158)"
  pitch-stripe: "oklch(0.20 0.07 158)"
  text-primary: "#F4F4F5"
  text-secondary: "#D4D4D8"
  text-muted: "#87878F"
  text-inverse: "#18181B"
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
  wire-token:
    backgroundColor: "transparent"
    textColor: "{colors.text-primary}"
    border: "none"
  wire-bench-line:
    backgroundColor: "transparent"
    textColor: "{colors.text-primary}"
    border: "none"
  wire-banner:
    textColor: "{colors.text-muted}"
    fontSize: 12px
    fontWeight: 800
    letterSpacing: 0.18em
---

# DESIGN.md — FPL Dugout Design System & Architecture

## 1. System Overview & Register

**FPL Dugout Analytics Terminal** is an institutional-grade sports analytics and mathematical decision cockpit modeled after financial engineering platforms (*Bloomberg Terminal*, *StatsBomb IQ*, *OptaPro*). It is designed specifically for quantitative Fantasy Premier League managers and data scientists seeking mathematical edges, LP solver optimizations, and probabilistic risk mitigation.

**Governing direction: Direction J, "Matchday Radio Wire"** (locked by the owner on 2026-09-21; full brief in `ROUND-2-CONTEXT.md`). The interface reads like a live matchday dispatch: fast typographic scanning and generous space instead of nested boxes, borders and badge pills.

- **Warm charcoal ground** (`--bg-canvas: #18181B`) on every tab and viewport.
- **Two-colour letterforms**: cream (`--text-primary`) for what matters, zinc (`--text-muted`) for context. Hierarchy comes from size and weight jumps, never fills.
- **No decorative borders or pills.** Grouping comes from vertical rhythm, column alignment and whitespace (64px desktop / 32px mobile gutters).
- **Tabular monospace** for every point, price and odds value.
- **Colour exception**: FDR 1–5 and up/down deltas may use colour, but always next to a number or arrow, never alone.

**Migration status:** the Lineup tab (`TacticalPitch.jsx`, `PlayerCard.jsx`) is on Direction J. The other tabs still use the legacy card components in §5 and move over in later rounds; do not add new legacy-style components.

---

## 2. Colors & Perceptual Colorimetry

Warm charcoal neutrals plus a two-colour letterform system. The accent tokens below still exist for legacy tabs, FDR and deltas; new Direction J surfaces use only the text tokens.

### 2.1 Color Tokens

- **Canvas (`--bg-canvas: #18181B`):** Warm charcoal ground, constant everywhere.
- **Surface 1 (`--bg-surface-1: #1C1C20`):** Legacy panels, modals, select menus.
- **Surface 2 (`--bg-surface-2: #232328`):** Legacy cards and table rows.
- **Surface Subtle (`--bg-surface-subtle: #2A2A30`):** Legacy hover and selection fills.
- **Cream (`--text-primary: #F4F4F5`):** Primary letterform role (about 65%): names, projected points, key telemetry.
- **Zinc light (`--text-secondary: #D4D4D8`):** Body copy on legacy surfaces.
- **Zinc (`--text-muted: #87878F`):** Secondary letterform role (about 35%): positions, opponents, labels, benchmarks. Deliberately lighter than J's `#71717A`, which fails WCAG AA (3.7:1) on the canvas; `#87878F` gives 5.0:1.
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

Each tab panel carries a `.surface-scope-<tab>` class (`pitch`, `planner`, `rivals`, `fixtures`, `market`, `studio`, `vault`). Under Direction J these are **namespaces only**: there are no per-tab accent colours, and the old `--scope-*` variables have been removed. Use the scope class to limit tab-specific rules, not to recolour.

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
| `canvas` | `#18181B` | `text-primary` (`#F4F4F5`) | **16.1 : 1** (Passes AAA) |
| `canvas` | `#18181B` | `text-muted` (`#87878F`) | **5.0 : 1** (Passes AA) |
| `surface-1` | `#1C1C20` | `text-secondary` (`#D4D4D8`) | **11.5 : 1** (Passes AAA) |

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
| `--text-name` | `15px` | `600` / `800` captain | `0` | Direction J player names and status values |
| `--text-hero-mobile` | `64px` | `800` | `-0.04em` | Matchday hero number, ≤768px |
| `--text-hero` | `88px` | `800` | `-0.04em` | Matchday hero number (line-height `0.9`) |
| `--text-hero-xl` | `104px` | `800` | `-0.04em` | Matchday hero number, ≥1280px |

Direction J banners (`.wire-banner`, `.wire-slug`) are `12px / 800 / 0.18em` uppercase in zinc; labels are `11px / 700 / 0.14em` uppercase.

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
- **`--space-9: 32px`**: Direction J mobile gutter, pitch row gap.
- **`--space-10: 48px`**: Direction J context-column section gap.
- **`--space-11: 64px`**: Direction J desktop gutter between summary, pitch and context.

### 4.2 Concentric Squircle Radius Scale
Direction J surfaces have no boxes, so they use no radius. Legacy tabs keep this concentric squircle scale until they migrate:
- **Panels, Drawers & Modals:** `8px` (`--radius-lg`)
- **Player & Telemetry Cards:** `6px` (`--radius-md`)
- **Interactive Switchers & Inputs:** `4px` (`--radius-sm`)
- **Data Chips, Status Tags & Role Badges:** `3px` (`--radius-xs`)

Concentric radius formula:
$$R_{\text{child}} = R_{\text{parent}} - \text{Padding}$$

---

## 5. Catalog of Repeatable Elements

All frontend surfaces are constructed by composing the following standardized repeatable elements:

### 5.0 Header & Navigation Wire (`.top-nav` / `Header.jsx`)
- **Container**: Flat `var(--bg-surface-1)` ground with a single hairline bottom border (`1px solid var(--border-subtle)`), zero ambient drop shadow.
- **Brand Lockup**: Bold typographic title (`800`) with an unboxed soccer ball icon in cream (`var(--text-primary)`), accompanied by a monospace gameweek selector styled with the `.wire-select` pattern.
- **Navigation Rail (`.segmented-nav-rail` > `.nav-tab-btn`)**: Flat, borderless horizontal wire rail. Active tab is indicated through typographic contrast (`700`, `--text-primary`) and a 2px baseline underline (`border-bottom: 2px solid var(--text-primary)`), without navy card boxes or glowing neon drop-shadows.
- **Tab Metadata Tags (`.tab-wire-tag`)**: Minimal monospace tags in zinc (`--text-muted`) for chip state and free transfer counts.
- **Manager Telemetry (`.live-manager-chip`)**: Flat token on `var(--bg-surface-2)` displaying manager name and `#ID` with a static 6px indicator dot in `var(--accent-emerald)` (no pulsating neon orbs).

### 5.1 Matchday Summary (`.wire-summary`)
- Three columns (`auto 1fr auto`, 64px gap): hero number, radio status list, actions. Collapses to two columns at ≤1024px and one at ≤768px.
- **Hero (`.wire-hero`)**: zinc slug (`GAMEWEEK 6 · PROJECTED`), mono hero number at `--text-hero` with a zinc `0.36em` unit (`XP` / `PTS`), then zinc formation line.
- **Radio status (`.wire-status` > `.wire-status-row`)**: a `<dl>`; zinc uppercase `dt` labels in a 9.5rem column, cream `dd` values beside them. Chip is a borderless `<select class="wire-select">`; goal is `.wire-segments` of `.wire-segment` buttons (active = cream, 800, underlined, `aria-pressed`).
- **Actions (`.wire-actions` > `.wire-action`)**: uppercase text buttons. `.is-primary` is cream and underlined. No button boxes.
- **Inline notice (`.wire-notice`)**: `role="status"` sentence under the summary, used instead of `alert()` (for example, a swap that breaks formation rules).

### 5.2 Section Banner (`.wire-banner`)
- `<h2>` in zinc, 12px / 800 / 0.18em uppercase, 24px below. Replaces panel headers and panel badges.

### 5.3 Player Token (`.wire-token` / `PlayerCard.jsx`)
- No background, border, radius, shadow or kit colour.
- **Main button (`.wire-token-main`)**: cream name at `--text-name` (captain 800) over mono points with a zinc unit. Click swaps or inspects; double-click inspects.
- **Meta row (`.wire-token-meta`)**: sibling buttons, never nested. `.wire-token-fixture` (zinc `POS · vs OPP`, opens the match preview) and `.wire-token-armband` (`C` / `VC` / `3×`, always visible, 24px minimum target, cream when active, `aria-label` and `aria-pressed`).
- **Status word (`.wire-token-status`)**: at most one zinc uppercase word, in priority order `BLANK` > `DGW` > `CAMEO` > `RISK`.
- **Swap target (`.is-target`)**: underlined name. No glow or colour.
- Rows are `.wire-pitch-row` flex lines inside `.wire-pitch` (a size container); under 460px names drop to 12px.

### 5.4 Bench Line (`.wire-bench` > `.wire-bench-line`)
- An `<ol>` of full-width buttons: grid of slot (`GK`, `1`–`3`), name, zinc `POS · sub odds` (`AUTO_SUB_LABELS` badge), mono points.
- Selected (`aria-pressed`) = bold, underlined name. Under Bench Boost, points show as `+x.x` beside a two-row Starting XI / Bench summary.

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

### 5.10 Drawers & Modals (Direction J Polish)
- **Universal Modal Architecture (`.modal-overlay`, `.modal-content`)**:
  - Ground & Scrim: Solid neutral scrim (`rgba(10, 10, 12, 0.82)`) with zero `backdrop-filter: blur()`. Modal shell sits on `var(--bg-surface-1)` (`#1C1C20`) with 1px hairline border (`var(--border-subtle)`), 8px radius (`var(--radius-lg)`), and tokenized institutional elevation (`var(--shadow-modal)`).
  - Modal Action Footer (`.modal-action-footer`): Flat `var(--bg-surface-1)` bar with hairline top border. Primary action uses high-contrast cream button (`var(--text-primary)` text on `var(--text-inverse)` background, weight 700) with zero neon halos. Ghost actions use `.modal-btn-ghost` with `var(--border-medium)`.
  - Unboxed Header Icons (`.modal-unboxed-icon`): Icons render inline without container boxes or squircle backgrounds (`color: var(--text-primary)`, flex-shrink 0).
- **Match Preview & Probability Forecast Drawer (`.fixture-drawer`, `.drawer-content` / `FixtureProbabilityDrawer.jsx`)**:
  - Header: Unboxed `<SoccerBall>` icon (`.modal-unboxed-icon`) paired with uppercase zinc slug (`.profile-tag.font-mono`) and clean matchup headline.
  - Joint Probability Matrix (`.matrix-wrapper`, `.scoreline-matrix-table`, `.matrix-cell`): Monochromatic luminance heat ramp (`rgba(255, 255, 255, 0.02..0.16)`) over `var(--bg-surface-2)` with hairline borders (`var(--border-subtle)`). Zero scale transforms, zero neon halo shadows. Hover uses `var(--bg-surface-subtle)` with `var(--border-medium)`.
  - Final Scores Grid (`.scorelines-grid`, `.scoreline-pill-card`): Flat cards on `var(--bg-surface-2)` with tabular monospace cream percentages (`.scoreline-prob` in `var(--text-primary)`).
- **Live Team Settings & Sync Modal (`.sync-modal-content` / `LiveTeamSyncModal.jsx`)**:
  - Header: Unboxed `<SoccerBall>` icon with two-tier typographic header.
  - Inputs & Action: Inputs (`.sync-input`) and sync action button (`.sync-submit-btn`) built on `var(--bg-surface-2)`, `var(--text-primary)`, and `var(--border-subtle)`.
  - Profile Spec Card (`.profile-preview-card`): Flat `var(--bg-surface-2)` card with static 6px connection dot (`.live-sync-indicator`).
- **Player DNA Inspector (`PlayerDNAInspector.jsx`)**:
  - Typographic Position Tag (`.dna-player-pos`): Clean uppercase zinc tags (`[MID]`, `[FWD]`) replacing saturated position pill badges.
  - Segmented Wire Rail (`.dna-modal-switcher` > `.wire-segments` > `.wire-segment`): Borderless wire segments where active is indicated by typographic weight (`800`), cream color (`--text-primary`), and underline offset (`aria-pressed="true"`), eliminating bubble pills.
  - Press Candor & Set-Piece Hierarchy: Pure typographic readouts in zinc (`--text-muted` / `--text-secondary`) and monospace tabular figures without pill borders.
- **Onboarding Gateway Guide (`.onboarding-modal-content` / `OnboardingModal.jsx`)**:
  - Header Slug (`.wire-slug`): Clean zinc uppercase slug (`FPL DUGOUT · 2026-27`) replacing green capsule pill badge.
  - Form & Discovery Guide (`.id-finder-card`, `.id-finder-url-box`): Tokenized `var(--bg-surface-2)` cards with unboxed typographic underline indicators (`mark`).
  - Action Pole (`.onboarding-actions`): Direction J high-contrast cream primary button (`.btn-primary-action`) and subtle zinc secondary button (`.btn-secondary-action`).
- **Matchday Handover Checklist & Transfer Recommendation Modals (`.handover-modal-content`, `.transfer-breakdown-modal-content` / `MatchdayHandoverModal.jsx`, `TransferBreakdownModal.jsx`)**:
  - Header: Unboxed icons (`.modal-unboxed-icon`, `<ShieldCheck>`, `<ArrowsLeftRight>`) without squircle containers.
  - Decision Cards (`.unified-transfer-card`): Direction J 2-color letterform hierarchy:
    - Cream (`--text-primary`, weight 700) for player web names and primary projected points ($xP$).
    - Muted zinc (`--text-muted`) for club, cost, position tags, and bridge arrows.
    - Pure typographic status tags (`.player-col-badge.out`, `.player-col-badge.in`) set as type without capsule backgrounds or colored borders.
    - Tabular monospace readout for net point gain (`.delta-pill` in `var(--text-primary)` with `font-feature-settings: 'tnum' 1`).
  - Rationale Surface (`.breakdown-rationale-card`): Unboxed zinc icons (`.rationale-icon`) without colored background squares or pill wrappers.
  - Armband Tactical Picks (`.handover-pick-card`): Flat tokenized cards with uniform hairline borders (`var(--border-subtle)`), eliminating colored halos.

### 5.11 Progressive Disclosure Tray (`.nike-collapsible-section` / `<CollapsibleSection>`)
- **Container**: Sharp 0px corners (`var(--radius-sharp)`), solid `#181818` background, 1px hairline border (`var(--border-subtle)`).
- **Header**: Accessible button trigger (`role="button"`, `aria-expanded`), uppercase title, optional pill badge (`badge-neutral`, `badge-accent`, `badge-warning`), and smooth rotating chevron (`CaretDown`).
- **Content Area**: CSS grid 0fr → 1fr zero-layout-shift transition. Eliminates viewport clutter by tucking auxiliary tables and reserves away until requested.

### 5.12 Retired
`.nike-hero-card`, `.nike-pill-cta` and `<HeroFocusCard>` were removed in round 2 (unused, and pill CTAs break Direction J).

### 5.13 Matchday Lineup Architecture (`TacticalPitch.jsx`)
- `.wire` root: `.wire-summary` (§5.1), optional `.wire-notice`, then `.wire-split` (`1.2fr 1fr`, 64px gap; one column at ≤768px).
- **Left, `.wire-pitch-col`**: `Starting XI` banner and formation rows of player tokens (§5.3). Bench Boost puts all 15 on the pitch.
- **Right, `.wire-context`**: `Recommended move` (a `.wire-directive` button listing `In … for Out …` lines, opening the reasoning modal, plus `.wire-link` to the Planner), then the bench (§5.4) and a zinc `.wire-footnote`.
- Retired with this redesign: `.matchday-status-bar`, `.tactical-hud-ribbon`, `.pitch-workspace`, `.pitch-sidebar`, `.bench-item`, `.player-pitch-card` on the Lineup tab (the Vault still uses it), captain badges, position pills, DIFF/CORE/PK/CK/BB/price badges.

### 5.14 Fixture Ticker Legend & Difficulty Formula Popover (`.fixture-legend-bar`)
- **Single-Line Legend Bar (`.fixture-legend-bar`)**: Replaces multi-row 90px+ header blocks with a compact 38px horizontal strip positioned beside the horizon pills. Reclaims ~60px of vertical height so 15+ clubs sit directly above the fold.
- **FDR Dot Track (`.legend-scale-group`)**: Unified 1-line scale with 7 micro-chips (`1 Very Easy` to `5 Very Tough`, `Blank`, `Past`) utilizing 6px colored dots (`--fdr-1` to `--fdr-5`, `--bg-canvas-subtle`, `--text-muted`) with uppercase 10px tracking.
- **Contextual Formula Trigger (`.formula-trigger-btn`) & Popover (`.formula-popover-card`)**: Accessible popover button trigger (`[ ℹ Avg Difficulty Formula ]`) toggling an on-demand mathematical explanation card ($280\text{px}$ width) with keyboard Escape / outside click dismissal, keeping mathematical nuances available without permanent table clutter.

### 5.15 Mini-League Tactical Telemetry Deck (`.rivals-telemetry-deck`)
- **Streamlined Command Strip (`.rivals-telemetry-deck`)**: Replaces the bulky 280px hero panel and 3-card asymmetric KPI grid with a compact 48–52px horizontal command strip. Reclaims ~228px of vertical height, lifting the primary Mini-League Table and Head-to-Head Tactical Duel directly into the initial viewport fold.
- **Integrated Identity & KPI Telemetry Chips (`.rivals-telemetry-left` & `.rivals-telemetry-right`)**:
  - Left: League badge with `UsersThree` icon, league ID monospace pill (`#1305495`), and active rivals counter chip (`{n} Rivals Tracked`).
  - Right: High-density micro-chips for Captain Consensus (`👑 {captain} · {pct}% backing`), Differential Advantage (`🛡️ {count} Differentials · +{xp} xP`), and Danger Pick (`⚠️ {player} · {freq}/{n} rivals`).
- **Contextual Telemetry Notes Trigger & Popover (`.telemetry-notes-btn` & `.telemetry-popover-card`)**: Accessible on-demand popover with keyboard Escape and click-outside dismissal explaining differential edge calculations ($\text{Net Delta} = \text{Your Differentials xP} - \text{Rival Differentials xP}$) and danger pick mechanics without permanent clutter.
- **Mobile Standings Scroll Cue (`.table-mobile-hint`) & Scroll Mask (`.rivals-scroll-wrapper`)**: Responsive visual affordance banner and dual-edge gradient masks alerting mobile users on viewports `<680px` that the standings table scrolls horizontally to access squad overlap metrics and the Head-to-Head compare action button.

### 5.16 Transfer Planner & Multi-Horizon Roadmap Architecture (`MultiGwPlanner.jsx`, `TransferWorkbench.jsx`)
- **Multi-Horizon Planner Control Deck (`.planner-control-deck`)**:
  - Ground & Shell: Flat `var(--bg-surface-1)` with 1px hairline border (`var(--border-subtle)`), 8px radius (`var(--radius-md)`), and institutional card elevation (`var(--shadow-card)`).
  - Wire Horizon Slug (`.planner-horizon-slug`): Unboxed zinc monospace indicator (`GW{start}–GW{end} HORIZON`) with inline `<CalendarCheck>` icon, replacing capsule badge containers.
  - Segmented Wire Rail (`.wire-segments` > `.wire-segment`): Borderless wire segment buttons (`5-Week Roadmap`, `Transfer Scout`, `Unified Canvas`) with `aria-pressed`, active state indicated by cream letterforms (`var(--text-primary)`, weight 800) and flat subtle background (`var(--bg-surface-subtle)`), eliminating green fills.
  - Tabular Telemetry Chips (`.planner-telemetry-chip`): Clean zinc monospace labels (`TARGET:`, `HITS:`, `BANK:`) paired with cream tabular monospace values (`var(--text-primary)`, `font-feature-settings: 'tnum' 1`), replacing pill containers and colored boxes.
  - On-Demand Strategy Notes Popover: Accessible trigger (`.telemetry-notes-btn`) toggling flat `var(--bg-surface-1)` rules card with keyboard Escape / click-outside dismissal.
- **5-Column Strategic Horizon Stepper (`.multi-gw-matrix-grid`, `.multi-gw-column-card`)**:
  - Flat cards on `var(--bg-surface-1)`. Active gameweek card highlighted by crisp hairline outline (`var(--border-strong)`) and subtle surface elevation (`var(--bg-surface-2)`), eliminating neon glows.
  - Header: Monospace title (`.gw-col-title`) with unboxed current tag (`.gw-current-tag`, `[CURRENT]`) and tabular free transfers readout (`{n} FT`).
  - Projection: Expected points in cream (`var(--text-primary)`, weight 800) with muted zinc unit (`xP`), bank in monospace zinc.
  - Tactical Moves (`.gw-transfer-box`, `.move-line`): Pure 2-color typography: player names in cream (`var(--text-primary)`), `<ArrowUpRight>` with `BUY:` and `<ArrowDownRight>` with `SELL:` in zinc letterforms without pill backgrounds or colored boxes.
  - Footer: Clean uppercase status indicator (`[ACTIVE]` vs `VIEW`).
- **Monochromatic Cumulative Trajectory Canvas (`.chart-canvas-container`)**:
  - Recharts `<AreaChart>` using a monochromatic luminance ramp (`linearGradient` from `rgba(255, 255, 255, 0.08)` to `0.00`) and hairline stroke (`var(--text-secondary)`, 1.5px), strictly removing saturated emerald fills.
  - X/Y Axes and Tooltip styled in `--font-mono` with tabular figures and flat tokenized surfaces (`var(--bg-surface-2)`, `var(--border-subtle)`).
- **Side-by-Side Transfer Comparison Workbench (`.compare-workbench-container`)**:
  - Header: Unboxed `<Scales>` icon (`.modal-unboxed-icon`) paired with uppercase monospace title (`DIRECT TRANSFER SWAP COMPARISON`) and wire close button.
  - Player Cards (`.compare-player-card`): Flat `var(--bg-surface-2)` cards with hairline borders (`var(--border-subtle)`), removing tinted green/red container borders.
  - Typographic Role Tags (`.transfer-role-tag`): Pure monospace indicators (`[OUT] SELLING`, `[IN] BUYING`, `[TARGET ACQUISITION]`).
  - Unboxed Position Tags (`.dna-player-pos`): Monospace bracketed format (`[MID]`, `[FWD]`) in muted zinc, replacing rainbow position pills.
  - Center Delta Readout (`.compare-delta-readout`): Unboxed `<TrendUp>` / `<TrendDown>` icon paired directly with tabular monospace numbers (`+X.X xP`), removing the floating `.delta-badge` pill.
- **2-Tier Transfer Scout Filter Deck & Marketplace Table (`.scout-controls-2tier`, `.data-table`)**:
  - Tier 1: Search input on `var(--bg-surface-2)`, `.wire-segments` position filter buttons (`ALL`, `GK`, `DEF`, `MID`, `FWD`) with `aria-pressed`, and `.wire-select` sort dropdown.
  - Tier 2: Tokenized budget slider and quick preset buttons (`.preset-btn`) with wire borders.
  - Table: Bracketed monospace position tags (`[MID]`), cream tabular expected points (`.table-cell-xp`, weight 700), and wire compare action button without green button fills.

### 5.17 Forecaster Control Deck & Calibration Drawer (`.forecaster-control-deck`)
- **Streamlined Command Strip (`.forecaster-control-deck`)**: Replaces the floating sub-view switcher, 280px hero panel, 3-card asymmetric KPI strip, and static parameter sliders with an integrated 48–52px operational header. Reclaims ~640px of vertical height, pulling the 600+ player projections table and position filters directly into the initial viewport fold.
- **Sub-View Rail & Accuracy Telemetry (`.forecaster-control-left`)**:
  - Segmented Switcher: Seamless toggling between `Formula Sandbox` and `Accuracy Scorecard`.
  - Accuracy Telemetry Micro-Chips: Monospace badges for Rank Accuracy (`Rank Acc: +0.417`), Starter Points Margin (`Margin: ±1.85 pts`), and Key Factors (`Factors: 10`).
- **On-Demand Calibration Drawer (`.calibration-drawer-container`)**: Activated via the `[ ⚙️ Calibration (500m · 1.10x) ]` button (`.calibration-toggle-btn`), expanding the recent form weighting slider, home venue multiplier, and positional baseline rates per 90 on demand without crowding the primary evaluation table.
- **Methodology Notes Popover (`.telemetry-notes-group` / `.telemetry-popover-card`)**: Accessible popover dialog explaining scoring factors, baseline prior weighting, and venue adjustments with keyboard Escape and outside-click dismissal.

### 5.18 Mini-League Rivals Telemetry Deck & H2H Wire Duel (`.rivals-telemetry-deck`)
- **Command Strip (`.rivals-telemetry-deck`)**: Modernized 48px telegraphic command strip replacing the legacy 280px hero panel. Renders active rival intelligence (`ACTIVE RIVAL:`, `CAPTAIN:`, `DIFFS:`, `DANGER:`) in crisp tabular monospace.
- **Monospace Threat Tags (`.rival-threat-tag`)**: Replaces rainbow badge stacks (`[HIGH]`, `[MED]`, `[LOW]`) with pure monospace tags paired with numeric rank and cream point totals (`font-mono font-bold`).
- **H2H Wire Duel & Segments (`.wire-segments`, `.h2h-compact-row`)**: Unboxed 2-column comparative duel using 2-color letterforms (cream/zinc), eliminating tinted green/red container borders and glow shadows. Tab switching governed by `.wire-segments > .wire-segment` with explicit `aria-pressed` states.

### 5.19 Fixture Horizon Legend Bar & Heatmap Table (`.fixture-legend-bar`, `.heatmap-table`)
- **38px Horizontal Legend Strip (`.fixture-legend-bar`)**: Replaces floating cards and detached pills with a fixed 38px horizontal strip directly above the fixture grid.
- **Strictly Paired FDR Tags (`.legend-fdr-tag.fdr-1` .. `.fdr-5`)**: Retains official Premier League FDR 1–5 color fills strictly paired with numeric text (`1` very easy to `5` very hard) and neutral tags for blanks and past fixtures. Eliminates detached colored dots and bubble pills.
- **Heatmap Horizon Segments (`.wire-segments`)**: Fixture planning horizon (Next 3, 5, 8 GWs) selectable via keyboard-accessible wire segments with `aria-pressed`. Average difficulty rendered as `.table-avg-diff.font-mono`.

### 5.20 Market Financial Wire & Velocity Tracking (`.market-wire-panel`, `.market-wire-table`)
- **Financial Wire Ledger (`.market-wire-panel`, `.market-wire-table`)**: Converts chunky `.velocity-card` containers into a high-density financial wire table. Columns include Player (`[POS] Web Name`), Current Price (`£X.Xm`), Net Transfers, Threshold Velocity Track, and Projected Delta.
- **Monospace Net Deltas (`.market-wire-delta`)**: Replaces rising/falling pill capsules with directional monospace indicators (`▲ +£0.1m`, `▼ -£0.1m`) in tabular figures.
- **Velocity Progress Rail (`.velocity-wire-track`)**: Subtle hairline bar displaying proximity to overnight price change thresholds without neon glow halos.

### 5.21 Points Forecaster Bayesian Calibration & Projections Ledger (`.calibration-drawer-container`)
- **Empirical Bayes Prior Display ($M_0 = 500\text{m}$)**: Tabular monospace display of prior weighting formula $w = \frac{N}{N + M_0}$ and recent minutes slider, reinforcing mathematical grounding without corporate jargon.
- **Unboxed Positional Baselines**: High-density 4-column ledger (GK, DEF, MID, FWD) showing points per 90 baseline metrics in tabular figures.
- **Projections Ledger (`.studio-players-table`)**: Tabular evaluation grid featuring bracketed position tags `[POS]`, club affiliation, and cream tabular expected points (`xP`).

### 5.22 Historical Vault Timeline Scrubber & Wire Pitch (`.vault-timeline-scrubber`, `.vault-telemetry-deck`)
- **Borderless Season Timeline Scrubber (`.vault-timeline-scrubber`)**: Sleek horizontal scrubber spanning 2016-17 to 2026-27 with smooth scroll alignment, previous/next controls, and active season indicator lines.
- **48px Season Telemetry Deck (`.vault-telemetry-deck`)**: Telegraphic metrics strip displaying Campaign details, League Firepower (Goals/Assists), Golden Boot winner, and Season MVP in cream tabular monospace figures.
- **Wire Pitch Tokens (`.wire-pitch`, `.vault-token`)**: Retires remaining `.player-pitch-card` instances in favor of Direction J `.wire-token` typographic elements (cream web name, cream tabular monospace points, meta strip `[{pos}] · {club} · £{cost}m`, and `[C]` armband).
- **Hall of Fame & 10-Season Overview**: Tabular records ledger with `[{pos}]` monospace bracketed tags and wire-button navigation.

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
| ❌ Capsule bubble pills and badge stacks | ✅ One zinc uppercase status word, set as type. |
| ❌ Floating glowing dots, pulsing orbs, or neon shadow halos | ✅ Weight, size and underline for emphasis. |
| ❌ Decorative 1px boxes around players, metrics or panels | ✅ Vertical rhythm, column alignment and whitespace. |
| ❌ Colour as decoration (position colours, amber captain, per-tab accents) | ✅ Cream / zinc letterforms; colour only for FDR and deltas, always paired with a number or arrow. |
| ❌ Decorative emojis (`⚡`, `🚀`, `🎯`, `✨`) in headers | ✅ Precise Phosphor / SVG icons and typographic tags. |
| ❌ Multi-hue decorative gradient fills | ✅ Flat charcoal ground (`var(--bg-canvas)`). |
| ❌ Proportional fonts for numerical statistics | ✅ Fixed-width tabular monospace typography (`JetBrains Mono`). |
| ❌ Duplicate strategy/scenario selectors stacked on one screen | ✅ Single unified control deck with contextual feedback. |
| ❌ Hardcoded ad-hoc hex colors in JSX components | ✅ Strict CSS custom property references (`var(--text-primary)`, `var(--bg-surface-2)`). |

---

## 8. Bi-Directional Design System Governance

To eliminate design drift across multi-agent sessions, all contributors and coding agents must abide by the **Bi-Directional Contract**:

1. **DESIGN.md → Code (Mandatory Consumption)**:
   - Prior to modifying any component under `frontend/src/`, agents must inspect this document.
   - All styling must reuse the repeatable elements and CSS custom property tokens defined above. New work follows Direction J (§1).
   - Introducing one-off hex colors, decorative borders, pills, or un-tokenized spacing is a constitutional violation. Hex values live only in `:root` in `frontend/src/styles/index.css`.

2. **Code → DESIGN.md (Mandatory Reciprocal Documentation)**:
   - When an agent implements a new repeatable UI component, layout primitive, or variant in `frontend/src/`, the agent is contractually mandated to document it in this file in the exact same pull request or task.

3. **Validation Gates**:
   - Run the Impeccable detector: `node .agent/skills/impeccable/scripts/detect.mjs --json frontend/src`
   - Run the voice & tone validator: `npm run check-copy`
   - Run the frontend build: `npm run build`

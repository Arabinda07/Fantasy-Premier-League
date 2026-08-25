# DESIGN.md — FPL Quantitative Analytics Terminal

This document is the permanent single source of truth for the visual design system, frontend architecture, and component interfaces of the **FPL Quantitative Analytics Terminal**.

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
| ❌ **Purple/Black with Radial Glowing Orbs** | Generic "AI wrapper" template trope | Deep Slate (`#090D16`) & Elevated Navy (`#111726`) with 1px border contrast. |
| ❌ **Multi-Hue Decorative Gradients** | Saturated AI decorative fill trope | Solid token accents (`var(--accent-emerald)`, `var(--accent-amber)`, `var(--accent-crimson)`). |
| ❌ **Fake Testimonials & $29/mo Pricing Tiers** | Clueless marketing clutter | Pure functional workspace consuming live JSON payloads. |
| ❌ **Sparkle Icons & Emojis everywhere (`⚡`, `🚀`)** | Childish gimmicks undermining technical credibility | Precise Phosphor SVG icons and typographic badges (`(LIVE)`, `[PK1]`). |
| ❌ **Hardcoded Hex Colors in Components** | Bypasses design token hierarchy | Strict CSS custom property references (`var(--text-inverse)`, `var(--text-primary)`). |
| ❌ **"It's not X, it's Y" Copy Tropes** | Cliche AI copywriting | Direct, factual status labels and clear action summaries. |
| ❌ **Side-Stripe Borders (Left Accent Lines)** | Saturated AI card scaffold | Clean, fully bordered containers with background contrast. |
| ❌ **Insanely Rounded Radii (>16px on cards)** | Codex-style over-rounding | Crisp geometric radii (`3px` to `8px`). |
| ❌ **Repeating Diagonal Stripe Backgrounds** | Distracting decorative noise | Functional sports field grass bands (`#064030` / `#053326`). |
| ❌ **Multi-Line Footer Link Farms** | Cluttered visual noise | Minimal single-line footer (Copyright left, icon-only GitHub right). |

---

## 3. Design System Tokens (CSS Custom Properties)

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

  /* Geometry Radii */
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

## 4. Mobile Responsive Architecture

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

## 5. Codebase Architecture: Deep Module System

Applying the **Deep Module Principles** (*large amount of internal capability hidden behind a small, testable interface at a clean seam*):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               DEEP MODULE COMPONENT MAP                                │
├──────────────────────────┬──────────────────────────────┬──────────────────────────────┤
│ Deep Module              │ Minimal Public Interface     │ Encapsulated Logic           │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `TacticalPitch`          │ `starters`, `bench`,         │ • Dynamic formation parser   │
│                          │ `onSelectPlayer`,            │ • Spatial 2D row grouping    │
│                          │ `onInspectPlayer`,           │ • Field line SVG geometry    │
│                          │ `startingXp`, `totalXp`      │ • Bench swap validity        │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `TransferWorkbench`      │ `roadmap`, `allPlayers`,     │ • Multi-criteria search      │
│                          │ `onInspectPlayer`            │ • Price threshold filtering  │
│                          │                              │ • Sort by xP / Cost / Form   │
│                          │                              │ • 3-GW bank math trajectory  │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `FixtureHeatmap`         │ `fixtures`, `teams`          │ • 38-GW 20-team matrix map   │
│                          │                              │ • Home/Away FDR mapper       │
│                          │                              │ • Rolling average score      │
│                          │                              │ • Mobile short name switcher │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `PlayerDNAInspector`     │ `player`, `onClose`          │ • 11-Component decomposition │
│                          │                              │ • Empirical Bayes math ($M_0$)│
│                          │                              │ • Lazy-loaded Recharts modal │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `MarketVelocityTicker`   │ `allPlayers`,                │ • Net transfer velocity math │
│                          │ `onInspectPlayer`            │ • Price rise/fall risk tiers │
│                          │                              │ • Seasonal chip EV guide     │
├──────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ `ComponentStudio`        │ `players`,                   │ • Bayesian shrinkage sandbox │
│                          │ `onInspectPlayer`            │ • Dynamic parameter sliders  │
│                          │                              │ • Multi-page paginated table │
└──────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

---

## 6. Interaction & Motion Rules

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

## 7. Pre-Flight Design Audit Checklist

Before releasing any new frontend view or feature:
- [ ] **Contrast Check**: All body text $\ge 4.5:1$, large labels $\ge 3:1$.
- [ ] **Typography**: All tabular numerical columns use `font-mono` (`JetBrains Mono`) with `font-feature-settings: "tnum" 1`.
- [ ] **No AI Slop Check**: Zero decorative multi-hue gradients, zero emojis in technical headers, zero hardcoded colors.
- [ ] **Keyboard Accessibility**: All clickable rows and cards have `tabIndex={0}`, `role="button"`, and `onKeyDown`.
- [ ] **Deep Module Seam**: Component props are minimal; complexity is encapsulated internally.
- [ ] **Responsive Breakpoints**: Layout renders without horizontal overflow across Desktop (1600px), Tablet (768px), and Mobile (375px).
- [ ] **Build Check**: `npm run build` compiles with 0 errors.


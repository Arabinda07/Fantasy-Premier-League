# ROUND-2-CONTEXT.md

## Governing Direction: Direction J (Matchday Radio Wire)
**Status:** Explicitly Locked by Human (2026-09-21)  
**Proof Level:** Direction Locked

---

### 1. Conceptual Premise
The visual language derives from the urgent tempo of live matchday radio dispatches, audio commentary feeds, and managerial dugout exchanges. It abandons heavy nested boxes, borders, and badge-pill fatigue in favor of rapid narrative scanning, high typographic velocity, and generous spatial breathing room.

---

### 2. Core Typographic Specification
- **Primary Typeface:** Expressive Humanist Sans-Serif (`"Segoe UI"`, `"Candara"`, `-apple-system`, sans-serif).
- **Telemetry Typeface:** Tabular Monospace (`"Consolas"`, `ui-monospace`, `font-feature-settings: 'tnum' 1`).
- **Hierarchy Steps:**
  - *Headline & Matchday Hero:* `88px` – `104px`, Weight `800`, tracking `-0.04em`, line-height `0.9`.
  - *Section Banners:* `12px`, Weight `800`, tracking `0.18em`, uppercase.
  - *Player Web Names & Actions:* `14px` – `15px`, Weight `600` (Starters) / `700` (Captain/Key Threats).
  - *Secondary Telemetry & Labels:* `11px` – `13px`, Weight `500` / `700`, uppercase tracking `0.14em`.
  - *Axiom / Footnotes:* `13px`, tracking `0.12em`, uppercase.

---

### 3. Palette & Colorimetry (Strict 2-Color Letterform System)
- **Canvas Foundation:** Warm dark charcoal (`#18181B` / `oklch(0.22 0.01 260)`).
- **Primary Letterform Role (65%):** Warm cream (`#F4F4F5`) for primary player names, active projected points, and core telemetry.
- **Secondary Letterform Role (35%):** Muted zinc (`#71717A`) for positional tags, baseline benchmarks, opponent details, and secondary states.
- **Color Discipline Law:** Color is never used as decorative fills, gradients, or glowing outlines. Hierarchy is achieved through size jumps, weight shifts, and typographic contrast.

---

### 4. Spatial Geometry & Layout Laws
- **Zero Decorative Border Policy:** No 1px hairline boxes around individual players or metric tags. Grouping is established through strict vertical rhythm and column alignments.
- **Asymmetric Split:** 1.2fr to 1fr two-column division between the Primary Tactical Surface (Starting XI & Bench) and the Situational Context (Rival Radar / Threat Intel).
- **Negative Space as Structural Material:** Generous gutters (`64px` desktop, `32px` mobile) eliminate the need for container dividers.

---

### 5. Invariants (Non-Negotiable Production Boundaries)
1. Warm charcoal ground (`#18181B`) remains constant across viewports.
2. The 2-color letterform discipline governs typography; do not re-introduce rainbow badge pills.
3. Monospace numbers with tabular figures (`'tnum' 1`) are mandatory for all points, costs, and odds.
4. Spoken-word velocity and rapid narrative parsing replace nested card dashboards.

---

### 6. Target Production Scope
- **Primary Component Target:** `frontend/src/components/TacticalPitch.jsx` (Redesign: eliminate card clutter, elevate typography to Direction J standard, clarify captaincy and bench swaps, improve mobile responsiveness).
- **System-Wide Alignment:** Propagate Direction J's borderless, typographic command into the remaining tabs (`transfers`, `rivals`, `fixtures`, `market`, `math`, `vault`).

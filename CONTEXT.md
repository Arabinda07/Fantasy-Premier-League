# Domain Vocabulary & Ubiquitous Language

This document tracks canonical domain terms, models, and boundaries for the Fantasy Premier League Multi-User Intelligence Platform.

## 1. Core Domain Entities

### Manager Profile
- **FPL Entry ID**: The official unique integer identifier assigned to a manager by Fantasy Premier League (e.g. `9500404`).
- **Entry Summary**: High-level manager metadata including `manager_name`, `team_name`, `overall_rank`, `total_points`, `bank` (£M), and `free_transfers` (1..5).
- **Gameweek Picks**: The active 15-player squad chosen for a specific Gameweek, including starting XI (positions 1-11), bench hierarchy (positions 12-15), captain, vice-captain, purchase prices, and selling prices.

### League & Rivals
- **Classic Mini-League ID**: The unique integer identifier of an FPL classic mini-league (e.g. `1305495`).
- **Rival Threat Matrix**: A matrix comparing the visitor's squad against the top rivals in their mini-league, identifying high-risk differential players (Effective Ownership deltas).

### Global Intelligence (Static Foundation)
- **Global Prediction Matrix**: Pre-calculated weekly projections containing multi-component expected points ($xP$), floor/ceiling percentiles (p10, p50, p90), Dixon-Coles match outcome probabilities, minutes hazard metrics, and set-piece responsibilities.
- **Permanent Player Code**: Opta/FPL permanent `code` (e.g. `118748` for Salah) used to reconcile across seasons and FPL ID changes.
- **Automated Pipeline Workflow**: A scheduled GitHub Action (`.github/workflows/weekly_fpl_pipeline.yml`) executing weekly post-matchday transitions, regenerating global prediction datasets and triggering Vercel zero-downtime auto-deployments.

### Real-Time Client Engine
- **Onboarding Gateway**: An introductory state presented to first-time visitors prompting for their FPL Entry ID and optional Mini-League ID, with a 1-click "Try Demo Squad" fallback that loads the pre-computed optimal template.
- **Session State**: Browser `localStorage` persistence keeping `fpl_synced_entry_id`, `fpl_synced_league_id`, and synced manager profile so returning visitors seamlessly bypass onboarding and immediately view their personal dashboard.
- **Aggregated Sync Endpoint**: A dedicated serverless route (`/api/sync`) that concurrently queries the official FPL entry summary, gameweek picks, transfer logs, and classic league standings, returning an aggregated, sanitized payload in a single round-trip.
- **Client-Side Lineup Optimizer**: Deterministic in-browser algorithm executing on visitor sync that selects the optimal starting XI under standard FPL formation constraints (1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD), assigns Captain / Vice-Captain based on ceiling/xP, and orders the bench by substitute value.
- **Client-Side Transfer Evaluator**: In-browser heuristic that filters candidate transfers from the global player pool matching the manager's available budget (`bank` + selling price) and free transfers.

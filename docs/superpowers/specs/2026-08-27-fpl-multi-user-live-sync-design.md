# Comprehensive Design Specification: Multi-User FPL Live Sync & Intelligence Platform

- **Date**: 2026-08-27
- **Status**: Ready for Implementation
- **Target Platform**: Vercel (Hobby Free Tier) + React 19 Frontend + Python Pipeline

---

## 1. Executive Summary & Goal

Transform the Fantasy Premier League Analytics Terminal from a single-manager static report into an open, zero-cost, multi-user FPL intelligence platform. 

Any visitor can:
1. Land on a sleek **Onboarding Gateway** or explore an **Instant Demo Squad**.
2. Enter their official **FPL Entry ID** (e.g. `9500404`) and optional **Classic Mini-League ID** (e.g. `1305495`).
3. Instantly retrieve their live 15-player squad, current starting XI, bench order, bank balance, available free transfers, and mini-league rival standings.
4. Have the platform run an **in-browser solver** calculating their personalized starting XI, captaincy recommendation, and budget-constrained transfer upgrades using the ML prediction engine ($xP$, Dixon-Coles odds, hazard rates).
5. Enjoy automatic weekly prediction updates powered by **GitHub Actions** with $0.00 operating cost.

---

## 2. Architecture & Data Flow

```
                               ┌────────────────────────────────────────────────────┐
                               │             Weekly ML Pipeline                     │
                               │  GitHub Actions (.github/workflows/weekly.yml)     │
                               │  - Fetches FPL bootstrap & Understat               │
                               │  - Computes xP, Dixon-Coles, Minutes Hazards       │
                               │  - Writes frontend/src/data/players_full.json      │
                               │  - Commits & triggers Vercel auto-build            │
                               └─────────────────────────┬──────────────────────────┘
                                                         │
                                                         ▼
┌────────────────────────────────┐         ┌────────────────────────────────────────┐
│         Visitor Browser        │         │      Vercel Serverless Function        │
│                                │         │      (/api/sync.js)                    │
│ 1. Enter Entry ID & League ID  │────────►│                                        │
│                                │         │ 2. Concurrent HTTP calls to FPL API    │
│ 4. Matches squad with          │◄────────│    • /api/entry/{id}/                  │
│    players_full.json           │         │    • /api/entry/{id}/event/{gw}/picks/ │
│ 5. Runs Client-Side Lineup &   │ 3. JSON │    • /api/entry/{id}/transfers/        │
│    Transfer Optimizer (<50ms)  │ payload │    • /api/leagues-classic/{id}/...     │
│ 6. Persists to localStorage    │         │                                        │
└────────────────────────────────┘         └───────────────────┬────────────────────┘
                                                               │
                                                               ▼
                                           ┌────────────────────────────────────────┐
                                           │       fantasy.premierleague.com        │
                                           │       (Official REST Endpoints)        │
                                           └────────────────────────────────────────┘
```

---

## 3. Detailed Component Plan

### 3.1. Backend / Serverless Layer (`api/sync.js` & `api/fpl/[...path].js`)
- **File**: `api/sync.js` (Node.js 18+ on Vercel)
- **Duties**:
  - Accept query parameters: `entry_id`, `league_id` (optional), `gw` (optional).
  - Execute parallel `fetch` calls to:
    1. `https://fantasy.premierleague.com/api/entry/{entry_id}/` (Manager profile, total points, rank, bank).
    2. `https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/` (15 player picks, starter/bench indices, captain, vice-captain).
    3. `https://fantasy.premierleague.com/api/entry/{entry_id}/transfers/` (Transfer history to deduce available Free Transfers 1..5).
    4. `https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/` (Mini-league standings and rival squad snapshots).
  - Handle rate limits, network timeouts, and FPL game update states (HTTP 503 maintenance mode).
  - Return consolidated, clean JSON response with standard CORS headers (`Access-Control-Allow-Origin: *`).

### 3.2. Client-Side Optimizer Engine (`frontend/src/utils/clientOptimizer.js`)
- **File**: `frontend/src/utils/clientOptimizer.js`
- **Duties**:
  - **Reconciliation**: Map official FPL `element_id` from picks to the global player dataset in `players_full.json` (using Opta `code` and `id`).
  - **Formation Solver**:
    - Select optimal 11 starters maximizing cumulative $xP$ subject to valid FPL formation constraints:
      - 1 Goalkeeper
      - 3 to 5 Defenders
      - 2 to 5 Midfielders
      - 1 to 3 Forwards
    - Assign Captain ($C$) based on maximum ceiling ($p90$ or raw $xP$) and Vice-Captain ($VC$).
    - Order bench players (positions 12, 13, 14, 15) by auto-sub expected point contribution.
  - **Transfer Evaluator**:
    - Identify 1-transfer and 2-transfer upgrades from the full player pool based on:
      - Transfer cost budget = `bank` + player selling price.
      - Net expected point gain $\Delta xP$ over 1 to 3 gameweek horizon.

### 3.3. UI / UX Integration
1. **Onboarding Gateway Screen (`frontend/src/components/OnboardingModal.jsx`)**:
   - Clean, high-aesthetic modal displayed on first visit if no `fpl_synced_entry_id` exists in `localStorage`.
   - Input: **FPL Team ID** (with direct link/guide showing how to copy it from fantasy.premierleague.com).
   - Input: **Mini-League ID** (optional).
   - Primary CTA: **"Sync My Squad"** (with live loading spinner & validation).
   - Secondary CTA: **"Explore Demo Template"** (loads pre-computed GW optimal template).
2. **Top Navigation Quick-Switch (`frontend/src/components/Header.jsx`)**:
   - Header shows current active manager badge (e.g. `👤 Arabinda Saha · 🏆 Fuljhore Giants`).
   - Clicking badge opens the Sync Configuration modal anytime to switch IDs or manually force-refresh.
3. **Live Sync Modal Enhancement (`frontend/src/components/LiveTeamSyncModal.jsx`)**:
   - Replace the static "proxy required" banner with an active "⚡ Live Cloud Sync Active" indicator.
   - Add a 1-click **"Refresh Live Data"** button.

### 3.4. Automated Weekly ML Pipeline (`.github/workflows/weekly_pipeline.yml`)
- **File**: `.github/workflows/weekly_pipeline.yml`
- **Trigger**:
  - `schedule`: `cron: '0 4 * * 2'` (Tuesdays at 04:00 UTC, after Monday night fixtures).
  - `workflow_dispatch`: Manual one-click trigger from GitHub Actions tab.
- **Workflow Steps**:
  1. Checkout repository with full history.
  2. Set up Python 3.11 with pip caching.
  3. Install dependencies from `requirements.txt`.
  4. Run `python -m model.gameweek_transition --mode full --season 2026-27`.
  5. Run `python -m model.enrich_frontend_data`.
  6. Git commit updated `data/` and `frontend/src/data/` files with message `chore(data): auto-update weekly FPL predictions [skip ci]`.
  7. Push to `main` branch $\to$ Vercel automatically deploys within 60 seconds.

---

## 4. Implementation Roadmap across Upcoming Sessions

| Phase | Milestone | Deliverables |
| :--- | :--- | :--- |
| **Phase 1** | **Vercel Serverless Sync Proxy** | Create `api/sync.js`, configure `vercel.json` rewrites, test live JSON responses against real FPL entry IDs. |
| **Phase 2** | **Client-Side Optimization Engine** | Build `clientOptimizer.js` (lineup formation solver, captain selector, transfer search). |
| **Phase 3** | **Frontend UI & State Wiring** | Connect `App.jsx`, `LiveTeamSyncModal.jsx`, and create `OnboardingModal.jsx` with `localStorage` persistence. |
| **Phase 4** | **Weekly GitHub Action Automation** | Create `.github/workflows/weekly_pipeline.yml` with secrets and scheduled cron. |
| **Phase 5** | **Edge Cases & Verification** | Test FPL downtime handling, invalid IDs, blank mini-leagues, and verify live deployment on Vercel. |

---

## 5. Reference Files
- Domain Dictionary: [`CONTEXT.md`](file:///e:/Fantasy-Premier-League/CONTEXT.md)
- Architectural Decision Record: [`docs/adr/0001-serverless-cors-proxy-and-client-side-solver.md`](file:///e:/Fantasy-Premier-League/docs/adr/0001-serverless-cors-proxy-and-client-side-solver.md)
- Python Ingestion Prototype: [`model/live_sync.py`](file:///e:/Fantasy-Premier-League/model/live_sync.py)
- Frontend Sync Modal: [`frontend/src/components/LiveTeamSyncModal.jsx`](file:///e:/Fantasy-Premier-League/frontend/src/components/LiveTeamSyncModal.jsx)
- Frontend Matchday Loader: [`frontend/src/utils/loadLatestMatchday.js`](file:///e:/Fantasy-Premier-League/frontend/src/utils/loadLatestMatchday.js)

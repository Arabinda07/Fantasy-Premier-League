# ADR 0001: Serverless CORS Proxy & Client-Side Squad Solver for Multi-User Platform

- **Status**: Approved
- **Date**: 2026-08-27
- **Deciders**: Repository Lead & AI Assistant
- **Consulted**: `AGENTS.md`, `CONTEXT.md`

## Context & Problem Statement
The platform was originally built as an institutional point-prediction model and static single-manager cockpit (pre-loaded with one team's GW2 squad data).
To transition the site into an open, multi-user FPL Intelligence Platform where any visitor can enter their FPL Entry ID and Classic Mini-League ID:
1. Direct browser requests to the official FPL REST API (`fantasy.premierleague.com/api/*`) are blocked by the browser due to the absence of `Access-Control-Allow-Origin` (CORS) headers.
2. Running a full heavyweight Python MILP optimization backend on every visitor request would require paid infrastructure, complex scaling, and introduce latency.
3. The platform is hosted on Vercel's free Hobby tier ($0/mo).

## Decision
We adopt a hybrid architecture:
1. **Global Intelligence (Static / Server-Side Weekly Build)**: The Python ML models (11-component xP, Dixon-Coles bivariate scorelines, continuous minutes hazards) calculate season and gameweek projections once per week via an automated GitHub Action. These are bundled into static JSON (`players_full.json`).
2. **Aggregated Vercel Serverless Function (`/api/sync`)**: A lightweight Node.js serverless route proxies and aggregates official FPL API calls (entry profile, gameweek picks, transfer history for FT calculation, and mini-league standings) concurrently, returning an authenticated, CORS-compliant payload in under 200ms.
3. **Client-Side Lineup & Transfer Optimizer**: The visitor's browser executes an in-memory optimization algorithm matching their 15 live player codes against the global prediction matrix to derive optimal starting XI, captaincy, bench order, and budget-constrained transfer targets.
4. **Onboarding Gateway & Local Storage Session**: First-time visitors are welcomed with a clean ID entry screen with a "Try Demo Squad" fallback. Returning visitors automatically load their saved team from `localStorage`.

## Consequences
### Positive
- **Zero Hosting Cost**: Operates 100% within Vercel's free serverless tier (100,000 requests/month) and free GitHub Actions runner minutes.
- **Sub-Second Performance**: Instant browser-side optimization with no server cold starts or execution timeout hazards.
- **Privacy & Simplicity**: No database infrastructure needed; user preferences and IDs remain on the client side.

### Negative / Trade-offs
- **Game Update Downtime**: When the official FPL API enters maintenance mode during active gameweek transitions, live sync calls return HTTP 503; the frontend must gracefully fall back to cached session data with clear UI toast messaging.

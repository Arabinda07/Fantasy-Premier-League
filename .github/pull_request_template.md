## Summary of Changes

<!-- Brief 2-3 sentence overview of what this pull request introduces, fixes, or refactors. -->

### Spec & Issue Reference
- **Feature Spec**: `specs/<feature-name>/spec.md` <!-- or N/A for minor hotfixes -->
- **Issue Reference**: Fixes #<!-- issue number -->

---

## Architectural Tier Check (CONSTITUTION.md Article I)

- [ ] **Tier 1 (Active Core)**: Modifies `model/`, `frontend/`, `knowledge/`, or `data/2026-27/`.
- [ ] **Tier 2 (Historical Vault)**: Strictly read-only; no modifications to past season folders (`data/2016-17/` to `data/2025-26/`).
- [ ] **Tier 3 (Quarantined Legacy)**: No new imports from `archive/` or `analysis/`; no unwanted refactoring of root legacy scrapers.

---

## Mandatory Constitutional Quality Gates (CONSTITUTION.md Article VI)

Before requesting review, ensure all four gates pass locally:

- [ ] **Gate 1: OKF v0.2 Schema & Link Conformance**
  ```bash
  python scripts/validate_okf.py
  ```
- [ ] **Gate 2: Voice, Tone & Copy Linter (FPL Dugout Standard)**
  ```bash
  npm run check-copy --prefix frontend
  pytest model/test_voice_and_tone.py
  ```
  *(Verified: No banned corporate terms like "assets", "portfolios", or untranslated raw math like "Poisson", "Bayesian shrinkage" in user UI)*
- [ ] **Gate 3: Mathematical Attestation & Invariant Checks**
  ```bash
  python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2
  python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2
  ```
- [ ] **Gate 4: Automated Test Suites & Build**
  ```bash
  pytest
  npm run build --prefix frontend
  ```

---

## Copy & Token Governance (CONSTITUTION.md Article IV)

- [ ] All new UI strings, strategy tips, and badge descriptions are imported from `frontend/src/constants/copyTokens.js`.
- [ ] All statistical terms are translated into conversational football English (*Exp Pts*, *Match Preview*, *Clean Sheet Odds*).

---

## Documentation & Journey Log

- [ ] Updated [JOURNEY.md](file:///e:/Fantasy-Premier-League/JOURNEY.md) with narrative context of changes.
- [ ] Updated [knowledge/index.md](file:///e:/Fantasy-Premier-League/knowledge/index.md) if models, datasets, or computations were touched.

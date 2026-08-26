# OKF Discipline & Context Rules for AI Coding Agents

This rule file is automatically active for all AI coding agents operating in this workspace.

## 1. Zero Hallucination Policy & Knowledge Ground Truth

1. **Never guess CSV column names or schemas**:
   - Before writing or editing data transformation code, always consult the verified schema in [`knowledge/datasets/`](/knowledge/datasets/index.md).
   - Key schemas:
     - [`players_raw.md`](/knowledge/datasets/players-raw.md)
     - [`merged_gw.md`](/knowledge/datasets/merged-gw.md)
     - [`model-dataset.md`](/knowledge/datasets/model-dataset.md)
     - [`predictions.md`](/knowledge/datasets/predictions.md)
     - [`fixture-predictions.md`](/knowledge/datasets/fixture-predictions.md)

2. **Never guess mathematical formulas or statistical parameters**:
   - All mathematical models are explicitly specified in [`knowledge/models/`](/knowledge/models/index.md).
   - Invariants:
     - Empirical Bayes Prior shrinkage: $M_0 = 500.0\text{ mins}$ towards positional priors.
     - Exact discrete Poisson $GC \ge 2$ summation penalty: $-\sum_{m=1}^5 m (P(2m) + P(2m+1))$.
     - Conjugate venue symmetry: $1.08 \longleftrightarrow 0.9259$ enforcing $\mathbb{E}[\text{Scored}] \equiv \mathbb{E}[\text{Conceded}]$.
     - MILP Solver: FPL 50% profit retention formula $\text{selling} = \text{purchase} + \lfloor (\text{current} - \text{purchase})/2 \rfloor$, discount $\gamma = 0.90$.

3. **Follow Attested Computation Contracts**:
   - Before implementing or modifying executable analytics pipelines, check the sanctioned contract in [`knowledge/computations/`](/knowledge/computations/index.md).

---

## 2. Validation & Verification Gates

Whenever code in `model/` or documentation in `knowledge/` is updated:

1. **Validate OKF Conformance**:
   ```powershell
   python scripts/validate_okf.py
   ```
2. **Run Deterministic Attesters**:
   ```powershell
   python knowledge/references/attesters/verify_schema.py --season 2026-27 --gw 2
   python knowledge/references/attesters/verify_solver.py --season 2026-27 --gw 2
   ```
3. **Run Unit Test Suite**:
   ```powershell
   pytest
   ```

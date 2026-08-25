# Next Session Starting Document: Phase 1 & 2 Remediation and Phase 3 Architecture

**Document Type:** Technical Specification & Session Handover  
**Target Date:** 2026-08-25  
**Scope:** Immediate remediation of 4 adversarial findings (Phases 1 & 2) + Architecture for Phase 3 (Fixture & Form Adjustments)

---

## 1. Executive Summary & Session Objectives

In this upcoming session, our work is divided into two sequential milestones:

```
┌────────────────────────────────────────────────────────┐
│  Milestone 1: Fix 4 Adversarial Issues in Phase 1 & 2  │
│  - Shrinkage / 500-min filter (Dowman anomaly)         │
│  - Exact discrete 2+ GC Poisson expectation            │
│  - FBref full-name matching via player_idlist.csv      │
│  - Starter minutes per start scaling                   │
└──────────────────────────┬─────────────────────────────┘
                           │ All 31+ unit tests passing & verified
                           ▼
┌────────────────────────────────────────────────────────┐
│  Milestone 2: Build Phase 3 (Fixture & Form Engine)    │
│  - Opponent attack/defense relative strength ratings   │
│  - Home vs. Away performance multipliers               │
│  - Short-form (6 GW) vs. Long-form blending            │
│  - Output: data/<season>/fixture_predictions.csv       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Technical Specifications: The 4 Remediation Fixes

### Fix 1: Empirical Bayes Prior Shrinkage (The Dowman Fix)
* **Problem**: Players with small sample sizes (e.g. Max Dowman, 152 mins) have extreme raw per-90 rates ($xG90 = 0.7046$), projecting them as the #1 asset in the league ($7.07\text{ xP}$).
* **Root Cause**: Linear application of raw per-90 rates without sample size shrinkage.
* **Mathematical Solution**:
  Apply Bayesian shrinkage toward positional league average priors:
  $$\text{xG90}_{\text{adj}} = \frac{M}{M + M_0} \times \text{xG90}_{\text{raw}} + \frac{M_0}{M + M_0} \times \text{Prior}_{\text{xG}}(\text{POS})$$
  $$\text{xA90}_{\text{adj}} = \frac{M}{M + M_0} \times \text{xA90}_{\text{raw}} + \frac{M_0}{M + M_0} \times \text{Prior}_{\text{xA}}(\text{POS})$$
  $$\text{DC90}_{\text{adj}} = \frac{M}{M + M_0} \times \text{DC90}_{\text{raw}} + \frac{M_0}{M + M_0} \times \text{Prior}_{\text{DC}}(\text{POS})$$
  where:
  - $M = \text{total minutes played in sample}$
  - $M_0 = 500.0\text{ minutes}$ (matching `MODEL.xlsx`'s `Mins Filter = 500`)
  - Positional baseline priors ($\text{Priors}$):
    - **FWD**: $\text{xG90} = 0.35, \text{xA90} = 0.15, \text{DC90} = 2.0$
    - **MID**: $\text{xG90} = 0.15, \text{xA90} = 0.15, \text{DC90} = 4.0$
    - **DEF**: $\text{xG90} = 0.05, \text{xA90} = 0.05, \text{DC90} = 8.0$
    - **GK**: $\text{xG90} = 0.00, \text{xA90} = 0.00, \text{DC90} = 1.0$
* **Expected Result**:
  For Dowman ($M = 152$ mins):
  $$\text{Weight}_{\text{raw}} = \frac{152}{152 + 500} = 23.3\%, \quad \text{Weight}_{\text{prior}} = 76.7\%$$
  $$\text{xG90}_{\text{adj}} = 0.233 \times 0.7046 + 0.767 \times 0.15 = \mathbf{0.279}$$
  His projected $xP$ drops from $7.07$ to an accurate ~**$3.2\text{ xP}$**.

---

### Fix 2: Exact Discrete Expectation for 2+ Goals Conceded Penalty ($C_{10}$)
* **Problem**: $C_{10} = -1.0 \times P(GC \ge 2)$ underestimates penalty in high-xGC games by up to 53% because it ignores $4\text{ GC} = -2\text{ pts}$ and $6\text{ GC} = -3\text{ pts}$.
* **Mathematical Solution**:
  In FPL, a defender/goalkeeper loses 1 point for every 2 goals conceded: $\text{Penalty}(k) = -\lfloor k / 2 \rfloor$.
  The exact mathematical expectation under Poisson($\lambda$) is:
  $$\mathbb{E}[\text{Penalty}] = -\sum_{m=1}^{5} m \times \left( P(X = 2m) + P(X = 2m + 1) \right)$$
* **Python Implementation**:
  ```python
  def poisson_exact_gc_penalty(xgc90: float) -> float:
      """Expected goals conceded penalty under FPL rules (-1 pt per 2 goals)."""
      if xgc90 <= 0.0:
          return 0.0
      total_penalty = 0.0
      for m in range(1, 6):  # accounts for up to 11 goals conceded
          p_2m = poisson_pmf(2 * m, xgc90)
          p_2m_plus_1 = poisson_pmf(2 * m + 1, xgc90)
          total_penalty += m * (p_2m + p_2m_plus_1)
      return -total_penalty
  ```

---

### Fix 3: Robust Full-Name Reconciliation for FBref Data
* **Problem**: Joining FBref on `web_name` failed on 100% of rows because FBref uses full names (`"Erling Haaland"`), while FPL `web_name` is a short surname (`"Haaland"`).
* **Implementation Solution in `model/build_dataset.py`**:
  Reconcile via `player_idlist.csv` (`first_name + ' ' + second_name`) with text normalization:
  ```python
  # Load player_idlist.csv to build a robust Name -> Code mapping
  idlist_path = os.path.join(season_dir, 'player_idlist.csv')
  idlist = pd.read_csv(idlist_path)
  idlist['full_name'] = (idlist['first_name'] + ' ' + idlist['second_name']).str.strip()

  # Match FBref player column to full_name
  fbref_df = load_fbref_summary(season, data_root)
  fbref_merged = fbref_df.merge(idlist[['id', 'full_name']], left_on='player', right_on='full_name', how='inner')
  ```

---

### Fix 4: Starter Minutes Proration in Active Ratio
* **Problem**: Starters substituted early (e.g. 60–70 mins) were modeled as playing a full 90 minutes ($active\_ratio = 1.0$), over-predicting attacking returns by up to 38%.
* **Mathematical Solution**:
  Scale the starter component by average minutes per start:
  $$\text{mins\_per\_start} = \min\left(90.0, \max\left(45.0, \frac{\text{Total Minutes}}{\text{Starts}}\right)\right) \quad (\text{default } 90.0\text{ for GK})$$
  $$\text{active\_ratio} = P(\text{Start}) \times \frac{\text{mins\_per\_start}}{90.0} + P(\text{Sub}) \times \frac{20.0}{90.0}$$

---

## 3. Phase 3 Architecture: Fixture & Form Adjustment Engine

### Component 1: Opponent Strength Relative Multipliers
Each fixture involves Team $A$ (attacking) vs. Team $B$ (defending). We compute relative strength ratios compared to the league average:
$$\text{League\_Avg\_xG} = \frac{1}{20}\sum_{t=1}^{20} \text{Team\_xG90}_t \approx 1.35$$
$$\text{League\_Avg\_xGC} = \frac{1}{20}\sum_{t=1}^{20} \text{Team\_xGC90}_t \approx 1.35$$

1. **Attacking Multiplier for Team $A$ against Team $B$**:
   $$\text{Attack\_Mult}(A \text{ vs } B) = \frac{\text{Team\_xG90}_A}{\text{League\_Avg\_xG}} \times \frac{\text{Team\_xGC90}_B}{\text{League\_Avg\_xGC}}$$

2. **Defensive Conceding Multiplier for Team $A$ against Team $B$**:
   $$\text{Defense\_xGC}(A \text{ vs } B) = \text{Team\_xGC90}_A \times \frac{\text{Team\_xG90}_B}{\text{League\_Avg\_xG}}$$

---

### Component 2: Home vs. Away Multipliers
Statistical analysis of Premier League historical data indicates consistent home advantage:
- **Home Advantage**: $+8\%$ attacking output, $-10\%$ goals conceded.
  $$\text{Home\_Attack\_Factor} = 1.08, \quad \text{Home\_Defense\_Factor} = 0.90$$
- **Away Disadvantage**: $-8\%$ attacking output, $+10\%$ goals conceded.
  $$\text{Away\_Attack\_Factor} = 0.92, \quad \text{Away\_Defense\_Factor} = 1.10$$

---

### Component 3: Form Blending Formula
Combine short-form (last 6 gameweeks) and long-form (season-to-date + prior season) using a configurable form weight $\alpha \in [0, 1]$ (default $\alpha = 0.35$):
$$\text{Blended Rate} = \alpha \times \text{ShortForm Rate} + (1 - \alpha) \times \text{LongForm Rate}$$

---

## 4. Execution Plan for Next Session

| Step | Action | Target File | Validation |
|---|---|---|---|
| **1** | Apply Prior Shrinkage & Mins Filter | `model/prediction_engine.py` | Verify Dowman drops from 7.07 to ~3.2 xP |
| **2** | Implement Discrete $C_{10}$ Expectation | `model/prediction_engine.py` | Test on high-xGC defenses |
| **3** | Update Starter Minutes Proration | `model/prediction_engine.py` | Verify rotation players scaled accurately |
| **4** | Fix FBref Reconciliation via `player_idlist` | `model/build_dataset.py` | Verify non-zero sub counts in dataset |
| **5** | Run Regression Tests | `model/test_*.py` | Ensure all 31+ unit tests pass |
| **6** | Implement Phase 3 Fixture Engine | `model/fixture_engine.py` | Verify Home/Away & FDR multipliers |
| **7** | Generate Fixture-Adjusted $xP$ | `data/<season>/fixture_predictions.csv` | Verify upcoming gameweek predictions |

# Phase 2 Design: FPL Point-Prediction Engine

Status: proposed, awaiting review  
Date: 2026-08-24  
Phase: 2 of 5 (Data pipeline → **Point-prediction engine** → Fixture/form adjustment → Squad solver → Excel write-back)

---

## 1. Problem Statement

In the original Excel workbook (`MODEL.xlsx` / `SIMPLE MODEL.xlsx`), predicting a player's points per gameweek requires evaluating over 180 columns of interconnected formulas across 23 sheets. While the statistical mathematics is sound, the Excel implementation suffers from:
1. **Scattered formulas**: Appearance probabilities, Poisson clean sheet distributions, and bonus point regressions are split across complex `INDEX(MATCH())` expressions and volatile named ranges.
2. **Performance bottlenecks**: Calculating predictions for 800+ players across 38 gameweeks locks Excel for minutes.
3. **Fragility**: Edge cases (zero minutes, non-standard minutes for new transfers, division by zero) rely on chained `IFERROR` statements that mask genuine data errors.

Phase 1 successfully unified data extraction into `data/<season>/model_dataset.csv`. Phase 2 translates the mathematical formulas into a clean, fast, vectorized Python engine under `model/prediction_engine.py`.

---

## 2. Goals & Non-Goals

### Goals
- Implement a pure Python function `predict_player_points(player_row, opponent_row=None, params=None) -> PredictionBreakdown` that computes expected points ($xP$) broken down into its 11 component terms.
- Support vectorized computation over the entire player DataFrame (`predict_all_players(df, fixtures_df=None) -> pd.DataFrame`).
- Provide clean mathematical implementations of:
  - **Playing Time & Starting Probability** ($P(\text{appearance})$, $P(60+\text{ mins})$).
  - **Attacking Returns** (Position-weighted Goals from $xG$, Assists from $xA$).
  - **Defensive Returns** (Poisson Clean Sheet $P(GC=0)$, 2+ Goals Conceded penalty $P(GC \ge 2)$).
  - **Defensive Contributions** (Poisson cumulative probability of hitting DC thresholds).
  - **Bonus & Card Penalties** (BPS/Bonus rate estimation, Yellow/Red card rates).
- Provide automated unit tests verifying that calculated outputs match hand-checked Excel calculations for known player profiles (starters, rotation players, goalkeepers, zero-minute players).

### Non-Goals (Scope for Later Phases)
- **Opponent fixture difficulty multipliers & home/away adjustments** (Phase 3).
- **Squad optimization and transfer planning** (Phase 4).
- **Writing back results to `.xlsx` files** (Phase 5).

---

## 3. Mathematical Formulation (The 11 Components)

Each player's Expected Points ($xP$) for a fixture is the sum of 11 distinct components:
$$xP = \sum_{k=1}^{11} C_k$$

### Component 1 ($C_1$): 1–60 Minutes Appearance
- **Points**: 1 point.
- **Probability**: $P(\text{App}) = P(\text{Start}) + (1 - P(\text{Start})) \times P(\text{Sub})$.
- **Formula**: $C_1 = 1 \times P(\text{App})$.

### Component 2 ($C_2$): 60+ Minutes Appearance
- **Points**: 1 additional point.
- **Probability**: $P(60+) = P(\text{Start}) \times P(\text{Plays } 60+ \mid \text{Start})$.
  - For Goalkeepers: $P(\text{Plays } 60+ \mid \text{Start}) \approx 0.99$.
  - For Outfield Players: estimated from average minutes per start:
    $$\text{minutes\_ratio} = \min(1.0, \frac{\text{Minutes per Start}}{90})$$
- **Formula**: $C_2 = 1 \times P(60+)$.

### Component 3 ($C_3$): Goalkeeper Saves
- **Points**: 1 point per 3 saves.
- **Applies to**: GK only (0 for DEF, MID, FWD).
- **Formula**: $C_3 = \frac{\text{Saves90}}{3.0} \times P(\text{Start})$.

### Component 4 ($C_4$): Yellow Cards
- **Points**: $-1$ point.
- **Formula**: $C_4 = -1 \times \text{YC90} \times P(\text{App})$.

### Component 5 ($C_5$): Red Cards
- **Points**: $-3$ points.
- **Formula**: $C_5 = -3 \times \text{RC90} \times P(\text{App})$.

### Component 6 ($C_6$): Bonus Points
- **Points**: Estimated expected bonus points (0 to 3).
- **Formula**: $C_6 = \text{Bonus90} \times P(\text{Start})$.

### Component 7 ($C_7$): Assists
- **Points**: 3 points (all positions).
- **Formula**: $C_7 = 3 \times xA90 \times \left( P(\text{Start}) + P(\text{Sub}) \times \frac{\text{Minutes per Sub}}{90} \right)$.

### Component 8 ($C_8$): Goals
- **Points**: Position-dependent ($GK=6, DEF=6, MID=5, FWD=4$).
- **Formula**: $C_8 = \text{Goal\_Pts}(\text{POS}) \times xG90 \times \left( P(\text{Start}) + P(\text{Sub}) \times \frac{\text{Minutes per Sub}}{90} \right)$.

### Component 9 ($C_9$): Clean Sheets
- **Points**: Position-dependent ($GK=4, DEF=4, MID=1, FWD=0$).
- **Probability**: Poisson distribution for 0 goals conceded:
  $$P(\text{CS}) = e^{-\text{Team\_xGC90}}$$
- **Formula**: $C_9 = \text{CS\_Pts}(\text{POS}) \times P(\text{CS}) \times P(60+)$.

### Component 10 ($C_{10}$): 2+ Goals Conceded Penalty
- **Points**: $-1$ point per 2 goals conceded.
- **Applies to**: GK and DEF only (0 for MID, FWD).
- **Probability**:
  $$P(\text{GC} \ge 2) = 1 - e^{-\text{Team\_xGC90}} - \text{Team\_xGC90} \times e^{-\text{Team\_xGC90}}$$
- **Formula**: $C_{10} = -1 \times P(\text{GC} \ge 2) \times P(60+)$.

### Component 11 ($C_{11}$): Defensive Contributions (DC)
- **Points**: 2 points for reaching the DC threshold.
- **Threshold**: 9 for DEF; 11 for MID/FWD/GK.
- **Probability**:
  $$P(\text{DC} \ge T) = 1 - \text{Poisson\_CDF}(T - 1, \lambda = \text{DC90})$$
- **Formula**: $C_{11} = 2 \times P(\text{DC} \ge T) \times P(\text{Start})$.

---

## 4. Architecture & Module Design

```
model_dataset.csv (from Phase 1)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│               model/prediction_engine.py               │
│                                                        │
│  - calculate_appearance_probs(df)                     │
│  - calculate_attacking_points(df)                      │
│  - calculate_defensive_points(df)                      │
│  - calculate_dc_bonus_points(df)                       │
│  - predict_player_points(row) -> PredictionBreakdown   │
│  - predict_all_players(df) -> pd.DataFrame             │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
              data/<season>/predictions.csv
```

---

## 5. Testing & Verification Plan

1. **`model/test_prediction_engine.py`**:
   - **Haaland (Elite Forward)**: verify attacking points dominate $xP$, clean sheets give 0, starting probability is ~0.95+.
   - **Gabriel / Saliba (Elite Defenders)**: verify clean sheet points and DC bonus contribute heavily to $xP$, goals give 6 pts per xG.
   - **David Raya (Goalkeeper)**: verify save points, clean sheets ($4 \times e^{-\lambda}$), and 2+ GC penalties.
   - **Inactive / Reserve Player (Zero Minutes)**: verify all components cleanly evaluate to 0.0 with no `NaN` or divide-by-zero exceptions.
   - **Vectorized vs Row-by-Row consistency**: assert `predict_all_players(df)` produces identical values to applying `predict_player_points` per row.

---

## 6. Rollout

- Add `model/prediction_engine.py`.
- Add `model/test_prediction_engine.py`.
- Update `JOURNEY.md` with Phase 2 documentation.

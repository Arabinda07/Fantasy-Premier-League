# M-03 Design Spec: Exponential Recency Decay (EWMA) in Rolling Form

**Document Type:** Design Specification  
**Topic:** M-03 Rolling Form Recency Weighting  
**Author:** AI Agent (Antigravity)  
**Date:** 2026-09-04  
**Status:** Approved & Implementing  

---

## 1. Problem Statement & Motivation

In the current rolling form implementation ([`model/rolling_form.py`](file:///e:/Fantasy-Premier-League/model/rolling_form.py)), player and team rates are aggregated with equal flat weights ($w = 1.0$) across historical gameweeks:
1. **Multi-Season Long-Form Distortion**:
   The long-form window (`window_gws=None`) reaches across the current season and the full prior season (up to 76 gameweeks). A match played 18 months ago receives the exact same statistical weight as a match played 4 days ago. In real-world football, tactical shifts, player ageing, role adjustments, and team form change substantially over multi-month horizons.
2. **Fixed-Window Cliff Edges**:
   The short-form window (e.g. 6 gameweeks) applies a hard cutoff: a fixture at GW $t - 6$ has weight $1.0$, while a fixture at GW $t - 7$ abruptly drops to weight $0.0$. This introduces artificial volatility into predicted per-90 rates.

---

## 2. Mathematical Formulation

To eliminate cliff edges and weight recent tactical form continuously, we introduce an **Exponentially Weighted Moving Average (EWMA)** decay with a half-life of $t_{1/2} = 8.0\text{ gameweeks}$.

### 2.1 Elapsed Gameweek Distance ($\Delta t$)

Given evaluation season $S_{\text{eval}}$ and gameweek $GW_{\text{eval}}$, for any match in season $S_i$ and gameweek $GW_i$:
$$\Delta t_i = \begin{cases}
GW_{\text{eval}} - GW_i & \text{if } S_i == S_{\text{eval}} \\
GW_{\text{eval}} + (38 - GW_i) & \text{if } S_i \text{ is prior season } (S_{\text{eval}} - 1) \\
GW_{\text{eval}} + 38 \cdot k + (38 - GW_i) & \text{if } S_i \text{ is } k+1 \text{ seasons prior}
\end{cases}$$

### 2.2 Exponential Decay Weight ($w_i$)

With half-life $t_{1/2} = 8.0$ gameweeks:
$$\lambda = \frac{\ln(2)}{t_{1/2}} \approx 0.08664339756$$
$$w_i = \exp(-\lambda \cdot \Delta t_i) = 2^{-\frac{\Delta t_i}{t_{1/2}}}$$

#### Properties:
- $\Delta t = 0$ (Current Gameweek): $w = 2^0 = 1.000$ (100% weight)
- $\Delta t = 4$ (1 month ago): $w = 2^{-0.5} \approx 0.707$ (70.7% weight)
- $\Delta t = 8$ (Half-life): $w = 2^{-1.0} = 0.500$ (50.0% weight)
- $\Delta t = 16$ (Two half-lives): $w = 2^{-2.0} = 0.250$ (25.0% weight)
- $\Delta t = 38$ (1 season ago): $w = 2^{-4.75} \approx 0.0372$ (~3.7% weight)
- $\Delta t = 76$ (2 seasons ago): $w = 2^{-9.5} \approx 0.0014$ (~0.14% weight)

### 2.3 Weighted Metrics & Per-90 Rate Derivation

For each player (grouped by cross-season stable `code`):
1. **Weighted Effective Minutes**:
   $$M_{\text{weighted}} = \sum_i w_i \cdot m_i$$
2. **Weighted Metric Accumulation**:
   For any volume metric $c \in \{\text{xG}, \text{xA}, \text{xGC}, \text{DC}, \text{bonus}, \text{bps}\}$:
   $$X_{c, \text{weighted}} = \sum_i w_i \cdot x_{i, c}$$
3. **Decayed Per-90 Rate**:
   $$\text{rate}_{c, 90} = \begin{cases}
   \frac{X_{c, \text{weighted}}}{M_{\text{weighted}} / 90.0} = 90.0 \cdot \frac{\sum_i w_i x_{i, c}}{\sum_i w_i m_i} & \text{if } M_{\text{weighted}} > 0 \\
   0.0 & \text{otherwise}
   \end{cases}$$

### 2.4 Team-Level Form Derivation

Similarly for team-level expected goals ($xG$) and expected goals conceded ($xGC$):
$$\text{team\_xG}_{\text{weighted}} = \sum_{\text{match } j} w_j \cdot \text{team\_xG}_j$$
$$\text{team\_xGC}_{\text{weighted}} = \sum_{\text{match } j} w_j \cdot \text{team\_xGC}_j$$
$$\text{team\_matches}_{\text{weighted}} = \sum_{\text{match } j} w_j$$
$$\text{team\_minutes}_{\text{weighted}} = 90.0 \cdot \text{team\_matches}_{\text{weighted}}$$
$$\text{team\_xG90} = \frac{\text{team\_xG}_{\text{weighted}}}{\text{team\_matches}_{\text{weighted}}}$$
$$\text{team\_xGC90} = \frac{\text{team\_xGC}_{\text{weighted}}}{\text{team\_matches}_{\text{weighted}}}$$

---

## 3. Architecture & Interface Design

### 3.1 Function Signatures in `model/rolling_form.py`

- `compute_player_form(season: str, gw: int, window_gws: Optional[int] = None, half_life: Optional[float] = 8.0, data_root: str = 'data') -> pd.DataFrame`
  - If `half_life` is passed (default $8.0$), applies exponential recency decay weights $w_i$.
  - If `half_life is None`, applies flat $w_i = 1.0$, guaranteeing exact backwards compatibility with all Phase 1 tests.
  - Returns `minutes` as weighted effective minutes, and includes `unweighted_minutes` as an informational diagnostic column.
- `compute_team_form(season: str, gw: int, window_gws: Optional[int] = None, half_life: Optional[float] = 8.0, data_root: str = 'data') -> pd.DataFrame`
  - Supports `half_life: Optional[float] = 8.0`.
- `build_player_form_dataset(season: str, gw: int, short_form_window: int = 6, half_life_long: Optional[float] = 8.0, half_life_short: Optional[float] = None, data_root: str = 'data') -> pd.DataFrame`
  - Applies $t_{1/2} = 8.0$ for long-form baseline rates, while allowing short-form to either use flat 6-GW window or decayed weighting.
- `build_team_form_dataset(...)`
  - Parallels player dataset with `half_life_long: Optional[float] = 8.0`.

---

## 4. Testing & Verification Plan

1. **Unit Tests (`model/test_ewma_form.py`)**:
   - Verify exact half-life decay: $w(\Delta t = 8) = 0.500$.
   - Verify lag calculation across season boundaries (GW38 of previous season to GW2 of current season).
   - Verify recency bias: an identical performance in GW10 carries strictly higher rate influence than in GW1.
   - Verify backwards compatibility: `half_life=None` yields identical results to flat summation.
2. **Regression Tests**:
   - `model/test_rolling_form.py`: all 13 tests must continue passing.
   - `model/test_minutes_integration.py` & `model/test_prediction_engine.py`: all pass without regressions.

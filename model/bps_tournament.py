"""Order-Statistic Tournament Modeling for BPS & Bonus Points (C6).

Under official Fantasy Premier League (FPL) rules, bonus points are a strictly
zero-sum match competition:
- Exactly 6 bonus points (3 for 1st, 2 for 2nd, 1 for 3rd) are distributed per fixture.
- Ties expand this slightly, yielding an empirical league average of ~6.15 bonus points per match.

This module replaces independent player-level bonus products with an exact
Plackett-Luce Order-Statistic Tournament that enforces fixture bonus conservation:
    sum_{i in Match} E[Bonus_i] == 6.0 * kappa_tie ~= 6.15
"""
import math
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from model.prediction_engine import _safe_float

# Empirical parameters
DEFAULT_BPS_TEMPERATURE: float = 6.0  # Softmax temperature tau for BPS ranking
DEFAULT_TIE_INFLATION: float = 1.025   # Empirical +2.5% bonus pool expansion from tied BPS
MIN_PARTICIPATION_PROB: float = 0.05   # Minimum P(App) to enter tournament


def compute_player_bps_propensity(player_pred: Dict[str, Any]) -> float:
    """Compute latent expected BPS score (theta_i) for a player in a specific fixture.

    Decomposes BPS from:
    1. Base playing time: +6 BPS for 60+ mins, +3 BPS for 1-59 mins.
    2. Base open-play rate (bps90) prorated by expected playing time.
    3. Attacking returns: Goals (+24 FWD, +18 MID, +12 DEF/GK), Assists (+9).
    4. Defensive returns: Clean sheets (+12 GK/DEF), Saves (+2 per save for GK),
       Defensive contributions (+1 per DC for DEF/MID), and GC penalty (-4 for 2+ GC).
    5. Disciplinary deductions: -3 for Yellow Card, -9 for Red Card.

    Args:
        player_pred: dict containing player fixture predictions and component breakdowns.

    Returns:
        Expected BPS score float (theta_i >= 0.0).
    """
    pos = str(player_pred.get('position', 'MID')).upper()
    p_app = _safe_float(player_pred.get('p_app', 0.0))
    p_60 = _safe_float(player_pred.get('p_60_plus', 0.0))

    if p_app <= 0.0:
        return 0.0

    # 1. Base appearance BPS: 6 for 60+ mins, 3 for 1-59 mins
    p_1_to_59 = max(0.0, p_app - p_60)
    bps_app = (6.0 * p_60) + (3.0 * p_1_to_59)

    # 2. Base open-play baseline rate (passing, tackles, open play action)
    # Under FPL rules, CBI, passes, dribbles, etc. generate ~6-12 BPS per 90.
    pos_open_play_bps90 = {
        'GK': 6.0,
        'DEF': 10.0,
        'MID': 12.0,
        'FWD': 8.0,
    }
    exp_mins = _safe_float(player_pred.get('expected_minutes', p_app * 75.0))
    # If historical bps_90 is provided, net out historical goal/assist/appearance contribution
    # to avoid double-counting attacking returns in the tournament propensity.
    raw_bps90 = _safe_float(player_pred.get('long_form_bps_90', player_pred.get('bps_90', 0.0)))
    if raw_bps90 > 0.0:
        hist_xg = _safe_float(player_pred.get('long_form_expected_goals_90', player_pred.get('xg_90', 0.0)))
        hist_xa = _safe_float(player_pred.get('long_form_expected_assists_90', player_pred.get('xa_90', 0.0)))
        goal_bps_val = {'FWD': 24.0, 'MID': 18.0, 'DEF': 12.0, 'GK': 12.0}.get(pos, 18.0)
        net_open_play = raw_bps90 - (hist_xg * goal_bps_val) - (hist_xa * 9.0) - 6.0
        open_play_bps90 = min(22.0, max(4.0, net_open_play))
    else:
        open_play_bps90 = pos_open_play_bps90.get(pos, 10.0)

    bps_open_play = open_play_bps90 * (exp_mins / 90.0)

    # 3. Attacking returns
    # Goals: FWD +24, MID +18, DEF/GK +12
    c8_goals = _safe_float(player_pred.get('c8_goals', 0.0))
    goal_multiplier = {'FWD': 24.0 / 4.0, 'MID': 18.0 / 5.0, 'DEF': 12.0 / 6.0, 'GK': 12.0 / 6.0}.get(pos, 4.0)
    bps_goals = c8_goals * goal_multiplier

    # Assists: +9 BPS per assist (c7 is 3.0 pts per assist)
    c7_assists = _safe_float(player_pred.get('c7_assists', 0.0))
    bps_assists = (c7_assists / 3.0) * 9.0

    # 4. Defensive returns
    bps_defense = 0.0
    if pos in ('GK', 'DEF'):
        # Clean Sheet: +12 BPS (c9 is 4.0 pts for GK/DEF)
        c9_cs = _safe_float(player_pred.get('c9_clean_sheets', 0.0))
        bps_defense += (c9_cs / 4.0) * 12.0

        # Goals Conceded deduction: -4 BPS for 2+ goals conceded
        c10_gc = _safe_float(player_pred.get('c10_goals_conceded', 0.0))
        # c10 is negative expectation of points lost (1 pt per 2 GC)
        bps_defense += c10_gc * 4.0

    # Saves for GK: +2 BPS per save (c3 is 1 pt per 3 saves, so saves = c3 * 3)
    if pos == 'GK':
        c3_saves = _safe_float(player_pred.get('c3_saves', 0.0))
        bps_defense += (c3_saves * 3.0) * 2.0

    # Defensive contributions (C11): +1 BPS per DC
    c11_dc = _safe_float(player_pred.get('c11_defensive_contributions', 0.0))
    bps_defense += c11_dc * 6.0

    # 5. Disciplinary deductions (-3 YC, -9 RC)
    c4_yc = _safe_float(player_pred.get('c4_yellow_cards', 0.0))
    c5_rc = _safe_float(player_pred.get('c5_red_cards', 0.0))
    bps_discipline = (c4_yc * 3.0) + (c5_rc * 3.0)  # c4 and c5 are already negative

    total_bps = bps_app + bps_open_play + bps_goals + bps_assists + bps_defense + bps_discipline
    return float(max(1.0, total_bps))


def solve_plackett_luce_tournament(
    players: List[Dict[str, Any]],
    tau: float = DEFAULT_BPS_TEMPERATURE,
    tie_inflation: float = DEFAULT_TIE_INFLATION,
) -> Dict[int, float]:
    """Solve Plackett-Luce ranking tournament across all active players in a match.

    Evaluates:
        P_1(i): Probability player i finishes 1st in match BPS (awards 3 pts)
        P_2(i): Probability player i finishes 2nd in match BPS (awards 2 pts)
        P_3(i): Probability player i finishes 3rd in match BPS (awards 1 pt)

    Guarantees exact mathematical conservation:
        sum_i E[Bonus_i] == (3*1 + 2*1 + 1*1) * tie_inflation == 6.0 * tie_inflation ~= 6.15

    Args:
        players: list of player dicts participating in the match.
        tau: softmax temperature parameter (default 6.0).
        tie_inflation: empirical factor for BPS tie expansion (default 1.025).

    Returns:
        Dict mapping player_code to expected bonus points float.
    """
    if not players:
        return {}

    # Filter players with meaningful appearance probability
    active_players = []
    for p in players:
        p_app = _safe_float(p.get('p_app', 0.0))
        if p_app >= MIN_PARTICIPATION_PROB:
            active_players.append(p)

    if not active_players:
        return {int(p.get('player_code', 0)): 0.0 for p in players}

    codes = [int(p.get('player_code', 0)) for p in active_players]
    n = len(active_players)

    # Compute latent BPS propensity scores
    thetas = np.array([compute_player_bps_propensity(p) for p in active_players], dtype=np.float64)
    p_apps = np.array([_safe_float(p.get('p_app', 0.85)) for p in active_players], dtype=np.float64)

    # Numerically stable softmax weights s_i = exp((theta_i - max_theta) / tau) * P(App)
    max_theta = np.max(thetas)
    # Shift relative to max_theta for float stability
    scaled_scores = (thetas - max_theta) / max(0.5, tau)
    s = np.exp(scaled_scores) * p_apps
    s = np.maximum(s, 1e-12)

    sum_s = float(np.sum(s))
    if sum_s <= 0 or not np.isfinite(sum_s):
        equal_bonus = (6.0 * tie_inflation) / n
        return {code: round(equal_bonus, 4) for code in codes}

    # 1. P_1(i) = s_i / sum_s
    p1 = s / sum_s

    # 2. P_2(i) = sum_{j != i} P_1(j) * (s_i / (sum_s - s_j))
    # Closed-form O(N):
    # term_j = s_j / (sum_s * (sum_s - s_j))
    # T1 = sum_{all j} term_j
    # P_2(i) = s_i * (T1 - term_i)
    term = s / (sum_s * np.maximum(1e-12, sum_s - s))
    t1 = float(np.sum(term))
    p2 = s * (t1 - term)
    p2 = np.maximum(0.0, p2)
    # Renormalize p2 to sum to 1.0 (guard against edge numerical float precision)
    sum_p2 = np.sum(p2)
    if sum_p2 > 0:
        p2 = p2 / sum_p2

    # 3. P_3(i) = sum_{j != i} sum_{k != i, j} P_1(j) * (s_k / (sum_s - s_j)) * (s_i / (sum_s - s_j - s_k))
    # Vectorized / O(N^2) evaluation (n <= 35 players, very fast <1ms):
    p3 = np.zeros(n, dtype=np.float64)
    for j in range(n):
        s_j = s[j]
        denom_j = max(1e-12, sum_s - s_j)
        p1_j = s_j / sum_s

        # Remaining players excluding j
        for k in range(n):
            if k == j:
                continue
            s_k = s[k]
            denom_jk = max(1e-12, denom_j - s_k)
            prob_jk = p1_j * (s_k / denom_j)

            # Distribute to all i not in {j, k}
            # For vectorization across all remaining i:
            coeff = prob_jk / denom_jk
            p3 += coeff * s
            # Zero out contributions to j and k
            p3[j] -= coeff * s[j]
            p3[k] -= coeff * s[k]

    p3 = np.maximum(0.0, p3)
    sum_p3 = np.sum(p3)
    if sum_p3 > 0:
        p3 = p3 / sum_p3

    # 4. Expected Bonus Points
    # E[Bonus_i] = (3 * P1 + 2 * P2 + 1 * P3) * tie_inflation
    expected_bonus = tie_inflation * (3.0 * p1 + 2.0 * p2 + 1.0 * p3)

    bonus_map: Dict[int, float] = {}
    for code, b in zip(codes, expected_bonus):
        bonus_map[code] = round(float(b), 4)

    # Inactive players receive 0.0
    for p in players:
        p_code = int(p.get('player_code', 0))
        if p_code not in bonus_map:
            bonus_map[p_code] = 0.0

    return bonus_map


def calibrate_fixture_bonus_points(
    predictions_df: pd.DataFrame,
    fixtures: List[Dict[str, Any]],
    tau: float = DEFAULT_BPS_TEMPERATURE,
    tie_inflation: float = DEFAULT_TIE_INFLATION,
) -> pd.DataFrame:
    """Run Plackett-Luce Order-Statistic Tournament across all fixtures in a gameweek.

    Updates 'c6_bonus' to the fixture-conserved expected bonus and adjusts
    'expected_points' to maintain exact accounting:
        xP_new = xP_old - c6_old + c6_new

    Args:
        predictions_df: DataFrame of player predictions from predict_gameweek_fixtures.
        fixtures: list of fixture dicts for the gameweek.
        tau: tournament softmax temperature.
        tie_inflation: tie expansion factor.

    Returns:
        DataFrame with calibrated c6_bonus and expected_points.
    """
    if predictions_df.empty or not fixtures:
        return predictions_df

    out_df = predictions_df.copy()

    # Create team to fixture map
    # A fixture has home_team, away_team
    fixture_matches: List[Tuple[str, str]] = []
    for fix in fixtures:
        h = fix.get('home_team')
        a = fix.get('away_team')
        if h and a:
            fixture_matches.append((h, a))

    calibrated_c6: Dict[int, float] = {}

    # Run tournament for each fixture matchup
    for home_team, away_team in fixture_matches:
        # Match players belonging to either home or away team in this fixture
        # Supports both single fixture ('Chelsea') and DGW multi-fixture ('Chelsea, Wolves')
        match_mask = (
            ((out_df['team'] == home_team) & out_df['fixture_opponent'].astype(str).str.contains(away_team, regex=False, na=False)) |
            ((out_df['team'] == away_team) & out_df['fixture_opponent'].astype(str).str.contains(home_team, regex=False, na=False))
        )
        match_players_df = out_df[match_mask]
        if match_players_df.empty:
            continue

        match_records = []
        for r in match_players_df.to_dict('records'):
            rec = dict(r)
            f_count = max(1, int(_safe_float(rec.get('fixture_count', 1))))
            if f_count > 1:
                # Prorate cumulative DGW stats to single match representation
                for c in ['c3_saves', 'c4_yellow_cards', 'c5_red_cards', 'c7_assists', 'c8_goals',
                          'c9_clean_sheets', 'c10_goals_conceded', 'c11_defensive_contributions']:
                    if c in rec:
                        rec[c] = _safe_float(rec[c]) / f_count
                if _safe_float(rec.get('p_app', 0.0)) > 1.0:
                    rec['p_app'] = min(1.0, _safe_float(rec['p_app']) / f_count)
                if _safe_float(rec.get('p_60_plus', 0.0)) > 1.0:
                    rec['p_60_plus'] = min(1.0, _safe_float(rec['p_60_plus']) / f_count)
            match_records.append(rec)

        match_bonus_map = solve_plackett_luce_tournament(
            match_records,
            tau=tau,
            tie_inflation=tie_inflation,
        )
        for code, b in match_bonus_map.items():
            calibrated_c6[code] = round(calibrated_c6.get(code, 0.0) + b, 4)

    # Apply calibrated bonus and update expected_points
    if calibrated_c6:
        def update_row(r):
            p_code = int(r.get('player_code', 0))
            if p_code in calibrated_c6:
                new_c6 = calibrated_c6[p_code]
                old_c6 = _safe_float(r.get('c6_bonus', 0.0))
                old_xp = _safe_float(r.get('expected_points', 0.0))
                new_xp = round(old_xp - old_c6 + new_c6, 4)
                r['c6_bonus'] = new_c6
                r['expected_points'] = new_xp
            return r

        out_df = out_df.apply(update_row, axis=1)

    return out_df

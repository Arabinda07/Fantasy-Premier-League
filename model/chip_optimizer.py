"""FPL Strategic Chip Timing Optimizer.

Evaluates schedule structure across all 38 gameweeks to recommend optimal deployment windows for:
- ⚡ Triple Captain (3xC): Target peak DGW for talisman assets (e.g. Haaland/Salah double home fixture).
- 🚀 Bench Boost (BB): Target peak DGW where 15 players have active fixtures.
- 🆓 Free Hit (FH): Target severe Blank Gameweeks (BGWs) with 4+ blanking teams.
- 🃏 Wildcard 1 (GW2-GW19) & Wildcard 2 (GW20-GW38): Structural squad reset before major fixture swings.

Usage:
    python -m model.chip_optimizer [--season 2026-27] [--gw 1]
"""
import argparse
from dataclasses import dataclass
import math
import os
import sys
from typing import Dict, Any, List, Tuple, Optional, Set
import pandas as pd
import numpy as np

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.fixture_engine import load_fixtures_for_gw


@dataclass
class GameweekScheduleProfile:
    """Gameweek schedule profile summarizing fixture density and blanks."""
    gw: int
    total_fixtures: int
    dgw_teams: List[str]
    bgw_teams: List[str]
    is_dgw: bool
    is_bgw: bool


@dataclass
class ChipRecommendation:
    """Specific chip recommendation with target gameweek and expected delta."""
    chip: str
    target_gw: int
    expected_value_delta: float
    rationale: str
    backup_gw: Optional[int] = None
    is_active_now: bool = False
    distress_score: float = 0.0
    urgent_reason: Optional[str] = None
    delta_npv: Optional[float] = None
    trapped_bench_capital: float = 0.0
    harvest_advisory: Optional[str] = None


@dataclass
class SeasonalChipPlan:
    """Complete seasonal roadmap for all FPL chips."""
    season: str
    current_gw: int
    recommendations: Dict[str, ChipRecommendation]
    schedule_profiles: List[GameweekScheduleProfile]


def detect_double_and_blank_gameweeks(
    season: str = '2026-27',
    data_root: str = 'data',
) -> List[GameweekScheduleProfile]:
    """Scan season fixtures to identify Double and Blank Gameweeks across all 38 GWs."""
    season_dir = os.path.join(data_root, season)
    fixtures_file = os.path.join(season_dir, 'fixtures.csv')
    teams_file = os.path.join(season_dir, 'teams.csv')

    all_teams: List[str] = []
    if os.path.exists(teams_file):
        t_df = pd.read_csv(teams_file)
        name_col = 'name' if 'name' in t_df.columns else ('team' if 'team' in t_df.columns else 'short_name')
        all_teams = t_df[name_col].tolist()

    if not os.path.exists(fixtures_file):
        # Default 38 standard gameweeks
        return [
            GameweekScheduleProfile(gw=g, total_fixtures=10, dgw_teams=[], bgw_teams=[], is_dgw=False, is_bgw=False)
            for g in range(1, 39)
        ]

    f_df = pd.read_csv(fixtures_file)
    event_col = 'event' if 'event' in f_df.columns else 'GW'
    team_h_col = 'team_h' if 'team_h' in f_df.columns else 'home_team'
    team_a_col = 'team_a' if 'team_a' in f_df.columns else 'away_team'

    profiles: List[GameweekScheduleProfile] = []

    # Map team IDs if integer
    team_id_map: Dict[int, str] = {}
    if os.path.exists(teams_file):
        t_df = pd.read_csv(teams_file)
        if 'id' in t_df.columns and 'name' in t_df.columns:
            team_id_map = dict(zip(t_df['id'], t_df['name']))

    for gw in range(1, 39):
        gw_fix = f_df[f_df[event_col] == gw]
        n_fix = len(gw_fix)

        team_counts: Dict[str, int] = {}
        for _, row in gw_fix.iterrows():
            h_raw = row.get(team_h_col)
            a_raw = row.get(team_a_col)

            h_name = team_id_map.get(int(h_raw), str(h_raw)) if isinstance(h_raw, (int, float)) and int(h_raw) in team_id_map else str(h_raw)
            a_name = team_id_map.get(int(a_raw), str(a_raw)) if isinstance(a_raw, (int, float)) and int(a_raw) in team_id_map else str(a_raw)

            team_counts[h_name] = team_counts.get(h_name, 0) + 1
            team_counts[a_name] = team_counts.get(a_name, 0) + 1

        dgw_teams = [t for t, cnt in team_counts.items() if cnt >= 2]
        bgw_teams = [t for t in all_teams if t not in team_counts or team_counts[t] == 0] if all_teams else []

        profiles.append(GameweekScheduleProfile(
            gw=gw,
            total_fixtures=n_fix,
            dgw_teams=dgw_teams,
            bgw_teams=bgw_teams,
            is_dgw=len(dgw_teams) > 0 or n_fix > 10,
            is_bgw=len(bgw_teams) > 0 or n_fix < 10,
        ))

    return profiles


def _build_constrained_optimal_xi(
    df: pd.DataFrame,
    budget_limit: float = 100.0,
    p_code_col: str = 'player_code',
) -> Tuple[float, float]:
    """Computes a realistic, legally constrained starting XI xP baseline.

    Enforces:
    - Exactly 1 GK
    - 3 to 5 DEF
    - 2 to 5 MID
    - 1 to 3 FWD
    - Total starters = 11
    - Max 3 players per club
    - Outfield starter budget constraint (~83% of total budget)
    """
    if df.empty or 'expected_points' not in df.columns:
        return 0.0, 0.0

    valid_df = df.copy()
    valid_df['cost'] = valid_df.get('now_cost', valid_df.get('cost', 50.0))
    if valid_df['cost'].max() > 20.0:  # Convert tenths to millions (£M)
        valid_df['cost'] = valid_df['cost'] / 10.0

    pos_col = 'position' if 'position' in valid_df.columns else ('element_type' if 'element_type' in valid_df.columns else None)
    team_col = 'team' if 'team' in valid_df.columns else ('team_code' if 'team_code' in valid_df.columns else None)

    def _norm_pos(val):
        s = str(val).upper().strip()
        if s in ('1', 'GK', 'GKP'):
            return 'GK'
        if s in ('2', 'DEF'):
            return 'DEF'
        if s in ('3', 'MID'):
            return 'MID'
        if s in ('4', 'FWD'):
            return 'FWD'
        return 'MID'

    if pos_col:
        valid_df['norm_pos'] = valid_df[pos_col].apply(_norm_pos)
    else:
        valid_df['norm_pos'] = 'MID'

    pool = valid_df.sort_values('expected_points', ascending=False)

    best_xi_xp = 0.0
    best_capt_bonus = 0.0

    # Test valid FPL formations: (DEF, MID, FWD)
    formations = [
        (3, 5, 2), (3, 4, 3), (4, 4, 2), (4, 3, 3), (4, 5, 1), (5, 3, 2), (5, 4, 1)
    ]
    xi_budget_target = max(75.0, budget_limit - 17.0)

    for n_def, n_mid, n_fwd in formations:
        selected_codes: Set[int] = set()
        club_counts: Dict[Any, int] = {}
        xi_xp = 0.0
        xi_cost = 0.0
        players_selected = 0
        reqs = {'GK': 1, 'DEF': n_def, 'MID': n_mid, 'FWD': n_fwd}
        top_xp_in_xi = 0.0

        for pos, needed in reqs.items():
            pos_candidates = pool[pool['norm_pos'] == pos]
            count = 0
            for _, row in pos_candidates.iterrows():
                code = int(row[p_code_col])
                club = str(row.get(team_col, 'Unknown')) if team_col else 'Unknown'
                cost = float(row['cost'])
                xp = float(row['expected_points'])

                if code in selected_codes:
                    continue
                if club != 'Unknown' and club_counts.get(club, 0) >= 3:
                    continue
                if xi_cost + cost > xi_budget_target + 5.0:  # Soft feasibility margin
                    continue

                selected_codes.add(code)
                if club != 'Unknown':
                    club_counts[club] = club_counts.get(club, 0) + 1
                xi_cost += cost
                xi_xp += xp
                if xp > top_xp_in_xi:
                    top_xp_in_xi = xp
                count += 1
                if count == needed:
                    break
            players_selected += count

        if players_selected == 11:
            total_formation_xp = xi_xp + top_xp_in_xi
            if total_formation_xp > best_xi_xp:
                best_xi_xp = total_formation_xp
                best_capt_bonus = top_xp_in_xi

    # Fallback to realistic heuristic if pool is small (e.g. synthetic test)
    if best_xi_xp == 0.0:
        sorted_pool = pool.head(15)
        top11_sub = sorted_pool.head(11)
        best_capt_bonus = float(top11_sub.iloc[0]['expected_points']) if not top11_sub.empty else 0.0
        best_xi_xp = float(top11_sub['expected_points'].sum()) * 0.90 + best_capt_bonus

    return best_xi_xp, best_capt_bonus


def evaluate_opportunistic_wildcard(
    current_squad_codes: List[int],
    gw1_df: pd.DataFrame,
    horizon_dfs: Optional[List[pd.DataFrame]] = None,
    free_transfers: int = 1,
    bank: float = 0.0,
    current_gw: int = 1,
    season: str = '2026-27',
    data_root: str = 'data',
    team_value: float = 100.0,
    enable_bench_optimization: bool = True,
) -> ChipRecommendation:
    """Evaluate whether the manager's current squad warrants an immediate Wildcard.

    Assesses:
    1. Squad Distress Index (SDI):
       Counts currently owned assets with injuries, doubtful status, low projected xP (< 3.3 for outfield, < 2.5 for GK).
       Exempts cheap bench enablers (<= £4.6M) unless actively injured or suspended.
    2. Multi-Gameweek Net Present Value (NPV):
       Compares projected net points across the lookahead horizon (up to 3 GWs) between:
       - Retaining current squad under standard transfer rules with replacement player EV.
       - A legally constrained £100M Wildcard rebuild squad.
    3. Blank Gameweek (BGW) Guardrail:
       If distress is driven by scheduled blank fixtures, suppresses Wildcard and advises Free Hit.
    """
    if not current_squad_codes or gw1_df.empty:
        wc1_gw = 6 if current_gw <= 6 else min(19, current_gw + 1)
        return ChipRecommendation(
            chip='wildcard_1',
            target_gw=wc1_gw,
            expected_value_delta=35.0,
            rationale=f"Gameweek {wc1_gw}: Early-season fixture swing structural pivot (target Arsenal, Man City, Liverpool fixture runs).",
            is_active_now=False,
        )

    p_code_col = 'player_code' if 'player_code' in gw1_df.columns else ('code' if 'code' in gw1_df.columns else 'id')
    owned_codes = set(int(c) for c in current_squad_codes)
    owned_df = gw1_df[gw1_df[p_code_col].astype(int).isin(owned_codes)].copy()

    # Determine starter vs bench status based on projected points
    owned_df = owned_df.sort_values('expected_points', ascending=False)
    starter_codes = set(owned_df.head(11)[p_code_col].astype(int).tolist())

    starter_distress_count = 0
    bench_distress_count = 0
    blank_distress_count = 0
    distressed_names = []

    for _, row in owned_df.iterrows():
        p_code = int(row[p_code_col])
        p_name = str(row.get('web_name', p_code))
        status = str(row.get('status', 'a')).lower()
        xp = float(row.get('expected_points', 0.0) or 0.0)
        chance = row.get('chance_of_playing_this_round')
        pos = str(row.get('position', 'MID')).upper()
        now_cost = float(row.get('now_cost', row.get('cost', 50.0)))
        if now_cost > 20.0:
            now_cost /= 10.0

        is_distressed = False
        is_blank = (xp == 0.0 and status == 'a')  # Zero points due to no scheduled fixture

        if is_blank:
            is_distressed = True
            blank_distress_count += 1
        elif status in ('i', 's', 'u'):
            is_distressed = True
        elif status == 'd' and (pd.isnull(chance) or float(chance) < 75.0):
            is_distressed = True
        elif p_code in starter_codes:
            # Strict thresholds for starting XI
            if pos in ('DEF', 'MID', 'FWD') and xp < 3.3:
                is_distressed = True
            elif pos == 'GK' and xp < 2.5:
                is_distressed = True
        else:
            # Bench enablers (£4.0M DEF, £4.5M MID) are expected to have low xP;
            # they are only distressed if truly injured/suspended or expensive (> £4.6M) with poor projections
            if now_cost > 4.6 and xp < 2.0:
                is_distressed = True

        if is_distressed:
            if p_code in starter_codes:
                starter_distress_count += 1
            else:
                bench_distress_count += 1
            distressed_names.append(p_name)

    # Effective Squad Distress Index (bench distress discounted by 85%)
    effective_distress = starter_distress_count + (0.15 * bench_distress_count)
    distress_score = round(effective_distress / 11.0, 3)

    # 1. Blank Gameweek Guardrail:
    # If distress is predominantly driven by scheduled fixture blanks (FA Cup),
    # Wildcard is toxic. Redirect manager to Free Hit.
    if blank_distress_count >= 3:
        target_gw = 6 if current_gw <= 6 else min(19, current_gw + 1)
        return ChipRecommendation(
            chip='wildcard_1',
            target_gw=target_gw,
            expected_value_delta=0.0,
            rationale=f"Gameweek {current_gw} contains {blank_distress_count} blanking assets. Deploy FREE HIT, not Wildcard.",
            is_active_now=False,
            distress_score=distress_score,
            delta_npv=0.0,
        )

    # 2. Multi-Gameweek Lookahead Net Present Value (NPV)
    lookahead_dfs = horizon_dfs if horizon_dfs else [gw1_df]
    h_len = min(3, len(lookahead_dfs))
    gamma = 0.90  # Gameweek discount factor

    current_starter_xp_sum = 0.0
    optimal_starter_xp_sum = 0.0

    for h_idx in range(h_len):
        h_df = lookahead_dfs[h_idx]
        h_p_col = 'player_code' if 'player_code' in h_df.columns else ('code' if 'code' in h_df.columns else 'id')
        discount = gamma ** h_idx

        # Legally and budget-constrained optimal starting XI
        opt_xi_xp, _ = _build_constrained_optimal_xi(
            h_df, budget_limit=team_value + bank, p_code_col=h_p_col
        )
        optimal_starter_xp_sum += opt_xi_xp * discount

        # Current squad projected starting XI
        h_owned = h_df[h_df[h_p_col].astype(int).isin(owned_codes)].copy()
        if not h_owned.empty:
            sorted_owned = h_owned.sort_values('expected_points', ascending=False)
            top11 = sorted_owned.head(11)
            capt_bonus = float(top11.iloc[0]['expected_points']) if not top11.empty else 0.0
            current_starter_xp_sum += (float(top11['expected_points'].sum()) + capt_bonus) * discount

    # If only 1 horizon DF was provided, extrapolate with discount and fixture dampener
    if h_len == 1:
        extrap_factor = 1.0 + (gamma * 0.85) + ((gamma ** 2) * 0.85)
        current_starter_xp_sum *= extrap_factor
        optimal_starter_xp_sum *= extrap_factor

    # 3. Mathematically Correct Replacement EV for Hits
    # Taking hits brings in replacement players (~5.0 xP/GW) to replace distressed starters (~0.5 xP/GW)
    needed_transfers = min(starter_distress_count, 3)
    net_transfer_benefit = 0.0
    hits_penalty = 0.0

    if needed_transfers > free_transfers:
        extra_hits = needed_transfers - free_transfers
        hits_penalty = extra_hits * 4.0
        replacement_gain = extra_hits * (5.0 - 0.5) * (1.0 + gamma + (gamma ** 2))
        net_transfer_benefit = replacement_gain - hits_penalty
    elif needed_transfers > 0:
        net_transfer_benefit = needed_transfers * (5.0 - 0.5) * (1.0 + gamma + (gamma ** 2))

    projected_held_xp = current_starter_xp_sum + net_transfer_benefit
    delta_npv = round(max(0.0, optimal_starter_xp_sum - projected_held_xp), 1)

    # 4. Trapped Capital Assessment & Residual Option Value Hurdle Gate
    # Calculate bench cost and trapped capital
    bench_cost = sum(
        (float(row.get('now_cost', row.get('cost', 50.0))) / (10.0 if float(row.get('now_cost', row.get('cost', 50.0))) > 20.0 else 1.0))
        for _, row in owned_df.iterrows()
        if int(row[p_code_col]) not in starter_codes
    )
    trapped_bench_capital = max(0.0, round(bench_cost - 17.5, 1))

    # Residual Wildcard 1 Option Value Hurdle Curve: Omega_WC(t) = 28.0 * ((19 - t) / 18)^0.65
    eff_gw = min(18, max(1, current_gw))
    omega_wc = round(28.0 * math.pow((19.0 - eff_gw) / 18.0, 0.65), 1) if current_gw < 19 else 15.0

    # Organic Harvest Simulation for Trapped Capital
    harvest_advisory = None
    if trapped_bench_capital >= 1.0:
        expensive_bench = [
            str(row.get('web_name', row[p_code_col]))
            for _, row in owned_df.iterrows()
            if int(row[p_code_col]) not in starter_codes and (float(row.get('now_cost', row.get('cost', 50.0))) / (10.0 if float(row.get('now_cost', row.get('cost', 50.0))) > 20.0 else 1.0)) > 4.7
        ]
        harvest_freed = min(trapped_bench_capital, 6.0)
        harvest_starter_gain = round(harvest_freed * 0.40 * (1.0 + gamma + (gamma ** 2)), 1)
        harvest_advisory = (
            f"Squad holds £{trapped_bench_capital:.1f}M in trapped bench capital ({', '.join(expensive_bench[:2])}). "
            f"Pruning via 2 FTs yields +{harvest_starter_gain:.1f} pts into starters without burning Wildcard (Option Hurdle: {omega_wc:.1f} pts)."
        )

    # 5. Rigorous Hurdle Logic
    # Requires REAL starter distress. A healthy starting XI cannot trigger a Wildcard.
    should_trigger = False
    if starter_distress_count >= 4:
        should_trigger = True
    elif starter_distress_count == 3:
        if free_transfers == 0 and delta_npv >= 14.0:
            should_trigger = True
        elif free_transfers == 1 and delta_npv >= 18.0:
            should_trigger = True
        elif free_transfers >= 2 and delta_npv >= 22.0:
            should_trigger = True
    elif starter_distress_count == 2 and free_transfers == 0 and delta_npv >= 24.0:
        should_trigger = True

    # Trapped Capital Hurdle Gate:
    # If starters are healthy (distress < 3), Wildcard is blocked unless net rebuild clears the option hurdle Omega_WC(t)
    if should_trigger and starter_distress_count < 3 and delta_npv < omega_wc and enable_bench_optimization:
        should_trigger = False

    if should_trigger and current_gw < 19:
        target_gw = current_gw
        is_active_now = True
        rationale = (
            f"Gameweek {current_gw} SQUAD REBUILD ALERT: {starter_distress_count} starting XI players distressed with "
            f"{free_transfers} FTs in bank. Wildcard projects +{delta_npv:.1f} net pts over 3 GWs while "
            f"eliminating transfer hits (-{hits_penalty:.0f} pts)."
        )
        urgent_reason = f"{free_transfers} FTs remaining; {starter_distress_count} distressed starters ({', '.join(distressed_names[:3])}); +{delta_npv:.1f} pts 3-GW delta."
    else:
        target_gw = 6 if current_gw <= 6 else min(19, current_gw + 1)
        is_active_now = False
        rationale = (
            f"Gameweek {target_gw}: Early-season fixture swing structural pivot (target Arsenal, Man City, Liverpool fixture runs). "
            f"Current 3-GW distress gap is +{delta_npv:.1f} pts ({starter_distress_count} starters distressed)."
        )
        urgent_reason = None

    return ChipRecommendation(
        chip='wildcard_1',
        target_gw=target_gw,
        expected_value_delta=delta_npv if is_active_now else 35.0,
        rationale=rationale,
        backup_gw=target_gw + 1 if target_gw < 19 else None,
        is_active_now=is_active_now,
        distress_score=distress_score,
        urgent_reason=urgent_reason,
        delta_npv=delta_npv,
        trapped_bench_capital=trapped_bench_capital,
        harvest_advisory=harvest_advisory,
    )


def evaluate_chip_schedule(
    season: str = '2026-27',
    current_gw: int = 1,
    data_root: str = 'data',
    current_squad_codes: Optional[List[int]] = None,
    gw1_df: Optional[pd.DataFrame] = None,
    horizon_dfs: Optional[List[pd.DataFrame]] = None,
    free_transfers: int = 1,
    bank: float = 0.0,
    team_value: float = 100.0,
    enable_bench_optimization: bool = True,
) -> SeasonalChipPlan:
    """Evaluate and recommend the optimal seasonal deployment plan for all FPL chips."""
    profiles = detect_double_and_blank_gameweeks(season=season, data_root=data_root)

    # 1. Triple Captain Candidate Analysis
    dgw_candidates = [p for p in profiles if p.is_dgw and p.gw >= current_gw]
    if dgw_candidates:
        dgw_candidates.sort(key=lambda p: (len(p.dgw_teams), p.total_fixtures), reverse=True)
        tc_gw = dgw_candidates[0].gw
        tc_val = 18.5
        tc_rationale = f"Double Gameweek {tc_gw} with {len(dgw_candidates[0].dgw_teams)} double-fixture teams ({', '.join(dgw_candidates[0].dgw_teams[:3])})."
    else:
        tc_gw = min(38, max(current_gw, 25))
        tc_val = 12.0
        tc_rationale = "Target peak home fixture vs promoted side during second half of season."

    # 2. Bench Boost Candidate Analysis (with Post-Chip Contraction Tax modeling)
    if len(dgw_candidates) > 1:
        bb_gw = dgw_candidates[1].gw
        bb_val = 22.0
        bb_rationale = f"Major Double Gameweek {bb_gw} maximizing 15 active playing fixtures across starting XI and bench."
    elif dgw_candidates:
        bb_gw = min(38, dgw_candidates[0].gw + 3)
        bb_val = 15.0
        bb_rationale = f"Deploy post-Wildcard in GW{bb_gw} when squad depth is maximized."
    else:
        bb_gw = 37
        bb_val = 14.0
        bb_rationale = "Traditional penultimate Gameweek 37 DGW window with maximum squad fitness."

    if bb_gw < 37 and enable_bench_optimization:
        bb_val = max(5.0, round(bb_val - 12.8, 1))
        bb_rationale += " (EV adjusted for -12.8 pt post-BB squad contraction tax)"

    # 3. Free Hit Candidate Analysis
    bgw_candidates = [p for p in profiles if p.is_bgw and len(p.bgw_teams) >= 4 and p.gw >= current_gw]
    if bgw_candidates:
        bgw_candidates.sort(key=lambda p: len(p.bgw_teams), reverse=True)
        fh_gw = bgw_candidates[0].gw
        fh_val = 28.0
        fh_rationale = f"Major Blank Gameweek {fh_gw} where {len(bgw_candidates[0].bgw_teams)} teams blank due to FA Cup clashes."
    else:
        fh_gw = 29
        fh_val = 20.0
        fh_rationale = "FA Cup Quarter-Final Blank Gameweek 29 navigation."

    # 4. Wildcard 1 (GW2 - GW19): Dynamic Opportunistic or Scheduled Swing
    if current_squad_codes and gw1_df is not None:
        wc1_rec = evaluate_opportunistic_wildcard(
            current_squad_codes=current_squad_codes,
            gw1_df=gw1_df,
            horizon_dfs=horizon_dfs,
            free_transfers=free_transfers,
            bank=bank,
            current_gw=current_gw,
            season=season,
            data_root=data_root,
            team_value=team_value,
            enable_bench_optimization=enable_bench_optimization,
        )
    else:
        wc1_gw = 6 if current_gw <= 6 else min(19, current_gw + 1)
        wc1_val = 35.0
        wc1_rationale = f"Gameweek {wc1_gw}: Early-season fixture swing structural pivot (target Arsenal, Man City, Liverpool fixture runs)."
        wc1_rec = ChipRecommendation(chip='wildcard_1', target_gw=wc1_gw, expected_value_delta=wc1_val, rationale=wc1_rationale)

    # 5. Wildcard 2 (GW20 - GW38)
    wc2_gw = max(20, min(33, bb_gw - 1 if bb_gw > 20 else 30))
    wc2_val = 40.0
    wc2_rationale = f"Gameweek {wc2_gw}: Structural setup immediately preceding Bench Boost / DGW window."

    recs: Dict[str, ChipRecommendation] = {
        '3xc': ChipRecommendation(chip='3xc', target_gw=tc_gw, expected_value_delta=tc_val, rationale=tc_rationale),
        'bboost': ChipRecommendation(chip='bboost', target_gw=bb_gw, expected_value_delta=bb_val, rationale=bb_rationale),
        'freehit': ChipRecommendation(chip='freehit', target_gw=fh_gw, expected_value_delta=fh_val, rationale=fh_rationale),
        'wildcard_1': wc1_rec,
        'wildcard_2': ChipRecommendation(chip='wildcard_2', target_gw=wc2_gw, expected_value_delta=wc2_val, rationale=wc2_rationale),
    }

    return SeasonalChipPlan(
        season=season,
        current_gw=current_gw,
        recommendations=recs,
        schedule_profiles=profiles,
    )


def format_chip_plan_output(plan: SeasonalChipPlan) -> str:
    """Render a clean ASCII executive summary of the seasonal chip strategy."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"            FPL STRATEGIC CHIP DEPLOYMENT ROADMAP ({plan.season})")
    lines.append("=" * 80)
    lines.append(f"Current Status: Gameweek {plan.current_gw} | Optimization Horizon: GW{plan.current_gw} - GW38")
    lines.append("-" * 80)
    lines.append(f"{'Chip':<15} | {'Target GW':<10} | {'Expected Delta':<15} | Rationale")
    lines.append("-" * 80)

    chip_labels = {
        'wildcard_1': 'Wildcard 1',
        '3xc': 'Triple Captain',
        'freehit': 'Free Hit',
        'wildcard_2': 'Wildcard 2',
        'bboost': 'Bench Boost',
    }

    for key, label in chip_labels.items():
        rec = plan.recommendations.get(key)
        if rec:
            print_val = f"+{rec.expected_value_delta:.1f} pts"
            status_tag = " [!] ACTIVE NOW" if getattr(rec, 'is_active_now', False) else ""
            lines.append(f"{label + status_tag:<15} | GW{rec.target_gw:<8} | {print_val:<15} | {rec.rationale}")

    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate FPL Strategic Chip Timing Roadmap")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Current gameweek number (1-38)")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    plan = evaluate_chip_schedule(season=args.season, current_gw=args.gw, data_root=args.data_root)
    print("\n" + format_chip_plan_output(plan) + "\n")


if __name__ == '__main__':
    main()

"""Historical Backtest Validation Engine for Fantasy Premier League.

Simulates autonomous FPL season playthroughs (GW 1 to 38) to rigorously validate
model performance against historical actuals:

1. **Gameweek-by-Gameweek Simulation**:
   - GW1: Optimal initial 15-man squad selection with £100.0M budget.
   - GW 2..38: Rolling squad state, accumulated Free Transfers (1..5), selling prices,
     and multi-horizon transfer optimization.
2. **Actual Point Scoring & Official Game Mechanics**:
   - Starting XI points with 2x captaincy multiplier (and vice-captain fallback if captain plays 0 mins).
   - Official Auto-Substitution: Bench players sub in if starters play 0 minutes,
     respecting positional constraints (min 3 DEF, min 2 MID, min 1 FWD, 1 GK).
   - Transfer hit penalties (-4 per hit).
3. **Comparative Strategy Benchmarking**:
   - Evaluates Next-Gen Alpha Engine vs Baseline Models.
   - Computes Total Season Points, Average GW Points, Captaincy Efficiency,
     and Transfer Value-Add.

Usage:
    python -m model.backtester [--season 2024-25] [--start-gw 1] [--end-gw 38] [--strategy pure_xp]
"""
import argparse
from dataclasses import dataclass, field
import json
import math
import os
import sys
import time
from typing import Dict, Any, List, Tuple, Optional, Set, Union
import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import _safe_float
from model.build_dataset import build_dataset
from model.fixture_engine import predict_gameweek_fixtures
from model.solver import (
    solve_initial_squad,
    solve_weekly_transfers,
    solve_multi_horizon_transfers,
    calculate_fpl_selling_price,
    PlayerPick,
    SquadSolution,
    TransferSolution,
)
from model.minutes_model import compute_player_minutes_hazard


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class GameweekBacktestResult:
    """Historical performance result for a single simulated gameweek."""
    gw: int
    starters: List[str]
    captain: str
    vice_captain: str
    captain_pts: int
    bench: List[str]
    auto_subs_in: List[str]
    auto_subs_out: List[str]
    transfers_in: List[str]
    transfers_out: List[str]
    transfers_count: int
    free_transfers_used: int
    free_transfers_remaining: int
    hits_taken: int
    hit_penalty: int
    gw_points_gross: int
    gw_points_net: int
    cumulative_points: int
    bank: float
    team_value: float
    chip_used: Optional[str] = None
    bench_points_unplayed: int = 0
    auto_sub_points: int = 0
    starting_xi_points: int = 0
    bench_cost: float = 0.0


@dataclass
class SeasonBacktestReport:
    """Complete 38-gameweek historical backtest report."""
    season: str
    strategy: str
    start_gw: int
    end_gw: int
    total_points_gross: int
    total_points_net: int
    total_hits_taken: int
    total_hit_penalties: int
    total_transfers_made: int
    captaincy_points_total: int
    captaincy_success_rate: float  # % of gameweeks where captain scored >= 6 pts
    chips_used: Dict[str, int]     # mapping chip -> GW
    gw_results: List[GameweekBacktestResult]
    bench_points_unplayed_total: int = 0
    auto_sub_points_total: int = 0
    starting_xi_points_total: int = 0
    avg_bench_cost: float = 0.0
    final_team_value: float = 0.0
    enable_bench_optimization: bool = True


# ---------------------------------------------------------------------------
# Historical Point Scoring & Auto-Sub Mechanics
# ---------------------------------------------------------------------------

def load_gameweek_actual_points(
    season: str = '2024-25',
    gw: int = 1,
    data_root: str = 'data',
) -> Dict[int, Dict[str, Any]]:
    """Load actual real-world FPL points and minutes from merged_gw.csv for a gameweek.

    Args:
        season: season string e.g. '2024-25'.
        gw: target gameweek integer (1..38).
        data_root: root data directory.

    Returns:
        Dict mapping player_code/element -> {total_points, minutes, web_name, position, team, cost}.
    """
    merged_path = os.path.join(data_root, season, 'gws', 'merged_gw.csv')
    if not os.path.exists(merged_path):
        merged_path = os.path.join(data_root, season, 'gws', f'gw{gw}.csv')
    if not os.path.exists(merged_path):
        return {}

    df = pd.read_csv(merged_path, low_memory=False)
    if 'GW' in df.columns:
        gw_df = df[df['GW'] == gw].copy()
    else:
        gw_df = df.copy()

    # Load player id map to permanent player_code if available
    raw_path = os.path.join(data_root, season, 'players_raw.csv')
    elem_to_code: Dict[int, int] = {}
    if os.path.exists(raw_path):
        raw_df = pd.read_csv(raw_path)
        id_col = 'id' if 'id' in raw_df.columns else 'element'
        code_col = 'code' if 'code' in raw_df.columns else ('player_code' if 'player_code' in raw_df.columns else id_col)
        for _, r in raw_df.iterrows():
            elem_to_code[int(r[id_col])] = int(r[code_col])

    actuals: Dict[int, Dict[str, Any]] = {}
    for _, r in gw_df.iterrows():
        elem = int(r.get('element', r.get('id', 0)))
        p_code = elem_to_code.get(elem, elem)
        pts = int(_safe_float(r.get('total_points', 0.0)))
        mins = int(_safe_float(r.get('minutes', 0.0)))
        wname = str(r.get('name', r.get('web_name', f'Player_{p_code}')))
        pos = str(r.get('position', 'MID')).upper()
        team = str(r.get('team', 'Unknown'))
        val = float(_safe_float(r.get('value', 50.0))) / 10.0 if float(_safe_float(r.get('value', 50.0))) > 25.0 else float(_safe_float(r.get('value', 5.0)))

        # In DGWs, sum points across fixtures
        if p_code in actuals:
            actuals[p_code]['total_points'] += pts
            actuals[p_code]['minutes'] += mins
        else:
            actuals[p_code] = {
                'total_points': pts,
                'minutes': mins,
                'web_name': wname,
                'position': pos,
                'team': team,
                'value': val,
            }

    return actuals


def score_squad_with_auto_subs(
    starters: List[PlayerPick],
    bench: List[PlayerPick],
    captain_pick: Optional[PlayerPick],
    vice_pick: Optional[PlayerPick],
    actuals: Dict[int, Dict[str, Any]],
    chip: Optional[str] = None,
) -> Tuple[int, int, List[str], List[str], int]:
    """Score starting XI with official FPL captaincy, auto-substitutions, and chip mechanics.

    Rules:
    1. If captain plays > 0 mins, captain gets 2x points (or 3x for Triple Captain).
    2. If captain plays 0 mins, vice-captain gets 2x points (or 3x for Triple Captain).
    3. If Bench Boost is active ('bboost'), all 15 squad players score points.
    4. Otherwise, outfield bench players sub in order if starters play 0 mins.

    Returns:
        Tuple of (gross_points, captain_pts, auto_subs_in_names, auto_subs_out_names, base_capt_score).
    """
    is_bboost = (chip == 'bboost')
    is_3xc = (chip == '3xc')
    capt_multiplier = 3 if is_3xc else 2

    # Handle Captaincy Evaluation
    effective_captain = captain_pick
    if captain_pick and actuals.get(captain_pick.player_code, {}).get('minutes', 0) == 0:
        if vice_pick and actuals.get(vice_pick.player_code, {}).get('minutes', 0) > 0:
            effective_captain = vice_pick

    if is_bboost:
        # Bench Boost: Score all 15 players directly
        gross_pts = 0
        capt_pts = 0
        for p in starters + bench:
            base_p = actuals.get(p.player_code, {}).get('total_points', 0)
            if effective_captain and p.player_code == effective_captain.player_code:
                gross_pts += base_p * capt_multiplier
                capt_pts = base_p * capt_multiplier
            else:
                gross_pts += base_p
        return gross_pts, capt_pts, [], [], (capt_pts // capt_multiplier) if capt_pts > 0 else 0

    dnp_starters = [p for p in starters if actuals.get(p.player_code, {}).get('minutes', 0) == 0]

    subs_in: List[PlayerPick] = []
    subs_out: List[PlayerPick] = []

    current_defs = sum(1 for p in starters if p.position == 'DEF')
    current_mids = sum(1 for p in starters if p.position == 'MID')
    current_fwds = sum(1 for p in starters if p.position == 'FWD')

    # Handle GK Auto-Sub
    starting_gk = next((p for p in starters if p.position == 'GK'), None)
    bench_gk = next((p for p in bench if p.position == 'GK'), None)
    if starting_gk and actuals.get(starting_gk.player_code, {}).get('minutes', 0) == 0:
        if bench_gk and actuals.get(bench_gk.player_code, {}).get('minutes', 0) > 0:
            subs_in.append(bench_gk)
            subs_out.append(starting_gk)

    # Handle Outfield Auto-Subs
    outfield_bench = [p for p in bench if p.position != 'GK']
    outfield_dnp_starters = [p for p in dnp_starters if p.position != 'GK']

    available_bench = [b for b in outfield_bench if actuals.get(b.player_code, {}).get('minutes', 0) > 0]

    for dnp_p in outfield_dnp_starters:
        for b_cand in list(available_bench):
            cand_defs = current_defs - (1 if dnp_p.position == 'DEF' else 0) + (1 if b_cand.position == 'DEF' else 0)
            cand_mids = current_mids - (1 if dnp_p.position == 'MID' else 0) + (1 if b_cand.position == 'MID' else 0)
            cand_fwds = current_fwds - (1 if dnp_p.position == 'FWD' else 0) + (1 if b_cand.position == 'FWD' else 0)

            if cand_defs >= 3 and cand_mids >= 2 and cand_fwds >= 1:
                subs_in.append(b_cand)
                subs_out.append(dnp_p)
                available_bench.remove(b_cand)
                current_defs = cand_defs
                current_mids = cand_mids
                current_fwds = cand_fwds
                break

    # Final scoring XI
    final_scoring_players = [p for p in starters if p not in subs_out] + subs_in

    gross_pts = 0
    capt_pts = 0

    for p in final_scoring_players:
        base_p = actuals.get(p.player_code, {}).get('total_points', 0)
        if effective_captain and p.player_code == effective_captain.player_code:
            gross_pts += base_p * capt_multiplier
            capt_pts = base_p * capt_multiplier
        else:
            gross_pts += base_p

    in_names = [p.web_name for p in subs_in]
    out_names = [p.web_name for p in subs_out]

    return gross_pts, capt_pts, in_names, out_names, (capt_pts // capt_multiplier) if capt_pts > 0 else 0


# ---------------------------------------------------------------------------
# Historical Backtest Simulator Orchestrator
# ---------------------------------------------------------------------------

def run_season_backtest(
    season: str = '2024-25',
    start_gw: int = 1,
    end_gw: int = 38,
    strategy: str = 'pure_xp',
    lambda_risk: float = 0.0,
    lambda_ft: float = 1.75,
    data_root: str = 'data',
    use_multi_horizon: bool = True,
    horizon: int = 3,
    enable_chips: bool = True,
    enable_bench_optimization: bool = True,
    pred_df_cache: Optional[Dict[int, pd.DataFrame]] = None,
    positional_calibration: bool = True,
    silent: bool = False,
) -> SeasonBacktestReport:
    """Run full historical backtest simulation across gameweeks start_gw..end_gw with chip automation.

    Args:
        season: historical season string e.g. '2024-25'.
        start_gw: starting gameweek (default 1).
        end_gw: ending gameweek (default 38).
        strategy: 'pure_xp', 'rank_protect', 'differential_chase'.
        lambda_risk: CVaR risk preference.
        lambda_ft: shadow value for banking free transfers (1.75 pts).
        data_root: root data directory.
        use_multi_horizon: whether to use multi-period lookahead transfer solver.
        horizon: lookahead gameweek horizon (default 3).
        enable_chips: whether to enable autonomous strategic chip deployment (WC1, WC2, FH, BB, 3xC).
        enable_bench_optimization: whether to enable audited bench capital drag, soft floor, and equity retention.
        pred_df_cache: optional shared prediction dataframe dictionary to guarantee 100% input parity in A/B tests.
        silent: if True, suppress gameweek print statements.

    Returns:
        SeasonBacktestReport dataclass with complete analytics.
    """
    bank: float = 0.0
    free_transfers: int = 1
    current_squad: Optional[SquadSolution] = None
    purchase_prices: Dict[int, float] = {}

    # Chip Strategy Management
    used_chips: Dict[str, int] = {}
    pre_fh_squad: Optional[SquadSolution] = None
    pre_fh_prices: Dict[int, float] = {}
    pre_fh_bank: float = 0.0

    chip_targets: Dict[str, int] = {}
    if enable_chips:
        try:
            from model.chip_optimizer import evaluate_chip_schedule
            chip_plan = evaluate_chip_schedule(
                season=season,
                current_gw=start_gw,
                data_root=data_root,
                enable_bench_optimization=enable_bench_optimization,
            )
            chip_targets = {k: rec.target_gw for k, rec in chip_plan.recommendations.items()}
        except Exception:
            chip_targets = {}

    gw_results: List[GameweekBacktestResult] = []
    cumulative_points = 0
    total_gross = 0
    total_hits = 0
    total_trans = 0
    total_capt_pts = 0
    capt_successes = 0

    total_unplayed_bench = 0
    total_auto_sub_pts = 0
    total_starting_xi_pts = 0
    total_bench_cost_sum = 0.0

    opt_label = "AUDITED" if enable_bench_optimization else "BASELINE"
    if not silent:
        print(f"[*] Starting Autonomous FPL Backtest for {season} (GW{start_gw} to GW{end_gw}, Model: {opt_label}, Strategy: {strategy}, Chips: {'ENABLED' if enable_chips else 'DISABLED'})...")

    for gw in range(start_gw, end_gw + 1):
        actuals = load_gameweek_actual_points(season=season, gw=gw, data_root=data_root)

        # 1. Build or retrieve Prediction Dataframe for current Gameweek
        if pred_df_cache is not None and gw in pred_df_cache:
            pred_df = pred_df_cache[gw]
        else:
            pred_df = predict_gameweek_fixtures(
                season=season,
                gw=gw,
                data_root=data_root,
                dynamic_dataset=True,
                save_csv=False,
                positional_calibration=positional_calibration,
            )
            if pred_df_cache is not None:
                pred_df_cache[gw] = pred_df

        # Restore pre-Free-Hit squad if Free Hit was played in gw-1
        if pre_fh_squad is not None:
            current_squad = pre_fh_squad
            purchase_prices = pre_fh_prices
            bank = pre_fh_bank
            pre_fh_squad = None
            pre_fh_prices = {}

        # Determine active chip for this gameweek
        active_chip: Optional[str] = None
        if enable_chips:
            if gw == chip_targets.get('freehit') and 'freehit' not in used_chips:
                active_chip = 'freehit'
                used_chips['freehit'] = gw
            elif gw == chip_targets.get('3xc') and '3xc' not in used_chips:
                active_chip = '3xc'
                used_chips['3xc'] = gw
            elif gw == chip_targets.get('bboost') and 'bboost' not in used_chips:
                active_chip = 'bboost'
                used_chips['bboost'] = gw
            elif gw == chip_targets.get('wildcard_1') and 'wildcard_1' not in used_chips and gw <= 19:
                active_chip = 'wildcard'
                used_chips['wildcard_1'] = gw
            elif gw == chip_targets.get('wildcard_2') and 'wildcard_2' not in used_chips and gw >= 20:
                active_chip = 'wildcard'
                used_chips['wildcard_2'] = gw

        if gw == start_gw or current_squad is None:
            # Solve Optimal Initial 15-Man Squad
            squad_sol = solve_initial_squad(
                df=pred_df,
                budget=100.0,
                season=season,
                data_root=data_root,
                strategy=strategy,
                lambda_risk=lambda_risk,
                current_gw=gw,
                enable_bench_optimization=enable_bench_optimization,
            )
            current_squad = squad_sol
            bank = round(100.0 - squad_sol.total_cost, 1)
            purchase_prices = {p.player_code: p.cost for p in squad_sol.squad}

            trans_in_names: List[str] = []
            trans_out_names: List[str] = []
            n_trans = 0
            hits_taken = 0
            hit_pen = 0
            ft_used = 0
            free_transfers = 1
        elif active_chip in ('wildcard', 'freehit'):
            # Save pre-FH squad if Free Hit
            if active_chip == 'freehit':
                pre_fh_squad = current_squad
                pre_fh_prices = dict(purchase_prices)
                pre_fh_bank = bank
                wc_budget = round(sum(p.cost for p in current_squad.squad) + bank, 1)
            else:
                # Calculate true selling value + bank for Wildcard
                wc_budget = round(sum(
                    calculate_fpl_selling_price(purchase_prices.get(p.player_code, p.cost), p.cost)
                    for p in current_squad.squad
                ) + bank, 1)

            # Solve unconstrained reset squad
            squad_sol = solve_initial_squad(
                df=pred_df,
                budget=wc_budget,
                season=season,
                data_root=data_root,
                strategy=strategy,
                lambda_risk=lambda_risk,
                current_gw=gw,
                enable_bench_optimization=enable_bench_optimization,
            )
            current_squad = squad_sol
            bank = round(wc_budget - squad_sol.total_cost, 1)
            if active_chip == 'wildcard':
                purchase_prices = {p.player_code: p.cost for p in squad_sol.squad}
            trans_in_names = [p.web_name for p in squad_sol.squad]
            trans_out_names = ["(Full Reset)"]
            n_trans = 15
            hits_taken = 0
            hit_pen = 0
            ft_used = free_transfers
            free_transfers = 1
        else:
            # Solve Weekly Transfers (respecting Bench Boost / 3xC chip incentives)
            current_codes = [p.player_code for p in current_squad.squad]

            if use_multi_horizon and horizon > 1:
                horizon_dfs: List[pd.DataFrame] = [pred_df]
                for h_step in range(1, horizon):
                    next_gw = gw + h_step
                    if next_gw <= 38:
                        if pred_df_cache is not None and next_gw in pred_df_cache:
                            h_df = pred_df_cache[next_gw]
                        else:
                            h_df = predict_gameweek_fixtures(
                                season=season,
                                gw=next_gw,
                                data_root=data_root,
                                dynamic_dataset=False,
                                save_csv=False,
                                positional_calibration=positional_calibration,
                            )
                            if pred_df_cache is not None:
                                pred_df_cache[next_gw] = h_df
                        horizon_dfs.append(h_df)
                    else:
                        horizon_dfs.append(pred_df)

                multi_sol = solve_multi_horizon_transfers(
                    current_squad_codes=current_codes,
                    horizon_dfs=horizon_dfs,
                    free_transfers=free_transfers,
                    bank=bank,
                    season=season,
                    data_root=data_root,
                    strategy=strategy,
                    lambda_risk=lambda_risk,
                    lambda_ft=lambda_ft,
                    chip=active_chip,
                    start_gw=gw,
                    enable_bench_optimization=enable_bench_optimization,
                )

                if multi_sol.gw_plans:
                    first_plan = multi_sol.gw_plans[0]
                    trans_in = first_plan.transfers_in
                    trans_out = first_plan.transfers_out
                    n_trans = first_plan.transfers_count
                    hits_taken = first_plan.hits_taken
                    hit_pen = int(first_plan.hit_penalty)
                    ft_used = min(n_trans, free_transfers)
                    free_transfers = first_plan.free_transfers_remaining
                    current_squad = first_plan.squad_solution
                    bank = first_plan.bank
                else:
                    trans_in = []
                    trans_out = []
                    n_trans = 0
                    hits_taken = 0
                    hit_pen = 0
                    ft_used = 0
                    free_transfers = min(5, free_transfers + 1)
            else:
                trans_sol = solve_weekly_transfers(
                    current_squad_codes=current_codes,
                    df=pred_df,
                    free_transfers=free_transfers,
                    bank=bank,
                    purchase_prices=purchase_prices,
                    season=season,
                    data_root=data_root,
                    strategy=strategy,
                    lambda_risk=lambda_risk,
                    chip=active_chip,
                    current_gw=gw,
                    enable_bench_optimization=enable_bench_optimization,
                )
                trans_in = trans_sol.transfers_in
                trans_out = trans_sol.transfers_out
                n_trans = trans_sol.transfers_count
                hits_taken = trans_sol.hits_taken
                hit_pen = int(trans_sol.hit_penalty)
                ft_used = trans_sol.free_transfers_used
                free_transfers = min(5, free_transfers - ft_used + 1)
                current_squad = trans_sol.squad_solution
                bank = round(100.0 - current_squad.total_cost, 1)

            trans_in_names = [p.web_name for p in trans_in]
            trans_out_names = [p.web_name for p in trans_out]

            for p in trans_in:
                purchase_prices[p.player_code] = p.cost
            for p in trans_out:
                purchase_prices.pop(p.player_code, None)

        # 2. Score Matchday Points with Actuals, Auto-Subs & Active Chip
        gross_pts, capt_pts, auto_in, auto_out, base_capt_score = score_squad_with_auto_subs(
            starters=current_squad.starters,
            bench=current_squad.bench,
            captain_pick=current_squad.captain,
            vice_pick=current_squad.vice_captain,
            actuals=actuals,
            chip=active_chip,
        )

        sub_in_codes = {p.player_code for p in current_squad.bench if p.web_name in auto_in}
        gw_auto_sub_pts = sum(actuals.get(c, {}).get('total_points', 0) for c in sub_in_codes)
        gw_unplayed_bench_pts = sum(actuals.get(p.player_code, {}).get('total_points', 0) for p in current_squad.bench if p.player_code not in sub_in_codes) if active_chip != 'bboost' else 0
        gw_starting_xi_pts = (gross_pts - gw_auto_sub_pts) if active_chip != 'bboost' else gross_pts
        gw_bench_cost = round(sum(p.cost for p in current_squad.bench), 1)

        net_pts = gross_pts - hit_pen
        cumulative_points += net_pts
        total_gross += gross_pts
        total_hits += hits_taken
        total_trans += n_trans
        total_capt_pts += capt_pts
        total_unplayed_bench += gw_unplayed_bench_pts
        total_auto_sub_pts += gw_auto_sub_pts
        total_starting_xi_pts += gw_starting_xi_pts
        total_bench_cost_sum += gw_bench_cost
        if base_capt_score >= 6:
            capt_successes += 1

        # 3. Dynamic Rolling Accuracy Logging & Positional Bias Feedback
        if positional_calibration:
            try:
                from model.accuracy_tracker import evaluate_gameweek_accuracy
                evaluate_gameweek_accuracy(
                    season=season,
                    gw=gw,
                    data_root=data_root,
                    save_log=True,
                    pred_df=pred_df,
                )
            except Exception:
                pass

        team_val = round(sum(p.cost for p in current_squad.squad) + bank, 1)

        result_row = GameweekBacktestResult(
            gw=gw,
            starters=[p.web_name for p in current_squad.starters],
            captain=current_squad.captain.web_name if current_squad.captain else "None",
            vice_captain=current_squad.vice_captain.web_name if current_squad.vice_captain else "None",
            captain_pts=capt_pts,
            bench=[p.web_name for p in current_squad.bench],
            auto_subs_in=auto_in,
            auto_subs_out=auto_out,
            transfers_in=trans_in_names,
            transfers_out=trans_out_names,
            transfers_count=n_trans,
            free_transfers_used=ft_used,
            free_transfers_remaining=free_transfers,
            hits_taken=hits_taken,
            hit_penalty=hit_pen,
            gw_points_gross=gross_pts,
            gw_points_net=net_pts,
            cumulative_points=cumulative_points,
            bank=bank,
            team_value=team_val,
            chip_used=active_chip,
            bench_points_unplayed=gw_unplayed_bench_pts,
            auto_sub_points=gw_auto_sub_pts,
            starting_xi_points=gw_starting_xi_pts,
            bench_cost=gw_bench_cost,
        )
        gw_results.append(result_row)

        chip_tag = f" [{active_chip.upper()}]" if active_chip else ""
        if not silent and (gw % 5 == 0 or gw == end_gw or gw == start_gw or active_chip):
            print(f"  * GW{gw:>2}{chip_tag:<10} | Net: {net_pts:>3} pts | Gross: {gross_pts:>3} pts (Capt: {result_row.captain} +{capt_pts}p) | Total: {cumulative_points:>4} pts | Bench: £{gw_bench_cost}M ({gw_unplayed_bench_pts}p) | FTs: {free_transfers} | Hits: {hits_taken}")

    num_gws = max(1, end_gw - start_gw + 1)
    capt_success_rate = round(capt_successes / num_gws, 4)

    return SeasonBacktestReport(
        season=season,
        strategy=strategy,
        start_gw=start_gw,
        end_gw=end_gw,
        total_points_gross=total_gross,
        total_points_net=cumulative_points,
        total_hits_taken=total_hits,
        total_hit_penalties=total_hits * 4,
        total_transfers_made=total_trans,
        captaincy_points_total=total_capt_pts,
        captaincy_success_rate=capt_success_rate,
        chips_used=used_chips,
        gw_results=gw_results,
        bench_points_unplayed_total=total_unplayed_bench,
        auto_sub_points_total=total_auto_sub_pts,
        starting_xi_points_total=total_starting_xi_pts,
        avg_bench_cost=round(total_bench_cost_sum / num_gws, 2),
        final_team_value=team_val,
        enable_bench_optimization=enable_bench_optimization,
    )


# ---------------------------------------------------------------------------
# Historical A/B Benchmark Suite
# ---------------------------------------------------------------------------

def run_ab_benchmark(
    season: str = '2025-26',
    start_gw: int = 1,
    end_gw: int = 38,
    strategy: str = 'pure_xp',
    lambda_risk: float = 0.0,
    lambda_ft: float = 1.75,
    data_root: str = 'data',
    use_multi_horizon: bool = True,
    horizon: int = 3,
    enable_chips: bool = True,
    positional_calibration: bool = True,
) -> Tuple[SeasonBacktestReport, SeasonBacktestReport, Dict[str, Any]]:
    """Run an A/B benchmark comparing Baseline (unoptimized bench) vs Audited (optimized bench).

    Shared precomputed predictions cache guarantees 100% data parity between runs.
    """
    print("\n" + "=" * 105)
    print(f"      FPL PRODUCTION ENGINE A/B BENCHMARK SUITE: {season} (GW{start_gw} to GW{end_gw})")
    print("=" * 105)
    print(f"Configuration: Horizon = {horizon} GWs | Strategy = {strategy.upper()} | Chips = {'ENABLED' if enable_chips else 'DISABLED'} | Pos-Cal = {'ENABLED' if positional_calibration else 'DISABLED'}")
    print("Pre-warming shared fixture predictions cache for strict input data parity...\n")

    # Clean prior accuracy logs for pristine calibration trajectory
    log_path = os.path.join(data_root, season, 'accuracy_log.csv')
    team_log_path = os.path.join(data_root, season, 'team_accuracy_log.csv')
    for p in (log_path, team_log_path):
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    shared_cache: Dict[int, pd.DataFrame] = {}

    print(">>> [1/2] RUNNING VARIANT A: BASELINE MODEL (Unconstrained Bench, Drag=0, Equity=0, Flat Auto-Subs)")
    t0_a = time.time()
    report_a = run_season_backtest(
        season=season,
        start_gw=start_gw,
        end_gw=end_gw,
        strategy=strategy,
        lambda_risk=lambda_risk,
        lambda_ft=lambda_ft,
        data_root=data_root,
        use_multi_horizon=use_multi_horizon,
        horizon=horizon,
        enable_chips=enable_chips,
        enable_bench_optimization=False,
        pred_df_cache=shared_cache,
        positional_calibration=positional_calibration,
    )
    time_a = time.time() - t0_a
    print(f"[OK] Variant A completed in {time_a:.1f}s | Total Net Points: {report_a.total_points_net} pts\n")

    print(">>> [2/2] RUNNING VARIANT B: AUDITED MODEL (Capital Drag, Soft Floor, Equity Preservation, Festive Shock)")
    t0_b = time.time()
    report_b = run_season_backtest(
        season=season,
        start_gw=start_gw,
        end_gw=end_gw,
        strategy=strategy,
        lambda_risk=lambda_risk,
        lambda_ft=lambda_ft,
        data_root=data_root,
        use_multi_horizon=use_multi_horizon,
        horizon=horizon,
        enable_chips=enable_chips,
        enable_bench_optimization=True,
        pred_df_cache=shared_cache,
        positional_calibration=positional_calibration,
    )
    time_b = time.time() - t0_b
    print(f"[OK] Variant B completed in {time_b:.1f}s | Total Net Points: {report_b.total_points_net} pts\n")

    # Compute comparative deltas
    delta_net = report_b.total_points_net - report_a.total_points_net
    pct_net = (delta_net / report_a.total_points_net * 100.0) if report_a.total_points_net > 0 else 0.0
    delta_gross = report_b.total_points_gross - report_a.total_points_gross
    delta_starting_xi = report_b.starting_xi_points_total - report_a.starting_xi_points_total
    delta_bench_waste = report_b.bench_points_unplayed_total - report_a.bench_points_unplayed_total
    delta_auto_subs = report_b.auto_sub_points_total - report_a.auto_sub_points_total
    delta_hits = report_b.total_hits_taken - report_a.total_hits_taken
    delta_transfers = report_b.total_transfers_made - report_a.total_transfers_made
    delta_capt = report_b.captaincy_points_total - report_a.captaincy_points_total
    delta_bench_cost = report_b.avg_bench_cost - report_a.avg_bench_cost
    delta_team_val = report_b.final_team_value - report_a.final_team_value

    summary_stats = {
        'season': season,
        'start_gw': start_gw,
        'end_gw': end_gw,
        'variant_a': {
            'name': 'Baseline Model',
            'net_points': report_a.total_points_net,
            'gross_points': report_a.total_points_gross,
            'starting_xi_points': report_a.starting_xi_points_total,
            'unplayed_bench_points': report_a.bench_points_unplayed_total,
            'auto_sub_points': report_a.auto_sub_points_total,
            'hits_taken': report_a.total_hits_taken,
            'transfers_made': report_a.total_transfers_made,
            'captaincy_points': report_a.captaincy_points_total,
            'captaincy_success_rate': report_a.captaincy_success_rate,
            'avg_bench_cost': report_a.avg_bench_cost,
            'final_team_value': report_a.final_team_value,
            'chips_used': report_a.chips_used,
        },
        'variant_b': {
            'name': 'Audited / Improved Model',
            'net_points': report_b.total_points_net,
            'gross_points': report_b.total_points_gross,
            'starting_xi_points': report_b.starting_xi_points_total,
            'unplayed_bench_points': report_b.bench_points_unplayed_total,
            'auto_sub_points': report_b.auto_sub_points_total,
            'hits_taken': report_b.total_hits_taken,
            'transfers_made': report_b.total_transfers_made,
            'captaincy_points': report_b.captaincy_points_total,
            'captaincy_success_rate': report_b.captaincy_success_rate,
            'avg_bench_cost': report_b.avg_bench_cost,
            'final_team_value': report_b.final_team_value,
            'chips_used': report_b.chips_used,
        },
        'deltas': {
            'delta_net_points': delta_net,
            'delta_net_pct': round(pct_net, 2),
            'delta_gross_points': delta_gross,
            'delta_starting_xi_points': delta_starting_xi,
            'delta_bench_waste': delta_bench_waste,
            'delta_auto_sub_points': delta_auto_subs,
            'delta_hits_taken': delta_hits,
            'delta_transfers_made': delta_transfers,
            'delta_captaincy_points': delta_capt,
            'delta_avg_bench_cost': round(delta_bench_cost, 2),
            'delta_final_team_value': round(delta_team_val, 2),
        }
    }

    # Print Comparative Scoreboard
    sign_net = "+" if delta_net >= 0 else ""
    sign_sxi = "+" if delta_starting_xi >= 0 else ""
    sign_bw = "+" if delta_bench_waste >= 0 else ""
    sign_as = "+" if delta_auto_subs >= 0 else ""
    sign_hits = "+" if delta_hits >= 0 else ""
    sign_tv = "+" if delta_team_val >= 0 else ""
    sign_bc = "+" if delta_bench_cost >= 0 else ""

    print("\n" + "=" * 105)
    print(f"             FPL HISTORICAL A/B BENCHMARK SCOREBOARD -- {season} (GW{start_gw} - GW{end_gw})")
    print("=" * 105)
    print(f"{'Performance Metric':<36} | {'Variant A (Baseline)':<22} | {'Variant B (Improved)':<22} | {'Net Alpha Delta':<16}")
    print("-" * 105)
    print(f"{'Total Net FPL Points':<36} | {report_a.total_points_net:>18} pts | {report_b.total_points_net:>18} pts | {sign_net}{delta_net:>5} pts ({sign_net}{pct_net:.1f}%)")
    print(f"{'Average Points Per Gameweek':<36} | {report_a.total_points_net / max(1, end_gw - start_gw + 1):>15.2f} pts/GW | {report_b.total_points_net / max(1, end_gw - start_gw + 1):>15.2f} pts/GW | {sign_net}{delta_net / max(1, end_gw - start_gw + 1):>5.2f} pts/GW")
    print(f"{'Starting XI Gross Points':<36} | {report_a.starting_xi_points_total:>18} pts | {report_b.starting_xi_points_total:>18} pts | {sign_sxi}{delta_starting_xi:>5} pts")
    print(f"{'Unplayed Bench Points (Wasted)':<36} | {report_a.bench_points_unplayed_total:>18} pts | {report_b.bench_points_unplayed_total:>18} pts | {sign_bw}{delta_bench_waste:>5} pts")
    print(f"{'Auto-Sub Points Rescued':<36} | {report_a.auto_sub_points_total:>18} pts | {report_b.auto_sub_points_total:>18} pts | {sign_as}{delta_auto_subs:>5} pts")
    print(f"{'Transfer Hits Taken':<36} | {report_a.total_hits_taken:>13} (-{report_a.total_hit_penalties}p) | {report_b.total_hits_taken:>13} (-{report_b.total_hit_penalties}p) | {sign_hits}{delta_hits:>5} hits")
    print(f"{'Total Transfers Executed':<36} | {report_a.total_transfers_made:>18}     | {report_b.total_transfers_made:>18}     | {report_b.total_transfers_made - report_a.total_transfers_made:>+5} trans")
    print(f"{'Captaincy Points Total':<36} | {report_a.captaincy_points_total:>18} pts | {report_b.captaincy_points_total:>18} pts | {delta_capt:>+5} pts")
    print(f"{'Captaincy Hit Rate (>= 6 pts)':<36} | {report_a.captaincy_success_rate * 100:>17.1f}% | {report_b.captaincy_success_rate * 100:>17.1f}% | {(report_b.captaincy_success_rate - report_a.captaincy_success_rate)*100:>+5.1f}%")
    print(f"{'Average Bench Squad Cost':<36} | £{report_a.avg_bench_cost:>17.2f}M | £{report_b.avg_bench_cost:>17.2f}M | {sign_bc}£{delta_bench_cost:.2f}M")
    print(f"{'Final Squad + Bank Value (GW38)':<36} | £{report_a.final_team_value:>17.1f}M | £{report_b.final_team_value:>17.1f}M | {sign_tv}£{delta_team_val:.1f}M")
    print("=" * 105)

    # Persist JSON report
    out_dir = os.path.join(data_root, season)
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, f"ab_benchmark_report_{season}.json")
    try:
        with open(out_json, 'w') as f:
            json.dump(summary_stats, f, indent=2)
        print(f"[*] Saved comprehensive A/B benchmark payload to {out_json}")
    except Exception as e:
        print(f"[!] Warning: failed to save benchmark JSON ({e})")

    return report_a, report_b, summary_stats


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description="Autonomous Historical FPL Backtest Engine")
    parser.add_argument('--season', default='2025-26', help="Historical season (e.g. 2025-26, 2024-25)")
    parser.add_argument('--start-gw', type=int, default=1, help="Starting gameweek (1-38)")
    parser.add_argument('--end-gw', type=int, default=38, help="Ending gameweek (1-38)")
    parser.add_argument('--strategy', default='pure_xp', choices=['pure_xp', 'rank_protect', 'differential_chase'], help="Optimization strategy")
    parser.add_argument('--lambda-risk', type=float, default=0.0, help="CVaR risk parameter")
    parser.add_argument('--lambda-ft', type=float, default=1.75, help="Free transfer banking shadow price")
    parser.add_argument('--horizon', type=int, default=3, help="Lookahead horizon in gameweeks (default: 3)")
    parser.add_argument('--disable-chips', action='store_true', help="Disable autonomous strategic chip activation")
    parser.add_argument('--disable-bench-optimization', action='store_true', help="Run standalone backtest with unoptimized bench baseline")
    parser.add_argument('--no-positional-calibration', action='store_true', help="Disable baseline empirical positional priors and rolling accuracy feedback")
    parser.add_argument('--ab-compare', action='store_true', help="Run side-by-side A/B benchmark between Baseline and Audited models")
    parser.add_argument('--data-root', default='data', help="Data root directory")
    args = parser.parse_args()

    pos_cal = not args.no_positional_calibration

    if args.ab_compare:
        run_ab_benchmark(
            season=args.season,
            start_gw=args.start_gw,
            end_gw=args.end_gw,
            strategy=args.strategy,
            lambda_risk=args.lambda_risk,
            lambda_ft=args.lambda_ft,
            data_root=args.data_root,
            horizon=args.horizon,
            enable_chips=not args.disable_chips,
            positional_calibration=pos_cal,
        )
    else:
        report = run_season_backtest(
            season=args.season,
            start_gw=args.start_gw,
            end_gw=args.end_gw,
            strategy=args.strategy,
            lambda_risk=args.lambda_risk,
            lambda_ft=args.lambda_ft,
            data_root=args.data_root,
            horizon=args.horizon,
            enable_chips=not args.disable_chips,
            enable_bench_optimization=not args.disable_bench_optimization,
            positional_calibration=pos_cal,
        )

        opt_tag = "AUDITED" if not args.disable_bench_optimization else "BASELINE"
        print("\n" + "=" * 90)
        print(f"      HISTORICAL BACKTEST SUMMARY REPORT -- {report.season} (GW{report.start_gw} - GW{report.end_gw})")
        print("=" * 90)
        print(f"Model: {opt_tag} | Strategy: {report.strategy.upper()} | Lookahead Horizon: {args.horizon} GWs | Chips: {'ENABLED' if not args.disable_chips else 'DISABLED'}")
        print(f"Total Season Points (Net):    {report.total_points_net:,} pts (Gross: {report.total_points_gross:,} pts)")
        print(f"Average Points Per Gameweek:  {report.total_points_net / max(1, report.end_gw - report.start_gw + 1):.2f} pts/GW")
        print(f"Starting XI Points:           {report.starting_xi_points_total:,} pts")
        print(f"Unplayed Bench Points (Waste):{report.bench_points_unplayed_total:,} pts")
        print(f"Auto-Sub Points Rescued:      {report.auto_sub_points_total:,} pts")
        print(f"Total Transfers Executed:     {report.total_transfers_made} transfers ({report.total_hits_taken} hits = -{report.total_hit_penalties} pts)")
        print(f"Captaincy Points Earned:      {report.captaincy_points_total:,} pts (Success Rate: {report.captaincy_success_rate*100:.1f}%)")
        print(f"Average Bench Squad Cost:     £{report.avg_bench_cost:.2f}M")
        print(f"Final Squad + Bank Value:     £{report.final_team_value:.1f}M")
        if report.chips_used:
            print(f"Strategic Chips Deployed:     " + ", ".join(f"{chip.upper()} (GW{gw})" for chip, gw in report.chips_used.items()))
        print("=" * 90 + "\n")


if __name__ == '__main__':
    main()

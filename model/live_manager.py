"""Live Gameweek Matchday Manager & Decision Cockpit.

Provides automated weekly management for the live FPL season:
- Real-time injury / availability status filtering ('i', 'd', 's', 'a').
- Multi-Gameweek lookahead transfer planning (3-5 GW horizon).
- Strategic chip recommendation integration.
- Executive terminal briefing, Excel report write-back, and JSON export.

Usage:
    python -m model.live_manager [--season 2026-27] [--gw 1] [--horizon 3] [--bank 0.0] [--ft 1]
"""
import argparse
from dataclasses import asdict
import json
import os
import sys
from typing import Dict, Any, List, Tuple, Optional, Union
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.fixture_engine import predict_gameweek_fixtures
from model.solver import (
    solve_initial_squad,
    solve_multi_horizon_transfers,
    MultiHorizonSolution,
    SquadSolution,
    PlayerPick,
    load_player_costs,
)
from model.chip_optimizer import evaluate_chip_schedule, SeasonalChipPlan
from model.excel_exporter import export_excel_report
from model.set_pieces import enrich_predictions_with_set_pieces, load_set_piece_roles
from model.ownership_engine import enrich_predictions_with_ownership
from model.price_predictor import enrich_predictions_with_price_trends, RISING_LOCK, RISING_ALERT, FALLING_ALERT, FALLING_LOCK
from model.rotation_intelligence import apply_rotation_dampening
from model.matchup_intelligence import enrich_predictions_with_matchup_intelligence


def apply_live_injury_dampening(
    pred_df: pd.DataFrame,
    season: str = '2026-27',
    data_root: str = 'data',
) -> pd.DataFrame:
    """Adjust expected points based on latest official FPL status flags and news."""
    season_dir = os.path.join(data_root, season)
    players_raw_path = os.path.join(season_dir, 'players_raw.csv')

    if not os.path.exists(players_raw_path):
        return pred_df

    p_raw = pd.read_csv(players_raw_path)
    status_map = dict(zip(p_raw['code'], p_raw['status']))
    chance_map = dict(zip(p_raw['code'], p_raw['chance_of_playing_this_round']))
    news_map = dict(zip(p_raw['code'], p_raw['news']))

    df = pred_df.copy()

    for idx, row in df.iterrows():
        p_code = int(row.get('player_code', 0))
        status = str(status_map.get(p_code, 'a')).lower()
        chance = chance_map.get(p_code)

        mult = 1.0
        if status in ('i', 's', 'u'):  # Injured, Suspended, Unavailable
            mult = 0.0
        elif status == 'd':  # Doubtful
            if pd.notnull(chance):
                try:
                    mult = float(chance) / 100.0
                except (ValueError, TypeError):
                    mult = 0.5
            else:
                mult = 0.5

        if mult < 1.0:
            df.at[idx, 'expected_points'] = round(float(row.get('expected_points', 0.0)) * mult, 4)
            df.at[idx, 'p_start'] = round(float(row.get('p_start', 0.0)) * mult, 4)
            df.at[idx, 'p_app'] = round(float(row.get('p_app', 0.0)) * mult, 4)
            df.at[idx, 'news'] = str(news_map.get(p_code, ''))

    return df


def manage_gameweek(
    season: str = '2026-27',
    gw: int = 1,
    current_squad_codes: Optional[List[int]] = None,
    bank: float = 0.0,
    free_transfers: int = 1,
    horizon: int = 3,
    chip: Optional[str] = None,
    strategy: str = 'pure_xp',
    locked_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    excluded_player_codes: Optional[Union[List[Union[int, str]], str]] = None,
    forced_captain_code: Optional[Union[int, str]] = None,
    forced_vice_captain_code: Optional[Union[int, str]] = None,
    data_root: str = 'data',
    export_excel: bool = True,
    export_json: bool = True,
) -> Dict[str, Any]:
    """Execute complete live gameweek management decision workflow with Elite Enhancements."""
    season_dir = os.path.join(data_root, season)

    # 1. Load predictions for all gameweeks in lookahead horizon
    horizon_dfs: List[pd.DataFrame] = []
    for step in range(horizon):
        target_gw = min(38, gw + step)
        pred_df = predict_gameweek_fixtures(season=season, gw=target_gw, data_root=data_root, save_csv=(step == 0))

        # Layer in Elite Enhancements & Matchup Intelligence
        pred_df = enrich_predictions_with_matchup_intelligence(pred_df, season=season, data_root=data_root)
        pred_df = enrich_predictions_with_set_pieces(pred_df, season=season, data_root=data_root)
        pred_df = enrich_predictions_with_ownership(pred_df, season=season, data_root=data_root, strategy=strategy)
        pred_df = enrich_predictions_with_price_trends(pred_df, season=season, data_root=data_root)

        # Apply injury and rotation dampening on immediate GW
        if step == 0:
            pred_df = apply_live_injury_dampening(pred_df, season=season, data_root=data_root)
            pred_df = apply_rotation_dampening(pred_df, season=season, data_root=data_root)

        horizon_dfs.append(pred_df)

    gw1_df = horizon_dfs[0]

    # 2. If no squad provided, solve initial optimal squad
    if not current_squad_codes or len(current_squad_codes) != 15:
        initial_solution = solve_initial_squad(
            df=gw1_df,
            budget=100.0 - bank,
            chip=chip,
            season=season,
            data_root=data_root,
            strategy=strategy,
            locked_player_codes=locked_player_codes,
            excluded_player_codes=excluded_player_codes,
            forced_captain_code=forced_captain_code,
            forced_vice_captain_code=forced_vice_captain_code,
        )
        current_squad_codes = [p.player_code for p in initial_solution.squad]

    # 3. Solve multi-gameweek lookahead transfer trajectory
    multi_sol = solve_multi_horizon_transfers(
        current_squad_codes=current_squad_codes,
        horizon_dfs=horizon_dfs,
        free_transfers=free_transfers,
        bank=bank,
        discount_factor=0.90,
        start_gw=gw,
        season=season,
        data_root=data_root,
        strategy=strategy,
        locked_player_codes=locked_player_codes,
        excluded_player_codes=excluded_player_codes,
        forced_captain_code=forced_captain_code,
        forced_vice_captain_code=forced_vice_captain_code,
    )

    # 4. Check seasonal chip recommendations
    chip_plan = evaluate_chip_schedule(season=season, current_gw=gw, data_root=data_root)

    # 5. Build Matchday Action Plan
    curr_plan = multi_sol.gw_plans[0] if multi_sol.gw_plans else None
    active_sq = curr_plan.squad_solution if curr_plan else None

    # Immediate Action Logic
    if curr_plan and curr_plan.transfers_count == 0:
        action_summary = "ROLL TRANSFER (Save free transfer to accumulate 2 FTs next week)"
    elif curr_plan and curr_plan.hits_taken == 0:
        trans_in_names = ", ".join([p.web_name for p in curr_plan.transfers_in])
        trans_out_names = ", ".join([p.web_name for p in curr_plan.transfers_out])
        action_summary = f"EXECUTE {curr_plan.transfers_count} FREE TRANSFER(S): [IN] {trans_in_names} | [OUT] {trans_out_names}"
    else:
        trans_in_names = ", ".join([p.web_name for p in curr_plan.transfers_in]) if curr_plan else ""
        trans_out_names = ", ".join([p.web_name for p in curr_plan.transfers_out]) if curr_plan else ""
        action_summary = f"EXECUTE TRANSFERS WITH HIT (-{curr_plan.hit_penalty:.0f} pts): [IN] {trans_in_names} | [OUT] {trans_out_names}"

    # Build lookup for player tags (set-pieces, EO, price trends)
    meta_lookup = {}
    if not gw1_df.empty and 'player_code' in gw1_df.columns:
        for _, r in gw1_df.iterrows():
            c = int(r.get('player_code', 0))
            meta_lookup[c] = {
                'eo': float(r.get('eo', 0.0)),
                'pk': float(r.get('sp_pk_order', 0.0) or 0.0),
                'ck': float(r.get('sp_ck_order', 0.0) or 0.0),
                'fk': float(r.get('sp_fk_order', 0.0) or 0.0),
                'trend': str(r.get('price_trend', 'STABLE')),
                'vel': int(r.get('price_net_velocity', 0)),
            }

    # 6. Terminal Briefing Output
    print("\n" + "=" * 90)
    print(f"               FPL LIVE MATCHDAY COMMAND COCKPIT -- {season} GAMEWEEK {gw}")
    print("=" * 90)
    print(f"Current Bank: £{bank:.1f}M | Free Transfers: {free_transfers} | Lookahead Horizon: {horizon} GWs | Strategy: {strategy.upper()}")
    if active_sq:
        capt_name = active_sq.captain.web_name if active_sq.captain else "None"
        vice_name = active_sq.vice_captain.web_name if active_sq.vice_captain else "None"
        print(f"Optimal Formation: {active_sq.formation} | Starting XI xP: {active_sq.starting_xp:.2f} | Total Projected xP: {active_sq.total_xp:.2f}")
        print(f"Captain: {capt_name} [C] (+{active_sq.captain_xp:.2f} xP) | Vice-Captain: {vice_name} [V]")
    print("-" * 90)
    print(f"IMMEDIATE MATCHDAY ACTION: {action_summary}")
    print("-" * 90)

    if active_sq:
        print("\nSTARTING XI LINEUP:")
        for p in active_sq.starters:
            c_tag = " [C]" if p.is_captain else (" [V]" if p.is_vice_captain else "")
            p_meta = meta_lookup.get(p.player_code, {})
            sp_tags = []
            if p_meta.get('pk') == 1.0: sp_tags.append("PK1")
            if p_meta.get('ck') == 1.0: sp_tags.append("CK1")
            if p_meta.get('fk') == 1.0: sp_tags.append("FK1")
            sp_str = f" [{' '.join(sp_tags)}]" if sp_tags else ""
            eo_str = f" (EO: {p_meta.get('eo', 0.0)*100:.0f}%)" if p_meta.get('eo', 0.0) > 0 else ""
            print(f"  * {p.position:<3} | {p.web_name + c_tag:<20}{sp_str:<8} ({p.team:<14}) | {p.expected_points:>4.2f} xP | £{p.cost:>4.1f}M{eo_str}")

        print("\nORDERED BENCH:")
        for p in active_sq.bench:
            slot_str = f"Slot {p.bench_order} (GK)" if p.bench_order == 1 else f"Slot {p.bench_order} (Sub {p.bench_order - 1})"
            p_meta = meta_lookup.get(p.player_code, {})
            print(f"  * {slot_str:<15} | {p.position:<3} | {p.web_name:<18} ({p.team:<14}) | {p.expected_points:>4.2f} xP | £{p.cost:>4.1f}M")

    # Multi-Horizon Trajectory Summary
    print("\n" + "-" * 90)
    print("MULTI-GAMEWEEK TRANSFER ROADMAP:")
    print("-" * 90)
    for p in multi_sol.gw_plans:
        t_in = ", ".join([x.web_name for x in p.transfers_in]) if p.transfers_in else "None (Roll)"
        t_out = ", ".join([x.web_name for x in p.transfers_out]) if p.transfers_out else "None"
        hit_str = f" (-{p.hit_penalty:.0f} hit)" if p.hits_taken > 0 else ""
        print(f"  * GW{p.gw}: IN: {t_in:<25} | OUT: {t_out:<20} | Projected xP: {p.net_xp:.2f}{hit_str} | Bank: £{p.bank:.1f}M")

    # Price Momentum & Market Alerts
    if not gw1_df.empty and 'price_trend' in gw1_df.columns:
        rising = gw1_df[gw1_df['price_trend'].isin([RISING_LOCK, RISING_ALERT])].sort_values('price_net_velocity', ascending=False).head(5)
        falling = gw1_df[gw1_df['price_trend'].isin([FALLING_LOCK, FALLING_ALERT])].sort_values('price_net_velocity', ascending=True).head(5)

        if not rising.empty or not falling.empty:
            print("\n" + "-" * 90)
            print("MARKET & PRICE CHANGE MOMENTUM ALERTS:")
            print("-" * 90)
            for _, r in rising.iterrows():
                print(f"  ▲ [PRICE RISE] {r.get('web_name')} ({r.get('team')}) | Trend: {r.get('price_trend')} (+{int(r.get('price_net_velocity', 0)):,} net transfers)")
            for _, r in falling.iterrows():
                print(f"  ▼ [PRICE FALL] {r.get('web_name')} ({r.get('team')}) | Trend: {r.get('price_trend')} ({int(r.get('price_net_velocity', 0)):,} net transfers)")

    # Chip Advice
    print("\n" + "-" * 90)
    print("STRATEGIC CHIP ALERTS:")
    print("-" * 90)
    for chip_k, chip_rec in chip_plan.recommendations.items():
        if chip_rec.target_gw == gw:
            print(f"  [ALERT] ACTIVE RECOMMENDATION: Trigger {chip_rec.chip.upper()} in GW{gw}! (+{chip_rec.expected_value_delta:.1f} pts expected) -> {chip_rec.rationale}")
        elif chip_rec.target_gw <= gw + horizon:
            print(f"  [NOTICE] UPCOMING CHIP: {chip_rec.chip.upper()} recommended for GW{chip_rec.target_gw} -> {chip_rec.rationale}")
    print("=" * 90 + "\n")

    # 7. Write Excel & JSON reports
    if export_excel and active_sq:
        out_excel = os.path.join(season_dir, f"fpl_matchday_live_gw{gw}.xlsx")
        export_excel_report(
            solution=active_sq,
            pred_df=gw1_df,
            season=season,
            gw=gw,
            budget=100.0,
            chip=chip,
            data_root=data_root,
            output_path=out_excel,
        )

    if export_json and active_sq:
        out_json = os.path.join(season_dir, f"fpl_matchday_live_gw{gw}.json")
        payload = {
            'season': season,
            'gameweek': gw,
            'strategy': strategy,
            'action_summary': action_summary,
            'starting_xp': active_sq.starting_xp,
            'total_xp': active_sq.total_xp,
            'captain': active_sq.captain.web_name if active_sq.captain else None,
            'vice_captain': active_sq.vice_captain.web_name if active_sq.vice_captain else None,
            'starters': [asdict(p) for p in active_sq.starters],
            'bench': [asdict(p) for p in active_sq.bench],
            'multi_horizon_roadmap': [
                {
                    'gw': p.gw,
                    'transfers_in': [x.web_name for x in p.transfers_in],
                    'transfers_out': [x.web_name for x in p.transfers_out],
                    'hits_taken': p.hits_taken,
                    'net_xp': p.net_xp,
                    'bank': p.bank,
                }
                for p in multi_sol.gw_plans
            ],
        }
        with open(out_json, 'w') as f:
            json.dump(payload, f, indent=2)

    return {
        'action_summary': action_summary,
        'squad_solution': active_sq,
        'multi_horizon_solution': multi_sol,
        'chip_plan': chip_plan,
    }


def main():
    parser = argparse.ArgumentParser(description="Live FPL Gameweek Matchday Manager & Decision Cockpit")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Current gameweek number (1-38)")
    parser.add_argument('--bank', type=float, default=0.0, help="Bank balance in £M")
    parser.add_argument('--ft', type=int, default=1, help="Available free transfers (1-5)")
    parser.add_argument('--horizon', type=int, default=3, help="Lookahead horizon in gameweeks (1-5)")
    parser.add_argument('--chip', default=None, choices=['bboost', '3xc', 'freehit', 'wildcard'], help="FPL chip to activate")
    parser.add_argument('--strategy', default='pure_xp', choices=['pure_xp', 'rank_protect', 'differential_chase'], help="Game theory strategy")
    parser.add_argument('--lock-players', default=None, help="Comma-separated player names/codes to lock into squad (e.g. 'Palmer,Haaland')")
    parser.add_argument('--exclude-players', default=None, help="Comma-separated player names/codes to exclude (e.g. 'B.Fernandes')")
    parser.add_argument('--captain', default=None, help="Player name or code to force as captain (e.g. 'Palmer')")
    parser.add_argument('--vice-captain', default=None, help="Player name or code to force as vice-captain")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    args = parser.parse_args()

    manage_gameweek(
        season=args.season,
        gw=args.gw,
        bank=args.bank,
        free_transfers=args.ft,
        horizon=args.horizon,
        chip=args.chip,
        strategy=args.strategy,
        locked_player_codes=args.lock_players,
        excluded_player_codes=args.exclude_players,
        forced_captain_code=args.captain,
        forced_vice_captain_code=args.vice_captain,
        data_root=args.data_root,
    )


if __name__ == '__main__':
    main()

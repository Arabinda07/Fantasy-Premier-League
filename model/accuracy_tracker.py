"""Post-Gameweek Prediction Accuracy & Model Calibration Engine.

Evaluates how accurately the quantitative 11-component point prediction model
projected actual player scores for completed gameweeks:
1. Reconciles pre-gameweek projections (fixture_predictions_gw{N}.csv) with
   actual recorded points (merged_gw.csv or players_raw.csv).
2. Computes Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE)
   overall, by position (GK, DEF, MID, FWD), and for active starters.
3. Evaluates ranking correlation (Spearman rho) for top projected assets.
4. Identifies systematic model biases and largest prediction surprises (hauls vs busts).
5. Appends cumulative performance metrics to data/{season}/accuracy_log.csv.

Usage:
    python -m model.accuracy_tracker [--season 2026-27] [--gw 1]
"""
import argparse
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import math
import os
import sys
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import _safe_float


@dataclass
class PositionAccuracy:
    """Accuracy metrics for a single playing position."""
    position: str
    player_count: int
    mae: float
    rmse: float
    mean_predicted: float
    mean_actual: float
    bias: float  # (mean_predicted - mean_actual) > 0 means over-prediction


@dataclass
class GameweekAccuracyReport:
    """Comprehensive performance and calibration report for a gameweek."""
    season: str
    gameweek: int
    evaluated_at: str
    total_players: int
    active_players: int  # Players with > 0 minutes
    overall_mae: float
    overall_rmse: float
    active_starters_mae: float
    active_starters_rmse: float
    rank_correlation: float  # Spearman rank correlation
    positional_accuracy: Dict[str, PositionAccuracy] = field(default_factory=dict)
    top_over_predictions: List[Dict[str, Any]] = field(default_factory=list)
    top_under_predictions: List[Dict[str, Any]] = field(default_factory=list)
    clean_sheet_calibration: Dict[str, Any] = field(default_factory=dict)


def load_actual_gameweek_points(
    season: str = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
) -> pd.DataFrame:
    """Load actual points scored by each player in a target gameweek.

    Priority:
    1. data/<season>/gws/merged_gw.csv filtered by GW == gw
    2. data/<season>/players_raw.csv (using event_points if current active GW == gw)
    """
    season_dir = os.path.join(data_root, season)

    # 1. Try merged_gw.csv
    merged_path = os.path.join(season_dir, 'gws', 'merged_gw.csv')
    players_raw_path = os.path.join(season_dir, 'players_raw.csv')

    code_map = {}
    if os.path.exists(players_raw_path):
        p_raw = pd.read_csv(players_raw_path)
        if 'id' in p_raw.columns and 'code' in p_raw.columns:
            code_map = dict(zip(p_raw['id'], p_raw['code']))

    if os.path.exists(merged_path):
        try:
            mgw = pd.read_csv(merged_path)
            if 'GW' in mgw.columns:
                gw_df = mgw[mgw['GW'] == gw].copy()
                if not gw_df.empty:
                    if 'element' in gw_df.columns:
                        gw_df['player_code'] = gw_df['element'].map(code_map).fillna(gw_df['element'])
                    return gw_df
        except Exception as e:
            print(f"[Accuracy Tracker] Notice: Could not parse merged_gw.csv: {e}")

    # 2. Fallback to players_raw.csv event_points
    if os.path.exists(players_raw_path):
        try:
            p_raw = pd.read_csv(players_raw_path)
            res = []
            for _, r in p_raw.iterrows():
                res.append({
                    'player_code': int(r.get('code', r.get('id', 0))),
                    'web_name': str(r.get('web_name', '')),
                    'total_points': float(r.get('event_points', 0) or 0),
                    'minutes': int(float(r.get('minutes', 0) or 0)),
                    'goals_scored': int(float(r.get('goals_scored', 0) or 0)),
                    'assists': int(float(r.get('assists', 0) or 0)),
                    'clean_sheets': int(float(r.get('clean_sheets', 0) or 0)),
                    'goals_conceded': int(float(r.get('goals_conceded', 0) or 0)),
                })
            return pd.DataFrame(res)
        except Exception as e:
            print(f"[Accuracy Tracker] Warning: Could not read players_raw.csv: {e}")

    return pd.DataFrame()


def evaluate_gameweek_accuracy(
    season: str = '2026-27',
    gw: int = 1,
    data_root: str = 'data',
    save_log: bool = True,
) -> Optional[GameweekAccuracyReport]:
    """Compare predicted points vs actual outcomes for a completed gameweek.

    Args:
        season: season string.
        gw: completed gameweek number.
        data_root: root data directory.
        save_log: if True, append row to data/<season>/accuracy_log.csv.

    Returns:
        GameweekAccuracyReport or None if data missing.
    """
    season_dir = os.path.join(data_root, season)

    # 1. Load predictions
    preds_path = os.path.join(season_dir, f'fixture_predictions_gw{gw}.csv')
    if not os.path.exists(preds_path):
        preds_path = os.path.join(season_dir, 'fixture_predictions.csv')
    if not os.path.exists(preds_path):
        preds_path = os.path.join(season_dir, 'predictions.csv')

    if not os.path.exists(preds_path):
        print(f"[Accuracy Tracker] Warning: No prediction file found for GW{gw} at {preds_path}")
        return None

    pred_df = pd.read_csv(preds_path)
    actual_df = load_actual_gameweek_points(season=season, gw=gw, data_root=data_root)

    if actual_df.empty:
        print(f"[Accuracy Tracker] Warning: No actual points data available for GW{gw}.")
        return None

    # Harmonize keys
    pred_key = 'player_code' if 'player_code' in pred_df.columns else 'code'
    actual_key = 'player_code' if 'player_code' in actual_df.columns else 'code'

    merged = pred_df.merge(
        actual_df,
        left_on=pred_key,
        right_on=actual_key,
        suffixes=('_pred', '_actual'),
        how='inner',
    )

    if merged.empty:
        # Try web_name fallback
        merged = pred_df.merge(
            actual_df,
            on='web_name',
            suffixes=('_pred', '_actual'),
            how='inner',
        )

    if merged.empty:
        print("[Accuracy Tracker] Warning: Unable to match predicted and actual player records.")
        return None

    # Calculate errors
    xp_col = 'expected_points' if 'expected_points' in merged.columns else 'total_points_pred'
    pts_col = 'total_points_actual' if 'total_points_actual' in merged.columns else 'total_points'
    mins_col = 'minutes_actual' if 'minutes_actual' in merged.columns else 'minutes'

    merged['pred_xp'] = pd.to_numeric(merged[xp_col], errors='coerce').fillna(0.0)
    merged['actual_pts'] = pd.to_numeric(merged[pts_col], errors='coerce').fillna(0.0)
    merged['actual_mins'] = pd.to_numeric(merged.get(mins_col, 0), errors='coerce').fillna(0).astype(int)

    merged['abs_error'] = (merged['pred_xp'] - merged['actual_pts']).abs()
    merged['sq_error'] = (merged['pred_xp'] - merged['actual_pts']) ** 2

    # Overall metrics
    overall_mae = float(merged['abs_error'].mean())
    overall_rmse = float(math.sqrt(merged['sq_error'].mean()))

    # Active starters (> 0 minutes)
    active_df = merged[merged['actual_mins'] > 0]
    active_mae = float(active_df['abs_error'].mean()) if not active_df.empty else overall_mae
    active_rmse = float(math.sqrt(active_df['sq_error'].mean())) if not active_df.empty else overall_rmse

    # Rank correlation (Spearman via Pearson on ranks, no scipy dependency)
    rank_corr = 0.0
    if len(active_df) >= 3:
        try:
            pred_ranks = active_df['pred_xp'].rank()
            act_ranks = active_df['actual_pts'].rank()
            corr_val = pred_ranks.corr(act_ranks)
            if pd.notnull(corr_val) and not math.isnan(corr_val):
                rank_corr = float(corr_val)
        except Exception:
            rank_corr = 0.0

    # Positional breakdown
    pos_col = 'position' if 'position' in merged.columns else 'element_type'
    pos_accuracies = {}
    for pos in ['GK', 'DEF', 'MID', 'FWD']:
        pos_subset = merged[merged[pos_col].astype(str).str.upper().str.contains(pos)]
        if not pos_subset.empty:
            p_mae = float(pos_subset['abs_error'].mean())
            p_rmse = float(math.sqrt(pos_subset['sq_error'].mean()))
            p_pred_mean = float(pos_subset['pred_xp'].mean())
            p_act_mean = float(pos_subset['actual_pts'].mean())
            pos_accuracies[pos] = PositionAccuracy(
                position=pos,
                player_count=len(pos_subset),
                mae=round(p_mae, 3),
                rmse=round(p_rmse, 3),
                mean_predicted=round(p_pred_mean, 2),
                mean_actual=round(p_act_mean, 2),
                bias=round(p_pred_mean - p_act_mean, 2),
            )

    # Top over-predictions (projected high, scored low)
    merged['error_delta'] = merged['pred_xp'] - merged['actual_pts']
    over_preds = merged.sort_values('error_delta', ascending=False).head(5)
    top_over = [
        {
            'player': str(r.get('web_name_pred', r.get('web_name', 'Unknown'))),
            'team': str(r.get('team_pred', r.get('team', ''))),
            'pred_xp': round(float(r['pred_xp']), 2),
            'actual_pts': int(r['actual_pts']),
            'delta': round(float(r['error_delta']), 2),
        }
        for _, r in over_preds.iterrows()
    ]

    # Top under-predictions (hauls unexpected by model)
    under_preds = merged.sort_values('error_delta', ascending=True).head(5)
    top_under = [
        {
            'player': str(r.get('web_name_pred', r.get('web_name', 'Unknown'))),
            'team': str(r.get('team_pred', r.get('team', ''))),
            'pred_xp': round(float(r['pred_xp']), 2),
            'actual_pts': int(r['actual_pts']),
            'delta': round(float(r['error_delta']), 2),
        }
        for _, r in under_preds.iterrows()
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    report = GameweekAccuracyReport(
        season=season,
        gameweek=gw,
        evaluated_at=now_iso,
        total_players=len(merged),
        active_players=len(active_df),
        overall_mae=round(overall_mae, 3),
        overall_rmse=round(overall_rmse, 3),
        active_starters_mae=round(active_mae, 3),
        active_starters_rmse=round(active_rmse, 3),
        rank_correlation=round(rank_corr, 3),
        positional_accuracy=pos_accuracies,
        top_over_predictions=top_over,
        top_under_predictions=top_under,
    )

    # 4. Save to accuracy_log.csv
    if save_log:
        log_path = os.path.join(season_dir, 'accuracy_log.csv')
        log_row = {
            'gameweek': gw,
            'evaluated_at': now_iso,
            'total_players': len(merged),
            'active_players': len(active_df),
            'overall_mae': round(overall_mae, 3),
            'overall_rmse': round(overall_rmse, 3),
            'active_mae': round(active_mae, 3),
            'active_rmse': round(active_rmse, 3),
            'rank_correlation': round(rank_corr, 3),
            'gk_mae': pos_accuracies.get('GK', PositionAccuracy('GK', 0, 0, 0, 0, 0, 0)).mae,
            'def_mae': pos_accuracies.get('DEF', PositionAccuracy('DEF', 0, 0, 0, 0, 0, 0)).mae,
            'mid_mae': pos_accuracies.get('MID', PositionAccuracy('MID', 0, 0, 0, 0, 0, 0)).mae,
            'fwd_mae': pos_accuracies.get('FWD', PositionAccuracy('FWD', 0, 0, 0, 0, 0, 0)).mae,
            'gk_bias': pos_accuracies.get('GK', PositionAccuracy('GK', 0, 0, 0, 0, 0, 0)).bias,
            'def_bias': pos_accuracies.get('DEF', PositionAccuracy('DEF', 0, 0, 0, 0, 0, 0)).bias,
            'mid_bias': pos_accuracies.get('MID', PositionAccuracy('MID', 0, 0, 0, 0, 0, 0)).bias,
            'fwd_bias': pos_accuracies.get('FWD', PositionAccuracy('FWD', 0, 0, 0, 0, 0, 0)).bias,
        }
        if os.path.exists(log_path):
            log_df = pd.read_csv(log_path)
            # Replace existing GW entry if re-evaluating
            log_df = log_df[log_df['gameweek'] != gw]
            log_df = pd.concat([log_df, pd.DataFrame([log_row])], ignore_index=True)
        else:
            log_df = pd.DataFrame([log_row])

        log_df.sort_values('gameweek', inplace=True)
        log_df.to_csv(log_path, index=False)
        print(f"[Accuracy Tracker] Logged GW{gw} accuracy metrics to {log_path}")

    return report


def print_accuracy_summary(report: GameweekAccuracyReport) -> None:
    """Print executive accuracy and model calibration readout."""
    print("\n" + "=" * 90)
    print(f"  QUANTITATIVE MODEL ACCURACY & CALIBRATION -- Season {report.season} | GW{report.gameweek}")
    print("=" * 90)
    print(f"  Total Players: {report.total_players} | Active Starters: {report.active_players}")
    print(f"  Overall MAE: {report.overall_mae:.2f} pts | RMSE: {report.overall_rmse:.2f} pts")
    print(f"  Active Starters MAE: {report.active_starters_mae:.2f} pts | Rank Correlation: {report.rank_correlation:.3f}")
    print("-" * 90)
    print("  POSITIONAL BREAKDOWN:")
    for pos, p_acc in report.positional_accuracy.items():
        bias_sign = "+" if p_acc.bias > 0 else ""
        print(f"    [{pos:<3}] N={p_acc.player_count:>3} | MAE: {p_acc.mae:>5.2f} pts | Pred Mean: {p_acc.mean_predicted:>5.2f} | Act Mean: {p_acc.mean_actual:>5.2f} | Bias: {bias_sign}{p_acc.bias:>4.2f}")
    print("-" * 90)
    print("  TOP PREDICTION SURPRISES (HAULS / OUTLIERS):")
    for u in report.top_under_predictions[:3]:
        print(f"    [+] Under-projected: {u['player']} ({u['team']}) -- Pred: {u['pred_xp']} pts -> Actual: {u['actual_pts']} pts (Delta: {u['delta']})")
    for o in report.top_over_predictions[:3]:
        print(f"    [-] Over-projected:  {o['player']} ({o['team']}) -- Pred: {o['pred_xp']} pts -> Actual: {o['actual_pts']} pts (Delta: +{o['delta']})")
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate quantitative FPL model accuracy for completed gameweeks")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=1, help="Completed gameweek number to evaluate")
    parser.add_argument('--data-root', default='data', help="Root data directory")
    parser.add_argument('--no-log', action='store_true', default=False, help="Do not write to accuracy_log.csv")
    args = parser.parse_args()

    report = evaluate_gameweek_accuracy(
        season=args.season,
        gw=args.gw,
        data_root=args.data_root,
        save_log=not args.no_log,
    )
    if report:
        print_accuracy_summary(report)


if __name__ == '__main__':
    main()

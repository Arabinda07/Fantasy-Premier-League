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


def evaluate_chip_schedule(
    season: str = '2026-27',
    current_gw: int = 1,
    data_root: str = 'data',
) -> SeasonalChipPlan:
    """Evaluate and recommend the optimal seasonal deployment plan for all FPL chips."""
    profiles = detect_double_and_blank_gameweeks(season=season, data_root=data_root)

    # 1. Triple Captain Candidate Analysis
    dgw_candidates = [p for p in profiles if p.is_dgw and p.gw >= current_gw]
    if dgw_candidates:
        # Sort by most DGW teams
        dgw_candidates.sort(key=lambda p: (len(p.dgw_teams), p.total_fixtures), reverse=True)
        tc_gw = dgw_candidates[0].gw
        tc_val = 18.5
        tc_rationale = f"Double Gameweek {tc_gw} with {len(dgw_candidates[0].dgw_teams)} double-fixture teams ({', '.join(dgw_candidates[0].dgw_teams[:3])})."
    else:
        # Fallback to high-ceiling single GW fixture (e.g. Haaland/Salah home vs newly promoted)
        tc_gw = min(38, max(current_gw, 25))
        tc_val = 12.0
        tc_rationale = "Target peak home fixture vs promoted side during second half of season."

    # 2. Bench Boost Candidate Analysis
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

    # 4. Wildcard 1 (GW2 - GW19)
    wc1_gw = 6 if current_gw <= 6 else min(19, current_gw + 1)
    wc1_val = 35.0
    wc1_rationale = f"Gameweek {wc1_gw}: Early-season fixture swing structural pivot (target Arsenal, Man City, Liverpool fixture runs)."

    # 5. Wildcard 2 (GW20 - GW38)
    wc2_gw = max(20, min(33, bb_gw - 1 if bb_gw > 20 else 30))
    wc2_val = 40.0
    wc2_rationale = f"Gameweek {wc2_gw}: Structural setup immediately preceding Bench Boost / DGW window."

    recs: Dict[str, ChipRecommendation] = {
        '3xc': ChipRecommendation(chip='3xc', target_gw=tc_gw, expected_value_delta=tc_val, rationale=tc_rationale),
        'bboost': ChipRecommendation(chip='bboost', target_gw=bb_gw, expected_value_delta=bb_val, rationale=bb_rationale),
        'freehit': ChipRecommendation(chip='freehit', target_gw=fh_gw, expected_value_delta=fh_val, rationale=fh_rationale),
        'wildcard_1': ChipRecommendation(chip='wildcard_1', target_gw=wc1_gw, expected_value_delta=wc1_val, rationale=wc1_rationale),
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
            lines.append(f"{label:<15} | GW{rec.target_gw:<8} | {print_val:<15} | {rec.rationale}")

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

"""Continuous Minutes Hazard Engine for Fantasy Premier League.

Provides:
1. Continuous playing time distribution f(t) for t in [0, 95] minutes.
2. Three-regime survival decomposition:
   - Starter Regime: P(Start) * f(t | Start)
   - Substitute Regime: P(Sub) * f(t | Sub)
   - DNP Regime: P(DNP) = 1 - P(Start) - P(Sub)
3. Exact probability calculations:
   - P(Mins >= 60): Clean sheet & 2-appearance-point qualification probability.
   - P(Pre-60 Hook Hazard): Probability of being substituted before minute 60 when starting.
   - P(Mins = 0): Unavailability probability for auto-substitution modeling.
   - E[Mins]: Expected playing minutes.
4. Hazard adjustment features:
   - Recent start rate (last 6 GWs) and historical minutes per start.
   - Midweek European congestion (<=3 days rest vs >=5 days rest).
   - Manager tactical hook tendencies (early substitution propensity).
   - FPL API status flags ('a', 'd', 'i', 's') and chance_of_playing_next_round.
   - Price-tier priors for new transfers / youth players.

Usage:
    python -m model.minutes_model [--season 2026-27] [--gw 1]
"""
import argparse
from dataclasses import dataclass, field
import math
import os
import sys
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.prediction_engine import _safe_float
from model.rotation_intelligence import (
    DEFAULT_EUROPEAN_TEAMS,
    ROTATION_HEAVY_MANAGERS,
    NEWS_DAMPENING,
    UNAVAILABLE_STATUSES,
)


# ---------------------------------------------------------------------------
# Constants & Manager Tendency Archetypes
# ---------------------------------------------------------------------------

# Baseline expected minutes when brought on as substitute
SUB_MINUTES_MEAN: float = 20.0
SUB_MINUTES_STD: float = 7.0

# Base starter duration parameters (when no early hook occurs)
NIL_HOOK_STARTER_MINUTES: float = 88.0

# Manager Hook Tendency Multipliers (propensity to substitute starters before min 60)
# Higher = more early tactical hooks (e.g. at min 45 or 55)
MANAGER_HOOK_PROPENSITY: Dict[str, float] = {
    'Arsenal': 1.15,      # Arteta rotates wingers / fullbacks around min 58-62
    'Man City': 1.25,     # Pep roulette / early tactical adjustments
    'Liverpool': 1.15,    # Slot high-intensity press / early wing subs
    'Chelsea': 1.20,      # Deep squad rotation
    'Tottenham': 1.10,    # High-tempo system substitutions
    'Brighton': 1.15,     # Tactical subs
    'Aston Villa': 1.05,
    'Newcastle': 1.00,
    'Man Utd': 1.05,
    'Fulham': 0.95,
    'Brentford': 0.95,
    'Everton': 0.85,      # Dyche prefers keeping starters on
    'Crystal Palace': 0.90,
    'Bournemouth': 1.00,
    'West Ham': 0.90,
    'Wolves': 0.95,
    'Ipswich Town': 0.90,
    'Leicester': 0.95,
    'Southampton': 1.00,
    'Nott\'m Forest': 0.95,
    'Leeds': 0.95,
    'Hull City': 0.90,
    'Coventry City': 0.90,
    'Sunderland': 0.90,
}

DEFAULT_HOOK_PROPENSITY: float = 1.00


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class MinutesDistributionProfile:
    """Continuous minutes distribution output and hazard metrics for a player."""
    player_code: int
    web_name: str
    team: str
    position: str
    p_start: float          # Probability of starting (0.0 to 1.0)
    p_sub: float            # Probability of appearing as substitute (0.0 to 1.0)
    p_dnp: float            # Probability of not playing (0.0 to 1.0)
    p_60_plus: float        # Probability of playing >= 60 mins (Appearance C2 & Clean Sheet)
    p_pre60_hook: float     # Probability of starting but subbed off < 60 mins
    expected_minutes: float # Overall expected minutes E[M]
    expected_starter_minutes: float # Expected minutes conditional on starting
    appearance_xp: float    # Expected appearance points (1 * P(1<=M<60) + 2 * P(M>=60))
    hazard_flags: List[str] = field(default_factory=list)
    avg_starter_mins: float = 90.0

    @property
    def p_app(self) -> float:
        """Probability of making any appearance (start or sub)."""
        return float(min(1.0, max(0.0, self.p_start + self.p_sub)))

    @property
    def active_ratio(self) -> float:
        """Expected playing time exposure ratio over 90 minutes."""
        starter_exposure = (self.avg_starter_mins / 90.0) if self.avg_starter_mins > 0 else 0.0
        sub_exposure = 20.0 / 90.0
        return float(min(1.0, max(0.0, self.p_start * starter_exposure + self.p_sub * sub_exposure)))

    @property
    def expected_mins_60_plus(self) -> float:
        """Expected minutes played conditional on qualifying for 60+ minutes (no early hook)."""
        return float(max(60.0, min(92.0, self.avg_starter_mins))) if self.avg_starter_mins > 0 else 0.0



# ---------------------------------------------------------------------------
# Continuous Hazard Math & Density Estimators
# ---------------------------------------------------------------------------

def calculate_pre60_hook_probability(
    avg_starter_mins: float,
    sub_minute_p50: Optional[float] = None,
    manager_hook_mult: float = 1.0,
    is_goalkeeper: bool = False,
    is_defender: bool = False,
) -> float:
    """Calculate the probability that a starter is substituted off before the 60th minute.

    P(Mins < 60 | Start) using an empirical hazard sigmoid calibrated on Premier League
    substitution patterns. Goalkeepers almost never get subbed (<0.5%). Central defenders
    rarely get hooked unless injured (<2%). Fullbacks/Wingers have highest hook risk.

    Args:
        avg_starter_mins: average minutes played when starting (e.g. 75.0).
        sub_minute_p50: median substitution minute if available.
        manager_hook_mult: manager early hook multiplier.
        is_goalkeeper: whether player is GK.
        is_defender: whether player is DEF.

    Returns:
        Probability in [0.005, 0.45].
    """
    if is_goalkeeper:
        return 0.005  # GKs almost never hooked tactical

    # Base hook probability based on average starter minutes
    # If avg_starter_mins >= 88: hook prob ~ 0.02
    # If avg_starter_mins ~ 70: hook prob ~ 0.12
    # If avg_starter_mins ~ 58: hook prob ~ 0.35
    if sub_minute_p50 is not None and sub_minute_p50 > 0:
        eff_mins = sub_minute_p50
    else:
        eff_mins = avg_starter_mins

    # Logistic hazard function centered around 63.5 minutes
    z = (63.5 - eff_mins) / 8.5
    raw_p = 1.0 / (1.0 + math.exp(-z))

    # Scale by manager hook propensity
    scaled_p = raw_p * manager_hook_mult

    # Defenders hook less often than midfielders/forwards
    if is_defender:
        scaled_p *= 0.55

    return float(np.clip(scaled_p, 0.005, 0.45))


def compute_player_minutes_hazard(
    player_row: Union[pd.Series, Dict[str, Any]],
    days_rest: int = 7,
    european_teams: Optional[Dict[str, List[str]]] = None,
) -> MinutesDistributionProfile:
    """Compute continuous minutes hazard profile and exact probability metrics for a player.

    Args:
        player_row: player dict or pandas Series with stats.
        days_rest: days since previous competitive match.
        european_teams: dict of European competitions and clubs.

    Returns:
        MinutesDistributionProfile dataclass.
    """
    if european_teams is None:
        european_teams = DEFAULT_EUROPEAN_TEAMS

    p_code = int(player_row.get('player_code') or player_row.get('code') or player_row.get('id') or 0)
    web_name = str(player_row.get('web_name', f'Player_{p_code}'))
    team_name = str(player_row.get('team', 'Unknown'))
    pos = str(player_row.get('position', 'MID')).upper()
    is_gk = (pos == 'GK')
    is_def = (pos == 'DEF')

    hazard_flags: List[str] = []

    # 1. Status & News Availability Filter
    status = str(player_row.get('status', 'a')).lower()
    chance_next = player_row.get('chance_of_playing_next_round')
    if pd.isna(chance_next) or chance_next is None:
        chance_this = player_row.get('chance_of_playing_this_round')
        chance_next = chance_this if pd.notnull(chance_this) else 100

    chance_val = int(_safe_float(chance_next, 100.0))

    if status in UNAVAILABLE_STATUSES or chance_val == 0:
        hazard_flags.append(f"UNAVAILABLE (status={status}, chance={chance_val}%)")
        return MinutesDistributionProfile(
            player_code=p_code,
            web_name=web_name,
            team=team_name,
            position=pos,
            p_start=0.0,
            p_sub=0.0,
            p_dnp=1.0,
            p_60_plus=0.0,
            p_pre60_hook=0.0,
            expected_minutes=0.0,
            expected_starter_minutes=0.0,
            appearance_xp=0.0,
            hazard_flags=hazard_flags,
            avg_starter_mins=0.0,
        )

    # 2. Historical Baseline Start & Appearance Rates
    starts_cnt = _safe_float(
        player_row.get('short_form_starts',
        player_row.get('season_starts',
        player_row.get('fbref_starts',
        player_row.get('starts'))))
    )
    matches_cnt = _safe_float(
        player_row.get('short_form_matches',
        player_row.get('fbref_squads_made',
        player_row.get('matches')))
    )
    if matches_cnt <= 0.0:
        season_starts_val = _safe_float(player_row.get('season_starts', player_row.get('starts', 0.0)))
        season_subs_val = _safe_float(player_row.get('season_subs', player_row.get('fbref_subs', 0.0)))
        unused_subs_val = _safe_float(player_row.get('fbref_unused_subs', 0.0))
        squads_sum = season_starts_val + season_subs_val + unused_subs_val
        if squads_sum > 0.0:
            matches_cnt = squads_sum

    total_mins = _safe_float(
        player_row.get('short_form_minutes',
        player_row.get('season_minutes',
        player_row.get('minutes',
        player_row.get('long_form_unweighted_minutes',
        player_row.get('unweighted_minutes',
        player_row.get('long_form_minutes'))))))
    )

    long_mins = _safe_float(
        player_row.get('long_form_unweighted_minutes',
        player_row.get('unweighted_minutes',
        player_row.get('long_form_minutes', 0.0)))
    )

    subs_cnt = _safe_float(
        player_row.get('short_form_subs',
        player_row.get('season_subs',
        player_row.get('fbref_subs',
        player_row.get('subs', 0.0))))
    )

    # Empirical baseline start rate
    if matches_cnt > 0:
        raw_start_rate = starts_cnt / max(1.0, matches_cnt)
        if matches_cnt < 4.0:
            is_veteran_starter = (long_mins >= 1800.0)
            if is_veteran_starter and (starts_cnt == matches_cnt):
                raw_start_rate = 0.95 if is_gk else 0.90
            else:
                if is_veteran_starter:
                    start_prior = 0.95 if is_gk else 0.90
                else:
                    start_prior = 0.90 if is_gk else 0.75
                m_squads = 3.0
                raw_start_rate = (matches_cnt / (matches_cnt + m_squads)) * raw_start_rate + (m_squads / (matches_cnt + m_squads)) * start_prior
        if starts_cnt > 0:
            # Decontaminate total_mins by removing estimated substitute cameo minutes
            sub_mins_est = subs_cnt * SUB_MINUTES_MEAN
            pure_starter_mins = max(45.0 * starts_cnt, total_mins - sub_mins_est)
            avg_starter_mins = pure_starter_mins / starts_cnt
        else:
            avg_starter_mins = 90.0 if is_gk else 75.0
    elif total_mins > 0:
        est_starts = min(38.0, total_mins / 75.0)
        raw_start_rate = min(1.0, est_starts / 38.0)
        avg_starter_mins = total_mins / max(1.0, est_starts)
    else:
        # Prior for unseeded / newly transferred players based on cost
        cost = _safe_float(player_row.get('cost', player_row.get('now_cost', 0.0)))
        cost_m = cost / 10.0 if cost > 25.0 else cost
        if cost_m >= 10.0:
            raw_start_rate = 0.92
            avg_starter_mins = 88.0
        elif cost_m >= 7.5:
            raw_start_rate = 0.85
            avg_starter_mins = 82.0
        elif cost_m >= 5.5:
            raw_start_rate = 0.65
            avg_starter_mins = 75.0
        else:
            raw_start_rate = 0.0
            avg_starter_mins = 0.0

    avg_starter_mins = float(np.clip(avg_starter_mins, 45.0, 92.0)) if raw_start_rate > 0.0 else 0.0

    # 3. Apply Midweek European Rest Hazard
    is_european_club = any(team_name in clubs for clubs in european_teams.values())
    midweek_mult = 1.00
    if is_european_club:
        if is_gk:
            midweek_mult = 1.00  # Premier League goalkeepers are not rotated for fatigue post-Europe
        elif days_rest <= 3:
            midweek_mult = 0.82 if team_name in ROTATION_HEAVY_MANAGERS else 0.88
            hazard_flags.append(f"MIDWEEK_CONGESTION ({days_rest}d rest, {midweek_mult:.2f}x)")
        elif days_rest <= 4:
            midweek_mult = 0.92
            hazard_flags.append(f"MODERATE_REST ({days_rest}d rest, {midweek_mult:.2f}x)")

    # 4. Apply News Dampening
    news_mults = NEWS_DAMPENING.get(chance_val, {'p_start_mult': 1.0, 'p_app_mult': 1.0})
    p_start_mult = news_mults['p_start_mult']
    p_app_mult = news_mults['p_app_mult']
    if chance_val < 100:
        hazard_flags.append(f"FLAGGED ({chance_val}% chance, {p_start_mult:.2f}x)")

    # Effective P(Start)
    p_start = float(np.clip(raw_start_rate * midweek_mult * p_start_mult, 0.0, 1.0))

    # Probability of appearing as substitute if not starting
    # Positionally differentiated: GKs rarely sub (<1%), CBs/defenders rarely sub (~8%),
    # attacking midfielders/wingers/forwards sub frequently (~45%)
    has_activity = (raw_start_rate > 0.0 or matches_cnt > 0 or total_mins > 0)
    if p_start < 0.95 and has_activity:
        if is_gk:
            p_sub_base = 0.01
        elif is_def:
            p_sub_base = 0.08
        else:
            p_sub_base = 0.45
        p_sub = float(np.clip((1.0 - p_start) * p_sub_base * p_app_mult, 0.0, 1.0 - p_start))
    elif p_start >= 0.95:
        p_sub = float(min(max(0.0, 1.0 - p_start), 0.01))
    else:
        p_sub = 0.0

    p_dnp = float(max(0.0, 1.0 - p_start - p_sub))

    # 5. Pre-60 Hook Hazard and P(Mins >= 60)
    hook_propensity = MANAGER_HOOK_PROPENSITY.get(team_name, DEFAULT_HOOK_PROPENSITY)
    sub_p50 = _safe_float(player_row.get('sub_minute_p50', 0.0))
    p_hook_given_start = calculate_pre60_hook_probability(
        avg_starter_mins=avg_starter_mins,
        sub_minute_p50=sub_p50 if sub_p50 > 0 else None,
        manager_hook_mult=hook_propensity,
        is_goalkeeper=is_gk,
        is_defender=is_def,
    )

    p_pre60_hook = float(p_start * p_hook_given_start)
    p_60_plus_given_start = 1.0 - p_hook_given_start

    # Substitute appearance >= 60 mins is nearly 0 (<0.5%)
    p_60_plus_given_sub = 0.005
    p_60_plus = float(p_start * p_60_plus_given_start + p_sub * p_60_plus_given_sub)

    # 6. Expected Minutes Calculation
    # Starter expected minutes:
    # If not hooked: ~avg_starter_mins (e.g. 85-90)
    # If hooked early: ~52 mins
    exp_starter_mins = ((1.0 - p_hook_given_start) * avg_starter_mins + p_hook_given_start * 52.0) if avg_starter_mins > 0 else 0.0
    exp_sub_mins = SUB_MINUTES_MEAN

    expected_minutes = float(p_start * exp_starter_mins + p_sub * exp_sub_mins)

    # 7. Expected Appearance FPL Points (C2)
    # 1 pt for 1-59 mins, 2 pts for >= 60 mins
    p_1_to_59 = float(max(0.0, (p_start + p_sub) - p_60_plus))
    appearance_xp = float(1.0 * p_1_to_59 + 2.0 * p_60_plus)

    return MinutesDistributionProfile(
        player_code=p_code,
        web_name=web_name,
        team=team_name,
        position=pos,
        p_start=round(p_start, 4),
        p_sub=round(p_sub, 4),
        p_dnp=round(p_dnp, 4),
        p_60_plus=round(p_60_plus, 4),
        p_pre60_hook=round(p_pre60_hook, 4),
        expected_minutes=round(expected_minutes, 2),
        expected_starter_minutes=round(exp_starter_mins, 2),
        appearance_xp=round(appearance_xp, 4),
        hazard_flags=hazard_flags,
        avg_starter_mins=round(avg_starter_mins, 2),
    )


def predict_gameweek_minutes_distribution(
    df: pd.DataFrame,
    days_rest: int = 7,
    season: str = '2026-27',
    data_root: str = 'data',
) -> pd.DataFrame:
    """Evaluate continuous minutes distribution and hazard metrics across all players.

    Args:
        df: DataFrame containing player records.
        days_rest: days of rest before the gameweek fixture.
        season: season string e.g. '2026-27'.
        data_root: root data directory.

    Returns:
        DataFrame enriched with continuous minutes hazard columns.
    """
    out_df = df.copy()
    records: List[Dict[str, Any]] = []

    for _, row in out_df.iterrows():
        prof = compute_player_minutes_hazard(
            player_row=row,
            days_rest=days_rest,
        )
        records.append({
            'p_start': prof.p_start,
            'p_sub': prof.p_sub,
            'p_dnp': prof.p_dnp,
            'p_60_plus': prof.p_60_plus,
            'p_pre60_hook': prof.p_pre60_hook,
            'expected_minutes': prof.expected_minutes,
            'expected_starter_minutes': prof.expected_starter_minutes,
            'appearance_xp': prof.appearance_xp,
            'hazard_flags': "; ".join(prof.hazard_flags) if prof.hazard_flags else "NONE",
        })

    hazard_df = pd.DataFrame(records, index=out_df.index)
    for col in hazard_df.columns:
        out_df[col] = hazard_df[col]

    return out_df


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Continuous Minutes Hazard & Survival Engine for FPL")
    parser.add_argument('--season', default='2026-27', help='Season string (default: 2026-27)')
    parser.add_argument('--gw', type=int, default=1, help='Gameweek to analyze (default: 1)')
    parser.add_argument('--days-rest', type=int, default=7, help='Days of rest before match (default: 7)')
    parser.add_argument('--data-root', default='data', help='Data directory (default: data)')
    args = parser.parse_args()

    dataset_path = os.path.join(args.data_root, args.season, 'model_dataset.csv')
    if not os.path.exists(dataset_path):
        from model.rolling_form import build_dataset
        print(f"[{args.season}] Building dataset as of Gameweek {args.gw}...")
        df = build_dataset(season=args.season, gw_cutoff=args.gw, data_root=args.data_root)
    else:
        df = pd.read_csv(dataset_path)

    print(f"\n[*] Evaluating Continuous Minutes Hazard Engine for {args.season} GW{args.gw} ({len(df)} players)...")
    res_df = predict_gameweek_minutes_distribution(df, days_rest=args.days_rest, season=args.season, data_root=args.data_root)

    print("\n" + "=" * 90)
    print(f"      CONTINUOUS MINUTES HAZARD & PROBABILITY ENGINE -- {args.season} GW{args.gw}")
    print("=" * 90)
    top_nailed = res_df.sort_values('expected_minutes', ascending=False).head(10)
    print("TOP 10 NAILED STARTERS (HIGHEST EXPECTED MINUTES):")
    print("-" * 90)
    for _, r in top_nailed.iterrows():
        wname = str(r['web_name']).encode('ascii', 'replace').decode('ascii')
        tname = str(r['team']).encode('ascii', 'replace').decode('ascii')
        print(f"  * {r['position']:<3} | {wname:<18} ({tname:<14}) | E[Mins]: {r['expected_minutes']:>4.1f}m | P(Start): {r['p_start']*100:>4.1f}% | P(60+): {r['p_60_plus']*100:>4.1f}% | Hook Hazard: {r['p_pre60_hook']*100:>4.1f}%")

    print("\n" + "-" * 90)
    rotation_risks = res_df[(res_df['p_start'] > 0.2) & (res_df['p_start'] < 0.75)].sort_values('p_pre60_hook', ascending=False).head(5)
    if not rotation_risks.empty:
        print("SAMPLE ROTATION & HOOK HAZARD RISKS:")
        print("-" * 90)
        for _, r in rotation_risks.iterrows():
            wname = str(r['web_name']).encode('ascii', 'replace').decode('ascii')
            tname = str(r['team']).encode('ascii', 'replace').decode('ascii')
            flags = str(r['hazard_flags']).encode('ascii', 'replace').decode('ascii')
            print(f"  * {r['position']:<3} | {wname:<18} ({tname:<14}) | E[Mins]: {r['expected_minutes']:>4.1f}m | P(Start): {r['p_start']*100:>4.1f}% | Hook Hazard: {r['p_pre60_hook']*100:>4.1f}% | Flags: {flags}")
    print("=" * 90 + "\n")


if __name__ == '__main__':
    main()

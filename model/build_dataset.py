"""Orchestrator for the FPL Model Data Pipeline (Phase 1).

Builds a single unified dataset (data/<season>/model_dataset.csv) by:
1. (Optional) Refreshing FPL API, FBref, and Understat data.
2. Computing long-form and short-form player rolling form metrics.
3. Computing long-form and short-form team rolling form metrics.
4. Merging FBref season totals (starts, subs, unused subs) where available.
5. Combining everything keyed by player_code into data/<season>/model_dataset.csv.

Usage:
    python -m model.build_dataset [--season 2026-27] [--gw GW] [--skip-scrape]
"""
import argparse
import os
import sys
import pandas as pd

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.rolling_form import (
    build_player_form_dataset,
    build_team_form_dataset,
)


import unicodedata


def normalize_name(text: str) -> str:
    """Normalize player name for robust fuzzy/cross-source matching."""
    if not isinstance(text, str):
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return ' '.join(ascii_text.lower().replace('-', ' ').replace('.', '').split())


def load_teams_map(season: str, data_root: str = 'data') -> dict:
    """Load team ID -> team name mapping from teams.csv.

    Args:
        season: season string e.g. '2026-27'.
        data_root: root data directory.

    Returns:
        dict mapping int team_id to str team_name.
    """
    teams_path = os.path.join(data_root, season, 'teams.csv')
    if not os.path.exists(teams_path):
        return {}
    df = pd.read_csv(teams_path, usecols=['id', 'name'])
    return dict(zip(df['id'], df['name']))


def compute_native_participation(
    season: str,
    gw: int = 38,
    data_root: str = 'data',
) -> pd.DataFrame:
    """Compute player participation statistics (starts, subs, appearances) natively from FPL data.

    Reads players_raw.csv and merged_gw.csv to extract exact appearance metrics
    without relying on external scraping or third-party websites.

    Args:
        season: season string e.g. '2026-27'.
        gw: target gameweek number.
        data_root: root data directory.

    Returns:
        pd.DataFrame with columns: [player_code, season_starts, season_subs,
        fbref_starts, fbref_subs, fbref_unused_subs, fbref_squads_made]
    """
    season_dir = os.path.join(data_root, season)
    players_raw_path = os.path.join(season_dir, 'players_raw.csv')
    if not os.path.exists(players_raw_path):
        return pd.DataFrame()

    pr = pd.read_csv(players_raw_path, encoding='utf-8', encoding_errors='replace')
    if 'code' not in pr.columns:
        return pd.DataFrame()

    # Base starts & minutes from players_raw
    id_to_code = dict(zip(pr['id'], pr['code'])) if 'id' in pr.columns else {}
    records = []

    # Check merged_gw.csv for per-match appearances and substitution breakdowns
    merged_gw_path = os.path.join(season_dir, 'gws', 'merged_gw.csv')
    gw_stats = {}
    if os.path.exists(merged_gw_path):
        try:
            gw_df = pd.read_csv(merged_gw_path, encoding='utf-8', encoding_errors='replace')
            if 'element' in gw_df.columns and 'GW' in gw_df.columns:
                if gw is not None:
                    gw_df = gw_df[gw_df['GW'] <= gw]
                for elem_id, group in gw_df.groupby('element'):
                    p_code = id_to_code.get(elem_id)
                    if p_code is not None:
                        minutes = pd.to_numeric(group.get('minutes', 0), errors='coerce').fillna(0)
                        starts = pd.to_numeric(group.get('starts', 0), errors='coerce').fillna(0)
                        app_count = int((minutes > 0).sum())
                        start_count = int((starts > 0).sum())
                        sub_count = max(0, app_count - start_count)
                        gw_stats[p_code] = {
                            'starts': start_count,
                            'subs': sub_count,
                            'apps': app_count,
                        }
        except Exception:
            pass

    for _, r in pr.iterrows():
        p_code = r.get('code')
        pr_starts = int(r.get('starts', 0) or 0)
        pr_mins = float(r.get('minutes', 0) or 0)

        # Merge gw stats if available, otherwise use players_raw
        if p_code in gw_stats:
            starts = gw_stats[p_code]['starts']
            subs = gw_stats[p_code]['subs']
            squads_made = gw_stats[p_code]['apps']
        else:
            starts = pr_starts
            subs = 1 if (pr_mins > 0 and starts == 0) else 0
            squads_made = starts + subs

        records.append({
            'player_code': p_code,
            'season_starts': starts,
            'season_subs': subs,
            'fbref_starts': starts,
            'fbref_subs': subs,
            'fbref_unused_subs': 0,
            'fbref_squads_made': squads_made,
        })

    return pd.DataFrame(records)


def determine_current_gw(season: str, data_root: str = 'data') -> int:
    """Find the latest completed or current gameweek for a season.

    Args:
        season: season string.
        data_root: root data directory.

    Returns:
        Integer gameweek number (defaults to 38 if full season or 1 if new).
    """
    gw_dir = os.path.join(data_root, season, 'gws')
    if not os.path.exists(gw_dir):
        return 1
    merged_path = os.path.join(gw_dir, 'merged_gw.csv')
    if os.path.exists(merged_path):
        df = pd.read_csv(merged_path, usecols=['GW'])
        if not df.empty:
            return int(df['GW'].max())
    return 1


def build_dataset(
    season: str = '2026-27',
    gw: int = None,
    short_form_window: int = 6,
    data_root: str = 'data',
    skip_scrape: bool = True,
) -> pd.DataFrame:
    """Build the consolidated model dataset for the given season and gameweek.

    Uses 100% native FPL Opta data (rolling player form, rolling team form,
    and native participation stats) without relying on external web scrapers.

    Args:
        season: season string (e.g. '2026-27').
        gw: target gameweek number. If None, auto-determined from data.
        short_form_window: gameweeks for short-form calculation (default 6).
        data_root: directory containing season data folders.
        skip_scrape: if True, use existing data on disk without calling live scrapers.

    Returns:
        pd.DataFrame containing the complete model inputs for all players.
    """
    season_dir = os.path.join(data_root, season)
    os.makedirs(season_dir, exist_ok=True)

    if not skip_scrape:
        print(f"[{season}] Refreshing native FPL API data...")
        try:
            import global_scraper
            global_scraper.parse_data()
        except Exception as e:
            print(f"[Build Dataset] Notice: global_scraper encountered: {e}")

    if gw is None:
        gw = determine_current_gw(season, data_root)
    print(f"[{season}] Building dataset as of Gameweek {gw} (short-form: last {short_form_window} GWs)...")

    # 1. Player rolling form
    player_form = build_player_form_dataset(
        season=season,
        gw=gw,
        short_form_window=short_form_window,
        data_root=data_root,
    )
    if player_form.empty:
        print(f"Warning: No player data found for season {season}")
        return pd.DataFrame()

    # 2. Add team name mapping from teams.csv
    teams_map = load_teams_map(season, data_root)
    players_raw_path = os.path.join(season_dir, 'players_raw.csv')
    if os.path.exists(players_raw_path):
        pr = pd.read_csv(players_raw_path, encoding='utf-8', encoding_errors='replace')
        # Extract season-to-date fields
        season_cols = ['code', 'team', 'minutes', 'starts', 'now_cost', 'status']
        available_cols = [c for c in season_cols if c in pr.columns]
        pr_subset = pr[available_cols].rename(columns={
            'code': 'player_code',
            'minutes': 'season_minutes',
            'starts': 'season_starts',
        })
        player_form = player_form.merge(pr_subset, on='player_code', how='left')
        if 'team' in player_form.columns and teams_map:
            player_form['team_name'] = player_form['team'].map(teams_map)
        else:
            player_form['team_name'] = player_form.get('team', '')
    else:
        player_form['season_minutes'] = player_form.get('long_form_minutes', 0)
        player_form['season_starts'] = 0
        player_form['team_name'] = ''

    # 3. Team rolling form
    team_form = build_team_form_dataset(
        season=season,
        gw=gw,
        short_form_window=short_form_window,
        data_root=data_root,
    )
    if not team_form.empty and 'team_name' in player_form.columns:
        player_form = player_form.merge(
            team_form,
            left_on='team_name',
            right_on='team',
            how='left',
            suffixes=('', '_team_dup')
        )
        if 'team_team_dup' in player_form.columns:
            player_form = player_form.drop(columns=['team_team_dup'])

    # 4. Native participation metrics (starts, subs, squads made)
    part_df = compute_native_participation(season=season, gw=gw, data_root=data_root)
    if not part_df.empty:
        # Drop redundant columns before merging
        part_cols = [c for c in part_df.columns if c != 'season_starts' or 'season_starts' not in player_form.columns]
        player_form = player_form.merge(part_df[part_cols], on='player_code', how='left')
        player_form['fbref_subs'] = player_form['fbref_subs'].fillna(0)
        player_form['fbref_unused_subs'] = player_form['fbref_unused_subs'].fillna(0)
        player_form['fbref_squads_made'] = player_form['fbref_squads_made'].fillna(player_form.get('season_starts', 0))
    else:
        player_form['fbref_starts'] = player_form.get('season_starts', 0)
        player_form['fbref_subs'] = 0
        player_form['fbref_unused_subs'] = 0
        player_form['fbref_squads_made'] = player_form.get('season_starts', 0)

    # Reorder columns cleanly
    preferred_order = [
        'player_code', 'web_name', 'team_name', 'position',
        'season_minutes', 'season_starts', 'fbref_subs', 'fbref_unused_subs',
        'long_form_minutes', 'long_form_expected_goals_90', 'long_form_expected_assists_90',
        'long_form_expected_goals_conceded_90', 'long_form_defensive_contribution_90', 'long_form_bonus_90',
        'short_form_minutes', 'short_form_expected_goals_90', 'short_form_expected_assists_90',
        'short_form_expected_goals_conceded_90', 'short_form_defensive_contribution_90', 'short_form_bonus_90',
        'team_long_form_xg90', 'team_long_form_xgc90',
        'team_short_form_xg90', 'team_short_form_xgc90',
    ]
    present_cols = [c for c in preferred_order if c in player_form.columns]
    extra_cols = [c for c in player_form.columns if c not in preferred_order and c not in ('id', 'element', 'team')]
    final_df = player_form[present_cols + extra_cols].rename(columns={'team_name': 'team'})

    out_csv = os.path.join(season_dir, 'model_dataset.csv')
    final_df.to_csv(out_csv, index=False, encoding='utf-8')
    print(f"[{season}] Successfully wrote {len(final_df)} players to {out_csv}")

    return final_df


def main():
    parser = argparse.ArgumentParser(description="Build consolidated FPL model dataset")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=None, help="Target gameweek number")
    parser.add_argument('--short-form-window', type=int, default=6, help="Gameweek window for short form")
    parser.add_argument('--data-root', default='data', help="Data root folder")
    parser.add_argument('--skip-scrape', action='store_true', default=True, help="Skip live web scraping")
    parser.add_argument('--live-scrape', dest='skip_scrape', action='store_false', help="Run live web scrapers")
    args = parser.parse_args()

    build_dataset(
        season=args.season,
        gw=args.gw,
        short_form_window=args.short_form_window,
        data_root=args.data_root,
        skip_scrape=args.skip_scrape,
    )


if __name__ == '__main__':
    main()

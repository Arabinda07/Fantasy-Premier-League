"""Compiler script: Ingests 10 seasons of historical Premier League / FPL data into a unified, indexed SQLite database (data/pl_history.db).

Builds clean, relational, indexed tables:
1. `seasons_summary`: Aggregated season metrics, golden boot, highest points, total goals.
2. `players_seasons`: Complete season player profiles, minutes, goals, assists, prices.
3. `season_dream_teams`: The top scoring starting XI + bench for each historical season.
4. `player_gameweeks`: Per-match performance logs across all 38 gameweeks per season.

Usage:
    python scripts/compile_pl_history.py [--include-active] [--skip-gws]
"""
import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from positions import POSITION_NAMES as POSITIONS

# FPL Global permanent team codes (immutable across all seasons)
GLOBAL_TEAM_CODES = {
    1: ("Man Utd", "MUN"),
    2: ("Leeds", "LEE"),
    3: ("Arsenal", "ARS"),
    4: ("Newcastle", "NEW"),
    6: ("Spurs", "TOT"),
    7: ("Aston Villa", "AVL"),
    8: ("Chelsea", "CHE"),
    9: ("Coventry City", "COV"),
    11: ("Everton", "EVE"),
    13: ("Leicester", "LEI"),
    14: ("Liverpool", "LIV"),
    17: ("Nott'm Forest", "NFO"),
    20: ("Southampton", "SOU"),
    21: ("West Ham", "WHU"),
    25: ("Middlesbrough", "MID"),
    31: ("Crystal Palace", "CRY"),
    35: ("West Brom", "WBA"),
    36: ("Brighton", "BHA"),
    38: ("Huddersfield", "HUD"),
    39: ("Wolves", "WOL"),
    40: ("Ipswich", "IPS"),
    43: ("Man City", "MCI"),
    45: ("Norwich", "NOR"),
    49: ("Sheffield Utd", "SHU"),
    54: ("Fulham", "FUL"),
    56: ("Sunderland", "SUN"),
    57: ("Watford", "WAT"),
    80: ("Swansea", "SWA"),
    88: ("Hull City", "HUL"),
    90: ("Burnley", "BUR"),
    91: ("Bournemouth", "BOU"),
    94: ("Brentford", "BRE"),
    97: ("Cardiff", "CAR"),
    102: ("Luton", "LUT"),
    110: ("Stoke", "STK"),
}

# Known team code maps for earlier seasons where teams.csv might be absent
SEASON_TEAMS_FALLBACK = {
    "2016-17": {
        1: "Arsenal", 2: "Bournemouth", 3: "Burnley", 4: "Chelsea", 5: "Crystal Palace",
        6: "Everton", 7: "Hull City", 8: "Leicester", 9: "Liverpool", 10: "Man City",
        11: "Man Utd", 12: "Middlesbrough", 13: "Southampton", 14: "Stoke", 15: "Sunderland",
        16: "Swansea", 17: "Spurs", 18: "Watford", 19: "West Brom", 20: "West Ham"
    },
    "2017-18": {
        1: "Arsenal", 2: "Bournemouth", 3: "Brighton", 4: "Burnley", 5: "Chelsea",
        6: "Crystal Palace", 7: "Everton", 8: "Huddersfield", 9: "Leicester", 10: "Liverpool",
        11: "Man City", 12: "Man Utd", 13: "Newcastle", 14: "Southampton", 15: "Stoke",
        16: "Swansea", 17: "Spurs", 18: "Watford", 19: "West Brom", 20: "West Ham"
    },
    "2018-19": {
        1: "Arsenal", 2: "Bournemouth", 3: "Brighton", 4: "Burnley", 5: "Cardiff",
        6: "Chelsea", 7: "Crystal Palace", 8: "Everton", 9: "Fulham", 10: "Huddersfield",
        11: "Leicester", 12: "Liverpool", 13: "Man City", 14: "Man Utd", 15: "Newcastle",
        16: "Southampton", 17: "Spurs", 18: "Watford", 19: "West Ham", 20: "Wolves"
    }
}
HISTORICAL_TEAM_CODES = SEASON_TEAMS_FALLBACK["2016-17"]


def safe_read_csv(path: Path, **kwargs) -> pd.DataFrame:
    """Read CSV with robust fallback for encoding differences in older seasons."""
    try:
        return pd.read_csv(path, encoding='utf-8', **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='latin-1', **kwargs)


def get_teams_map(season_dir: Path) -> Dict[int, str]:
    """Resolve team ID -> team name dictionary for a given season.
    
    Resolution order:
    1. Primary: Canonical teams.csv in season directory.
    2. Secondary: raw.json teams list in season directory.
    3. Multi-season dictionary lookup (SEASON_TEAMS_FALLBACK).
    4. Fallback: HISTORICAL_TEAM_CODES.
    """
    teams_path = season_dir / "teams.csv"
    if teams_path.exists():
        try:
            df = safe_read_csv(teams_path)
            if 'id' in df.columns and 'name' in df.columns:
                return dict(zip(df['id'].astype(int), df['name'].astype(str)))
        except Exception:
            pass

    raw_json_path = season_dir / "raw.json"
    if raw_json_path.exists():
        try:
            import json
            with open(raw_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'teams' in data and isinstance(data['teams'], list):
                teams_dict = {}
                for t in data['teams']:
                    if isinstance(t, dict) and 'id' in t and 'name' in t:
                        teams_dict[int(t['id'])] = str(t['name'])
                if teams_dict:
                    return teams_dict
        except Exception:
            pass

    season_name = season_dir.name
    if season_name in SEASON_TEAMS_FALLBACK:
        return dict(SEASON_TEAMS_FALLBACK[season_name])

    return HISTORICAL_TEAM_CODES


def create_schema(conn: sqlite3.Connection) -> None:
    """Create normalized relational tables and indexes."""
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS seasons_summary")
    cursor.execute("DROP TABLE IF EXISTS players_seasons")
    cursor.execute("DROP TABLE IF EXISTS season_dream_teams")
    cursor.execute("DROP TABLE IF EXISTS player_gameweeks")

    cursor.execute("""
        CREATE TABLE seasons_summary (
            season TEXT PRIMARY KEY,
            start_year INTEGER,
            total_players INTEGER,
            total_goals INTEGER,
            total_assists INTEGER,
            top_scorer_name TEXT,
            top_scorer_goals INTEGER,
            top_points_name TEXT,
            top_points INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE players_seasons (
            season TEXT,
            player_code INTEGER,
            element_id INTEGER,
            web_name TEXT,
            first_name TEXT,
            second_name TEXT,
            team_name TEXT,
            position TEXT,
            now_cost REAL,
            total_points INTEGER,
            minutes INTEGER,
            goals_scored INTEGER,
            assists INTEGER,
            clean_sheets INTEGER,
            goals_conceded INTEGER,
            bonus INTEGER,
            bps INTEGER,
            ict_index REAL,
            points_per_90 REAL,
            value_season REAL,
            PRIMARY KEY (season, player_code)
        )
    """)

    cursor.execute("""
        CREATE TABLE season_dream_teams (
            season TEXT,
            player_code INTEGER,
            web_name TEXT,
            team_name TEXT,
            position TEXT,
            total_points INTEGER,
            now_cost REAL,
            is_starter INTEGER,
            PRIMARY KEY (season, player_code)
        )
    """)

    cursor.execute("""
        CREATE TABLE player_gameweeks (
            season TEXT,
            gw INTEGER,
            player_code INTEGER,
            web_name TEXT,
            total_points INTEGER,
            minutes INTEGER,
            goals_scored INTEGER,
            assists INTEGER,
            clean_sheets INTEGER,
            goals_conceded INTEGER,
            bonus INTEGER,
            bps INTEGER,
            expected_goals REAL,
            expected_assists REAL,
            value REAL,
            PRIMARY KEY (season, gw, player_code)
        )
    """)

    conn.commit()


def compute_dream_team(df: pd.DataFrame, season: str) -> List[Dict]:
    """Select highest-scoring valid 11 starters (1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD) and 4 bench."""
    candidates = df.sort_values('total_points', ascending=False).copy()
    
    # Required positional baselines
    gks = candidates[candidates['position'] == 'GK'].head(2)
    defs = candidates[candidates['position'] == 'DEF'].head(5)
    mids = candidates[candidates['position'] == 'MID'].head(5)
    fwds = candidates[candidates['position'] == 'FWD'].head(3)

    squad = pd.concat([gks, defs, mids, fwds])
    if len(squad) < 15:
        return []

    # Choose starting XI: 1 GK, min 3 DEF, min 2 MID, min 1 FWD
    starter_gk = gks.head(1)
    bench_gk = gks.iloc[1:2]

    outfield = squad[squad['position'] != 'GK'].sort_values('total_points', ascending=False)
    starters = [starter_gk.iloc[0].to_dict()]
    starters[0]['is_starter'] = 1

    # Ensure valid formation minimums: 3 DEF, 2 MID, 1 FWD
    mandatory_defs = defs.head(3)
    mandatory_mids = mids.head(2)
    mandatory_fwds = fwds.head(1)

    assigned_codes = set([starters[0]['player_code']])
    for subset in [mandatory_defs, mandatory_mids, mandatory_fwds]:
        for _, row in subset.iterrows():
            d = row.to_dict()
            d['is_starter'] = 1
            starters.append(d)
            assigned_codes.add(d['player_code'])

    # Fill remaining 4 outfield starter slots with best remaining by points
    remaining_outfield = outfield[~outfield['player_code'].isin(assigned_codes)].sort_values('total_points', ascending=False)
    for _, row in remaining_outfield.head(4).iterrows():
        d = row.to_dict()
        d['is_starter'] = 1
        starters.append(d)
        assigned_codes.add(d['player_code'])

    # Remaining 4 are bench
    bench = []
    for _, row in bench_gk.iterrows():
        d = row.to_dict()
        d['is_starter'] = 0
        bench.append(d)

    for _, row in outfield[~outfield['player_code'].isin(assigned_codes)].iterrows():
        d = row.to_dict()
        d['is_starter'] = 0
        bench.append(d)

    dream_picks = starters + bench
    for p in dream_picks:
        p['season'] = season
    return dream_picks


def export_vault_json(conn: sqlite3.Connection, json_path: Path) -> None:
    """Export atomic JSON for the frontend Historical Vault.
    
    Extracts:
    - seasons: List of season summary metrics sorted by start_year descending
    - dream_teams: Dict mapping season -> list of starter and bench players with detailed stats
    - hall_of_fame_points: Top 15 historical player-seasons by points
    - hall_of_fame_goals: Top 15 historical player-seasons by goals
    """
    cursor = conn.cursor()
    
    # 1. Seasons summary
    cursor.execute("""
        SELECT season, start_year, total_players, total_goals, total_assists,
               top_scorer_name, top_scorer_goals, top_points_name, top_points
        FROM seasons_summary
        ORDER BY start_year DESC
    """)
    seasons = []
    for row in cursor.fetchall():
        seasons.append({
            "season": row[0],
            "start_year": int(row[1]),
            "total_players": int(row[2]),
            "total_goals": int(row[3]),
            "total_assists": int(row[4]),
            "top_scorer_name": row[5],
            "top_scorer_goals": int(row[6]),
            "top_points_name": row[7],
            "top_points": int(row[8]),
        })
    
    # 2. Dream Teams per season
    cursor.execute("SELECT DISTINCT season FROM season_dream_teams ORDER BY season DESC")
    season_names = [r[0] for r in cursor.fetchall()]
    
    dream_teams = {}
    for s_name in season_names:
        cursor.execute("""
            SELECT 
                dt.season, dt.player_code, dt.web_name, dt.team_name, dt.position,
                dt.total_points, dt.now_cost, dt.is_starter,
                COALESCE(ps.goals_scored, 0), COALESCE(ps.assists, 0),
                COALESCE(ps.clean_sheets, 0), COALESCE(ps.bonus, 0),
                COALESCE(ps.minutes, 0)
            FROM season_dream_teams dt
            LEFT JOIN players_seasons ps 
              ON dt.season = ps.season AND dt.player_code = ps.player_code
            WHERE dt.season = ?
            ORDER BY dt.is_starter DESC, dt.total_points DESC
        """, (s_name,))
        
        dt_players = []
        for r in cursor.fetchall():
            dt_players.append({
                "season": r[0],
                "player_code": int(r[1]),
                "web_name": r[2],
                "team_name": r[3],
                "position": r[4],
                "total_points": int(r[5]),
                "now_cost": float(r[6]),
                "is_starter": int(r[7]),
                "goals_scored": int(r[8]),
                "assists": int(r[9]),
                "clean_sheets": int(r[10]),
                "bonus": int(r[11]),
                "minutes": int(r[12]),
            })
        dream_teams[s_name] = dt_players

    # 3. Hall of Fame - Points
    cursor.execute("""
        SELECT season, player_code, web_name, team_name, position, now_cost,
               total_points, goals_scored, assists, clean_sheets, bonus
        FROM players_seasons
        ORDER BY total_points DESC, goals_scored DESC
        LIMIT 15
    """)
    hof_points = []
    for r in cursor.fetchall():
        hof_points.append({
            "season": r[0],
            "player_code": int(r[1]),
            "web_name": r[2],
            "team_name": r[3],
            "position": r[4],
            "now_cost": float(r[5]),
            "total_points": int(r[6]),
            "goals_scored": int(r[7]),
            "assists": int(r[8]),
            "clean_sheets": int(r[9]),
            "bonus": int(r[10]),
        })

    # 4. Hall of Fame - Goals
    cursor.execute("""
        SELECT season, player_code, web_name, team_name, position, now_cost,
               total_points, goals_scored, assists, clean_sheets, bonus
        FROM players_seasons
        ORDER BY goals_scored DESC, total_points DESC
        LIMIT 15
    """)
    hof_goals = []
    for r in cursor.fetchall():
        hof_goals.append({
            "season": r[0],
            "player_code": int(r[1]),
            "web_name": r[2],
            "team_name": r[3],
            "position": r[4],
            "now_cost": float(r[5]),
            "total_points": int(r[6]),
            "goals_scored": int(r[7]),
            "assists": int(r[8]),
            "clean_sheets": int(r[9]),
            "bonus": int(r[10]),
        })

    vault_payload = {
        "seasons": seasons,
        "dream_teams": dream_teams,
        "hall_of_fame_points": hof_points,
        "hall_of_fame_goals": hof_goals,
    }

    import json
    json_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = json_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(vault_payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    temp_path.replace(json_path)
    print(f"[*] Exported Historical Vault JSON to {json_path}")


def compile_history(
    db_path: Path,
    include_active: bool = False,
    skip_gws: bool = False,
    export_json_path: Optional[Path] = None,
) -> None:
    """Main compilation routine."""
    start_time = time.time()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    create_schema(conn)

    data_dir = REPO_ROOT / "data"
    all_seasons = sorted([d.name for d in data_dir.iterdir() if d.is_dir() and d.name[:4].isdigit()])
    if not include_active:
        all_seasons = [s for s in all_seasons if s != '2026-27']

    print(f"[*] Compiling {len(all_seasons)} Premier League seasons into {db_path}...")

    cursor = conn.cursor()
    total_players_inserted = 0
    total_gw_rows_inserted = 0

    for season in all_seasons:
        season_dir = data_dir / season
        raw_path = season_dir / "players_raw.csv"
        if not raw_path.exists():
            continue

        teams_map = get_teams_map(season_dir)
        df_raw = safe_read_csv(raw_path)

        # Normalize column mappings
        if 'code' not in df_raw.columns:
            df_raw['code'] = df_raw['id']
        df_raw['player_code'] = df_raw['code']

        df_raw['position'] = df_raw['element_type'].astype(str).map(POSITIONS).fillna('MID')
        if 'team_code' in df_raw.columns:
            df_raw['team_name'] = df_raw.apply(
                lambda r: teams_map.get(int(r['team'])) if pd.notna(r.get('team')) and int(r['team']) in teams_map
                else (GLOBAL_TEAM_CODES.get(int(r['team_code']), (str(r.get('team', '')), ''))[0] if pd.notna(r.get('team_code')) else str(r.get('team', ''))),
                axis=1
            )
        else:
            df_raw['team_name'] = df_raw['team'].map(teams_map).fillna(df_raw['team'].astype(str))
        
        # Normalize costs: FPL stores now_cost in tenths (e.g. 125 -> 12.5)
        df_raw['cost_norm'] = df_raw['now_cost'].apply(lambda c: round(c / 10.0, 1) if c > 25.0 else round(float(c), 1))
        
        # Minutes per 90 calculation
        df_raw['pts_per_90'] = df_raw.apply(
            lambda r: round((r['total_points'] / (r['minutes'] / 90.0)), 2) if r.get('minutes', 0) >= 450 else 0.0,
            axis=1
        )
        df_raw['val_season'] = df_raw.apply(
            lambda r: round(r['total_points'] / r['cost_norm'], 2) if r['cost_norm'] > 0 else 0.0,
            axis=1
        )

        # 1. Insert players_seasons
        player_rows = []
        for _, row in df_raw.iterrows():
            player_rows.append((
                season,
                int(row['code']),
                int(row.get('id', 0)),
                str(row.get('web_name', '')),
                str(row.get('first_name', '')),
                str(row.get('second_name', '')),
                str(row.get('team_name', '')),
                str(row.get('position', 'MID')),
                float(row.get('cost_norm', 5.0)),
                int(row.get('total_points', 0)),
                int(row.get('minutes', 0)),
                int(row.get('goals_scored', 0)),
                int(row.get('assists', 0)),
                int(row.get('clean_sheets', 0)),
                int(row.get('goals_conceded', 0)),
                int(row.get('bonus', 0)),
                int(row.get('bps', 0)),
                float(row.get('ict_index', 0.0)),
                float(row.get('pts_per_90', 0.0)),
                float(row.get('val_season', 0.0)),
            ))

        cursor.executemany("""
            INSERT OR REPLACE INTO players_seasons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, player_rows)
        total_players_inserted += len(player_rows)

        # 2. Seasons summary metrics
        start_yr = int(season.split('-')[0])
        tot_goals = int(df_raw['goals_scored'].sum())
        tot_assists = int(df_raw['assists'].sum())
        
        top_scorer = df_raw.sort_values('goals_scored', ascending=False).iloc[0]
        top_points = df_raw.sort_values('total_points', ascending=False).iloc[0]

        cursor.execute("""
            INSERT OR REPLACE INTO seasons_summary VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            season,
            start_yr,
            len(df_raw),
            tot_goals,
            tot_assists,
            top_scorer['web_name'],
            int(top_scorer['goals_scored']),
            top_points['web_name'],
            int(top_points['total_points']),
        ))

        # 3. Season Dream Team
        dt_picks = compute_dream_team(df_raw, season)
        dt_rows = [(
            p['season'], p['player_code'] if 'player_code' in p else p['code'],
            p['web_name'], p['team_name'], p['position'],
            int(p['total_points']), float(p['cost_norm']), int(p['is_starter'])
        ) for p in dt_picks]

        cursor.executemany("""
            INSERT OR REPLACE INTO season_dream_teams VALUES (?,?,?,?,?,?,?,?)
        """, dt_rows)

        # 4. Optional Matchday Logs (merged_gw.csv)
        if not skip_gws:
            gw_path = season_dir / "gws" / "merged_gw.csv"
            if gw_path.exists():
                try:
                    df_gw = safe_read_csv(gw_path, low_memory=False)
                    # Create element -> code map from players_raw
                    elem_to_code = dict(zip(df_raw['id'], df_raw['code']))
                    
                    gw_rows = []
                    for _, grow in df_gw.iterrows():
                        el_id = grow.get('element')
                        p_code = elem_to_code.get(el_id, grow.get('code', el_id))
                        if pd.isna(p_code):
                            continue
                        
                        gw_num = grow.get('GW') or grow.get('round') or 1
                        gw_rows.append((
                            season,
                            int(gw_num),
                            int(p_code),
                            str(grow.get('name') or grow.get('web_name', '')),
                            int(grow.get('total_points', 0)),
                            int(grow.get('minutes', 0)),
                            int(grow.get('goals_scored', 0)),
                            int(grow.get('assists', 0)),
                            int(grow.get('clean_sheets', 0)),
                            int(grow.get('goals_conceded', 0)),
                            int(grow.get('bonus', 0)),
                            int(grow.get('bps', 0)),
                            float(grow.get('expected_goals', 0.0)),
                            float(grow.get('expected_assists', 0.0)),
                            float(grow.get('value', 50) / 10.0 if grow.get('value', 0) > 25 else grow.get('value', 5.0)),
                        ))
                    
                    cursor.executemany("""
                        INSERT OR IGNORE INTO player_gameweeks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, gw_rows)
                    total_gw_rows_inserted += len(gw_rows)
                except Exception as e:
                    print(f"  [!] Note: GW logs skipped for {season} ({e})")

        print(f"  -> Processed {season}: {len(player_rows)} players, Dream Team compiled.")

    # Create Indexes for fast querying
    print("[*] Creating high-performance indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_season ON players_seasons(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_code ON players_seasons(player_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_pos ON players_seasons(position)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ps_pts ON players_seasons(season, total_points DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dt_season ON season_dream_teams(season)")
    if not skip_gws:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gw_player ON player_gameweeks(player_code, season)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gw_season ON player_gameweeks(season, gw)")

    conn.commit()

    if export_json_path is not None:
        export_vault_json(conn, export_json_path)

    conn.close()

    elapsed = round(time.time() - start_time, 2)
    db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    print(f"\n[SUCCESS] Compiled {len(all_seasons)} seasons in {elapsed}s.")
    print(f"          Database Path: {db_path} ({db_size_mb} MB)")
    print(f"          Total Player Records: {total_players_inserted}")
    if not skip_gws:
        print(f"          Total Matchday Logs: {total_gw_rows_inserted}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Compile historical FPL CSVs into SQLite database")
    parser.add_argument('--db-path', default='data/pl_history.db', help="Path to SQLite database")
    parser.add_argument('--include-active', action='store_true', help="Include 2026-27 season")
    parser.add_argument('--skip-gws', action='store_true', help="Skip matchday logs (faster, smaller DB)")
    parser.add_argument('--export-json', default='frontend/src/data/historical_vault.json', help="Path to export frontend vault JSON (pass empty string to disable)")
    args = parser.parse_args()

    export_json = (REPO_ROOT / args.export_json) if args.export_json else None

    compile_history(
        db_path=REPO_ROOT / args.db_path,
        include_active=args.include_active,
        skip_gws=args.skip_gws,
        export_json_path=export_json,
    )

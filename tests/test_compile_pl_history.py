"""Unit test verifying the historical Premier League SQLite compiler."""
import sqlite3
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "pl_history.db"


def test_pl_history_database_exists_and_valid():
    """Verify that pl_history.db exists and contains all 10 seasons."""
    assert DB_PATH.is_file(), f"Database not found at {DB_PATH}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Seasons summary table
    cursor.execute("SELECT COUNT(*), MIN(start_year), MAX(start_year) FROM seasons_summary")
    count, min_yr, max_yr = cursor.fetchone()
    assert count >= 10
    assert min_yr == 2016
    assert max_yr >= 2025

    # 2. Players seasons table
    cursor.execute("SELECT COUNT(*) FROM players_seasons")
    total_players = cursor.fetchone()[0]
    assert total_players > 5000

    # 3. Dream teams table
    cursor.execute("SELECT COUNT(DISTINCT season) FROM season_dream_teams")
    dt_seasons = cursor.fetchone()[0]
    assert dt_seasons >= 10

    # 4. Spot check Salah 2017-18 record
    cursor.execute("""
        SELECT total_points, goals_scored FROM players_seasons 
        WHERE season = '2017-18' AND web_name LIKE '%Salah%'
    """)
    salah = cursor.fetchone()
    assert salah is not None
    assert salah[0] == 303  # 303 points in 2017-18
    assert salah[1] == 32   # 32 goals

    conn.close()


def test_historical_club_assignments():
    """Verify that historical club assignments for 2017-18 and 2018-19 are accurately resolved."""
    assert DB_PATH.is_file(), f"Database not found at {DB_PATH}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Assert Salah (2017-18 & 2018-19) has team_name == 'Liverpool'
    cursor.execute("""
        SELECT season, team_name FROM players_seasons
        WHERE season IN ('2017-18', '2018-19') AND web_name LIKE '%Salah%'
    """)
    salah_rows = cursor.fetchall()
    assert len(salah_rows) == 2, f"Expected 2 Salah rows, got {len(salah_rows)}"
    for season, team in salah_rows:
        assert team == 'Liverpool', f"Salah in {season} expected Liverpool, got {team}"

    # 2. Assert Hazard (2018-19) has team_name == 'Chelsea'
    cursor.execute("""
        SELECT team_name FROM players_seasons
        WHERE season = '2018-19' AND web_name = 'Hazard'
    """)
    hazard = cursor.fetchone()
    assert hazard is not None, "Hazard 2018-19 not found"
    assert hazard[0] == 'Chelsea', f"Hazard in 2018-19 expected Chelsea, got {hazard[0]}"

    # 3. Assert Sterling (2017-18 & 2018-19) has team_name == 'Man City'
    cursor.execute("""
        SELECT season, team_name FROM players_seasons
        WHERE season IN ('2017-18', '2018-19') AND web_name = 'Sterling' AND first_name = 'Raheem'
    """)
    sterling_rows = cursor.fetchall()
    assert len(sterling_rows) == 2, f"Expected 2 Sterling rows, got {len(sterling_rows)}"
    for season, team in sterling_rows:
        assert team == 'Man City', f"Sterling in {season} expected Man City, got {team}"

    # 4. Assert no Middlesbrough in 2018-19 dream team
    cursor.execute("""
        SELECT COUNT(*) FROM season_dream_teams
        WHERE season = '2018-19' AND team_name = 'Middlesbrough'
    """)
    count_boro = cursor.fetchone()[0]
    assert count_boro == 0, f"Found {count_boro} Middlesbrough players in 2018-19 dream team"

    # 5. Assert Liverpool players in 2018-19 dream team
    cursor.execute("""
        SELECT web_name FROM season_dream_teams
        WHERE season = '2018-19' AND team_name = 'Liverpool'
    """)
    liv_names = [r[0] for r in cursor.fetchall()]
    assert len(liv_names) >= 5, f"Expected at least 5 Liverpool players in 2018-19 dream team, got {len(liv_names)}"

    conn.close()


def test_historical_vault_json_sync():
    """Verify that frontend historical_vault.json is synchronized with accurate team mappings."""
    import json
    json_path = REPO_ROOT / "frontend" / "src" / "data" / "historical_vault.json"
    assert json_path.is_file(), f"Historical vault JSON not found at {json_path}"

    with open(json_path, 'r', encoding='utf-8') as f:
        vault = json.load(f)

    # 2018-19 Dream Team checks
    dt_18_19 = vault.get("dream_teams", {}).get("2018-19", [])
    assert len(dt_18_19) == 15
    for p in dt_18_19:
        assert p['team_name'] != 'Middlesbrough', f"Player {p['web_name']} in 2018-19 dream team has Middlesbrough"
        if p['web_name'] in ['Salah', 'Mané', 'van Dijk', 'Alisson', 'Robertson', 'Alexander-Arnold']:
            assert p['team_name'] == 'Liverpool', f"{p['web_name']} expected Liverpool, got {p['team_name']}"
        if p['web_name'] == 'Hazard':
            assert p['team_name'] == 'Chelsea', f"Hazard expected Chelsea, got {p['team_name']}"
        if p['web_name'] in ['Sterling', 'Agüero']:
            assert p['team_name'] == 'Man City', f"{p['web_name']} expected Man City, got {p['team_name']}"

    # Hall of fame checks
    for record in vault.get("hall_of_fame_points", []):
        if record['season'] in ('2017-18', '2018-19', '2021-22', '2024-25') and 'Salah' in record['web_name']:
            assert record['team_name'] == 'Liverpool', f"Salah in {record['season']} expected Liverpool, got {record['team_name']}"

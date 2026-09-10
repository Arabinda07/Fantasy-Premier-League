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

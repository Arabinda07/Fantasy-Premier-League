import sqlite3
import tempfile
import os

import pytest

from analyze import analyze_combos, analyze_combos_points


@pytest.fixture
def db_file():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE players (
            web_name TEXT,
            total_points INTEGER,
            now_cost INTEGER,
            element_type INTEGER,
            ppm REAL
        )
    """)
    # (web_name, total_points, now_cost, element_type)
    rows = [
        ("Cheap Def A", 100, 40, 2),   # ppm = 25.0
        ("Cheap Def B", 90, 40, 2),    # ppm = 22.5
        ("Pricey Def",  120, 80, 2),   # ppm = 15.0
        ("Some Mid",    150, 60, 3),   # ppm = 25.0 (different position)
        ("Low Points Def", 50, 40, 2),  # ppm = 12.5, below minimum_points
    ]
    for web_name, total_points, now_cost, element_type in rows:
        ppm = total_points * 10 / now_cost
        conn.execute(
            "INSERT INTO players (web_name, total_points, now_cost, element_type, ppm) VALUES (?, ?, ?, ?, ?)",
            (web_name, total_points, now_cost, element_type, ppm),
        )
    conn.commit()
    conn.close()

    yield path
    os.remove(path)


def test_analyze_combos_ranks_by_ppm(db_file):
    results = analyze_combos(
        db_file=db_file, position=2, current_picks=[],
        remaining_budget=80, remaining_slots=2, current_ppm=0, minimum_points=60,
    )
    top = results.iloc[0]
    assert set(top["new_picks"]) == {"Cheap Def A", "Cheap Def B"}


def test_analyze_combos_points_ranks_by_points(db_file):
    results = analyze_combos_points(
        db_file=db_file, position=2, current_picks=[],
        remaining_budget=120, remaining_slots=2, current_points=0, minimum_points=60,
    )
    top = results.iloc[0]
    assert set(top["new_picks"]) == {"Cheap Def A", "Pricey Def"}


def test_budget_constraint_enforced(db_file):
    results = analyze_combos_points(
        db_file=db_file, position=2, current_picks=[],
        remaining_budget=80, remaining_slots=2, current_points=0, minimum_points=60,
    )
    for combo_cost in results["combo_cost"]:
        assert combo_cost * 10 <= 80


def test_current_picks_excluded(db_file):
    results = analyze_combos_points(
        db_file=db_file, position=2, current_picks=["Cheap Def A"],
        remaining_budget=120, remaining_slots=2, current_points=0, minimum_points=60,
    )
    for picks in results["new_picks"]:
        assert "Cheap Def A" not in picks


def test_position_filter_excludes_other_positions(db_file):
    results = analyze_combos_points(
        db_file=db_file, position=2, current_picks=[],
        remaining_budget=200, remaining_slots=3, current_points=0, minimum_points=60,
    )
    for picks in results["new_picks"]:
        assert "Some Mid" not in picks


def test_minimum_points_filter_applied(db_file):
    results = analyze_combos_points(
        db_file=db_file, position=2, current_picks=[],
        remaining_budget=200, remaining_slots=3, current_points=0, minimum_points=60,
    )
    for picks in results["new_picks"]:
        assert "Low Points Def" not in picks


def test_invalid_position_raises():
    with pytest.raises(ValueError):
        analyze_combos_points(
            db_file="unused.db", position=1, current_picks=[],
            remaining_budget=100, remaining_slots=1, current_points=0, minimum_points=0,
        )

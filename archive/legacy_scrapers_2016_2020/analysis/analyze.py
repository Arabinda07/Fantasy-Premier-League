import sqlite3
import sys
import pandas as pd
from itertools import combinations


VALID_POSITIONS = (2, 3, 4)  # 2=DEF, 3=MID, 4=FWD (1=GK unused, 5=AM unused)

# preset_name -> (remaining_budget, remaining_slots, minimum_points, uses_points_ranking)
PRESETS = {
    (2, "budget"): (400, 5, 90, False), (2, "general"): (190, 3, 90, True), (2, "bench_fodder"): (350, 4, 90, True),
    (3, "budget"): (400, 5, 90, False), (3, "general"): (375, 5, 90, True), (3, "bench_fodder"): (350, 4, 90, True),
    (4, "budget"): (400, 5, 90, False), (4, "general"): (220, 2, 0, True),  (4, "bench_fodder"): (350, 4, 90, True),
}

POSITION_NAMES = {"DEF": 2, "MID": 3, "FWD": 4}


def _fetch_eligible_players(db_file, position, current_picks, minimum_points):
    if position not in VALID_POSITIONS:
        raise ValueError(f"position must be one of {VALID_POSITIONS} (2=DEF, 3=MID, 4=FWD), got {position!r}")

    conn = sqlite3.connect(db_file)

    query = """
        SELECT
            web_name,
            total_points,
            now_cost,
            ppm
        FROM players
        WHERE element_type = ?
          AND total_points >= ?
    """
    params = [position, minimum_points]

    if current_picks:
        placeholders = ",".join("?" for _ in current_picks)
        query += f" AND web_name NOT IN ({placeholders})"
        params.extend(current_picks)

    players = pd.read_sql_query(query, conn, params=params)
    conn.close()

    print(f"Eligible players: {len(players)}")
    return players


def analyze_combos(
    db_file,
    position,
    current_picks,
    remaining_budget,
    remaining_slots,
    current_ppm,
    minimum_points,
):
    """
    Find the top 10 combinations of players at a given position that:

    - Are not already in current_picks
    - Have at least minimum_points total points
    - Fit within remaining_budget
    - Contain exactly remaining_slots players
    - Maximize total points-per-million (ppm)

    Parameters
    ----------
    db_file : str
        Path to SQLite database.

    position : int
        element_type to filter on (2=DEF, 3=MID, 4=FWD).

    current_picks : list[str]
        Names of already selected players.

    remaining_budget : float
        Budget available for remaining players.

    remaining_slots : int
        Number of players still to select.

    current_ppm : float
        Total ppm of already selected players (unused in ranking, kept for
        parity with analyze_combos_points' current_points).

    minimum_points : float
        Minimum total_points required for a candidate player.

    Returns
    -------
    pd.DataFrame
        Top 10 combinations ranked by total ppm.
    """
    players = _fetch_eligible_players(db_file, position, current_picks, minimum_points)

    if len(players) < remaining_slots:
        return pd.DataFrame()

    results = []

    for combo in combinations(players.itertuples(index=False), remaining_slots):
        combo_cost = sum(p.now_cost for p in combo)

        if combo_cost > remaining_budget:
            continue

        combo_ppm = sum(p.ppm for p in combo)
        combo_points = sum(p.total_points for p in combo)

        results.append({
            "combo_cost": combo_cost / 10,
            "total_ppm": combo_ppm,
            "total_points": combo_points,
            "new_picks": [p.web_name for p in combo],
            "remaining_budget": (remaining_budget - combo_cost) / 10,
        })

    if not results:
        return pd.DataFrame()

    return (
        pd.DataFrame(results)
        .sort_values(["total_ppm", "remaining_budget"], ascending=[False, False])
        .head(10)
        .reset_index(drop=True)
    )


def analyze_combos_points(
    db_file,
    position,
    current_picks,
    remaining_budget,
    remaining_slots,
    current_points,
    minimum_points,
):
    """
    Find the top 10 combinations of players at a given position that:

    - Are not already in current_picks
    - Have at least minimum_points total points
    - Fit within remaining_budget
    - Contain exactly remaining_slots players
    - Maximize total points

    Parameters
    ----------
    db_file : str
        Path to SQLite database.

    position : int
        element_type to filter on (2=DEF, 3=MID, 4=FWD).

    current_picks : list[str]
        Names of already selected players.

    remaining_budget : float
        Budget available for remaining players.

    remaining_slots : int
        Number of players still to select.

    current_points : float
        Total points of already selected players.

    minimum_points : float
        Minimum total_points required for a candidate player.

    Returns
    -------
    pd.DataFrame
        Top 10 combinations ranked by total points.
    """
    players = _fetch_eligible_players(db_file, position, current_picks, minimum_points)

    if len(players) < remaining_slots:
        return pd.DataFrame()

    results = []

    for combo in combinations(players.itertuples(index=False), remaining_slots):
        combo_cost = sum(player.now_cost for player in combo)

        if combo_cost > remaining_budget:
            continue

        combo_points = sum(player.total_points for player in combo)
        total_points = current_points + combo_points

        results.append({
            "combo_cost": combo_cost / 10,
            "total_points": total_points,
            "new_picks": [player.web_name for player in combo],
            "remaining_budget": (remaining_budget - combo_cost) / 10,
        })

    if not results:
        return pd.DataFrame()

    return (
        pd.DataFrame(results)
        .sort_values(["total_points", "remaining_budget"], ascending=[False, False])
        .head(10)
        .reset_index(drop=True)
    )


def run_preset(position, preset_name, db_file="fpl.db", current_picks=None):
    """Look up a (position, preset_name) combo in PRESETS and run it."""
    key = (position, preset_name)
    if key not in PRESETS:
        valid_presets = sorted({p for pos, p in PRESETS if pos == position})
        raise ValueError(f"no preset {preset_name!r} for position {position!r}; valid presets: {valid_presets}")

    remaining_budget, remaining_slots, minimum_points, uses_points_ranking = PRESETS[key]
    current_picks = current_picks or []

    if uses_points_ranking:
        return analyze_combos_points(
            db_file=db_file,
            position=position,
            current_picks=current_picks,
            remaining_budget=remaining_budget,
            remaining_slots=remaining_slots,
            current_points=0,
            minimum_points=minimum_points,
        )

    return analyze_combos(
        db_file=db_file,
        position=position,
        current_picks=current_picks,
        remaining_budget=remaining_budget,
        remaining_slots=remaining_slots,
        current_ppm=0,
        minimum_points=minimum_points,
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: python analyze.py <DEF|MID|FWD> <budget|general|bench_fodder> [db_file]")
        sys.exit(1)

    position_name = sys.argv[1].upper()
    preset_name = sys.argv[2]
    db_file = sys.argv[3] if len(sys.argv) > 3 else "fpl.db"

    if position_name not in POSITION_NAMES:
        print("Usage: python analyze.py <DEF|MID|FWD> <budget|general|bench_fodder> [db_file]")
        print(f"Unknown position: {sys.argv[1]!r}")
        sys.exit(1)

    try:
        results = run_preset(POSITION_NAMES[position_name], preset_name, db_file=db_file)
    except ValueError as e:
        print("Usage: python analyze.py <DEF|MID|FWD> <budget|general|bench_fodder> [db_file]")
        print(str(e))
        sys.exit(1)

    print(results.to_string(index=False))


if __name__ == "__main__":
    main()

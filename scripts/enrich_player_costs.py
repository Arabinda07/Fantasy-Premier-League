"""
Enrich players_full.json with now_cost and seasonal element IDs from players_raw.csv.
players_raw.csv uses FPL integer encoding: 60 = 6.0m, divide by 10.
Match on: players_full player_code <-> players_raw code, with web_name fallback.
"""
import json
import csv
import os
import sys

def enrich_player_costs(season: str = "2026-27") -> bool:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    players_raw_path = os.path.join(repo_root, "data", season, "players_raw.csv")
    players_full_path = os.path.join(repo_root, "frontend", "src", "data", "players_full.json")

    if not os.path.exists(players_raw_path):
        print(f"[WARN] players_raw.csv not found at: {players_raw_path}")
        return False

    if not os.path.exists(players_full_path):
        print(f"[WARN] players_full.json not found at: {players_full_path}")
        return False

    # Build lookups:
    # 1. code -> { now_cost, id }
    # 2. web_name.lower() -> { now_cost, id, code }
    cost_map = {}
    elem_map = {}
    name_map = {}

    with open(players_raw_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                code = int(row.get("code", 0))
                elem_id = int(row.get("id", 0))
                raw_cost = row.get("now_cost", "0") or "0"
                cost_pounds = round(int(raw_cost) / 10, 1)
                web_name = row.get("web_name", "").strip().lower()

                if code:
                    cost_map[code] = cost_pounds
                    elem_map[code] = elem_id
                if web_name:
                    name_map[web_name] = {
                        "code": code,
                        "id": elem_id,
                        "now_cost": cost_pounds
                    }
            except (ValueError, KeyError) as e:
                continue

    print(f"Loaded costs & IDs for {len(cost_map)} players from players_raw.csv")

    with open(players_full_path, encoding="utf-8") as f:
        players = json.load(f)

    matched = 0
    for p in players:
        code = int(p.get("player_code", 0) or p.get("code", 0))
        web_name = str(p.get("web_name", "")).strip().lower()

        if code in cost_map:
            p["now_cost"] = cost_map[code]
            p["id"] = elem_map[code]
            p["element_id"] = elem_map[code]
            p["code"] = code
            matched += 1
        elif web_name in name_map:
            fallback = name_map[web_name]
            p["now_cost"] = fallback["now_cost"]
            p["id"] = fallback["id"]
            p["element_id"] = fallback["id"]
            p["code"] = fallback["code"]
            p["player_code"] = fallback["code"]
            matched += 1
        else:
            # Fallback to existing cost or positional baseline
            pos = p.get("position", "MID")
            default_cost = 4.5 if pos in ("GK", "DEF") else 5.0
            p["now_cost"] = float(p.get("cost", default_cost) or default_cost)
            p["id"] = p.get("id", code)
            p["element_id"] = p.get("element_id", code)
            p["code"] = code

    print(f"Matched costs & IDs for {matched}/{len(players)} players")

    with open(players_full_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    print(f"Successfully enriched {players_full_path}")
    return True

if __name__ == "__main__":
    season_arg = sys.argv[1] if len(sys.argv) > 1 else "2026-27"
    success = enrich_player_costs(season_arg)
    sys.exit(0 if success else 1)

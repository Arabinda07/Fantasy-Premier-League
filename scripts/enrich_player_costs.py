"""
Enrich players_full.json with now_cost from players_raw.csv.
players_raw.csv uses FPL integer encoding: 60 = 6.0m, divide by 10.
Match on: players_full player_code  <->  players_raw code
"""
import json
import csv
import os

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
PLAYERS_RAW = os.path.join(REPO_ROOT, "data", "2026-27", "players_raw.csv")
PLAYERS_FULL = os.path.join(REPO_ROOT, "frontend", "src", "data", "players_full.json")

# Build lookup: player code (int) -> now_cost (float in poundsM)
cost_map = {}
with open(PLAYERS_RAW, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        code = int(row["code"])
        raw_cost = row.get("now_cost", "0") or "0"
        cost_map[code] = round(int(raw_cost) / 10, 1)

print(f"Loaded costs for {len(cost_map)} players from players_raw.csv")

# Load players_full.json
with open(PLAYERS_FULL, encoding="utf-8") as f:
    players = json.load(f)

print(f"Loaded {len(players)} players from players_full.json")

# Enrich
matched = 0
for p in players:
    code = int(p.get("player_code", 0))
    if code in cost_map:
        p["now_cost"] = cost_map[code]
        matched += 1
    else:
        p["now_cost"] = 0.0

print(f"Matched costs for {matched}/{len(players)} players")

# Write back
with open(PLAYERS_FULL, "w", encoding="utf-8") as f:
    json.dump(players, f, indent=2, ensure_ascii=False)

print("Written enriched players_full.json")

# Quick sanity check
for p in players[:6]:
    print(f"  {p['web_name']} ({p['team']}): now_cost={p['now_cost']}m")

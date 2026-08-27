"""Export calibrated player predictions and metadata to frontend/src/data/players_full.json."""
import csv
import json
import os
import sys
import tempfile
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def export_frontend_players(season: str = "2026-27", gw: int = 2) -> bool:
    preds_gw_path = os.path.join(REPO_ROOT, "data", season, f"fixture_predictions_gw{gw}.csv")
    preds_main_path = os.path.join(REPO_ROOT, "data", season, "fixture_predictions.csv")
    preds_path = preds_gw_path if os.path.exists(preds_gw_path) else preds_main_path

    players_raw_path = os.path.join(REPO_ROOT, "data", season, "players_raw.csv")
    out_json_path = os.path.join(REPO_ROOT, "frontend", "src", "data", "players_full.json")

    if not os.path.exists(preds_path):
        print(f"[ERROR] Predictions file not found at: {preds_path}")
        return False

    preds_df = pd.read_csv(preds_path)
    print(f"Loaded {len(preds_df)} player predictions from {preds_path}")

    # Load players_raw for element_id and cost mappings
    raw_lookup = {}
    if os.path.exists(players_raw_path):
        with open(players_raw_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    c = int(r.get("code", 0))
                    raw_id = int(r.get("id", 0))
                    raw_cost = float(r.get("now_cost", 0)) / 10.0
                    raw_lookup[c] = {
                        "id": raw_id,
                        "element_id": raw_id,
                        "code": c,
                        "now_cost": raw_cost,
                        "status": r.get("status", "a"),
                        "news": r.get("news", ""),
                        "chance_of_playing_next_round": r.get("chance_of_playing_next_round"),
                    }
                except (ValueError, TypeError):
                    continue

    records = []
    for _, row in preds_df.iterrows():
        rec = row.to_dict()
        # Clean NaNs
        clean_rec = {}
        for k, v in rec.items():
            if pd.isnull(v):
                clean_rec[k] = None
            else:
                clean_rec[k] = v

        p_code = int(clean_rec.get("player_code", clean_rec.get("code", 0)))
        raw_meta = raw_lookup.get(p_code, {})

        cost = raw_meta.get("now_cost")
        if cost is None:
            cost = clean_rec.get("now_cost")
        if cost is None or float(cost) <= 0:
            pos = str(clean_rec.get("position", "MID")).upper()
            cost = 4.0 if pos == "GK" else (4.5 if pos == "DEF" else 5.0)
        else:
            cost = float(cost)
            if cost > 25.0:
                cost = round(cost / 10.0, 1)

        clean_rec["now_cost"] = round(cost, 1)
        clean_rec["cost"] = round(cost, 1)
        clean_rec["id"] = raw_meta.get("id", clean_rec.get("id", p_code))
        clean_rec["element_id"] = raw_meta.get("element_id", clean_rec.get("element_id", p_code))
        clean_rec["code"] = p_code
        clean_rec["player_code"] = p_code
        if "status" in raw_meta:
            clean_rec["status"] = raw_meta["status"]
        if "news" in raw_meta:
            clean_rec["news"] = raw_meta["news"]

        # Ensure expected_points and components are numeric floats
        clean_rec["expected_points"] = float(clean_rec.get("expected_points") or 0.0)
        for i in range(1, 12):
            comp_key = f"c{i}_"
            matched_k = [k for k in clean_rec.keys() if k.startswith(comp_key)]
            for mk in matched_k:
                clean_rec[mk] = float(clean_rec.get(mk) or 0.0)

        records.append(clean_rec)

    # Sort descending by expected points
    records.sort(key=lambda x: float(x.get("expected_points", 0.0)), reverse=True)

    # Atomic write to players_full.json
    dir_name = os.path.dirname(out_json_path)
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".json.tmp", dir=dir_name)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, out_json_path)

    print(f"[+] Successfully exported {len(records)} players to {out_json_path}")
    return True

if __name__ == "__main__":
    gw_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    export_frontend_players(season="2026-27", gw=gw_arg)

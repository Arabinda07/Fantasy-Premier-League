#!/usr/bin/env python3
"""Sync Live FPL Squad CLI Utility.

Connects directly to the official Fantasy Premier League API to fetch the
manager's authoritative squad picks, free transfers, bank balance, and
recent transfer activity.

Persists the verified ground truth to:
- data/<season>/actual_squad.json
- data/<season>/manager_squad_<entry_id>_actual.json
- data/<season>/manager_squad_<entry_id>.json
- data/<season>/current_squad.json

Usage:
    python scripts/sync_live_squad.py --entry-id 9500404
    python scripts/sync_live_squad.py --entry-id 9500404 --gw 6 --bank 2.1 --ft 0
    python scripts/sync_live_squad.py --entry-id 9500404 --players "Raya, Leno, Gabriel, Robinson, Robertson, Calafiori, De Cuyper, Gibbs-White, Tavernier, Szoboszlai, Palmer, B.Fernandes, Barry, Calvert-Lewin, Wissa" --bank 2.1 --ft 0
"""
import argparse
import io
import json
import os
import sys
import time
from typing import Dict, Any, List, Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import requests
import pandas as pd

from model.live_sync import (
    DEFAULT_HEADERS,
    FPL_BASE_URL,
    load_element_to_code_map,
    calculate_available_free_transfers,
)


def resolve_player_names_to_codes(names: List[str], players_df: pd.DataFrame) -> List[int]:
    """Resolve a list of string web_names / full names to FPL player codes."""
    codes: List[int] = []
    for raw_name in names:
        n = raw_name.strip()
        if not n:
            continue
        # Exact match
        matches = players_df[players_df['web_name'].str.lower() == n.lower()]
        if matches.empty:
            # Substring match
            matches = players_df[players_df['web_name'].str.lower().str.contains(n.lower(), regex=False)]
        if not matches.empty:
            codes.append(int(matches.iloc[0]['code']))
        else:
            print(f"[!] Warning: Could not match player name: '{n}'")
    return codes


def sync_live_squad(
    entry_id: int = 9500404,
    season: str = '2026-27',
    gw: Optional[int] = None,
    bank: Optional[float] = None,
    free_transfers: Optional[int] = None,
    manual_players: Optional[str] = None,
    data_root: str = 'data',
    timeout: int = 10,
) -> Dict[str, Any]:
    """Fetch live squad from official FPL API and save immutable actual squad."""
    season_dir = os.path.join(data_root, season)
    os.makedirs(season_dir, exist_ok=True)

    elem_to_code = load_element_to_code_map(season=season, data_root=data_root)
    players_path = os.path.join(season_dir, 'players_raw.csv')
    players_df = pd.read_csv(players_path) if os.path.exists(players_path) else pd.DataFrame()

    # 1. Fetch entry summary
    summary_url = f"{FPL_BASE_URL}/entry/{entry_id}/"
    summary_data = {}
    try:
        resp = requests.get(summary_url, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            summary_data = resp.json()
    except Exception as e:
        print(f"[!] Warning: Failed to fetch entry summary ({e})")

    manager_name = f"{summary_data.get('player_first_name', '')} {summary_data.get('player_last_name', '')}".strip() or f"Manager {entry_id}"
    team_name = summary_data.get('name', f"Team {entry_id}")
    overall_rank = summary_data.get('summary_overall_rank') or 0
    overall_points = summary_data.get('summary_overall_points') or 0
    current_event = int(summary_data.get('current_event') or 1)

    target_gw = gw or (current_event + 1)

    # 2. Fetch history and transfers
    transfers_url = f"{FPL_BASE_URL}/entry/{entry_id}/transfers/"
    transfers_list = []
    try:
        t_resp = requests.get(transfers_url, headers=DEFAULT_HEADERS, timeout=timeout)
        if t_resp.status_code == 200:
            transfers_list = t_resp.json()
    except Exception as e:
        print(f"[!] Warning: Failed to fetch transfer history ({e})")

    computed_ft = calculate_available_free_transfers(summary_data, transfers_list, current_gw=target_gw)
    final_ft = free_transfers if free_transfers is not None else computed_ft

    # 3. Determine squad codes
    squad_codes: List[int] = []
    starter_codes: List[int] = []
    bench_codes: List[int] = []
    captain_code: Optional[int] = None
    vice_captain_code: Optional[int] = None
    final_bank = bank

    if manual_players:
        names = [p.strip() for p in manual_players.split(',') if p.strip()]
        squad_codes = resolve_player_names_to_codes(names, players_df)
        if len(squad_codes) == 15:
            print(f"[*] Successfully resolved 15 players from manual specification.")
            starter_codes = squad_codes[:11]
            bench_codes = squad_codes[11:]
        else:
            print(f"[!] Warning: Manual player list resolved {len(squad_codes)}/15 players.")

    # If manual players not provided or incomplete, fetch from FPL API picks
    if len(squad_codes) != 15:
        # Search published picks backwards from current_event
        picks_list = []
        for cand_gw in range(target_gw, 0, -1):
            p_url = f"{FPL_BASE_URL}/entry/{entry_id}/event/{cand_gw}/picks/"
            try:
                p_resp = requests.get(p_url, headers=DEFAULT_HEADERS, timeout=timeout)
                if p_resp.status_code == 200:
                    p_data = p_resp.json()
                    if p_data.get('picks'):
                        picks_list = p_data.get('picks', [])
                        if final_bank is None and p_data.get('entry_history', {}).get('bank') is not None:
                            final_bank = float(p_data['entry_history']['bank']) / 10.0
                        print(f"[*] Fetched {len(picks_list)} picks from FPL API for GW{cand_gw}.")
                        break
            except Exception:
                pass

        if len(picks_list) == 15:
            squad_codes = []
            starter_codes = []
            bench_codes = []
            for p in picks_list:
                elem = int(p.get('element', 0))
                code = elem_to_code.get(elem, elem)
                squad_codes.append(code)
                slot = int(p.get('position', 1))
                if slot <= 11:
                    starter_codes.append(code)
                else:
                    bench_codes.append(code)
                if p.get('is_captain'):
                    captain_code = code
                if p.get('is_vice_captain'):
                    vice_captain_code = code

    # Fallback bank if not determined
    if final_bank is None:
        last_bank = summary_data.get('last_deadline_bank')
        final_bank = float(last_bank) / 10.0 if last_bank is not None else 0.0

    # Ensure 15 squad codes
    if len(squad_codes) != 15:
        # Attempt fallback to actual_squad.json if present
        actual_path = os.path.join(season_dir, 'actual_squad.json')
        if os.path.exists(actual_path):
            with open(actual_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if len(cached.get('squad_codes', [])) == 15:
                    squad_codes = cached['squad_codes']
                    starter_codes = cached.get('starter_codes', squad_codes[:11])
                    bench_codes = cached.get('bench_codes', squad_codes[11:])
                    captain_code = cached.get('captain_code')
                    vice_captain_code = cached.get('vice_captain_code')
                    print(f"[*] Fallback loaded 15 players from {actual_path}")

    assert len(squad_codes) == 15, f"Could not resolve 15 players (got {len(squad_codes)})"

    # Build authoritative payload
    payload = {
        'entry_id': entry_id,
        'manager_name': manager_name,
        'team_name': team_name,
        'season': season,
        'last_updated_gw': target_gw,
        'squad_status': 'EXECUTED',
        'overall_rank': overall_rank,
        'overall_points': overall_points,
        'bank': round(final_bank, 1),
        'free_transfers': final_ft,
        'squad_codes': squad_codes,
        'baseline_squad_codes': squad_codes,
        'starter_codes': starter_codes,
        'bench_codes': bench_codes,
        'captain_code': captain_code or starter_codes[0],
        'vice_captain_code': vice_captain_code or starter_codes[1],
        'updated_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
    }

    # Write to all authoritative squad files
    targets = [
        os.path.join(season_dir, 'actual_squad.json'),
        os.path.join(season_dir, f'manager_squad_{entry_id}_actual.json'),
        os.path.join(season_dir, f'manager_squad_{entry_id}.json'),
        os.path.join(season_dir, 'current_squad.json'),
    ]

    import tempfile
    for target in targets:
        dir_name = os.path.dirname(target)
        fd, tmp_path = tempfile.mkstemp(suffix='.json.tmp', dir=dir_name)
        with os.fdopen(fd, 'w') as tmp_f:
            json.dump(payload, tmp_f, indent=2)
        os.replace(tmp_path, target)
        print(f"[OK] Saved authoritative squad snapshot: {target}")

    # Print summary
    print("\n" + "=" * 60)
    print(f"  FPL SQUAD GROUND TRUTH SYNCHRONIZED — GW{target_gw}")
    print("=" * 60)
    print(f"Manager:        {manager_name} ({team_name}) [ID: #{entry_id}]")
    print(f"Bank Balance:   £{final_bank:.1f}M")
    print(f"Free Transfers: {final_ft}")
    print(f"Squad Status:   EXECUTED (Immutable Ground Truth)")
    print("-" * 60)
    print("Verified 15-Man Squad:")
    if not players_df.empty:
        code_to_name = dict(zip(players_df['code'], players_df['web_name']))
        code_to_team = dict(zip(players_df['code'], players_df['team']))
        for i, c in enumerate(squad_codes, 1):
            pname = code_to_name.get(c, str(c))
            tag = " [Starter]" if c in starter_codes else " [Bench]"
            print(f"  {i:2d}. {pname:<16} (Code: {c}){tag}")
    print("=" * 60 + "\n")

    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Synchronize live FPL manager squad ground truth.")
    parser.add_argument('--entry-id', type=int, default=9500404, help="FPL Entry ID (default: 9500404)")
    parser.add_argument('--season', default='2026-27', help="Season string (default: 2026-27)")
    parser.add_argument('--gw', type=int, default=6, help="Target gameweek (default: 6)")
    parser.add_argument('--bank', type=float, default=None, help="Bank balance in £M (e.g. 2.1)")
    parser.add_argument('--ft', type=int, default=None, help="Free transfers available (e.g. 0)")
    parser.add_argument('--players', type=str, default=None, help="Comma-separated player names to override")

    args = parser.parse_args()
    sync_live_squad(
        entry_id=args.entry_id,
        season=args.season,
        gw=args.gw,
        bank=args.bank,
        free_transfers=args.ft,
        manual_players=args.players,
    )

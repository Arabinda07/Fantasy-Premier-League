"""Export multi-chip scenario solutions and enrich live matchday JSONs."""
import argparse
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.enrich_frontend_data import enrich_matchday_json


def run(season: str = '2026-27', gw: int = 2, data_root: str = 'data'):
    print(f"[Chip Export] Enriching 4-chip simulations for Season {season}, GW{gw}...")
    success = enrich_matchday_json(gw=gw, season=season, data_root=data_root)
    if success:
        print(f"[Chip Export] Successfully generated enriched chip scenarios for GW{gw}.")
    else:
        print(f"[Chip Export] Failed to enrich chip scenarios for GW{gw}.")
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export 4-chip scenario simulations into live matchday JSONs")
    parser.add_argument('--season', default='2026-27', help="Season string (e.g. 2026-27)")
    parser.add_argument('--gw', type=int, default=2, help="Gameweek number (default 2)")
    parser.add_argument('--data-root', default='data', help="Data root directory")
    args = parser.parse_args()
    run(season=args.season, gw=args.gw, data_root=args.data_root)

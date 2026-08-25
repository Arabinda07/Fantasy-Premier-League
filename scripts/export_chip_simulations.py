"""Export multi-chip scenario solutions to frontend/src/data/live_matchday_gw2.json."""
import json
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

import numpy as np
import pandas as pd
from dataclasses import asdict
from model.solver import solve_initial_squad
from model.fixture_engine import predict_gameweek_fixtures

def sanitize_val(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (np.floating, float)) and (np.isnan(val) or np.isinf(val)):
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        return round(float(val), 4)
    return val

def sanitize_dict(d):
    return {k: sanitize_val(v) for k, v in d.items()}

def run():
    season = '2026-27'
    gw = 2
    data_root = 'data'
    
    df = predict_gameweek_fixtures(season=season, gw=gw, data_root=data_root)
    
    # Solve 4 chip scenarios
    wc_sol = solve_initial_squad(df=df, budget=100.0, chip='wildcard')
    fh_sol = solve_initial_squad(df=df, budget=100.0, chip='freehit')
    bb_sol = solve_initial_squad(df=df, budget=100.0, chip='bboost')
    tc_sol = solve_initial_squad(df=df, budget=100.0, chip='3xc')
    
    chips_payload = {
        'wildcard': {
            'chip_name': 'Wildcard',
            'formation': wc_sol.formation,
            'starting_xp': wc_sol.starting_xp,
            'total_xp': wc_sol.total_xp,
            'captain': wc_sol.captain.web_name if wc_sol.captain else None,
            'vice_captain': wc_sol.vice_captain.web_name if wc_sol.vice_captain else None,
            'starters': [sanitize_dict(asdict(p)) for p in wc_sol.starters],
            'bench': [sanitize_dict(asdict(p)) for p in wc_sol.bench],
            'description': 'Complete 15-man squad overhaul under £100.0M budget without hit penalties for long-term fixture runs.',
            'budget_used': wc_sol.total_cost,
        },
        'freehit': {
            'chip_name': 'Free Hit',
            'formation': fh_sol.formation,
            'starting_xp': fh_sol.starting_xp,
            'total_xp': fh_sol.total_xp,
            'captain': fh_sol.captain.web_name if fh_sol.captain else None,
            'vice_captain': fh_sol.vice_captain.web_name if fh_sol.vice_captain else None,
            'starters': [sanitize_dict(asdict(p)) for p in fh_sol.starters],
            'bench': [sanitize_dict(asdict(p)) for p in fh_sol.bench],
            'description': 'Temporary 1-week squad targeting maximum single-round ceiling with cheap £4.0M bench enablers.',
            'budget_used': fh_sol.total_cost,
        },
        'bboost': {
            'chip_name': 'Bench Boost',
            'formation': bb_sol.formation,
            'starting_xp': bb_sol.starting_xp,
            'total_xp': bb_sol.total_xp,
            'captain': bb_sol.captain.web_name if bb_sol.captain else None,
            'vice_captain': bb_sol.vice_captain.web_name if bb_sol.vice_captain else None,
            'starters': [sanitize_dict(asdict(p)) for p in bb_sol.starters],
            'bench': [sanitize_dict(asdict(p)) for p in bb_sol.bench],
            'description': 'All 15 players are active point scorers. Optimizes both Starting XI and all 4 bench slots.',
            'budget_used': bb_sol.total_cost,
        },
        '3xc': {
            'chip_name': 'Triple Captain',
            'formation': tc_sol.formation,
            'starting_xp': tc_sol.starting_xp,
            'total_xp': tc_sol.total_xp,
            'captain': tc_sol.captain.web_name if tc_sol.captain else None,
            'vice_captain': tc_sol.vice_captain.web_name if tc_sol.vice_captain else None,
            'starters': [sanitize_dict(asdict(p)) for p in tc_sol.starters],
            'bench': [sanitize_dict(asdict(p)) for p in tc_sol.bench],
            'description': 'Triples the point returns of your selected captain (+3x multiplier instead of standard 2x).',
            'budget_used': tc_sol.total_cost,
        }
    }
    
    # Load existing live matchday data
    frontend_json = os.path.join('frontend', 'src', 'data', 'live_matchday_gw2.json')
    if os.path.exists(frontend_json):
        with open(frontend_json, 'r') as f:
            live_data = json.load(f)
        live_data['chip_simulations'] = chips_payload
        with open(frontend_json, 'w') as f:
            json.dump(live_data, f, indent=2)
        print("Successfully enriched live_matchday_gw2.json with 4 chip simulations!")

if __name__ == '__main__':
    run()

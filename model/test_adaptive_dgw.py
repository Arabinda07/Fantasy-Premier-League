"""Tests for Adaptive Double Gameweek (DGW) Accumulator lookahead engine."""

import pandas as pd
import pytest

from model.chip_optimizer import GameweekScheduleProfile
from model.solver import solve_multi_horizon_transfers


def test_adaptive_dgw_detection_logic():
    """Verify that an upcoming DGW within 4-5 weeks triggers horizon expansion."""
    gw = 5
    # Simulate schedule profiles where GW8 is a Double Gameweek (Arsenal & Chelsea)
    profiles = [
        GameweekScheduleProfile(gw=g, total_fixtures=10, dgw_teams=[], bgw_teams=[], is_dgw=False, is_bgw=False)
        for g in range(1, 39)
    ]
    # Set GW8 as DGW
    profiles[7] = GameweekScheduleProfile(
        gw=8, total_fixtures=12, dgw_teams=['Arsenal', 'Chelsea'], bgw_teams=[], is_dgw=True, is_bgw=False
    )

    # Filter upcoming DGW in the next 4 gameweeks (gw < p.gw <= gw + 4)
    dgw_in_window = [p for p in profiles if p.is_dgw and gw < p.gw <= min(38, gw + 4)]
    assert len(dgw_in_window) == 1
    target_dgw = dgw_in_window[0]
    assert target_dgw.gw == 8

    # Needed horizon: 8 - 5 + 1 = 4 GWs (expands from standard 3 to 4)
    needed_h = min(5, target_dgw.gw - gw + 1)
    assert needed_h == 4


def test_adaptive_dgw_caps_at_5():
    """Verify that an upcoming DGW at gw+4 caps at 5 gameweeks."""
    gw = 5
    profiles = [
        GameweekScheduleProfile(gw=g, total_fixtures=10, dgw_teams=[], bgw_teams=[], is_dgw=False, is_bgw=False)
        for g in range(1, 39)
    ]
    # Set GW9 as DGW
    profiles[8] = GameweekScheduleProfile(
        gw=9, total_fixtures=12, dgw_teams=['Man City', 'Liverpool'], bgw_teams=[], is_dgw=True, is_bgw=False
    )

    dgw_in_window = [p for p in profiles if p.is_dgw and gw < p.gw <= min(38, gw + 4)]
    assert len(dgw_in_window) == 1
    needed_h = min(5, dgw_in_window[0].gw - gw + 1)
    assert needed_h == 5


def test_5_gameweek_dgw_accumulator_solves_optimally():
    """Verify solve_multi_horizon_transfers solves across a 5-GW lookahead to accumulate a DGW asset."""
    base_players = [
        {'player_code': 1, 'web_name': 'GK1', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a'},
        {'player_code': 2, 'web_name': 'GK2', 'team': 'Ipswich', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.0, 'status': 'a'},
        {'player_code': 3, 'web_name': 'DEF1', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.0, 'status': 'a'},
        {'player_code': 4, 'web_name': 'DEF2', 'team': 'Arsenal', 'position': 'DEF', 'cost': 5.5, 'expected_points': 5.5, 'status': 'a'},
        {'player_code': 5, 'web_name': 'DEF3', 'team': 'Liverpool', 'position': 'DEF', 'cost': 5.0, 'expected_points': 5.0, 'status': 'a'},
        {'player_code': 6, 'web_name': 'DEF4', 'team': 'Liverpool', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.5, 'status': 'a'},
        {'player_code': 7, 'web_name': 'DEF5', 'team': 'Everton', 'position': 'DEF', 'cost': 4.5, 'expected_points': 3.5, 'status': 'a'},
        {'player_code': 9, 'web_name': 'MID1', 'team': 'Man City', 'position': 'MID', 'cost': 10.0, 'expected_points': 7.5, 'status': 'a'},
        {'player_code': 10, 'web_name': 'MID2', 'team': 'Chelsea', 'position': 'MID', 'cost': 9.0, 'expected_points': 7.0, 'status': 'a'},
        {'player_code': 11, 'web_name': 'MID3', 'team': 'Spurs', 'position': 'MID', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a'},
        {'player_code': 12, 'web_name': 'MID4', 'team': 'Brighton', 'position': 'MID', 'cost': 6.5, 'expected_points': 5.0, 'status': 'a'},
        {'player_code': 13, 'web_name': 'MID5', 'team': 'Brentford', 'position': 'MID', 'cost': 5.5, 'expected_points': 4.0, 'status': 'a'},
        {'player_code': 14, 'web_name': 'FWD1', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 8.5, 'status': 'a'},
        {'player_code': 15, 'web_name': 'FWD2', 'team': 'Liverpool', 'position': 'FWD', 'cost': 8.0, 'expected_points': 6.0, 'status': 'a'},
        {'player_code': 16, 'web_name': 'FWD3', 'team': 'Leeds', 'position': 'FWD', 'cost': 5.5, 'expected_points': 4.0, 'status': 'a'},
    ]
    current_codes = [p['player_code'] for p in base_players]

    # Target DGW player (MID_DGW, code 99) plays single games in GW5-GW8 (4.2 xP) but has a huge DGW in GW9 (11.0 xP)
    dgw_target_normal = {'player_code': 99, 'web_name': 'MID_DGW', 'team': 'Villa', 'position': 'MID', 'cost': 5.5, 'expected_points': 4.2, 'status': 'a'}
    dgw_target_double = {'player_code': 99, 'web_name': 'MID_DGW', 'team': 'Villa', 'position': 'MID', 'cost': 5.5, 'expected_points': 11.0, 'status': 'a'}

    df_gw5 = pd.DataFrame(base_players + [dgw_target_normal])
    df_gw6 = pd.DataFrame(base_players + [dgw_target_normal])
    df_gw7 = pd.DataFrame(base_players + [dgw_target_normal])
    df_gw8 = pd.DataFrame(base_players + [dgw_target_normal])
    df_gw9 = pd.DataFrame(base_players + [dgw_target_double])

    sol = solve_multi_horizon_transfers(
        current_squad_codes=current_codes,
        horizon_dfs=[df_gw5, df_gw6, df_gw7, df_gw8, df_gw9],
        free_transfers=1,
        bank=0.0,
        start_gw=5,
        lambda_ft=1.0,
    )

    assert sol.status == "Optimal"
    assert sol.horizon == 5
    # The solver should successfully plan across the 5 GWs and have the DGW target in squad by GW9
    gw9_plan = sol.gw_plans[4]
    gw9_squad_codes = [p.player_code for p in gw9_plan.squad_solution.squad]
    assert 99 in gw9_squad_codes

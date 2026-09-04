"""Unit tests for Order-Statistic Tournament Modeling of BPS & Bonus Points (M-04)."""
import math
import numpy as np
import pandas as pd
import pytest

from model.bps_tournament import (
    compute_player_bps_propensity,
    solve_plackett_luce_tournament,
    calibrate_fixture_bonus_points,
    DEFAULT_BPS_TEMPERATURE,
    DEFAULT_TIE_INFLATION,
)


def _make_mock_match_players(n_home=11, n_away=11, match_type='balanced'):
    """Helper to generate mock active player predictions for a fixture."""
    players = []
    # Home team
    for i in range(1, n_home + 1):
        if i == 1:
            pos = 'GK'
            xg, xa = 0.0, 0.0
            cs = 3.6 if match_type == 'defensive' else 0.4
            c3 = 2.0 if match_type == 'defensive' else 1.0
        elif i <= 5:
            pos = 'DEF'
            xg, xa = (0.0, 0.0) if match_type == 'defensive' else (0.05, 0.05)
            cs = 3.6 if match_type == 'defensive' else 0.4
            c3 = 0.0
        elif i <= 9:
            pos = 'MID'
            xg = 0.6 if match_type == 'shootout' else (0.02 if match_type == 'defensive' else 0.15)
            xa = 0.4 if match_type == 'shootout' else (0.01 if match_type == 'defensive' else 0.15)
            cs = 0.8 if match_type == 'defensive' else 0.2
            c3 = 0.0
        else:
            pos = 'FWD'
            xg = 1.2 if match_type == 'shootout' else (0.02 if match_type == 'defensive' else 0.35)
            xa = 0.3 if match_type == 'shootout' else (0.01 if match_type == 'defensive' else 0.10)
            cs = 0.0
            c3 = 0.0

        players.append({
            'player_code': 100 + i,
            'web_name': f'Home_{pos}_{i}',
            'team': 'Arsenal',
            'position': pos,
            'fixture_opponent': 'Chelsea',
            'p_start': 0.95,
            'p_app': 0.98,
            'p_60_plus': 0.90,
            'expected_minutes': 85.0,
            'c8_goals': xg * 4.0,
            'c7_assists': xa * 3.0,
            'c9_clean_sheets': cs,
            'c10_goals_conceded': -0.05 if match_type == 'defensive' else (-1.2 if match_type == 'shootout' else -0.3),
            'c3_saves': c3,
            'c11_defensive_contributions': 0.5 if pos in ('DEF', 'MID') else 0.0,
            'c4_yellow_cards': -0.1,
            'c5_red_cards': 0.0,
            'c6_bonus': 0.5,
            'expected_points': 5.0,
        })

    # Away team
    for i in range(1, n_away + 1):
        if i == 1:
            pos = 'GK'
            xg, xa = 0.0, 0.0
            cs = 3.6 if match_type == 'defensive' else 0.4
            c3 = 2.0 if match_type == 'defensive' else 1.2
        elif i <= 5:
            pos = 'DEF'
            xg, xa = (0.0, 0.0) if match_type == 'defensive' else (0.05, 0.05)
            cs = 3.6 if match_type == 'defensive' else 0.4
            c3 = 0.0
        elif i <= 9:
            pos = 'MID'
            xg = 0.5 if match_type == 'shootout' else (0.02 if match_type == 'defensive' else 0.15)
            xa = 0.3 if match_type == 'shootout' else (0.01 if match_type == 'defensive' else 0.15)
            cs = 0.8 if match_type == 'defensive' else 0.2
            c3 = 0.0
        else:
            pos = 'FWD'
            xg = 0.9 if match_type == 'shootout' else (0.02 if match_type == 'defensive' else 0.30)
            xa = 0.2 if match_type == 'shootout' else (0.01 if match_type == 'defensive' else 0.10)
            cs = 0.0
            c3 = 0.0

        players.append({
            'player_code': 200 + i,
            'web_name': f'Away_{pos}_{i}',
            'team': 'Chelsea',
            'position': pos,
            'fixture_opponent': 'Arsenal',
            'p_start': 0.95,
            'p_app': 0.98,
            'p_60_plus': 0.90,
            'expected_minutes': 85.0,
            'c8_goals': xg * 4.0,
            'c7_assists': xa * 3.0,
            'c9_clean_sheets': cs,
            'c10_goals_conceded': -0.1 if match_type == 'defensive' else -1.2,
            'c3_saves': c3,
            'c11_defensive_contributions': 0.3 if pos in ('DEF', 'MID') else 0.0,
            'c4_yellow_cards': -0.1,
            'c5_red_cards': 0.0,
            'c6_bonus': 0.5,
            'expected_points': 4.8,
        })

    return players


class TestPlackettLuceTournament:
    """Verify mathematical properties and conservation of the BPS tournament engine."""

    def test_plackett_luce_exact_conservation(self):
        """Sum of expected bonus points across any simulated match equals 6.0 * tie_inflation (~6.15)."""
        players = _make_mock_match_players(n_home=11, n_away=11, match_type='balanced')
        bonus_map = solve_plackett_luce_tournament(players, tie_inflation=DEFAULT_TIE_INFLATION)

        total_bonus = sum(bonus_map.values())
        expected_total = 6.0 * DEFAULT_TIE_INFLATION  # 6.15
        assert abs(total_bonus - expected_total) < 0.02

    def test_defensive_sweep_in_nil_nil_draw(self):
        """In a defensive 0-0 match, defenders and goalkeepers capture >= 65% of all match bonus points."""
        players = _make_mock_match_players(n_home=11, n_away=11, match_type='defensive')
        bonus_map = solve_plackett_luce_tournament(players)

        total_bonus = sum(bonus_map.values())
        def_gk_bonus = sum(
            bonus_map[p['player_code']]
            for p in players
            if p['position'] in ('GK', 'DEF')
        )

        def_share = def_gk_bonus / total_bonus
        # In a 0-0 grind, clean sheets dominate BPS (+12 for CS vs 0 goals scored)
        assert def_share >= 0.65

    def test_attacking_domination_in_shootout(self):
        """In a high-scoring shootout, goalscorers and assisters capture >= 70% of match bonus points."""
        players = _make_mock_match_players(n_home=11, n_away=11, match_type='shootout')
        bonus_map = solve_plackett_luce_tournament(players)

        total_bonus = sum(bonus_map.values())
        mid_fwd_bonus = sum(
            bonus_map[p['player_code']]
            for p in players
            if p['position'] in ('MID', 'FWD')
        )

        att_share = mid_fwd_bonus / total_bonus
        # In a 4-3 shootout, goals (+24/+18) and assists (+9) overwhelm clean-sheet-less defenders
        assert att_share >= 0.70

    def test_monotonic_xg_bonus_scaling(self):
        """Increasing a player's goal threat strictly increases their expected bonus points."""
        players_low = _make_mock_match_players(n_home=11, n_away=11, match_type='balanced')
        players_high = _make_mock_match_players(n_home=11, n_away=11, match_type='balanced')

        # Player 111 (FWD) gets boosted xG in high scenario
        players_high[10]['c8_goals'] = 8.0  # 2 expected goals

        b_low = solve_plackett_luce_tournament(players_low)[111]
        b_high = solve_plackett_luce_tournament(players_high)[111]

        assert b_high > b_low
        assert b_high >= 1.5  # Heavy favorite to take 3 or 2 bonus points

    def test_inactive_players_receive_zero_bonus(self):
        """Players with 0 minutes or 0 appearance probability receive 0.0 bonus points."""
        players = _make_mock_match_players(n_home=11, n_away=11, match_type='balanced')
        # Add inactive reserve player
        players.append({
            'player_code': 999,
            'web_name': 'InactiveReserve',
            'team': 'Arsenal',
            'position': 'GK',
            'fixture_opponent': 'Chelsea',
            'p_start': 0.0,
            'p_app': 0.0,
            'p_60_plus': 0.0,
            'expected_minutes': 0.0,
            'c8_goals': 0.0,
            'c7_assists': 0.0,
            'c9_clean_sheets': 0.0,
            'c10_goals_conceded': 0.0,
            'c3_saves': 0.0,
            'c11_defensive_contributions': 0.0,
            'c4_yellow_cards': 0.0,
            'c5_red_cards': 0.0,
            'c6_bonus': 0.0,
            'expected_points': 0.0,
        })
        bonus_map = solve_plackett_luce_tournament(players)
        assert bonus_map[999] == 0.0
        # Active players still conserve total bonus pool
        assert abs(sum(bonus_map.values()) - (6.0 * DEFAULT_TIE_INFLATION)) < 0.02


class TestCalibrateFixtureBonusPoints:
    """Verify DataFrame calibration, exact point accounting, and DGW handling."""

    def test_calibrate_fixture_bonus_points_pipeline(self):
        """calibrate_fixture_bonus_points updates c6_bonus and maintains exact expected_points accounting."""
        players = _make_mock_match_players(n_home=11, n_away=11, match_type='balanced')
        df = pd.DataFrame(players)
        fixtures = [{'home_team': 'Arsenal', 'away_team': 'Chelsea'}]

        calibrated_df = calibrate_fixture_bonus_points(df, fixtures)

        assert not calibrated_df.empty
        # Verify exact point adjustment accounting for each player: xP_new == xP_old - c6_old + c6_new
        for i in range(len(df)):
            old_row = df.iloc[i]
            new_row = calibrated_df.iloc[i]
            diff_c6 = new_row['c6_bonus'] - old_row['c6_bonus']
            diff_xp = new_row['expected_points'] - old_row['expected_points']
            assert abs(diff_xp - diff_c6) < 1e-4

        # Total bonus points in fixture equals ~6.15
        fixture_bonus = calibrated_df['c6_bonus'].sum()
        assert abs(fixture_bonus - (6.0 * DEFAULT_TIE_INFLATION)) < 0.05

    def test_dgw_multi_match_accumulation(self):
        """DGW players correctly accumulate bonus points across both scheduled matches."""
        # Arsenal plays Chelsea (match 1) AND Wolves (match 2)
        match1 = _make_mock_match_players(n_home=11, n_away=11, match_type='balanced')
        # Simulate cumulative DGW representation for Arsenal players (2 matches of volume)
        for p in match1:
            if p['team'] == 'Arsenal':
                p['fixture_count'] = 2
                p['fixture_opponent'] = 'Chelsea, Wolves'
                p['c8_goals'] = p['c8_goals'] * 2.0
                p['c7_assists'] = p['c7_assists'] * 2.0
                p['p_app'] = 1.95
                p['p_60_plus'] = 1.80
                p['c6_bonus'] = 1.0
                p['expected_points'] = 10.0

        # Wolves players for match 2 (balanced 11 players)
        wolves_players = _make_mock_match_players(n_home=0, n_away=11, match_type='balanced')
        for i, p in enumerate(wolves_players):
            p['player_code'] = 300 + i
            p['web_name'] = f'Wolves_{p["position"]}_{i}'
            p['team'] = 'Wolves'
            p['fixture_opponent'] = 'Arsenal'
            p['fixture_count'] = 1

        all_players = match1 + wolves_players
        df = pd.DataFrame(all_players)
        fixtures = [
            {'home_team': 'Arsenal', 'away_team': 'Chelsea'},
            {'home_team': 'Arsenal', 'away_team': 'Wolves'},
        ]

        calibrated_df = calibrate_fixture_bonus_points(df, fixtures)
        # Arsenal players played in 2 tournaments, so their total bonus should be accumulated across both matches
        ars_fwd = calibrated_df[calibrated_df['player_code'] == 111].iloc[0]
        # In each balanced match, ars_fwd receives ~0.44 bonus points, so in DGW ~0.85-0.90
        assert ars_fwd['c6_bonus'] > 0.70
        assert ars_fwd['c6_bonus'] < 1.50

    def test_event_bps_not_double_counted(self):
        """Verify that historical total BPS (which includes goals/assists) does not double-count attacking returns."""
        # Forward with total historical bps90 = 30.0, long_form_xg90 = 0.80, long_form_xa90 = 0.20
        # Under old code, total BPS (30) was added to projected goals (24 * 0.8 = 19.2) + app (6) = 55.2 BPS!
        # Under new code, net open play is 30 - (0.8*24 + 0.2*9 + 6) = 30 - 27 = 3.0 -> clamped to 4.0.
        # Total propensity = 4.0 + 19.2 + 1.8 + 6.0 = 31.0 BPS.
        player_pred = {
            'position': 'FWD',
            'p_app': 1.0,
            'p_60_plus': 1.0,
            'expected_minutes': 90.0,
            'long_form_bps_90': 30.0,
            'long_form_expected_goals_90': 0.80,
            'long_form_expected_assists_90': 0.20,
            'c8_goals': 0.80 * 4.0,  # 3.2 pts
            'c7_assists': 0.20 * 3.0, # 0.6 pts
        }
        propensity = compute_player_bps_propensity(player_pred)
        # Latent propensity should be in realistic range ~28-35 BPS, NOT double-counted to 55+ BPS
        assert propensity < 40.0
        assert propensity > 25.0

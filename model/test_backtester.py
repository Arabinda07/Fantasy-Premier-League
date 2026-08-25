"""Unit tests for Historical Backtest Validation Engine (model/test_backtester.py)."""
import pytest
import pandas as pd

from model.solver import PlayerPick
from model.backtester import (
    score_squad_with_auto_subs,
    load_gameweek_actual_points,
    run_season_backtest,
    SeasonBacktestReport,
)


class TestBacktestMechanics:
    """Test auto-substitution, captaincy fallback, and backtest scoring rules."""

    def test_auto_sub_gk_and_outfield_substitution(self):
        """Verify that 0-minute starters trigger correct bench auto-substitutions."""
        starters = [
            PlayerPick(1, 'Raya', 'Arsenal', 'GK', 5.5, 5.0, True, False, False),
            PlayerPick(2, 'Gabriel', 'Arsenal', 'DEF', 6.0, 5.0, True, False, False),
            PlayerPick(3, 'Saliba', 'Arsenal', 'DEF', 6.0, 5.0, True, False, False),
            PlayerPick(4, 'Trent', 'Liverpool', 'DEF', 7.0, 5.0, True, False, False),
            PlayerPick(5, 'Palmer', 'Chelsea', 'MID', 10.5, 7.0, True, True, False), # Captain
            PlayerPick(6, 'Saka', 'Arsenal', 'MID', 10.0, 6.5, True, False, True),  # Vice Captain
            PlayerPick(7, 'Foden', 'Man City', 'MID', 9.5, 6.0, True, False, False),
            PlayerPick(8, 'Gordon', 'Newcastle', 'MID', 7.5, 5.5, True, False, False),
            PlayerPick(9, 'Mbeumo', 'Brentford', 'MID', 7.0, 5.0, True, False, False),
            PlayerPick(10, 'Haaland', 'Man City', 'FWD', 15.0, 8.0, True, False, False),
            PlayerPick(11, 'Isak', 'Newcastle', 'FWD', 8.5, 6.0, True, False, False),
        ]

        bench = [
            PlayerPick(12, 'Turner', 'Crystal Palace', 'GK', 4.0, 0.0, False, False, False, bench_order=1),
            PlayerPick(13, 'Konsa', 'Aston Villa', 'DEF', 4.5, 3.5, False, False, False, bench_order=2),
            PlayerPick(14, 'Rogers', 'Aston Villa', 'MID', 5.0, 4.0, False, False, False, bench_order=3),
            PlayerPick(15, 'Stewart', 'Southampton', 'FWD', 4.5, 1.0, False, False, False, bench_order=4),
        ]

        # Case 1: All starters play. Palmer scores 10 (20 with captaincy), Saka scores 6, Raya scores 6.
        actuals_case1 = {
            1: {'total_points': 6, 'minutes': 90},
            2: {'total_points': 6, 'minutes': 90},
            3: {'total_points': 6, 'minutes': 90},
            4: {'total_points': 2, 'minutes': 90},
            5: {'total_points': 10, 'minutes': 90}, # Capt -> 20 pts
            6: {'total_points': 6, 'minutes': 90},
            7: {'total_points': 5, 'minutes': 90},
            8: {'total_points': 5, 'minutes': 90},
            9: {'total_points': 8, 'minutes': 90},
            10: {'total_points': 9, 'minutes': 90},
            11: {'total_points': 8, 'minutes': 90},
            12: {'total_points': 0, 'minutes': 0},
            13: {'total_points': 6, 'minutes': 90}, # Bench DEF (6 pts)
            14: {'total_points': 7, 'minutes': 90}, # Bench MID (7 pts)
            15: {'total_points': 1, 'minutes': 15},
        }

        gross, capt_pts, in_subs, out_subs, _ = score_squad_with_auto_subs(
            starters=starters, bench=bench, captain_pick=starters[4], vice_pick=starters[5], actuals=actuals_case1
        )
        # Expected: sum(6,6,6,2,10*2,6,5,5,8,9,8) = 81 pts
        assert gross == 81
        assert capt_pts == 20
        assert in_subs == []

        # Case 2: Raya (GK) and Palmer (Capt) play 0 minutes.
        # GK Turner (0 pts, but plays 90m) subs for Raya.
        # Palmer DNP -> Vice Captain Saka (6 pts -> 12 pts) becomes effective captain.
        # Bench Sub 1 (Konsa, DEF) subs in for Palmer (maintaining valid 4-4-2 formation).
        actuals_case2 = dict(actuals_case1)
        actuals_case2[1] = {'total_points': 0, 'minutes': 0}  # Raya DNP
        actuals_case2[12] = {'total_points': 3, 'minutes': 90} # Turner played! 3 pts
        actuals_case2[5] = {'total_points': 0, 'minutes': 0}  # Palmer DNP

        gross2, capt_pts2, in_subs2, out_subs2, _ = score_squad_with_auto_subs(
            starters=starters, bench=bench, captain_pick=starters[4], vice_pick=starters[5], actuals=actuals_case2
        )

        assert 'Turner' in in_subs2
        assert 'Raya' in out_subs2
        assert 'Palmer' in out_subs2
        assert 'Konsa' in in_subs2
        # Captaincy transferred to Vice Captain Saka (6 * 2 = 12 pts)
        assert capt_pts2 == 12

    def test_load_gameweek_actual_points(self):
        """Verify loading actual points from 2024-25 season data."""
        actuals = load_gameweek_actual_points(season='2024-25', gw=1)
        assert len(actuals) > 0
        first_player = next(iter(actuals.values()))
        assert 'total_points' in first_player
        assert 'minutes' in first_player
        assert 'position' in first_player

    def test_triple_captain_and_bench_boost_scoring(self):
        """Verify that Triple Captain multiplies by 3 and Bench Boost scores all 15 players."""
        starters = [
            PlayerPick(1, 'Raya', 'Arsenal', 'GK', 5.5, 5.0, True, False, False),
            PlayerPick(2, 'Gabriel', 'Arsenal', 'DEF', 6.0, 5.0, True, False, False),
            PlayerPick(3, 'Saliba', 'Arsenal', 'DEF', 6.0, 5.0, True, False, False),
            PlayerPick(4, 'Trent', 'Liverpool', 'DEF', 7.0, 5.0, True, False, False),
            PlayerPick(5, 'Palmer', 'Chelsea', 'MID', 10.5, 7.0, True, True, False), # Captain
            PlayerPick(6, 'Saka', 'Arsenal', 'MID', 10.0, 6.5, True, False, True),
            PlayerPick(7, 'Foden', 'Man City', 'MID', 9.5, 6.0, True, False, False),
            PlayerPick(8, 'Gordon', 'Newcastle', 'MID', 7.5, 5.5, True, False, False),
            PlayerPick(9, 'Mbeumo', 'Brentford', 'MID', 7.0, 5.0, True, False, False),
            PlayerPick(10, 'Haaland', 'Man City', 'FWD', 15.0, 8.0, True, False, False),
            PlayerPick(11, 'Isak', 'Newcastle', 'FWD', 8.5, 6.0, True, False, False),
        ]

        bench = [
            PlayerPick(12, 'Turner', 'Crystal Palace', 'GK', 4.0, 0.0, False, False, False, bench_order=1),
            PlayerPick(13, 'Konsa', 'Aston Villa', 'DEF', 4.5, 3.5, False, False, False, bench_order=2),
            PlayerPick(14, 'Rogers', 'Aston Villa', 'MID', 5.0, 4.0, False, False, False, bench_order=3),
            PlayerPick(15, 'Stewart', 'Southampton', 'FWD', 4.5, 1.0, False, False, False, bench_order=4),
        ]

        actuals = {
            1: {'total_points': 6, 'minutes': 90},
            2: {'total_points': 6, 'minutes': 90},
            3: {'total_points': 6, 'minutes': 90},
            4: {'total_points': 2, 'minutes': 90},
            5: {'total_points': 10, 'minutes': 90}, # Palmer -> 10 pts
            6: {'total_points': 6, 'minutes': 90},
            7: {'total_points': 5, 'minutes': 90},
            8: {'total_points': 5, 'minutes': 90},
            9: {'total_points': 8, 'minutes': 90},
            10: {'total_points': 9, 'minutes': 90},
            11: {'total_points': 8, 'minutes': 90},
            12: {'total_points': 2, 'minutes': 90}, # Bench GK
            13: {'total_points': 6, 'minutes': 90}, # Bench DEF
            14: {'total_points': 7, 'minutes': 90}, # Bench MID
            15: {'total_points': 1, 'minutes': 15}, # Bench FWD
        }

        # 1. Test Triple Captain (Palmer gets 10 * 3 = 30 pts)
        gross_3xc, capt_3xc, _, _, _ = score_squad_with_auto_subs(
            starters=starters, bench=bench, captain_pick=starters[4], vice_pick=starters[5], actuals=actuals, chip='3xc'
        )
        assert capt_3xc == 30
        assert gross_3xc == 91  # 81 (standard) + 10 (extra 3xc point multiplier) = 91

        # 2. Test Bench Boost (all 15 score: 81 + 2 + 6 + 7 + 1 = 97)
        gross_bb, capt_bb, _, _, _ = score_squad_with_auto_subs(
            starters=starters, bench=bench, captain_pick=starters[4], vice_pick=starters[5], actuals=actuals, chip='bboost'
        )
        assert capt_bb == 20
        assert gross_bb == 97

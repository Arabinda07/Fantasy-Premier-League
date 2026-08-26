"""Unit tests for Live Auto-Substitutions & Captaincy Rollover (model/live_sync.py)."""
import pytest

from model.live_sync import (
    evaluate_live_captaincy_rollover,
    evaluate_live_auto_substitutions,
)


class TestCaptaincyRollover:
    """Test live matchday captaincy rollover rules."""

    def test_captain_played_keeps_multiplier(self):
        players = [
            {'player_code': 101, 'web_name': 'Haaland', 'minutes': 90},
            {'player_code': 102, 'web_name': 'Salah', 'minutes': 85},
        ]
        res = evaluate_live_captaincy_rollover(players, captain_code=101, vice_captain_code=102)
        assert res['effective_captain_code'] == 101
        assert res['multiplier_applied'] == 2

    def test_captain_dnp_promotes_vice_captain(self):
        players = [
            {'player_code': 101, 'web_name': 'Haaland', 'minutes': 0},
            {'player_code': 102, 'web_name': 'Salah', 'minutes': 90},
        ]
        res = evaluate_live_captaincy_rollover(players, captain_code=101, vice_captain_code=102)
        assert res['effective_captain_code'] == 102
        assert res['multiplier_applied'] == 2

    def test_both_dnp_drops_multiplier(self):
        players = [
            {'player_code': 101, 'web_name': 'Haaland', 'minutes': 0},
            {'player_code': 102, 'web_name': 'Salah', 'minutes': 0},
        ]
        res = evaluate_live_captaincy_rollover(players, captain_code=101, vice_captain_code=102)
        assert res['effective_captain_code'] is None
        assert res['multiplier_applied'] == 1


class TestAutoSubstitutions:
    """Test formation-safe bench auto-substitution engine."""

    def test_gk_dnp_subbed_by_bench_gk(self):
        starters = [
            {'player_code': 1, 'position': 'GK', 'minutes': 0, 'web_name': 'Raya'},
            {'player_code': 2, 'position': 'DEF', 'minutes': 90, 'web_name': 'Gabriel'},
            {'player_code': 3, 'position': 'DEF', 'minutes': 90, 'web_name': 'Saliba'},
            {'player_code': 4, 'position': 'DEF', 'minutes': 90, 'web_name': 'Gvardiol'},
            {'player_code': 5, 'position': 'MID', 'minutes': 90, 'web_name': 'Salah'},
            {'player_code': 6, 'position': 'MID', 'minutes': 90, 'web_name': 'Saka'},
            {'player_code': 7, 'position': 'MID', 'minutes': 90, 'web_name': 'Palmer'},
            {'player_code': 8, 'position': 'MID', 'minutes': 90, 'web_name': 'Rogers'},
            {'player_code': 9, 'position': 'FWD', 'minutes': 90, 'web_name': 'Haaland'},
            {'player_code': 10, 'position': 'FWD', 'minutes': 90, 'web_name': 'Isak'},
            {'player_code': 11, 'position': 'FWD', 'minutes': 90, 'web_name': 'Watkins'},
        ]
        bench = [
            {'player_code': 12, 'position': 'GK', 'minutes': 90, 'bench_order': 0, 'web_name': 'Fabianski'},
            {'player_code': 13, 'position': 'DEF', 'minutes': 90, 'bench_order': 1, 'web_name': 'Bednarek'},
            {'player_code': 14, 'position': 'MID', 'minutes': 90, 'bench_order': 2, 'web_name': 'Winks'},
            {'player_code': 15, 'position': 'FWD', 'minutes': 90, 'bench_order': 3, 'web_name': 'Jebbison'},
        ]

        res = evaluate_live_auto_substitutions(starters, bench)
        assert len(res['substitutions']) == 1
        assert res['substitutions'][0]['off'] == 1
        assert res['substitutions'][0]['on'] == 12

    def test_outfield_dnp_respects_formation_constraints(self):
        # 3-5-2 formation with 1 DEF unplayed.
        # Bench order: 1st bench is MID (played), 2nd bench is DEF (played).
        # Subbing 1st bench MID would yield 2 DEF (ILLEGAL!).
        # Engine MUST skip MID and sub 2nd bench DEF to preserve 3 DEF minimum.
        starters = [
            {'player_code': 1, 'position': 'GK', 'minutes': 90, 'web_name': 'Raya'},
            {'player_code': 2, 'position': 'DEF', 'minutes': 90, 'web_name': 'Gabriel'},
            {'player_code': 3, 'position': 'DEF', 'minutes': 90, 'web_name': 'Saliba'},
            {'player_code': 4, 'position': 'DEF', 'minutes': 0, 'web_name': 'Gvardiol'},  # 3rd DEF DNP!
            {'player_code': 5, 'position': 'MID', 'minutes': 90, 'web_name': 'Salah'},
            {'player_code': 6, 'position': 'MID', 'minutes': 90, 'web_name': 'Saka'},
            {'player_code': 7, 'position': 'MID', 'minutes': 90, 'web_name': 'Palmer'},
            {'player_code': 8, 'position': 'MID', 'minutes': 90, 'web_name': 'Rogers'},
            {'player_code': 9, 'position': 'MID', 'minutes': 90, 'web_name': 'Gordon'},
            {'player_code': 10, 'position': 'FWD', 'minutes': 90, 'web_name': 'Haaland'},
            {'player_code': 11, 'position': 'FWD', 'minutes': 90, 'web_name': 'Isak'},
        ]
        bench = [
            {'player_code': 12, 'position': 'GK', 'minutes': 90, 'bench_order': 0, 'web_name': 'Fabianski'},
            {'player_code': 13, 'position': 'MID', 'minutes': 90, 'bench_order': 1, 'web_name': 'Winks'},     # 1st bench (MID)
            {'player_code': 14, 'position': 'DEF', 'minutes': 90, 'bench_order': 2, 'web_name': 'Bednarek'},  # 2nd bench (DEF)
            {'player_code': 15, 'position': 'FWD', 'minutes': 90, 'bench_order': 3, 'web_name': 'Jebbison'},
        ]

        res = evaluate_live_auto_substitutions(starters, bench)
        assert len(res['substitutions']) == 1
        assert res['substitutions'][0]['off'] == 4
        # MUST sub Bednarek (DEF, code 14) and NOT Winks (MID, code 13)
        assert res['substitutions'][0]['on'] == 14
        assert res['formation'] == '3-5-2'

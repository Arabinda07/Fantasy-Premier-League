"""Unit tests for the Dynamic Opportunistic Wildcard Engine and Team Bias Feedback."""
import os
import sys
import tempfile
import shutil
import pandas as pd
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.chip_optimizer import (
    evaluate_opportunistic_wildcard,
    evaluate_chip_schedule,
    ChipRecommendation,
)
from model.fixture_engine import load_team_bias_corrections


@pytest.fixture
def temp_test_env():
    tmpdir = tempfile.mkdtemp()
    season_dir = os.path.join(tmpdir, '2026-27')
    os.makedirs(season_dir, exist_ok=True)
    yield {'root': tmpdir, 'season_dir': season_dir, 'season': '2026-27'}
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_opportunistic_wildcard_triggers_on_zero_ft_and_distress(temp_test_env):
    """When a manager has 0 FTs and a large projected deficit, Wildcard should trigger immediately."""
    gw1_data = []
    # 15 owned players with mediocre/low xP
    owned_codes = list(range(101, 116))
    for code in owned_codes:
        gw1_data.append({
            'player_code': code,
            'web_name': f'Player_{code}',
            'position': 'MID' if code % 2 == 0 else 'DEF',
            'expected_points': 2.8,  # Below 3.3 threshold -> distressed
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })

    # Unowned top tier players with high xP
    for code in range(201, 216):
        gw1_data.append({
            'player_code': code,
            'web_name': f'Star_{code}',
            'position': 'MID' if code % 2 == 0 else 'FWD',
            'expected_points': 6.5,
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })

    df = pd.DataFrame(gw1_data)

    rec = evaluate_opportunistic_wildcard(
        current_squad_codes=owned_codes,
        gw1_df=df,
        horizon_dfs=[df, df, df],
        free_transfers=0,
        bank=0.6,
        current_gw=5,
        season=temp_test_env['season'],
        data_root=temp_test_env['root'],
    )

    assert rec.is_active_now is True
    assert rec.target_gw == 5
    assert rec.expected_value_delta >= 14.0
    assert "SQUAD REBUILD ALERT" in rec.rationale


def test_opportunistic_wildcard_withholds_when_healthy_and_plenty_fts(temp_test_env):
    """When a manager has 3 FTs and a healthy squad, Wildcard should hold for scheduled swing."""
    gw1_data = []
    owned_codes = list(range(101, 116))
    for code in owned_codes:
        gw1_data.append({
            'player_code': code,
            'web_name': f'Player_{code}',
            'position': 'MID' if code % 2 == 0 else 'FWD',
            'expected_points': 5.2,  # Strong projections
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })

    df = pd.DataFrame(gw1_data)

    rec = evaluate_opportunistic_wildcard(
        current_squad_codes=owned_codes,
        gw1_df=df,
        horizon_dfs=[df, df, df],
        free_transfers=3,
        bank=1.5,
        current_gw=4,
        season=temp_test_env['season'],
        data_root=temp_test_env['root'],
    )

    assert rec.is_active_now is False
    assert rec.target_gw == 6  # Scheduled for GW6 swing
    assert "Gameweek 6" in rec.rationale


def test_evaluate_chip_schedule_integrates_opportunistic_wildcard(temp_test_env):
    """evaluate_chip_schedule should incorporate opportunistic recommendations when squad passed."""
    gw1_data = []
    owned_codes = list(range(101, 116))
    for code in owned_codes:
        gw1_data.append({
            'player_code': code,
            'web_name': f'Player_{code}',
            'position': 'MID',
            'expected_points': 2.0,
            'status': 'i' if code in (101, 102, 103) else 'a',
            'chance_of_playing_this_round': 0 if code in (101, 102, 103) else 100,
        })
    # Top targets
    for code in range(201, 216):
        gw1_data.append({
            'player_code': code,
            'web_name': f'Star_{code}',
            'position': 'MID',
            'expected_points': 6.0,
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })
    df = pd.DataFrame(gw1_data)

    plan = evaluate_chip_schedule(
        season=temp_test_env['season'],
        current_gw=5,
        data_root=temp_test_env['root'],
        current_squad_codes=owned_codes,
        gw1_df=df,
        free_transfers=0,
        bank=0.6,
    )

    wc_rec = plan.recommendations['wildcard_1']
    assert wc_rec.is_active_now is True
    assert wc_rec.target_gw == 5


def test_load_team_bias_corrections(temp_test_env):
    """load_team_bias_corrections computes clamped EWMA offsets from team_accuracy_log.csv."""
    log_rows = [
        {'gameweek': 1, 'team': 'Arsenal', 'pred_xp': 50.0, 'actual_pts': 40.0, 'bias': 10.0, 'actual_goals': 1},
        {'gameweek': 2, 'team': 'Arsenal', 'pred_xp': 52.0, 'actual_pts': 42.0, 'bias': 10.0, 'actual_goals': 1},
        {'gameweek': 1, 'team': 'Man City', 'pred_xp': 45.0, 'actual_pts': 55.0, 'bias': -10.0, 'actual_goals': 3},
        {'gameweek': 2, 'team': 'Man City', 'pred_xp': 46.0, 'actual_pts': 56.0, 'bias': -10.0, 'actual_goals': 3},
    ]
    pd.DataFrame(log_rows).to_csv(os.path.join(temp_test_env['season_dir'], 'team_accuracy_log.csv'), index=False)

    corrections = load_team_bias_corrections(season=temp_test_env['season'], data_root=temp_test_env['root'])
    assert 'Arsenal' in corrections
    assert 'Man City' in corrections
    # Arsenal was over-predicted (+bias) -> correction is negative (reduce)
    assert corrections['Arsenal'] < 0.0
    # Man City was under-predicted (-bias) -> correction is positive (boost)
    assert corrections['Man City'] > 0.0


def test_opportunistic_wildcard_ignores_cheap_bench_enablers(temp_test_env):
    """A healthy starting XI with low-cost bench enablers (<= 4.5M) should NOT trigger an emergency Wildcard."""
    gw1_data = []
    # 11 elite starters with high xP
    starter_codes = list(range(101, 112))
    for code in starter_codes:
        gw1_data.append({
            'player_code': code,
            'web_name': f'Starter_{code}',
            'position': 'MID' if code % 2 == 0 else 'DEF',
            'expected_points': 5.8,
            'now_cost': 75.0,  # £7.5M
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })
    # 4 cheap bench enablers with low xP (e.g. 1.2 to 2.2) but completely healthy
    bench_codes = list(range(112, 116))
    for code in bench_codes:
        gw1_data.append({
            'player_code': code,
            'web_name': f'Bench_{code}',
            'position': 'DEF' if code == 112 else ('GK' if code == 113 else 'MID'),
            'expected_points': 1.5,  # Below 3.3, but intentional cheap fodder
            'now_cost': 40.0 if code < 114 else 45.0,  # £4.0M - £4.5M
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })
    # Top available targets
    for code in range(201, 216):
        gw1_data.append({
            'player_code': code,
            'web_name': f'Target_{code}',
            'position': 'MID',
            'expected_points': 6.2,
            'now_cost': 80.0,
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })
    df = pd.DataFrame(gw1_data)

    rec = evaluate_opportunistic_wildcard(
        current_squad_codes=starter_codes + bench_codes,
        gw1_df=df,
        horizon_dfs=[df, df, df],
        free_transfers=0,
        bank=0.2,
        current_gw=2,
        season=temp_test_env['season'],
        data_root=temp_test_env['root'],
    )

    # Wildcard should NOT be triggered on healthy starting XI
    assert rec.is_active_now is False
    assert rec.target_gw == 6


def test_opportunistic_wildcard_aborts_on_blank_gameweek(temp_test_env):
    """When distress is driven by scheduled Blank Gameweek fixtures (FA Cup), Wildcard should abort and recommend Free Hit."""
    gw1_data = []
    owned_codes = list(range(101, 116))
    for code in owned_codes:
        # 4 blanking assets (xP = 0.0, status = 'a')
        is_blank = code in (101, 102, 103, 104)
        gw1_data.append({
            'player_code': code,
            'web_name': f'Player_{code}',
            'position': 'MID' if code % 2 == 0 else 'DEF',
            'expected_points': 0.0 if is_blank else 4.5,
            'now_cost': 70.0,
            'status': 'a',
            'chance_of_playing_this_round': 100,
        })
    df = pd.DataFrame(gw1_data)

    rec = evaluate_opportunistic_wildcard(
        current_squad_codes=owned_codes,
        gw1_df=df,
        horizon_dfs=[df, df, df],
        free_transfers=0,
        bank=0.5,
        current_gw=29,
        season=temp_test_env['season'],
        data_root=temp_test_env['root'],
    )

    # Must withhold Wildcard and recommend Free Hit
    assert rec.is_active_now is False
    assert "FREE HIT" in rec.rationale


def test_constrained_optimal_xi_respects_budget_and_formation():
    """_build_constrained_optimal_xi must respect FPL positional rules and budget constraints."""
    from model.chip_optimizer import _build_constrained_optimal_xi

    players = []
    # Generate a full pool of 50 players across positions
    code = 1
    for pos, count in [('GK', 5), ('DEF', 15), ('MID', 20), ('FWD', 10)]:
        for i in range(count):
            players.append({
                'player_code': code,
                'position': pos,
                'team': f'Team_{code % 10}',
                'cost': 5.5 + (i * 0.3),
                'expected_points': 3.0 + (i * 0.4),
            })
            code += 1
    df = pd.DataFrame(players)

    best_xp, capt_bonus = _build_constrained_optimal_xi(df, budget_limit=100.0)
    assert best_xp > 0.0
    assert capt_bonus > 0.0
    assert best_xp > capt_bonus


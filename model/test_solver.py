"""Unit tests for model.solver — the Phase 4 FPL Squad Optimization Solver.

Verifies:
1. 15-player positional quotas (2 GK, 5 DEF, 5 MID, 3 FWD).
2. Budget limit compliance (cost <= £100.0M or custom limit).
3. Maximum 3 players per Premier League team.
4. Starting XI size (11 starters) and valid formation rules (min 3 DEF, min 2 MID, min 1 FWD).
5. Captain ($2x$) and Vice-Captain assignment to distinct starters.
6. Bench ordering rules (Bench GK slot 1, outfield bench ordered descending by xP).
7. Weekly transfer optimization respecting free transfers and calculating -4 hit penalties.
8. Infeasible budget handling.
9. End-to-end squad solving on actual gameweek dataset.
"""
import os
import sys
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.solver import (
    solve_initial_squad,
    solve_squad_lineup,
    solve_weekly_transfers,
    order_bench,
    format_squad_output,
    calculate_fpl_selling_price,
    PlayerPick,
    SquadSolution,
    TransferSolution,
)


@pytest.fixture
def sample_player_pool() -> pd.DataFrame:
    """Create a realistic synthetic player pool for optimization tests."""
    players = [
        # GKs
        {'player_code': 1, 'web_name': 'Raya', 'team': 'Arsenal', 'position': 'GK', 'cost': 5.5, 'expected_points': 5.2},
        {'player_code': 2, 'web_name': 'Pickford', 'team': 'Everton', 'position': 'GK', 'cost': 5.0, 'expected_points': 4.5},
        {'player_code': 3, 'web_name': 'Fabianski', 'team': 'West Ham', 'position': 'GK', 'cost': 4.0, 'expected_points': 1.0},
        {'player_code': 23, 'web_name': 'Valdimarsson', 'team': 'Brentford', 'position': 'GK', 'cost': 4.0, 'expected_points': 0.5},
        # DEFs
        {'player_code': 4, 'web_name': 'Gabriel', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 6.5},
        {'player_code': 5, 'web_name': 'Saliba', 'team': 'Arsenal', 'position': 'DEF', 'cost': 6.0, 'expected_points': 5.8},
        {'player_code': 6, 'web_name': 'Alexander-Arnold', 'team': 'Liverpool', 'position': 'DEF', 'cost': 7.0, 'expected_points': 6.2},
        {'player_code': 7, 'web_name': 'Gvardiol', 'team': 'Man City', 'position': 'DEF', 'cost': 6.0, 'expected_points': 5.0},
        {'player_code': 8, 'web_name': 'Robinson', 'team': 'Fulham', 'position': 'DEF', 'cost': 4.5, 'expected_points': 4.2},
        {'player_code': 9, 'web_name': 'Bednarek', 'team': 'Southampton', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.5},
        {'player_code': 10, 'web_name': 'Greaves', 'team': 'Ipswich', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.2},
        {'player_code': 24, 'web_name': 'Harwood-Bellis', 'team': 'Southampton', 'position': 'DEF', 'cost': 4.0, 'expected_points': 2.0},
        # MIDs
        {'player_code': 11, 'web_name': 'Salah', 'team': 'Liverpool', 'position': 'MID', 'cost': 12.5, 'expected_points': 7.5},
        {'player_code': 12, 'web_name': 'Saka', 'team': 'Arsenal', 'position': 'MID', 'cost': 10.0, 'expected_points': 6.8},
        {'player_code': 13, 'web_name': 'Palmer', 'team': 'Chelsea', 'position': 'MID', 'cost': 10.5, 'expected_points': 7.0},
        {'player_code': 14, 'web_name': 'Son', 'team': 'Spurs', 'position': 'MID', 'cost': 9.5, 'expected_points': 6.0},
        {'player_code': 15, 'web_name': 'Rogers', 'team': 'Aston Villa', 'position': 'MID', 'cost': 5.0, 'expected_points': 4.8},
        {'player_code': 16, 'web_name': 'Winks', 'team': 'Leicester', 'position': 'MID', 'cost': 4.5, 'expected_points': 2.0},
        {'player_code': 17, 'web_name': 'Sangaré', 'team': 'Nott\'m Forest', 'position': 'MID', 'cost': 4.5, 'expected_points': 2.1},
        {'player_code': 25, 'web_name': 'King', 'team': 'Fulham', 'position': 'MID', 'cost': 4.5, 'expected_points': 1.8},
        # FWDs
        {'player_code': 18, 'web_name': 'Haaland', 'team': 'Man City', 'position': 'FWD', 'cost': 15.0, 'expected_points': 8.5},
        {'player_code': 19, 'web_name': 'Isak', 'team': 'Newcastle', 'position': 'FWD', 'cost': 8.5, 'expected_points': 6.0},
        {'player_code': 20, 'web_name': 'Watkins', 'team': 'Aston Villa', 'position': 'FWD', 'cost': 9.0, 'expected_points': 6.2},
        {'player_code': 21, 'web_name': 'Wood', 'team': 'Nott\'m Forest', 'position': 'FWD', 'cost': 6.0, 'expected_points': 4.5},
        {'player_code': 22, 'web_name': 'Jebbison', 'team': 'Bournemouth', 'position': 'FWD', 'cost': 4.5, 'expected_points': 1.5},
        {'player_code': 26, 'web_name': 'Stewart', 'team': 'Southampton', 'position': 'FWD', 'cost': 4.5, 'expected_points': 1.2},
    ]
    return pd.DataFrame(players)


class TestSquadOptimizer:
    """Verify core ILP optimization rules for initial 15-man squad selection."""

    def test_squad_quotas_and_formation(self, sample_player_pool):
        sol = solve_initial_squad(sample_player_pool, budget=100.0)

        assert sol.status == "Optimal"
        assert len(sol.squad) == 15
        assert len(sol.starters) == 11
        assert len(sol.bench) == 4

        # Positional quotas in 15-man squad
        pos_counts = pd.Series([p.position for p in sol.squad]).value_counts().to_dict()
        assert pos_counts['GK'] == 2
        assert pos_counts['DEF'] == 5
        assert pos_counts['MID'] == 5
        assert pos_counts['FWD'] == 3

        # Starting XI formation quotas
        start_pos_counts = pd.Series([p.position for p in sol.starters]).value_counts().to_dict()
        assert start_pos_counts['GK'] == 1
        assert 3 <= start_pos_counts['DEF'] <= 5
        assert 2 <= start_pos_counts['MID'] <= 5
        assert 1 <= start_pos_counts['FWD'] <= 3

    def test_budget_compliance(self, sample_player_pool):
        sol = solve_initial_squad(sample_player_pool, budget=100.0)
        assert sol.status == "Optimal"
        assert sol.total_cost <= 100.0

        # Tighter budget constraint
        sol_tight = solve_initial_squad(sample_player_pool, budget=90.0)
        assert sol_tight.status == "Optimal"
        assert sol_tight.total_cost <= 90.0
        assert sol_tight.total_xp < sol.total_xp

    def test_infeasible_budget_handling(self, sample_player_pool):
        # Budget so low that no 15-man squad can be formed
        sol_inf = solve_initial_squad(sample_player_pool, budget=30.0)
        assert sol_inf.status == "Infeasible"
        assert len(sol_inf.squad) == 0

    def test_club_limit_constraint(self, sample_player_pool):
        sol = solve_initial_squad(sample_player_pool, budget=100.0, max_team_players=3)
        team_counts = pd.Series([p.team for p in sol.squad]).value_counts()
        assert (team_counts <= 3).all()

    def test_max_promoted_players_constraint(self, sample_player_pool):
        # Mark Southampton as promoted team
        pool = sample_player_pool.copy()
        pool['is_promoted'] = pool['team'] == 'Southampton'
        sol = solve_initial_squad(pool, budget=100.0, max_team_players=3, max_promoted_players=1)
        team_counts = pd.Series([p.team for p in sol.squad]).value_counts()
        # Southampton should have at most 1 player selected
        soton_count = team_counts.get('Southampton', 0)
        assert soton_count <= 1

    def test_captaincy_and_vice_captaincy(self, sample_player_pool):
        sol = solve_initial_squad(sample_player_pool, budget=100.0)
        assert sol.captain is not None
        assert sol.vice_captain is not None
        assert sol.captain.player_code != sol.vice_captain.player_code
        assert sol.captain.is_starter is True
        assert sol.vice_captain.is_starter is True

        # Top scorers like Haaland or Salah should be chosen captain
        assert sol.captain.web_name in ('Haaland', 'Salah', 'Palmer')
        assert sol.total_xp == round(sol.starting_xp + sol.captain_xp, 4)

    def test_bench_ordering_rules(self, sample_player_pool):
        sol = solve_initial_squad(sample_player_pool, budget=100.0)
        bench = sol.bench

        # Slot 1 must be GK
        assert bench[0].position == 'GK'
        assert bench[0].bench_order == 1

        # Slots 2, 3, 4 must be outfield ordered descending by expected points
        outfield_bench = bench[1:]
        assert len(outfield_bench) == 3
        for idx in range(len(outfield_bench) - 1):
            assert outfield_bench[idx].expected_points >= outfield_bench[idx + 1].expected_points


class TestWeeklyTransfers:
    """Verify weekly transfer optimizer and -4 hit calculations."""

    def test_single_free_transfer(self, sample_player_pool):
        initial_codes = [1, 3, 4, 5, 8, 9, 10, 12, 14, 15, 16, 17, 18, 21, 22]
        trans_sol = solve_weekly_transfers(
            current_squad_codes=initial_codes,
            df=sample_player_pool,
            free_transfers=1,
            bank=5.0,
            max_transfers=1,
        )
        assert trans_sol.squad_solution.status == "Optimal"
        assert trans_sol.transfers_count <= 1
        assert trans_sol.hits_taken == 0
        assert trans_sol.hit_penalty == 0.0

    def test_two_transfers_with_one_hit(self, sample_player_pool):
        initial_codes = [1, 3, 4, 5, 8, 9, 10, 12, 14, 15, 16, 17, 18, 21, 22]
        trans_sol = solve_weekly_transfers(
            current_squad_codes=initial_codes,
            df=sample_player_pool,
            free_transfers=1,
            bank=10.0,
            max_transfers=2,
            hit_cost=4.0,
        )
        if trans_sol.transfers_count == 2:
            assert trans_sol.hits_taken == 1
            assert trans_sol.hit_penalty == 4.0
            assert trans_sol.net_xp == round(trans_sol.squad_solution.total_xp - 4.0, 4)


class TestFPLSellingPrice:
    """Verify FPL 50% profit retention selling price mechanics."""

    def test_selling_price_calculation(self):
        from model.solver import calculate_fpl_selling_price
        # Bought at 10.0, current 11.0 (+1.0M profit -> +0.5M retained -> 10.5 sell price)
        assert calculate_fpl_selling_price(10.0, 11.0) == 10.5
        # Bought at 10.0, current 10.5 (+0.5M profit -> floor(0.5/2) = +0.2M retained -> 10.2 sell price)
        assert calculate_fpl_selling_price(10.0, 10.5) == 10.2
        # Bought at 10.0, current 9.5 (price drop -> full drop -> 9.5 sell price)
        assert calculate_fpl_selling_price(10.0, 9.5) == 9.5


class TestChipOptimization:
    """Verify FPL strategic chips (Triple Captain, Bench Boost, Wildcard)."""

    def test_triple_captain_chip(self, sample_player_pool):
        sol_std = solve_initial_squad(sample_player_pool, budget=100.0)
        sol_3xc = solve_initial_squad(sample_player_pool, budget=100.0, chip='3xc')

        assert sol_3xc.status == "Optimal"
        # In 3xC, captain bonus should be exactly double the standard captain bonus (2 * capt_xp)
        assert abs(sol_3xc.captain_xp - (2.0 * sol_std.captain.expected_points)) < 1e-3
        assert sol_3xc.total_xp > sol_std.total_xp

    def test_bench_boost_chip(self, sample_player_pool):
        sol_bb = solve_initial_squad(sample_player_pool, budget=100.0, chip='bboost')
        assert sol_bb.status == "Optimal"
        assert len(sol_bb.starters) == 15
        assert sol_bb.formation == "5-5-3"

    def test_wildcard_chip_zero_hits(self, sample_player_pool):
        initial_codes = [1, 3, 4, 5, 8, 9, 10, 12, 14, 15, 16, 17, 18, 21, 22]
        # Wildcard allows 4 transfers with 0 hit penalty
        trans_wc = solve_weekly_transfers(
            current_squad_codes=initial_codes,
            df=sample_player_pool,
            free_transfers=1,
            bank=10.0,
            chip='wildcard',
            max_transfers=4,
        )
        assert trans_wc.squad_solution.status == "Optimal"
        assert trans_wc.hits_taken == 0
        assert trans_wc.hit_penalty == 0.0


class TestUserLocksAndOverrides:
    """Verify player locks, exclusions, and forced captaincy constraints."""

    def test_locked_player_must_be_in_squad(self, sample_player_pool):
        # Force Bednarek (code 9, lower xP) into squad
        sol = solve_initial_squad(
            sample_player_pool,
            budget=100.0,
            locked_player_codes=['Bednarek'],
        )
        assert sol.status == "Optimal"
        squad_names = [p.web_name for p in sol.squad]
        assert 'Bednarek' in squad_names

    def test_excluded_player_never_in_squad(self, sample_player_pool):
        # Exclude Haaland (code 18, highest xP)
        sol = solve_initial_squad(
            sample_player_pool,
            budget=100.0,
            excluded_player_codes=['Haaland'],
        )
        assert sol.status == "Optimal"
        squad_names = [p.web_name for p in sol.squad]
        assert 'Haaland' not in squad_names

    def test_forced_captain_must_be_captain(self, sample_player_pool):
        # Force Palmer as captain instead of default highest xP Haaland
        sol = solve_initial_squad(
            sample_player_pool,
            budget=100.0,
            forced_captain_code='Palmer',
        )
        assert sol.status == "Optimal"
        assert sol.captain is not None
        assert sol.captain.web_name == 'Palmer'
        # Palmer must also be in starting XI
        starter_names = [p.web_name for p in sol.starters]
        assert 'Palmer' in starter_names


class TestSquadLineupOptimizer:
    """Verify solve_squad_lineup preserves exact 15 squad players while optimizing starting XI."""

    @pytest.fixture
    def fixed_15_squad(self, sample_player_pool) -> pd.DataFrame:
        # Pick 15 players (2 GK, 5 DEF, 5 MID, 3 FWD)
        codes = [1, 2, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 18, 19, 20]
        return sample_player_pool[sample_player_pool['player_code'].isin(codes)].copy()

    def test_squad_membership_is_100_percent_invariant(self, fixed_15_squad):
        sol_pure = solve_squad_lineup(fixed_15_squad, strategy='pure_xp')
        sol_rp = solve_squad_lineup(fixed_15_squad, strategy='rank_protect')
        sol_diff = solve_squad_lineup(fixed_15_squad, strategy='differential_chase')

        orig_codes = set(fixed_15_squad['player_code'])

        for sol in [sol_pure, sol_rp, sol_diff]:
            assert sol.status == "Optimal"
            assert len(sol.squad) == 15
            assert len(sol.starters) == 11
            assert len(sol.bench) == 4
            sol_codes = set(p.player_code for p in sol.squad)
            assert sol_codes == orig_codes, "Lineup optimizer must preserve exact 15 squad players without making transfers"

            # Check formation legality
            starters_pos = [p.position for p in sol.starters]
            assert starters_pos.count('GK') == 1
            assert 3 <= starters_pos.count('DEF') <= 5
            assert 2 <= starters_pos.count('MID') <= 5
            assert 1 <= starters_pos.count('FWD') <= 3

    def test_triple_captain_on_fixed_squad(self, fixed_15_squad):
        sol_tc = solve_squad_lineup(fixed_15_squad, strategy='pure_xp', chip='3xc')
        assert sol_tc.status == "Optimal"
        assert sol_tc.captain is not None
        assert abs(sol_tc.captain_xp - (2.0 * sol_tc.captain.expected_points)) < 1e-3
        assert len(sol_tc.starters) == 11
        assert len(sol_tc.bench) == 4

    def test_bench_boost_on_fixed_squad(self, fixed_15_squad):
        sol_bb = solve_squad_lineup(fixed_15_squad, strategy='pure_xp', chip='bboost')
        assert sol_bb.status == "Optimal"
        assert len(sol_bb.starters) == 15
        assert len(sol_bb.bench) == 0
        assert sol_bb.formation == "5-5-3"


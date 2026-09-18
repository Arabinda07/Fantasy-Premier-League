"""Unit and integration tests for Dynamic Tactical Prior Updating (Gap B).

Verifies:
1. Dynamic loading from JSON file with clean fallback to static TACTICAL_ARCHETYPES.
2. Score to multiplier calibration (1.0 -> 0.85, 3.0 -> 1.00, 5.0 -> 1.20).
3. EWMA smoothing behavior across iterations.
4. TypeSafeBridge key resolution, caching, and offline mock safety.
5. End-to-end integration with enrich_predictions_with_matchup_intelligence.
"""
import json
import os
import shutil
import sys
import tempfile
import pytest
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.matchup_intelligence import (
    TACTICAL_ARCHETYPES,
    PLAYER_TACTICAL_AFFINITIES,
    load_dynamic_tactical_archetypes,
    compute_tactical_archetype_multiplier,
    enrich_predictions_with_matchup_intelligence,
)
from model.tactical_prior_updater import (
    score_to_multiplier,
    apply_ewma_smoothing,
    TacticalPriorUpdater,
    save_tactical_archetypes_file,
    load_tactical_archetypes_file,
)
from model.typesafe_bridge import (
    TypeSafeBridge,
    resolve_typesafe_api_key,
)


@pytest.fixture
def temp_dir():
    """Create and clean up temporary directory."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


class TestDynamicTacticalLoading:
    """Tests for loading and fallback of tactical archetypes."""

    def test_fallback_when_file_missing(self, temp_dir):
        """When JSON file does not exist, returns exact default baselines."""
        teams, affinities = load_dynamic_tactical_archetypes(season='2026-27', data_root=temp_dir)
        assert teams['Brighton'] == TACTICAL_ARCHETYPES['Brighton']
        assert affinities['Palmer'] == 'transition_playmaker'

    def test_overlay_dynamic_values(self, temp_dir):
        """When JSON file exists, dynamic values overlay onto baselines."""
        season_dir = os.path.join(temp_dir, '2026-27')
        os.makedirs(season_dir, exist_ok=True)
        fpath = os.path.join(season_dir, 'tactical_archetypes.json')

        payload = {
            "season": "2026-27",
            "teams": {
                "Brighton": {"defensive_line": 1.25, "transition_vulnerability": 1.22},
                "NewTeam": {"defensive_line": 0.88, "transition_vulnerability": 0.90}
            },
            "player_affinities": {
                "Joao Pedro": "transition_playmaker",
                "NewPoacher": "poacher"
            }
        }
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(payload, f)

        teams, affinities = load_dynamic_tactical_archetypes(season='2026-27', data_root=temp_dir)
        assert teams['Brighton']['defensive_line'] == 1.25
        assert teams['NewTeam']['defensive_line'] == 0.88
        assert affinities['Joao Pedro'] == 'transition_playmaker'
        # Unchanged teams still retain baseline
        assert teams['Arsenal'] == TACTICAL_ARCHETYPES['Arsenal']


class TestScoreToMultiplier:
    """Tests for linear piecewise score-to-multiplier conversion."""

    def test_anchor_points(self):
        """Test scores 1.0, 3.0, and 5.0 map to 0.85, 1.00, and 1.20."""
        assert score_to_multiplier(1.0) == 0.85
        assert score_to_multiplier(3.0) == 1.00
        assert score_to_multiplier(5.0) == 1.20

    def test_interpolated_points(self):
        """Test intermediate values (2.0 and 4.0)."""
        # 1.0 -> 0.85, 3.0 -> 1.00: mid is 0.925
        assert score_to_multiplier(2.0) == 0.925
        # 3.0 -> 1.00, 5.0 -> 1.20: mid is 1.10
        assert score_to_multiplier(4.0) == 1.10

    def test_clipping_bounds(self):
        """Values beyond 1.0 and 5.0 are clipped."""
        assert score_to_multiplier(0.5) == 0.85
        assert score_to_multiplier(6.0) == 1.20


class TestEwmaSmoothing:
    """Tests for EWMA update logic."""

    def test_ewma_weighted_combination(self):
        """70% prior + 30% new value."""
        prior = 1.00
        new_val = 1.20
        # 0.70 * 1.00 + 0.30 * 1.20 = 0.70 + 0.36 = 1.06
        smoothed = apply_ewma_smoothing(prior, new_val, alpha=0.30)
        assert smoothed == 1.06


class TestTypeSafeBridge:
    """Tests for TypeSafeBridge caching and offline execution."""

    def test_key_resolution(self):
        """Bridge resolves key if present in env or registry."""
        resolved = resolve_typesafe_api_key()
        # Verify it is either None or a non-empty string
        if resolved is not None:
            assert isinstance(resolved, str)
            assert len(resolved) > 10

    def test_disk_cache_behavior(self, temp_dir):
        """Second identical call must be served from disk cache."""
        cache_dir = os.path.join(temp_dir, "cache")
        bridge = TypeSafeBridge(cache_dir=cache_dir, enable_cache=True)

        state = {"team": "Brentford", "notes": "Solid mid-block"}
        questions = {
            "test_score": {
                "type": "score",
                "instruction": "Rate defensive line",
                "legend": {"1": "Low", "3": "Mid", "5": "High"}
            }
        }

        # First call (executes or mocks)
        res1 = bridge.ask(state, questions)
        assert res1.cached is False

        # Second call with identical state & questions MUST be cached
        res2 = bridge.ask(state, questions)
        assert res2.cached is True
        assert res2.answers == res1.answers


class TestEndToEndEnrichmentWithDynamicArchetypes:
    """Tests for enrich_predictions_with_matchup_intelligence with dynamic archetypes."""

    def test_dynamic_archetype_alters_xp(self, temp_dir):
        """Altering opponent line to extreme high-line increases playmaker xP."""
        season_dir = os.path.join(temp_dir, '2026-27')
        os.makedirs(season_dir, exist_ok=True)

        # 1. Baseline calculation
        sample_df = pd.DataFrame([
            {
                'player_code': 244851,
                'web_name': 'Palmer',
                'fixture_opponent': 'Everton',
                'expected_points': 5.0,
                'c8_goals': 1.5,
                'c7_assists': 1.0,
            }
        ])
        baseline_enriched = enrich_predictions_with_matchup_intelligence(
            sample_df, season='2026-27', data_root=temp_dir
        )
        baseline_xp = baseline_enriched.iloc[0]['expected_points']

        # 2. Update Everton in dynamic JSON to an extreme suicidal high-line (1.20)
        save_tactical_archetypes_file(
            {
                "season": "2026-27",
                "teams": {
                    "Everton": {"defensive_line": 1.20, "transition_vulnerability": 1.18}
                },
                "player_affinities": {
                    "Palmer": "transition_playmaker"
                }
            },
            season='2026-27',
            data_root=temp_dir
        )

        # 3. Dynamic calculation with updated archetype
        dynamic_enriched = enrich_predictions_with_matchup_intelligence(
            sample_df, season='2026-27', data_root=temp_dir
        )
        dynamic_xp = dynamic_enriched.iloc[0]['expected_points']

        # Under the dynamic high-line Everton profile, transition playmaker Palmer's xP must increase
        assert dynamic_xp > baseline_xp
        assert dynamic_enriched.iloc[0]['tactical_mult'] > baseline_enriched.iloc[0]['tactical_mult']

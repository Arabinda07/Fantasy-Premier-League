"""Comprehensive Test Suite for TypeSafe AI (Jev System One) Decision Integrations.

Tests:
1. ContextRouter: Selective ground-truth spec and skill routing from developer prompts.
2. PlayerEntityResolver: External player entity reconciliation with diacritics and compound names.
3. SetPieceSuccession: Dynamic secondary set-piece taker election and equity allocation.
4. Offline Resilience: Verification that pipelines execute deterministically when offline.
"""
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from model.player_entity_resolver import (
    PlayerEntityResolver,
    ResolutionResult,
    normalize_name,
    strip_accents,
)
from model.set_pieces import (
    elect_substitute_set_piece_taker,
    enrich_predictions_with_set_pieces,
)
from model.typesafe_bridge import (
    ChoiceResult,
    ScoreResult,
    NoulResult,
    TypeSafeBridge,
    TypeSafeResponse,
)
from scripts.route_agent_context import ContextRouter, RoutedContextResult


@pytest.fixture
def temp_data_root():
    """Create a temporary data directory with mock player files."""
    tmp = tempfile.mkdtemp()
    season = "2026-27"
    season_dir = os.path.join(tmp, season)
    os.makedirs(season_dir, exist_ok=True)

    # Mock player_idlist.csv
    idlist_content = """first_name,second_name,id
David,Raya Martín,1
Gabriel,Martinelli Silva,18
Martin,Ødegaard,15
Darwin,Núñez,19
Rodrigo,Hernandez Cascante,20
Bukayo,Saka,12
Cole,Palmer,10
"""
    with open(os.path.join(season_dir, "player_idlist.csv"), "w", encoding="utf-8") as f:
        f.write(idlist_content)

    # Mock players_raw.csv
    players_raw_content = """code,id,web_name,first_name,second_name,team,element_type,now_cost,penalties_order,corners_and_indirect_freekicks_order,direct_freekicks_order
101,1,Raya,David,Raya Martín,1,1,55,,,
118,18,Martinelli,Gabriel,Martinelli Silva,1,3,70,2.0,2.0,2.0
115,15,Ødegaard,Martin,Ødegaard,1,3,85,,,
119,19,Nunez,Darwin,Núñez,2,4,75,,,
120,20,Rodri,Rodrigo,Hernandez Cascante,3,3,65,,,
112,12,Saka,Bukayo,Saka,1,3,100,1.0,1.0,1.0
110,10,Palmer,Cole,Palmer,4,3,105,1.0,1.0,1.0
"""
    with open(os.path.join(season_dir, "players_raw.csv"), "w", encoding="utf-8") as f:
        f.write(players_raw_content)

    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


class TestContextRouter:
    """Test suite for Dynamic Context & Skill Router."""

    def test_route_design_system_prompt(self):
        router = ContextRouter()
        # Test offline deterministic heuristic
        res = router._generate_heuristic_answers("Fix button color and token styling in BenchCard.jsx")
        assert res["selected_domain_spec"]["choice"] == "design_system_tokens"

    def test_route_copy_tone_prompt(self):
        router = ContextRouter()
        res = router._generate_heuristic_answers("Review tooltip copy for corporate jargon")
        assert res["selected_domain_spec"]["choice"] == "voice_and_tone_guide"

    def test_route_solver_prompt(self):
        router = ContextRouter()
        res = router._generate_heuristic_answers("Optimize transfer hits with multi-horizon solver")
        assert res["selected_domain_spec"]["choice"] == "milp_solver_model"

    def test_route_mock_bridge_execution(self):
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.is_authenticated = True
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "selected_domain_spec": {
                    "type": "choice",
                    "choice": "fixture_and_set_piece_engine",
                    "confidence": 0.94,
                    "probabilities": {"fixture_and_set_piece_engine": 0.94},
                },
                "required_skill": {
                    "type": "choice",
                    "choice": "typesafe_ai",
                    "confidence": 0.91,
                    "probabilities": {"typesafe_ai": 0.91},
                },
                "needs_execution_check": {
                    "type": "noul",
                    "noul": 0.12,
                }
            },
            usage={"input_tokens": 120, "output_tokens": 25},
            cached=False,
            latency_ms=15.0,
        )
        router = ContextRouter(bridge=mock_bridge)
        res = router.route("Calibrate penalty taker probabilities using Jev")
        assert res.domain_spec_choice == "fixture_and_set_piece_engine"
        assert res.domain_spec_confidence == 0.94
        assert res.required_skill_choice == "typesafe_ai"
        assert "knowledge/models/set-pieces.md" in res.recommended_files


class TestPlayerEntityResolver:
    """Test suite for PlayerEntityResolver."""

    def test_normalize_name_and_strip_accents(self):
        assert strip_accents("Darwin Núñez") == "Darwin Nunez"
        assert strip_accents("Martin Ødegaard") == "Martin Odegaard"
        assert normalize_name("Gabriel Martinelli Silva") == "gabriel martinelli silva"

    def test_exact_and_normalized_matching(self, temp_data_root):
        resolver = PlayerEntityResolver(season="2026-27", data_root=temp_data_root)

        # Exact match
        res_exact = resolver.resolve("Bukayo Saka")
        assert res_exact.fpl_code == 112
        assert res_exact.method in ("exact", "normalized_diacritic")

        # Diacritic match
        res_diacritic = resolver.resolve("Darwin Nunez")
        assert res_diacritic.fpl_code == 119
        assert res_diacritic.method in ("exact", "normalized_diacritic")

        # Compound Spanish surname match
        res_compound = resolver.resolve("Gabriel Martinelli")
        assert res_compound.fpl_code == 118
        assert res_compound.method in ("exact", "normalized_diacritic", "heuristic_token_overlap", "typesafe_jev")

    def test_mock_jev_resolution_for_nickname(self, temp_data_root):
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.is_authenticated = True
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "matched_player": {
                    "type": "choice",
                    "choice": "player_120",
                    "confidence": 0.92,
                    "probabilities": {"player_120": 0.92, "none_of_these": 0.08},
                }
            },
            usage={"input_tokens": 150, "output_tokens": 20},
            cached=False,
            latency_ms=20.0,
        )
        resolver = PlayerEntityResolver(season="2026-27", data_root=temp_data_root, bridge=mock_bridge)
        # Rodri is ambiguous without knowledge that his full name is Rodrigo Hernandez Cascante
        res = resolver.resolve("Rodri", team_hint="3")
        assert res.fpl_code == 120
        assert res.canonical_name == "Rodrigo Hernandez Cascante"


class TestSetPieceSuccession:
    """Test suite for Set-Piece Succession Deduction."""

    def test_elect_substitute_taker_mock_jev(self):
        starters = [
            {"player_code": 115, "web_name": "Odegaard", "position": "MID", "expected_points": 5.5},
            {"player_code": 118, "web_name": "Martinelli", "position": "MID", "expected_points": 5.2},
            {"player_code": 105, "web_name": "Saliba", "position": "DEF", "expected_points": 3.8},
        ]
        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.is_authenticated = True
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "elected_taker": {
                    "type": "choice",
                    "choice": "starter_118",
                    "confidence": 0.88,
                    "probabilities": {"starter_118": 0.88, "starter_115": 0.12},
                }
            },
            usage={"input_tokens": 100, "output_tokens": 15},
            cached=False,
            latency_ms=12.0,
        )
        elected_code, conf = elect_substitute_set_piece_taker(
            team_name="Arsenal", active_starters=starters, role="penalty", bridge=mock_bridge
        )
        assert elected_code == 118
        assert conf == 0.88

    def test_enrich_predictions_with_absent_primary_taker(self, temp_data_root):
        # Saka (pk_order=1.0) is absent (p_start=0.0). Martinelli (pk_order=2.0) is starting (p_start=1.0).
        pred_df = pd.DataFrame([
            {"player_code": 112, "web_name": "Saka", "position": "MID", "team": "1", "p_start": 0.0, "expected_points": 0.0},
            {"player_code": 118, "web_name": "Martinelli", "position": "MID", "team": "1", "p_start": 1.0, "expected_points": 5.0},
            {"player_code": 115, "web_name": "Odegaard", "position": "MID", "team": "1", "p_start": 1.0, "expected_points": 5.5},
        ])

        mock_bridge = MagicMock(spec=TypeSafeBridge)
        mock_bridge.is_authenticated = True
        mock_bridge.ask.return_value = TypeSafeResponse(
            answers={
                "elected_taker": {
                    "type": "choice",
                    "choice": "starter_118",
                    "confidence": 0.85,
                    "probabilities": {"starter_118": 0.85},
                }
            },
            usage={"input_tokens": 50, "output_tokens": 10},
            cached=False,
            latency_ms=10.0,
        )

        res_df = enrich_predictions_with_set_pieces(
            pred_df, season="2026-27", data_root=temp_data_root, bridge=mock_bridge
        )

        # Martinelli should have inherited secondary/primary penalty equity (> 0.0)
        martinelli_row = res_df[res_df['player_code'] == 118].iloc[0]
        assert martinelli_row['delta_c8_sp'] > 0.0
        assert martinelli_row['expected_points'] > 5.0

    def test_enrich_predictions_without_p_start_column(self, temp_data_root):
        """Ensure DataFrames without a p_start column (e.g. synthetic solver fixtures) execute safely."""
        pred_df = pd.DataFrame([
            {"player_code": 112, "web_name": "Saka", "position": "MID", "team": "1", "expected_points": 5.0},
            {"player_code": 118, "web_name": "Martinelli", "position": "MID", "team": "1", "expected_points": 4.5},
        ])
        res_df = enrich_predictions_with_set_pieces(
            pred_df, season="2026-27", data_root=temp_data_root
        )
        assert len(res_df) == 2
        assert "sp_pk_order" in res_df.columns


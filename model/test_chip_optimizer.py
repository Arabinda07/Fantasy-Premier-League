"""Unit tests for FPL Strategic Chip Timing Optimizer."""
import os
import sys
import pytest
import pandas as pd

# Add repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.chip_optimizer import (
    detect_double_and_blank_gameweeks,
    evaluate_chip_schedule,
    SeasonalChipPlan,
)


class TestChipOptimizer:
    """Verify chip timing heuristics, DGW/BGW detection, and schedule plan generation."""

    def test_schedule_profile_detection(self):
        profiles = detect_double_and_blank_gameweeks(season='2026-27')
        assert len(profiles) == 38
        assert all(p.gw == idx for idx, p in enumerate(profiles, start=1))

    def test_seasonal_chip_plan_generation(self):
        plan = evaluate_chip_schedule(season='2026-27', current_gw=1)
        assert isinstance(plan, SeasonalChipPlan)
        assert plan.season == '2026-27'
        assert plan.current_gw == 1

        recs = plan.recommendations
        assert '3xc' in recs
        assert 'bboost' in recs
        assert 'freehit' in recs
        assert 'wildcard_1' in recs
        assert 'wildcard_2' in recs

        # Wildcard 1 must be in first half (<= GW19)
        assert recs['wildcard_1'].target_gw <= 19

        # Wildcard 2 must be in second half (>= GW20)
        assert recs['wildcard_2'].target_gw >= 20

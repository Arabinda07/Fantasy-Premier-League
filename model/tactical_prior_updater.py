"""Tactical Prior Updater Engine for Fantasy Premier League.

Dynamically updates opponent defensive archetypes and player tactical affinities
using TypeSafe Jev System One judgments with EWMA smoothing, eliminating
hardcoded static dictionaries.
"""
from datetime import datetime, timezone
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.typesafe_bridge import TypeSafeBridge

# Rubric definitions for Team Defensive Archetypes (Score 1-5)
DEFENSIVE_LINE_LEGEND: Dict[str, str] = {
    "1": "Deep Low-Block: Deep penalty-box bunker, compresses space, leaves zero grass behind.",
    "2": "Mid-to-Low Block: Conservative defensive posture, disciplined positioning.",
    "3": "Standard Balanced Line: Neutral defensive height, balanced spacing.",
    "4": "Moderately High Line: Active territorial press, defends outside the penalty area.",
    "5": "Aggressive / Suicidal High Line: Extreme offside trap, defends near halfway, leaves vast space behind."
}

TRANSITION_VULNERABILITY_LEGEND: Dict[str, str] = {
    "1": "Transition Impervious: Relentless counter-press, fouls tactically, never exposed on turnovers.",
    "2": "Compact Recovery: Quick defensive recovery runs, rarely caught in transition.",
    "3": "Average: Standard recovery speed and transition concession.",
    "4": "Counter-Vulnerable: Midfield bypassed easily, susceptible to quick breaks.",
    "5": "Severe Transition Concession: High turnover exposure, leaves backline completely stranded."
}

# Rubric definitions for Player Tactical Affinities (Choice)
PLAYER_AFFINITY_OPTIONS: Dict[str, str] = {
    "transition_playmaker": "Transition Playmaker: Thrives on open grass, exploits high lines and transitions (e.g. Palmer, Saka, Bruno Fernandes).",
    "poacher": "Poacher: Penalty-box finisher relying on inside-box delivery and volume (e.g. Haaland).",
    "cross_specialist": "Cross Delivery Specialist: Benefits from low-block wide delivery and set-pieces.",
    "standard": "Standard Open-Play Attacker: Balanced attacking profile without extreme line-depth dependence."
}

DEFAULT_EWMA_ALPHA: float = 0.30  # 70% historical prior, 30% new evaluation


def score_to_multiplier(
    score: float,
    min_mult: float = 0.85,
    neutral_mult: float = 1.00,
    max_mult: float = 1.20,
) -> float:
    """Convert a 1.0-5.0 Score into a calibrated tactical multiplier.

    Scale:
        Score 1.0 -> min_mult (0.85)
        Score 3.0 -> neutral_mult (1.00)
        Score 5.0 -> max_mult (1.20)
    """
    score = max(1.0, min(5.0, float(score)))
    if score <= 3.0:
        # Interpolate between min_mult and neutral_mult
        frac = (score - 1.0) / 2.0
        mult = min_mult + frac * (neutral_mult - min_mult)
    else:
        # Interpolate between neutral_mult and max_mult
        frac = (score - 3.0) / 2.0
        mult = neutral_mult + frac * (max_mult - neutral_mult)
    return round(mult, 4)


def apply_ewma_smoothing(
    prior_val: float,
    new_val: float,
    alpha: float = DEFAULT_EWMA_ALPHA,
) -> float:
    """Apply Exponential Weighted Moving Average to smooth tactical transitions."""
    smoothed = (1.0 - alpha) * prior_val + alpha * new_val
    return round(smoothed, 4)


def get_tactical_archetypes_path(season: str = '2026-27', data_root: str = 'data') -> str:
    """Return path to season tactical_archetypes.json."""
    if os.path.isabs(data_root):
        season_dir = os.path.join(data_root, season)
    else:
        season_dir = os.path.join(REPO_ROOT, data_root, season)
    return os.path.join(season_dir, 'tactical_archetypes.json')


def load_tactical_archetypes_file(
    season: str = '2026-27',
    data_root: str = 'data',
) -> Optional[Dict[str, Any]]:
    """Load tactical archetypes JSON file if it exists."""
    fpath = get_tactical_archetypes_path(season, data_root)
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_tactical_archetypes_file(
    data: Dict[str, Any],
    season: str = '2026-27',
    data_root: str = 'data',
) -> str:
    """Save tactical archetypes to JSON file."""
    fpath = get_tactical_archetypes_path(season, data_root)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return fpath


class TacticalPriorUpdater:
    """Engine for evaluating and updating dynamic tactical priors."""

    def __init__(self, bridge: Optional[TypeSafeBridge] = None):
        self.bridge = bridge or TypeSafeBridge()

    def evaluate_team(
        self,
        team_name: str,
        tactical_summary: str,
    ) -> Dict[str, float]:
        """Evaluate a single team's defensive line depth and transition vulnerability.

        Returns:
            Dict with 'defensive_line' and 'transition_vulnerability' multipliers.
        """
        state = {
            "team": team_name,
            "tactical_observations": tactical_summary,
        }
        questions = {
            "defensive_line_depth": {
                "type": "score",
                "instruction": f"Rate {team_name}'s typical defensive line height and willingness to play an offside trap.",
                "legend": DEFENSIVE_LINE_LEGEND,
            },
            "transition_vulnerability": {
                "type": "score",
                "instruction": f"Rate {team_name}'s vulnerability to fast transitions and counter-attacks when losing possession.",
                "legend": TRANSITION_VULNERABILITY_LEGEND,
            }
        }

        # Safe defaults if offline
        mock = {
            "defensive_line_depth": {"type": "score", "score": 3.0, "confidence": 0.5},
            "transition_vulnerability": {"type": "score", "score": 3.0, "confidence": 0.5},
        }

        resp = self.bridge.ask(state, questions, mock_fallback=mock)

        raw_line = float(resp.answers.get("defensive_line_depth", {}).get("score", 2.0))
        raw_trans = float(resp.answers.get("transition_vulnerability", {}).get("score", 2.0))

        # Jev score is 0-indexed across 5 criteria (0.0=min, 2.0=neutral, 4.0=max).
        # Offset by +1.0 to map to the 1.0-5.0 rubric scale:
        line_1_to_5 = (raw_line + 1.0) if raw_line <= 4.0 else raw_line
        trans_1_to_5 = (raw_trans + 1.0) if raw_trans <= 4.0 else raw_trans

        return {
            "defensive_line": score_to_multiplier(line_1_to_5),
            "transition_vulnerability": score_to_multiplier(trans_1_to_5),
            "raw_line_score": raw_line,
            "raw_trans_score": raw_trans,
        }

    def evaluate_player_affinity(
        self,
        player_name: str,
        player_profile: str,
    ) -> str:
        """Categorize an active player's tactical affinity."""
        state = {
            "player": player_name,
            "scouting_profile": player_profile,
        }
        choice_res = self.bridge.ask_choice(
            state=state,
            instruction=f"Determine {player_name}'s primary tactical playing profile in open play.",
            options=PLAYER_AFFINITY_OPTIONS,
            question_id="affinity_choice",
        )
        return choice_res.value

    def update_team_in_dataset(
        self,
        team_name: str,
        tactical_summary: str,
        season: str = '2026-27',
        data_root: str = 'data',
        alpha: float = DEFAULT_EWMA_ALPHA,
        fallback_defaults: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, float]:
        """Evaluate team, apply EWMA smoothing against existing prior, and save."""
        dataset = load_tactical_archetypes_file(season, data_root) or {
            "season": season,
            "teams": {},
            "player_affinities": {},
        }

        existing_teams = dataset.setdefault("teams", {})
        prior_team = existing_teams.get(team_name)
        if not prior_team and fallback_defaults and team_name in fallback_defaults:
            prior_team = fallback_defaults[team_name]

        eval_res = self.evaluate_team(team_name, tactical_summary)
        new_line = eval_res["defensive_line"]
        new_trans = eval_res["transition_vulnerability"]

        if prior_team:
            smoothed_line = apply_ewma_smoothing(prior_team.get("defensive_line", 1.00), new_line, alpha)
            smoothed_trans = apply_ewma_smoothing(prior_team.get("transition_vulnerability", 1.00), new_trans, alpha)
        else:
            smoothed_line = new_line
            smoothed_trans = new_trans

        existing_teams[team_name] = {
            "defensive_line": smoothed_line,
            "transition_vulnerability": smoothed_trans,
        }

        save_tactical_archetypes_file(dataset, season, data_root)
        return existing_teams[team_name]

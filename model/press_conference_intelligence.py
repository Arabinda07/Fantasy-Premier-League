"""Press Conference & Injury Intelligence Engine for Fantasy Premier League.

Utilizes TypeSafe AI System One (Jev) to evaluate manager press conference quotes,
injury flags, and training reports into calibrated starter probabilities and sub-60 hook hazards.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.typesafe_bridge import TypeSafeBridge

# Premier League 2026-27 Manager Mapping
PREMIER_LEAGUE_MANAGERS: Dict[str, str] = {
    'Arsenal': 'Mikel Arteta',
    'Aston Villa': 'Unai Emery',
    'Bournemouth': 'Andoni Iraola',
    'Brentford': 'Thomas Frank',
    'Brighton': 'Fabian Hürzeler',
    'Chelsea': 'Enzo Maresca',
    'Crystal Palace': 'Oliver Glasner',
    'Everton': 'Sean Dyche',
    'Fulham': 'Marco Silva',
    'Ipswich Town': 'Kieran McKenna',
    'Leicester': 'Steve Cooper',
    'Liverpool': 'Arne Slot',
    'Man City': 'Pep Guardiola',
    'Man Utd': 'Erik ten Hag',
    'Newcastle': 'Eddie Howe',
    "Nott'm Forest": 'Nuno Espírito Santo',
    'Southampton': 'Russell Martin',
    'Spurs': 'Ange Postecoglou',
    'West Ham': 'Julen Lopetegui',
    'Wolves': "Gary O'Neil",
}

# Manager Candor & Mind-Game Rubric (Score 0-3)
MANAGER_CANDOR_LEGEND: Dict[str, str] = {
    "0": "Transparent & Direct: Manager gives clear, honest injury updates without games (e.g. Postecoglou, Iraola).",
    "1": "Generally Reliable: Straightforward with occasional minor tactical ambiguity.",
    "2": "Coded / Guarded: Frequently evasive, downplays or exaggerates severity.",
    "3": "Extreme Obfuscation: Deliberately misleads press, cryptic quotes, 'we will see' (e.g. Arteta, Guardiola)."
}

# Injury Severity Categories (Choice)
INJURY_SEVERITY_OPTIONS: Dict[str, str] = {
    "fit_to_start": "Fit to Start: Minor knock or precautionary rest; expected to start full match.",
    "minor_doubt_likely_start": "Minor Doubt: Will undergo late fitness test; probable starter (>60%).",
    "managed_minutes_risk": "Managed Minutes: Likely to start but under strict minutes restriction (<60 mins).",
    "bench_cameo_only": "Bench Cameo Only: Returning from injury; will start on bench with late 10-25 min cameo.",
    "unfit_ruled_out": "Ruled Out / Unfit: Will not participate in matchday squad."
}


@dataclass
class PressConferenceEvaluation:
    player_code: int
    player_name: str
    team: str
    manager: str
    status: str
    chance_of_playing: Optional[float]
    news: str
    p_start: float
    sub_60_hook_risk: float
    cameo_risk: float
    injury_severity: str
    manager_candor_score: float
    calibrated_p_start_mult: float
    calibrated_p_app_mult: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_press_evaluations_path(season: str = '2026-27', data_root: str = 'data') -> str:
    """Return path to season press_conference_evaluations.json."""
    if os.path.isabs(data_root):
        season_dir = os.path.join(data_root, season)
    else:
        season_dir = os.path.join(REPO_ROOT, data_root, season)
    return os.path.join(season_dir, 'press_conference_evaluations.json')


def load_press_evaluations(
    season: str = '2026-27',
    data_root: str = 'data',
) -> Dict[int, Dict[str, Any]]:
    """Load existing press conference evaluations keyed by player_code."""
    fpath = get_press_evaluations_path(season, data_root)
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                players = data.get('players', {})
                return {int(k): v for k, v in players.items()}
        except Exception:
            return {}
    return {}


def save_press_evaluations(
    evaluations: Dict[int, Dict[str, Any]],
    season: str = '2026-27',
    data_root: str = 'data',
) -> str:
    """Persist press conference evaluations to disk."""
    fpath = get_press_evaluations_path(season, data_root)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    payload = {
        'season': season,
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'total_evaluated': len(evaluations),
        'players': {str(k): v for k, v in evaluations.items()},
    }
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return fpath


class PressConferenceIntelligence:
    """Engine for decoding manager press conference quotes with Jev System One."""

    def __init__(self, bridge: Optional[TypeSafeBridge] = None):
        self.bridge = bridge or TypeSafeBridge()

    def evaluate_player_news(
        self,
        player_code: int,
        player_name: str,
        team_name: str,
        status: str = 'a',
        chance_of_playing: Optional[float] = None,
        news_text: str = '',
        days_rest: int = 7,
        manager_name: Optional[str] = None,
        fixture_context: Optional[str] = None,
    ) -> PressConferenceEvaluation:
        """Evaluate a single player's injury news and press conference context.

        Args:
            player_code: FPL player code.
            player_name: Player name (web_name or full name).
            team_name: Team name.
            status: FPL status code ('a', 'd', 'i', 's', 'u').
            chance_of_playing: API chance of playing (0-100 or None).
            news_text: Raw news / quote string from API or press briefing.
            days_rest: Days since team's last match.
            manager_name: Manager's name (defaults to lookup).
            fixture_context: Optional context string (e.g. 'UCL in 3 days').

        Returns:
            PressConferenceEvaluation with calibrated starter and hook hazards.
        """
        norm_status = str(status).lower().strip() if status else 'a'
        manager = manager_name or PREMIER_LEAGUE_MANAGERS.get(team_name, 'Team Manager')

        # DETERMINISTIC ANCHOR: Official FPL status strictly overrides subjective manager quotes.
        # Suspended ('s'), unavailable ('u'), or injured ('i' with chance == 0 or chance is None) are hard-zeros.
        is_strictly_unavailable = (norm_status in ('s', 'u')) or (norm_status == 'i' and (chance_of_playing == 0 or chance_of_playing is None))
        if is_strictly_unavailable:
            return PressConferenceEvaluation(
                player_code=player_code,
                player_name=player_name,
                team=team_name,
                manager=manager,
                status=norm_status,
                chance_of_playing=chance_of_playing,
                news=news_text,
                p_start=0.0,
                sub_60_hook_risk=0.0,
                cameo_risk=0.0,
                injury_severity='unfit_ruled_out',
                manager_candor_score=1.0,
                calibrated_p_start_mult=0.0,
                calibrated_p_app_mult=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # ADVERSARIAL SANITIZATION: strip null bytes, whitespace, truncate to 1000 chars
        sanitized_news = str(news_text or '').replace('\x00', '').strip()[:1000]
        if not sanitized_news:
            sanitized_news = "No specific injury reported; routine match preparation."

        # Build Jev State context
        state = {
            "player": player_name,
            "team": team_name,
            "manager": manager,
            "fpl_status": norm_status,
            "fpl_reported_chance": chance_of_playing,
            "news_and_manager_quotes": sanitized_news,
            "days_since_last_match": days_rest,
            "fixture_context": fixture_context or "Standard Premier League gameweek match.",
        }

        # Formulate typed Jev questions
        questions = {
            "p_start": {
                "type": "noul",
                "instructions": f"Calibrated probability that {player_name} will be in the starting XI for the upcoming Premier League match."
            },
            "sub_60_hook_risk": {
                "type": "noul",
                "instructions": f"If {player_name} starts, calibrated probability that he is substituted before the 60th minute due to fitness, precaution, or minutes management."
            },
            "cameo_risk": {
                "type": "noul",
                "instructions": f"Probability that {player_name} begins on the bench and is brought on as a late substitute for 10-25 minutes."
            },
            "injury_severity": {
                "type": "choice",
                "instructions": f"Classify the true injury and readiness state of {player_name}.",
                "options": INJURY_SEVERITY_OPTIONS,
            },
            "manager_candor": {
                "type": "score",
                "instructions": f"Rate the level of obfuscation or mind games typically associated with {manager}'s press briefings.",
                "legend": MANAGER_CANDOR_LEGEND,
            }
        }

        # Deterministic offline mock fallback
        prior_chance = float(chance_of_playing) / 100.0 if (chance_of_playing is not None and not math.isnan(chance_of_playing)) else 0.90
        if norm_status == 'd' and chance_of_playing is None:
            prior_chance = 0.50
        elif norm_status in ('i', 's', 'u'):
            prior_chance = 0.0

        default_severity = "fit_to_start" if prior_chance >= 0.85 else ("minor_doubt_likely_start" if prior_chance >= 0.50 else "unfit_ruled_out")

        mock_fallback = {
            "p_start": {"type": "noul", "noul": prior_chance},
            "sub_60_hook_risk": {"type": "noul", "noul": 0.20 if prior_chance < 0.80 else 0.05},
            "cameo_risk": {"type": "noul", "noul": 0.35 if (0.20 <= prior_chance <= 0.75) else 0.05},
            "injury_severity": {"type": "choice", "choice": default_severity, "confidence": 0.80},
            "manager_candor": {"type": "score", "score": 2.0 if manager in ('Mikel Arteta', 'Pep Guardiola') else 1.0, "confidence": 0.70},
        }

        resp = self.bridge.ask(state, questions, mock_fallback=mock_fallback)
        ans = resp.answers or {}

        p_start_val = float((ans.get("p_start") or {}).get("noul", prior_chance))
        hook_val = float((ans.get("sub_60_hook_risk") or {}).get("noul", 0.05))
        cameo_val = float((ans.get("cameo_risk") or {}).get("noul", 0.05))
        severity_val = str((ans.get("injury_severity") or {}).get("choice", default_severity))
        candor_val = float((ans.get("manager_candor") or {}).get("score", 1.0))

        # Constrain probabilities
        p_start_clamped = max(0.0, min(1.0, p_start_val))
        hook_clamped = max(0.0, min(1.0, hook_val))
        cameo_clamped = max(0.0, min(1.0, cameo_val))

        # Total Appearance Probability:
        # P(App) = P(Start) + P(Cameo | Bench)*P(Bench)
        p_bench_eligible = (1.0 - p_start_clamped) if severity_val != "unfit_ruled_out" else 0.0
        p_app_mult = max(0.0, min(1.0, p_start_clamped + p_bench_eligible * cameo_clamped))

        return PressConferenceEvaluation(
            player_code=player_code,
            player_name=player_name,
            team=team_name,
            manager=manager,
            status=norm_status,
            chance_of_playing=chance_of_playing,
            news=sanitized_news,
            p_start=round(p_start_clamped, 4),
            sub_60_hook_risk=round(hook_clamped, 4),
            cameo_risk=round(cameo_clamped, 4),
            injury_severity=severity_val,
            manager_candor_score=round(candor_val, 2),
            calibrated_p_start_mult=round(p_start_clamped, 4),
            calibrated_p_app_mult=round(p_app_mult, 4),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def evaluate_flagged_players(
        self,
        players_df: pd.DataFrame,
        season: str = '2026-27',
        data_root: str = 'data',
        persist: bool = True,
    ) -> Dict[int, Dict[str, Any]]:
        """Batch evaluate all flagged or doubtful players from players_raw.

        Args:
            players_df: DataFrame containing at least ['code', 'web_name', 'team', 'status'].
            season: Season string.
            data_root: Data root directory.
            persist: Whether to save results to press_conference_evaluations.json.

        Returns:
            Dict of evaluations keyed by player_code.
        """
        evaluations: Dict[int, Dict[str, Any]] = {}

        # Filter for flagged or reported players
        for _, row in players_df.iterrows():
            code = int(row.get('code', 0))
            status = str(row.get('status', 'a')).lower()
            chance = row.get('chance_of_playing_this_round')
            news = str(row.get('news', ''))

            has_chance = pd.notnull(chance) and not math.isnan(float(chance))
            chance_val = float(chance) if has_chance else None

            # Only evaluate players who are flagged, doubtful, or have active news
            is_flagged = (
                status != 'a'
                or (has_chance and chance_val < 100.0)
                or (len(news.strip()) > 0 and news.strip().lower() != 'nan')
            )

            if not is_flagged:
                continue

            name = str(row.get('web_name', row.get('second_name', f'Player_{code}')))
            team = str(row.get('team', 'Unknown'))

            eval_res = self.evaluate_player_news(
                player_code=code,
                player_name=name,
                team_name=team,
                status=status,
                chance_of_playing=chance_val,
                news_text=news,
            )
            evaluations[code] = eval_res.to_dict()

        if persist and evaluations:
            save_press_evaluations(evaluations, season=season, data_root=data_root)

        return evaluations

"""External Player Entity Resolution Engine for Fantasy Premier League.

Utilizes TypeSafe AI System One (Jev) alongside deterministic diacritic/token
normalization to reconcile disparate external player names (from Understat, FBref,
and external scouting feeds) to canonical FPL player codes and IDs.

Handles:
- Spanish/Portuguese maternal & paternal compound surnames (e.g. "Gabriel Martinelli Silva" -> "Gabriel Martinelli")
- Diacritics and special characters (e.g. "Darwin Núñez" -> "Darwin Nunez", "Martin Ødegaard" -> "Martin Odegaard")
- Mononyms and nicknames (e.g. "Rodri" -> "Rodrigo Hernandez Cascante")
- Transposed first and last names (e.g. "Son Heung-Min" -> "Heung-Min Son")

Persistent disk caching guarantees O(1) resolution on subsequent pipeline runs.
"""
from dataclasses import asdict, dataclass
import json
import os
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.typesafe_bridge import TypeSafeBridge, TypeSafeResponse


SPECIAL_CHAR_MAP: Dict[str, str] = {
    'Ø': 'O', 'ø': 'o',
    'Æ': 'AE', 'æ': 'ae',
    'Œ': 'OE', 'œ': 'oe',
    'Ð': 'D', 'ð': 'd',
    'Þ': 'TH', 'þ': 'th',
    'ß': 'ss',
}


def strip_accents(text: str) -> str:
    """Normalize unicode text and remove diacritics/accents."""
    if not text:
        return ""
    for k, v in SPECIAL_CHAR_MAP.items():
        text = text.replace(k, v)
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c)).strip()


def normalize_name(text: str) -> str:
    """Lowercase, strip accents, remove hyphens/periods, and collapse whitespace."""
    if not text:
        return ""
    clean = strip_accents(text).lower()
    for char in ('-', '.', "'", '’', '_'):
        clean = clean.replace(char, ' ')
    return ' '.join(clean.split())


@dataclass
class ResolutionResult:
    external_name: str
    fpl_code: Optional[int]
    fpl_id: Optional[int]
    canonical_name: Optional[str]
    confidence: float
    method: str  # 'exact', 'normalized_diacritic', 'typesafe_jev', 'cached', 'unresolved'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlayerEntityResolver:
    """Resolves external athlete identities to canonical FPL codes using Jev."""

    def __init__(
        self,
        season: str = "2026-27",
        data_root: str = "data",
        bridge: Optional[TypeSafeBridge] = None,
    ):
        self.season = season
        self.data_root = os.path.join(REPO_ROOT, data_root) if not os.path.isabs(data_root) else data_root
        self.bridge = bridge or TypeSafeBridge()

        # Cache file path
        self.cache_file = os.path.join(self.data_root, self.season, "resolved_player_entities.json")
        self.resolved_cache: Dict[str, Dict[str, Any]] = self._load_cache()

        # Load canonical FPL registry
        self._load_fpl_registry()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load persistent resolution cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        """Persist resolution cache to disk."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.resolved_cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_fpl_registry(self) -> None:
        """Load canonical player registry from players_raw.csv or player_idlist.csv."""
        self.fpl_players: List[Dict[str, Any]] = []
        self.exact_name_map: Dict[str, Dict[str, Any]] = {}
        self.norm_name_map: Dict[str, Dict[str, Any]] = {}

        players_raw_path = os.path.join(self.data_root, self.season, "players_raw.csv")
        idlist_path = os.path.join(self.data_root, self.season, "player_idlist.csv")

        if os.path.exists(players_raw_path):
            try:
                df = pd.read_csv(players_raw_path)
                for _, row in df.iterrows():
                    code = int(row.get("code", 0))
                    fpl_id = int(row.get("id", 0))
                    first = str(row.get("first_name", "")).strip()
                    second = str(row.get("second_name", "")).strip()
                    web_name = str(row.get("web_name", "")).strip()
                    team = str(row.get("team", ""))
                    full_name = f"{first} {second}".strip()

                    entry = {
                        "code": code,
                        "id": fpl_id,
                        "full_name": full_name,
                        "web_name": web_name,
                        "first_name": first,
                        "second_name": second,
                        "team": team,
                    }
                    self.fpl_players.append(entry)

                    # Exact lookups
                    if full_name:
                        self.exact_name_map[full_name.lower()] = entry
                    if web_name:
                        self.exact_name_map[web_name.lower()] = entry

                    # Normalized lookups
                    if full_name:
                        self.norm_name_map[normalize_name(full_name)] = entry
                    if web_name:
                        self.norm_name_map[normalize_name(web_name)] = entry
                    # Also try second name only if distinct
                    if second:
                        self.norm_name_map[normalize_name(second)] = entry
                return
            except Exception:
                pass

        # Fallback to player_idlist.csv
        if os.path.exists(idlist_path):
            try:
                df = pd.read_csv(idlist_path)
                for _, row in df.iterrows():
                    fpl_id = int(row.get("id", 0))
                    first = str(row.get("first_name", "")).strip()
                    second = str(row.get("second_name", "")).strip()
                    full_name = f"{first} {second}".strip()

                    entry = {
                        "code": fpl_id,
                        "id": fpl_id,
                        "full_name": full_name,
                        "web_name": second or full_name,
                        "first_name": first,
                        "second_name": second,
                        "team": "",
                    }
                    self.fpl_players.append(entry)
                    if full_name:
                        self.exact_name_map[full_name.lower()] = entry
                        self.norm_name_map[normalize_name(full_name)] = entry
                    if second:
                        self.norm_name_map[normalize_name(second)] = entry
            except Exception:
                pass

    def resolve(
        self,
        external_name: str,
        team_hint: Optional[str] = None,
    ) -> ResolutionResult:
        """Resolve external player name to canonical FPL identity."""
        cleaned_external = str(external_name).strip()
        if not cleaned_external:
            return ResolutionResult(
                external_name=external_name,
                fpl_code=None,
                fpl_id=None,
                canonical_name=None,
                confidence=0.0,
                method="unresolved",
            )

        # 1. Check persistent cache
        cache_key = cleaned_external.lower()
        if cache_key in self.resolved_cache:
            hit = self.resolved_cache[cache_key]
            return ResolutionResult(
                external_name=cleaned_external,
                fpl_code=hit.get("fpl_code"),
                fpl_id=hit.get("fpl_id"),
                canonical_name=hit.get("canonical_name"),
                confidence=hit.get("confidence", 1.0),
                method="cached",
            )

        # 2. Check exact string match
        if cache_key in self.exact_name_map:
            match = self.exact_name_map[cache_key]
            res = ResolutionResult(
                external_name=cleaned_external,
                fpl_code=match["code"],
                fpl_id=match["id"],
                canonical_name=match["full_name"],
                confidence=1.0,
                method="exact",
            )
            self._cache_result(cache_key, res)
            return res

        # 3. Check normalized diacritic / accent-stripped match
        norm_ext = normalize_name(cleaned_external)
        if norm_ext in self.norm_name_map:
            match = self.norm_name_map[norm_ext]
            res = ResolutionResult(
                external_name=cleaned_external,
                fpl_code=match["code"],
                fpl_id=match["id"],
                canonical_name=match["full_name"],
                confidence=0.98,
                method="normalized_diacritic",
            )
            self._cache_result(cache_key, res)
            return res

        # 4. Filter top candidate FPL records for semantic Jev evaluation
        candidates = self._find_candidates(norm_ext, team_hint)
        if not candidates:
            res = ResolutionResult(
                external_name=cleaned_external,
                fpl_code=None,
                fpl_id=None,
                canonical_name=None,
                confidence=0.0,
                method="unresolved",
            )
            return res

        # 5. TypeSafe Jev System One Choice Evaluation
        return self._evaluate_with_jev(cleaned_external, candidates, team_hint)

    def _find_candidates(
        self,
        norm_ext: str,
        team_hint: Optional[str] = None,
        max_candidates: int = 5,
    ) -> List[Dict[str, Any]]:
        """Identify plausible candidate FPL players for ambiguous name."""
        tokens = set(norm_ext.split())
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for p in self.fpl_players:
            p_full = normalize_name(p["full_name"])
            p_web = normalize_name(p["web_name"])
            p_tokens = set(p_full.split()) | set(p_web.split())

            # Token overlap score
            overlap = len(tokens & p_tokens)
            score = float(overlap)

            # Substring match bonus
            if norm_ext in p_full or p_web in norm_ext:
                score += 1.5

            # Team match bonus
            if team_hint and str(p.get("team", "")).lower() == str(team_hint).lower():
                score += 1.0

            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:max_candidates]]

    def _evaluate_with_jev(
        self,
        external_name: str,
        candidates: List[Dict[str, Any]],
        team_hint: Optional[str] = None,
    ) -> ResolutionResult:
        """Query TypeSafe Jev to select the correct athlete identity."""
        state = {
            "external_record_name": external_name,
            "team_hint": team_hint or "Unknown",
            "candidate_fpl_players": [
                {
                    "option_key": f"player_{c['code']}",
                    "fpl_code": c["code"],
                    "fpl_id": c["id"],
                    "full_name": c["full_name"],
                    "web_name": c["web_name"],
                    "team": c.get("team", ""),
                }
                for c in candidates
            ],
        }

        criteria = {
            f"player_{c['code']}": f"{c['full_name']} ({c['web_name']}, {c.get('team', 'PL')})"
            for c in candidates
        }
        criteria["none_of_these"] = "None of the candidates represent the exact same football player."

        questions = {
            "matched_player": {
                "type": "choice",
                "instructions": (
                    f"Which of the candidate FPL players is the exact same athlete as '{external_name}'? "
                    "Account for accents, nicknames, maternal/paternal surname order, and team. "
                    "If none match with certainty, choose 'none_of_these'."
                ),
                "criteria": criteria,
            }
        }

        # Intelligent fallback for offline / mock / 401 scenarios
        best_c = candidates[0]
        ext_tokens = set(normalize_name(external_name).split())
        best_full_tokens = set(normalize_name(best_c["full_name"]).split())
        best_web_tokens = set(normalize_name(best_c["web_name"]).split())
        is_token_subset = ext_tokens.issubset(best_full_tokens) or ext_tokens.issubset(best_web_tokens)

        fallback_choice = f"player_{best_c['code']}" if is_token_subset else "none_of_these"
        fallback_confidence = 0.90 if is_token_subset else 0.50

        mock_fallback = {
            "matched_player": {
                "type": "choice",
                "choice": fallback_choice,
                "confidence": fallback_confidence,
                "probabilities": {fallback_choice: fallback_confidence},
            }
        }

        resp: TypeSafeResponse = self.bridge.ask(state=state, questions=questions, mock_fallback=mock_fallback)
        ans = resp.answers.get("matched_player") or {}
        chosen_key = ans.get("choice", "none_of_these") if isinstance(ans, dict) else getattr(ans, "value", "none_of_these")
        confidence = float(ans.get("confidence", 0.0) if isinstance(ans, dict) else getattr(ans, "confidence", 0.0))

        if chosen_key != "none_of_these" and confidence >= 0.70:
            chosen_code = int(chosen_key.replace("player_", ""))
            matched_candidate = next((c for c in candidates if c["code"] == chosen_code), None)
            if matched_candidate:
                res = ResolutionResult(
                    external_name=external_name,
                    fpl_code=matched_candidate["code"],
                    fpl_id=matched_candidate["id"],
                    canonical_name=matched_candidate["full_name"],
                    confidence=confidence,
                    method="typesafe_jev",
                )
                self._cache_result(external_name.lower(), res)
                return res

        # Unresolved
        return ResolutionResult(
            external_name=external_name,
            fpl_code=None,
            fpl_id=None,
            canonical_name=None,
            confidence=confidence,
            method="unresolved",
        )

    def _cache_result(self, key: str, res: ResolutionResult) -> None:
        """Store resolved match in memory and persist to disk."""
        if res.fpl_code is not None:
            self.resolved_cache[key] = {
                "external_name": res.external_name,
                "fpl_code": res.fpl_code,
                "fpl_id": res.fpl_id,
                "canonical_name": res.canonical_name,
                "confidence": res.confidence,
                "method": res.method,
            }
            self._save_cache()

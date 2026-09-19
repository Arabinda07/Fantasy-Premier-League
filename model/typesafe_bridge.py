"""TypeSafe AI System One Bridge for FPL Dugout.

Encapsulates Jev API interactions with:
1. Dual-source API key resolution (Environment Variable and Windows User Registry).
2. Local disk caching in data/.cache/typesafe/ to eliminate redundant token cost and latency.
3. Safe offline fallback (Mock Mode) ensuring automated pipelines never crash.
"""
from dataclasses import dataclass, field
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Union
import urllib.error
import urllib.request

# Ensure repo root is available
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DEFAULT_TYPESAFE_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_TYPESAFE_MODEL = "jev-latest"
DEFAULT_CACHE_DIR = os.path.join(REPO_ROOT, "data", ".cache", "typesafe")
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 0.5


@dataclass
class ChoiceResult:
    value: str
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)


@dataclass
class ScoreResult:
    value: float
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    raw_level: Optional[str] = None


@dataclass
class NoulResult:
    probability: float


@dataclass
class TypeSafeResponse:
    answers: Dict[str, Any]
    usage: Dict[str, int]
    cached: bool = False
    latency_ms: float = 0.0


def resolve_typesafe_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """Resolve TYPESAFE_API_KEY from argument, os.environ, or Windows Registry."""
    if explicit_key is not None:
        return explicit_key.strip() if explicit_key.strip() else None

    # 1. Check process environment
    env_key = os.environ.get("TYPESAFE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # 2. Check Windows User Registry
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                val, _ = winreg.QueryValueEx(key, "TYPESAFE_API_KEY")
                if val and str(val).strip():
                    return str(val).strip()
        except Exception:
            pass

    return None


class TypeSafeBridge:
    """Production bridge for TypeSafe System One (Jev) evaluations."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_TYPESAFE_MODEL,
        endpoint: str = DEFAULT_TYPESAFE_ENDPOINT,
        cache_dir: str = DEFAULT_CACHE_DIR,
        enable_cache: bool = True,
        timeout_seconds: float = 10.0,
    ):
        self.api_key = resolve_typesafe_api_key(api_key)
        self.model = model
        self.endpoint = endpoint
        self.cache_dir = cache_dir
        self.enable_cache = enable_cache
        self.timeout_seconds = timeout_seconds

        if self.enable_cache:
            os.makedirs(self.cache_dir, exist_ok=True)

    @property
    def is_authenticated(self) -> bool:
        """Return True if an API key is resolved."""
        return bool(self.api_key)

    def _compute_cache_key(self, state: Any, questions: Dict[str, Any]) -> str:
        """Compute SHA-256 fingerprint for request payload."""
        payload = {
            "model": self.model,
            "state": state,
            "questions": questions,
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _read_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Read cached response from disk if present."""
        if not self.enable_cache:
            return None
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Corrupted disk cache artifact: unlink to self-heal
                try:
                    os.remove(cache_file)
                except OSError:
                    pass
                return None
            except Exception:
                return None
        return None

    def _write_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save successful response to disk cache."""
        if not self.enable_cache:
            return
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _normalize_questions(self, questions: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize question definitions to match TypeSafe API specifications."""
        normalized = {}
        for q_id, q_body in questions.items():
            item = dict(q_body)
            q_type = item.get("type", "choice").lower()
            item["type"] = q_type

            # Ensure 'instructions' field is used
            if "instruction" in item:
                item.setdefault("instructions", item.pop("instruction"))

            # Ensure 'criteria' field is used
            if q_type == "choice":
                if "options" in item and "criteria" not in item:
                    item["criteria"] = item.pop("options")
            elif q_type == "score":
                if "legend" in item and "criteria" not in item:
                    leg = item.pop("legend")
                    if isinstance(leg, dict):
                        sorted_keys = sorted(leg.keys(), key=lambda x: float(x))
                        item["criteria"] = [leg[k] for k in sorted_keys]
                    else:
                        item["criteria"] = list(leg)
            normalized[q_id] = item
        return normalized

    def ask(
        self,
        state: Any,
        questions: Dict[str, Any],
        mock_fallback: Optional[Dict[str, Any]] = None,
    ) -> TypeSafeResponse:
        """Submit questions over state to TypeSafe System One.

        Args:
            state: Context object (dict, string, or list).
            questions: Dictionary of typed question definitions.
            mock_fallback: Optional default answer dict if unauthenticated or offline.

        Returns:
            TypeSafeResponse with answers and usage.
        """
        norm_questions = self._normalize_questions(questions)
        cache_key = self._compute_cache_key(state, norm_questions)

        # 1. Check disk cache
        cached_data = self._read_cache(cache_key)
        if cached_data is not None:
            return TypeSafeResponse(
                answers=cached_data.get("answers", {}),
                usage=cached_data.get("usage", {"input_tokens": 0, "output_tokens": 0}),
                cached=True,
                latency_ms=0.0,
            )

        # 2. Check authentication / offline guardrail
        if not self.is_authenticated:
            fallback_answers = mock_fallback or self._generate_default_mock(norm_questions)
            return TypeSafeResponse(
                answers=fallback_answers,
                usage={"input_tokens": 0, "output_tokens": 0},
                cached=False,
                latency_ms=0.0,
            )

        # 3. Live network execution
        payload = {
            "model": self.model,
            "state": state,
            "questions": norm_questions,
        }
        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(self.endpoint, data=req_data, headers=headers)

        start_time = time.time()
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    latency_ms = (time.time() - start_time) * 1000.0
                    raw_body = resp.read().decode("utf-8")
                    res_json = json.loads(raw_body)

                    answers = res_json.get("answers", {})
                    usage = res_json.get("usage", {})

                    # Persist successful call to disk cache
                    self._write_cache(cache_key, {"answers": answers, "usage": usage})

                    return TypeSafeResponse(
                        answers=answers,
                        usage=usage,
                        cached=False,
                        latency_ms=round(latency_ms, 2),
                    )
            except urllib.error.HTTPError as he:
                last_exception = he
                if he.code in (429, 500, 502, 503, 504, 529) and attempt < MAX_RETRIES - 1:
                    backoff = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    time.sleep(backoff)
                    continue
                break
            except Exception as e:
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(INITIAL_BACKOFF_SECONDS * (2 ** attempt))
                    continue
                break

        # Fall back safely on network or API failures (never cache failures)
        fallback_answers = mock_fallback or self._generate_default_mock(norm_questions)
        return TypeSafeResponse(
            answers=fallback_answers,
            usage={"input_tokens": 0, "output_tokens": 0, "error": str(last_exception)},
            cached=False,
            latency_ms=round((time.time() - start_time) * 1000.0, 2),
        )

    def _generate_default_mock(self, questions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate neutral, schema-compliant fallback answers for mock execution."""
        mock_answers = {}
        for q_id, q_body in questions.items():
            q_type = q_body.get("type", "choice").lower()
            if q_type == "choice":
                crit = q_body.get("criteria", q_body.get("options", {}))
                opts = list(crit.keys()) if isinstance(crit, dict) else list(crit)
                first_opt = opts[0] if opts else "standard"
                prob_split = {opt: (1.0 / len(opts)) for opt in opts} if opts else {first_opt: 1.0}
                mock_answers[q_id] = {
                    "type": "choice",
                    "choice": first_opt,
                    "confidence": 0.5,
                    "probabilities": prob_split,
                }
            elif q_type == "score":
                crit = q_body.get("criteria", q_body.get("legend", []))
                if isinstance(crit, list):
                    num_levels = max(1, len(crit))
                    mid_score = float(num_levels - 1) / 2.0
                    probs = {str(i): 1.0 / num_levels for i in range(num_levels)}
                    legend_map = {str(i): str(c) for i, c in enumerate(crit)}
                elif isinstance(crit, dict):
                    levels = [float(k) for k in crit.keys()]
                    mid_score = sum(levels) / len(levels) if levels else 0.0
                    probs = {str(k): (1.0 / len(levels)) for k in levels} if levels else {"0": 1.0}
                    legend_map = {str(k): str(v) for k, v in crit.items()}
                else:
                    mid_score = 0.0
                    probs = {"0": 1.0}
                    legend_map = {}
                mock_answers[q_id] = {
                    "type": "score",
                    "score": mid_score,
                    "confidence": 0.5,
                    "legend": legend_map,
                    "probabilities": probs,
                }
            elif q_type == "noul":
                mock_answers[q_id] = {
                    "type": "noul",
                    "noul": 0.5,
                }
        return mock_answers

    # -----------------------------------------------------------------------
    # Typed Convenience Wrappers
    # -----------------------------------------------------------------------

    def ask_choice(
        self,
        state: Any,
        instruction: str,
        options: Dict[str, str],
        question_id: str = "q_choice",
    ) -> ChoiceResult:
        """Ask a single Choice question and parse typed result."""
        questions = {
            question_id: {
                "type": "choice",
                "instruction": instruction,
                "options": options,
            }
        }
        res = self.ask(state, questions)
        ans = res.answers.get(question_id) or {}
        val = ans.get("choice", list(options.keys())[0] if options else "standard")
        conf = float(ans.get("confidence", 0.5))
        probs = ans.get("probabilities") or {}
        return ChoiceResult(value=val, confidence=conf, probabilities=probs)

    def ask_score(
        self,
        state: Any,
        instruction: str,
        legend: Dict[Union[int, str], str],
        question_id: str = "q_score",
    ) -> ScoreResult:
        """Ask a single Score question and parse typed result."""
        str_legend = {str(k): str(v) for k, v in legend.items()}
        questions = {
            question_id: {
                "type": "score",
                "instruction": instruction,
                "legend": str_legend,
            }
        }
        res = self.ask(state, questions)
        ans = res.answers.get(question_id) or {}
        default_score = float(len(legend) - 1) / 2.0 if legend else 0.0
        val = float(ans.get("score", default_score))
        conf = float(ans.get("confidence", 0.5))
        probs = ans.get("probabilities") or {}
        raw_level_val = None
        if "legend" in ans and str(round(val)) in ans["legend"]:
            raw_level_val = str(ans["legend"][str(round(val))])
        return ScoreResult(value=val, confidence=conf, probabilities=probs, raw_level=raw_level_val)

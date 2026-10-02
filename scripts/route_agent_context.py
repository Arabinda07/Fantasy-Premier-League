#!/usr/bin/env python3
"""Dynamic Context & Skill Router for FPL Dugout.

Utilizes TypeSafe AI System One (Jev) to evaluate developer prompts and workspace
state in ~0.20-0.35s, selecting only the necessary OKF domain specifications and
specialized agent skills. Prunes 8,000-12,000 tokens of redundant prompt overhead.

Usage:
    python scripts/route_agent_context.py --prompt "Refactor solver penalty equity"
    python scripts/route_agent_context.py --prompt "Fix button styles in BenchCard" --json
"""
import argparse
from dataclasses import asdict, dataclass
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add repo root to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model.typesafe_bridge import TypeSafeBridge, TypeSafeResponse

# Mapping from Jev choice options to actual repository relative file paths
DOMAIN_SPEC_MAPPINGS: Dict[str, List[str]] = {
    'okf_dataset_schema': [
        'knowledge/datasets/players-raw.md',
        'knowledge/datasets/merged-gw.md',
        'knowledge/datasets/model-dataset.md',
        'knowledge/datasets/predictions.md',
    ],
    'milp_solver_model': [
        'knowledge/models/squad-optimization-solver.md',
        'knowledge/models/point-prediction-engine.md',
    ],
    'design_system_tokens': [
        'DESIGN.md',
        'frontend/src/styles/index.css',
    ],
    'voice_and_tone_guide': [
        'docs/voice-and-tone-guide.md',
        'frontend/src/constants/copyTokens.js',
    ],
    'fixture_and_set_piece_engine': [
        'knowledge/models/fixture-and-form-engine.md',
        'knowledge/models/set-pieces.md',
    ],
    'none_of_these': [],
}

SKILL_NAME_MAPPINGS: Dict[str, str] = {
    'codebase_design': 'codebase-design',
    'diagnosing_bugs': 'diagnosing-bugs',
    'ui_ux_pro_max': 'ui-ux-pro-max',
    'typesafe_ai': 'typesafe-ai',
    'none_of_these': '',
}


@dataclass
class RoutedContextResult:
    prompt: str
    domain_spec_choice: str
    domain_spec_confidence: float
    required_skill_choice: str
    required_skill_confidence: float
    needs_execution: bool
    execution_probability: float
    recommended_files: List[str]
    recommended_skill: Optional[str]
    latency_ms: float
    cached: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextRouter:
    """Evaluates task intent to selectively load specifications and skills."""

    def __init__(self, bridge: Optional[TypeSafeBridge] = None):
        self.bridge = bridge or TypeSafeBridge()

    def route(
        self,
        task_prompt: str,
        open_files: Optional[List[str]] = None,
        workspace_area: Optional[str] = None,
    ) -> RoutedContextResult:
        """Route prompt through Jev System One judgments."""
        state = {
            "task_prompt": task_prompt.strip(),
            "open_files": open_files or [],
            "workspace_area": workspace_area or "fpl-dugout",
        }

        questions = {
            "selected_domain_spec": {
                "type": "choice",
                "instructions": "Which domain specification does this task require as ground truth?",
                "criteria": {
                    "okf_dataset_schema": "Task touches CSV columns, raw player records, or merged gameweeks.",
                    "milp_solver_model": "Task touches transfer mathematics, objective functions, or chip equations.",
                    "design_system_tokens": "Task touches frontend UI components, CSS variables, or visual layout.",
                    "voice_and_tone_guide": "Task touches copywriting, tooltips, or matchday fan-facing copy.",
                    "fixture_and_set_piece_engine": "Task touches penalty/corner hierarchy or Poisson match forecasting.",
                    "none_of_these": "Task is general programming or self-contained without needing domain specs."
                }
            },
            "required_skill": {
                "type": "choice",
                "instructions": "Which specialized workflow skill must be loaded for this task?",
                "criteria": {
                    "codebase_design": "Refactoring module seams, interfaces, or dependency coupling.",
                    "diagnosing_bugs": "Investigating unexpected numerical regressions or test failures.",
                    "ui_ux_pro_max": "Creating or modifying frontend user interfaces and design systems.",
                    "typesafe_ai": "Writing or calibrating TypeSafe Jev System One questions and prompts.",
                    "none_of_these": "Standard coding task that does not require specialized workflow playbooks."
                }
            },
            "needs_execution_check": {
                "type": "noul",
                "instructions": "Does this request involve running solvers, pipelines, or simulation suites?",
                "criteria": {
                    "true": "The task asks to run, test, or compute solver solutions, model projections, or sync scripts.",
                    "false": "The task is purely code inspection, editing, or static file maintenance."
                }
            }
        }

        mock_fallback = self._generate_heuristic_answers(task_prompt, open_files)
        response: TypeSafeResponse = self.bridge.ask(state=state, questions=questions, mock_fallback=mock_fallback)
        answers = response.answers

        # Extract selected_domain_spec
        spec_ans = answers.get('selected_domain_spec') or {}
        if isinstance(spec_ans, dict):
            spec_choice = spec_ans.get('choice', 'none_of_these')
            spec_conf = float(spec_ans.get('confidence', 0.0))
        else:
            spec_choice = getattr(spec_ans, 'value', 'none_of_these')
            spec_conf = getattr(spec_ans, 'confidence', 0.0)

        # Extract required_skill
        skill_ans = answers.get('required_skill') or {}
        if isinstance(skill_ans, dict):
            skill_choice = skill_ans.get('choice', 'none_of_these')
            skill_conf = float(skill_ans.get('confidence', 0.0))
        else:
            skill_choice = getattr(skill_ans, 'value', 'none_of_these')
            skill_conf = getattr(skill_ans, 'confidence', 0.0)

        # Extract needs_execution_check
        exec_ans = answers.get('needs_execution_check') or {}
        if isinstance(exec_ans, dict):
            exec_prob = float(exec_ans.get('noul', 0.0))
        else:
            exec_prob = getattr(exec_ans, 'probability', 0.0)
        needs_exec = exec_prob >= 0.50

        # Resolve paths
        recommended_files = list(DOMAIN_SPEC_MAPPINGS.get(spec_choice, []))
        recommended_skill = SKILL_NAME_MAPPINGS.get(skill_choice) or None

        return RoutedContextResult(
            prompt=task_prompt,
            domain_spec_choice=spec_choice,
            domain_spec_confidence=spec_conf,
            required_skill_choice=skill_choice,
            required_skill_confidence=skill_conf,
            needs_execution=needs_exec,
            execution_probability=exec_prob,
            recommended_files=recommended_files,
            recommended_skill=recommended_skill,
            latency_ms=response.latency_ms,
            cached=response.cached,
        )

    def _generate_heuristic_answers(
        self,
        task_prompt: str,
        open_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Deterministic keyword answers map used for offline or fallback execution."""
        prompt_lower = task_prompt.lower()

        # Domain Spec Inference
        if any(w in prompt_lower for w in ('css', 'color', 'style', 'token', 'button', 'component', 'ui', 'frontend')):
            spec_choice = 'design_system_tokens'
        elif any(w in prompt_lower for w in ('copy', 'tone', 'voice', 'jargon', 'tooltip', 'words')):
            spec_choice = 'voice_and_tone_guide'
        elif any(w in prompt_lower for w in ('penalty', 'penalties', 'corner', 'free-kick', 'set-piece', 'fixture')):
            spec_choice = 'fixture_and_set_piece_engine'
        elif any(w in prompt_lower for w in ('solver', 'milp', 'hit', 'transfer', 'lineup', 'chip', 'wildcard')):
            spec_choice = 'milp_solver_model'
        elif any(w in prompt_lower for w in ('csv', 'dataset', 'column', 'schema', 'merged_gw', 'players_raw')):
            spec_choice = 'okf_dataset_schema'
        else:
            spec_choice = 'none_of_these'

        # Skill Inference
        if any(w in prompt_lower for w in ('jev', 'typesafe', 'system one', 'noul', 'rubric')):
            skill_choice = 'typesafe_ai'
        elif any(w in prompt_lower for w in ('bug', 'error', 'fail', 'regression', 'crash', 'exception')):
            skill_choice = 'diagnosing_bugs'
        elif any(w in prompt_lower for w in ('design', 'css', 'layout', 'tailwind', 'theme')):
            skill_choice = 'ui_ux_pro_max'
        elif any(w in prompt_lower for w in ('refactor', 'architecture', 'coupling', 'clean code')):
            skill_choice = 'codebase_design'
        else:
            skill_choice = 'none_of_these'

        needs_exec = any(w in prompt_lower for w in ('run', 'execute', 'test', 'simulate', 'solve', 'sync'))
        exec_prob = 0.85 if needs_exec else 0.15

        return {
            "selected_domain_spec": {
                "type": "choice",
                "choice": spec_choice,
                "confidence": 0.88,
                "probabilities": {spec_choice: 0.88},
            },
            "required_skill": {
                "type": "choice",
                "choice": skill_choice,
                "confidence": 0.88,
                "probabilities": {skill_choice: 0.88},
            },
            "needs_execution_check": {
                "type": "noul",
                "noul": exec_prob,
            }
        }


def main():
    parser = argparse.ArgumentParser(description="TypeSafe Context & Skill Router")
    parser.add_argument("--prompt", type=str, required=True, help="Developer task prompt or query")
    parser.add_argument("--files", nargs="*", default=[], help="Currently open file paths")
    parser.add_argument("--json", action="store_true", help="Output raw JSON payload")
    args = parser.parse_args()

    router = ContextRouter()
    result = router.route(task_prompt=args.prompt, open_files=args.files)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\n[TypeSafe Context Router] Result ({result.latency_ms:.1f}ms, cached={result.cached})")
        print(f"• Domain Spec Choice : {result.domain_spec_choice} (conf: {result.domain_spec_confidence:.2f})")
        print(f"• Required Skill     : {result.required_skill_choice} (conf: {result.required_skill_confidence:.2f})")
        print(f"• Needs Execution    : {result.needs_execution} (prob: {result.execution_probability:.2f})")
        if result.recommended_files:
            print("• Target Ground Truth Specs:")
            for f in result.recommended_files:
                print(f"    - {f}")
        if result.recommended_skill:
            print(f"• Load Workflow Skill: {result.recommended_skill}")
        print()


if __name__ == "__main__":
    main()

"""Deterministic, rubric-based evaluation of LLM output.

The tool scores text, it does not generate it. Checks are pure functions and
rubric scoring is explicit arithmetic, so a score can always be explained.
"""

from __future__ import annotations

__version__ = "1.0.0"

from .checks import BANNED_PHRASES, CheckResult, run_checks
from .rubric import Dimension, DimensionScore, Rubric, Scored, apply, default_rubric
from .runner import CaseResult, RunResult, load_cases, load_outputs, run

__all__ = [
    "BANNED_PHRASES",
    "CaseResult",
    "CheckResult",
    "Dimension",
    "DimensionScore",
    "Rubric",
    "RunResult",
    "Scored",
    "apply",
    "default_rubric",
    "load_cases",
    "load_outputs",
    "run",
    "run_checks",
    "__version__",
]

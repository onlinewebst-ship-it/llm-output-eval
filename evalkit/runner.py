"""Load cases, run checks, attach rubric scores, produce one results document."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .checks import CheckResult, run_checks
from .rubric import DimensionScore, Rubric, Scored, apply, default_rubric


@dataclass
class CaseResult:
    case_id: str
    title: str
    checks: List[CheckResult] = field(default_factory=list)
    scored: Optional[Scored] = None
    output_chars: int = 0

    @property
    def checks_passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> List[CheckResult]:
        return [check for check in self.checks if not check.passed]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "output_chars": self.output_chars,
            "checks_passed": self.checks_passed,
            "checks": [check.as_dict() for check in self.checks],
            "rubric": self.scored.as_dict() if self.scored else None,
        }


@dataclass
class RunResult:
    caseset: str
    rubric: Rubric
    results: List[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def clean(self) -> int:
        return sum(1 for r in self.results if r.checks_passed)

    @property
    def scored(self) -> List[CaseResult]:
        return [r for r in self.results if r.scored is not None]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "caseset": self.caseset,
            "cases": self.total,
            "checks_passed": self.clean,
            "checks_failed": self.total - self.clean,
            "rubric": self.rubric.as_dict(),
            "results": [r.as_dict() for r in self.results],
        }


def load_cases(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(cases, list) or not cases:
        raise ValueError("{} contains no cases".format(path))
    for case in cases:
        if not isinstance(case, dict) or not case.get("id"):
            raise ValueError("every case needs an 'id'")
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ids in {}".format(path))
    return cases


def load_outputs(directory: Path) -> Dict[str, str]:
    """Read ``<case id>.<ext>`` files, ignoring anything else in the directory."""
    found: Dict[str, str] = {}
    for path in sorted(Path(directory).glob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".md", ".txt", ".json"):
            continue
        found[path.stem] = path.read_text(encoding="utf-8")
    return found


def load_scores(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if path is None:
        return {}
    if not path.exists():
        raise ValueError("scores file not found: {}".format(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _scores_for(entry: Dict[str, Any]) -> List[DimensionScore]:
    out: List[DimensionScore] = []
    for key, value in (entry or {}).items():
        if isinstance(value, dict):
            out.append(
                DimensionScore(
                    key=key,
                    score=int(value.get("score", 0)),
                    rationale=str(value.get("rationale") or ""),
                )
            )
    return out


def run(
    cases_path: Path,
    outputs_dir: Path,
    scores_path: Optional[Path] = None,
    rubric: Optional[Rubric] = None,
) -> RunResult:
    """Evaluate every output that exists. A case with no output is an error.

    A silent skip would make a partial run look complete, which is the failure
    mode that matters here: an evaluator who reports "4 of 12 passed" without
    saying six outputs were missing has misled the reader.
    """
    cases = load_cases(cases_path)
    outputs = load_outputs(outputs_dir)
    scores = load_scores(scores_path)
    chosen = rubric or default_rubric()

    missing = [case["id"] for case in cases if case["id"] not in outputs]
    if missing:
        raise ValueError(
            "no output for {} case(s): {}. Every case in the set needs one.".format(
                len(missing), ", ".join(missing)
            )
        )

    result = RunResult(caseset=str(cases_path), rubric=chosen)
    for case in cases:
        text = outputs[case["id"]]
        case_result = CaseResult(
            case_id=case["id"],
            title=str(case.get("title") or case["id"]),
            checks=run_checks(text, case),
            output_chars=len(text),
        )
        if case["id"] in scores:
            case_result.scored = apply(chosen, _scores_for(scores[case["id"]]))
        result.results.append(case_result)
    return result

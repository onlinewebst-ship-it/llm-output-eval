"""Render a run as Markdown for a human reader, or JSON for a machine."""

from __future__ import annotations

import json
from typing import List

from .checks import CheckResult
from .runner import CaseResult, RunResult


def _tick(passed: bool) -> str:
    return "pass" if passed else "**FAIL**"


def render_markdown(run: RunResult, note: str = "") -> str:
    lines: List[str] = []
    lines.append("# LLM output evaluation")
    lines.append("")
    lines.append("Rubric: **{}**  ".format(run.rubric.name))
    lines.append(
        "Cases: **{}**  |  deterministic checks clean: **{}**  |  checks failing: **{}**".format(
            run.total, run.clean, run.total - run.clean
        )
    )
    if note:
        lines.append("")
        lines.append(note)
    lines.append("")

    lines.append("## Per case")
    lines.append("")
    lines.append("| Case | Title | Checks | Rubric | Verdict |")
    lines.append("| --- | --- | --- | --- | --- |")
    for result in run.results:
        rubric_cell = "not scored"
        verdict = "-"
        if result.scored is not None:
            rubric_cell = "{}/100".format(result.scored.total)
            verdict = result.scored.verdict
        lines.append(
            "| `{}` | {} | {} of {} | {} | {} |".format(
                result.case_id,
                result.title,
                sum(1 for c in result.checks if c.passed),
                len(result.checks),
                rubric_cell,
                verdict,
            )
        )
    lines.append("")

    failures = [r for r in run.results if not r.checks_passed]
    if failures:
        lines.append("## Failed checks")
        lines.append("")
        for result in failures:
            lines.append("### `{}` {}".format(result.case_id, result.title))
            for check in result.failed_checks:
                lines.append("")
                lines.append("- **{}**: {}".format(check.name, check.detail))
                for item in check.evidence[:6]:
                    lines.append("  - `{}`".format(item))
            lines.append("")
    else:
        lines.append("## Failed checks")
        lines.append("")
        lines.append("None. Every deterministic check passed on every case.")
        lines.append("")

    scored = run.scored
    if scored:
        lines.append("## Rubric detail")
        lines.append("")
        for result in scored:
            lines.append("### `{}` {} - {}/100 ({})".format(
                result.case_id, result.title, result.scored.total, result.scored.verdict
            ))
            lines.append("")
            lines.append("| Dimension | Score | Weight | Awarded | Rationale |")
            lines.append("| --- | --- | --- | --- | --- |")
            for key, data in result.scored.per_dimension.items():
                lines.append(
                    "| {} | {}/5 | {} | {} | {} |".format(
                        key, data["score"], data["weight"], data["awarded"], data["rationale"]
                    )
                )
            lines.append("")
            if result.scored.problems:
                lines.append("Problems: {}".format("; ".join(result.scored.problems)))
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(run: RunResult) -> str:
    return json.dumps(run.as_dict(), indent=2, ensure_ascii=False)

"""Rubric scoring: dimensions, anchors, and the weighted verdict.

The design goal is that two reviewers reading the same anchors reach the same
number, or can point at the anchor they disagree about. That is why every
dimension has five written anchors rather than a bare 1-5 scale, and why the
total is a fixed arithmetic function rather than a judgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class Dimension:
    """One axis of quality, with anchors that describe each score."""

    key: str
    name: str
    weight: int
    question: str
    anchors: Dict[int, str]

    def validate(self) -> List[str]:
        problems: List[str] = []
        if self.weight <= 0:
            problems.append("dimension {!r} has non-positive weight".format(self.key))
        if set(self.anchors) != {1, 2, 3, 4, 5}:
            problems.append("dimension {!r} must define anchors 1-5".format(self.key))
        return problems

    def as_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "weight": self.weight,
            "question": self.question,
            "anchors": {str(k): v for k, v in sorted(self.anchors.items())},
        }


@dataclass(frozen=True)
class Rubric:
    """A weighted set of dimensions plus the thresholds for a verdict."""

    name: str
    dimensions: Sequence[Dimension]
    pass_mark: int = 70
    revise_mark: int = 50

    def validate(self) -> List[str]:
        problems: List[str] = []
        if not self.dimensions:
            problems.append("rubric has no dimensions")
        keys = [d.key for d in self.dimensions]
        if len(keys) != len(set(keys)):
            problems.append("duplicate dimension keys")
        for dimension in self.dimensions:
            problems.extend(dimension.validate())
        if not (0 < self.revise_mark <= self.pass_mark <= 100):
            problems.append("thresholds must satisfy 0 < revise <= pass <= 100")
        return problems

    @property
    def total_weight(self) -> int:
        return sum(d.weight for d in self.dimensions)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pass_mark": self.pass_mark,
            "revise_mark": self.revise_mark,
            "total_weight": self.total_weight,
            "dimensions": [d.as_dict() for d in self.dimensions],
        }


@dataclass
class DimensionScore:
    key: str
    score: int
    rationale: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "score": self.score, "rationale": self.rationale}


@dataclass
class Scored:
    """The result of applying a rubric to one output."""

    total: int
    verdict: str
    per_dimension: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    problems: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "verdict": self.verdict,
            "per_dimension": self.per_dimension,
            "problems": list(self.problems),
        }


def verdict_for(total: int, rubric: Rubric) -> str:
    if total >= rubric.pass_mark:
        return "pass"
    if total >= rubric.revise_mark:
        return "revise"
    return "fail"


def apply(rubric: Rubric, scores: Sequence[DimensionScore]) -> Scored:
    """Compute the weighted total.

    A missing dimension scores zero and is recorded as a problem rather than
    being silently treated as an average: an unscored dimension is missing
    judgement, not neutral judgement.
    """
    problems = rubric.validate()
    by_key = {score.key: score for score in scores}
    per: Dict[str, Dict[str, Any]] = {}
    total = 0.0

    for dimension in rubric.dimensions:
        given = by_key.get(dimension.key)
        if given is None:
            problems.append("dimension {!r} was not scored".format(dimension.key))
            per[dimension.key] = {
                "score": 0,
                "weight": dimension.weight,
                "awarded": 0,
                "rationale": "not scored",
            }
            continue
        if given.score not in (1, 2, 3, 4, 5):
            problems.append(
                "dimension {!r} scored {!r}, must be 1-5".format(dimension.key, given.score)
            )
            continue
        # 1 -> 20%, 5 -> 100% of the dimension's weight.
        fraction = given.score / 5.0
        awarded = dimension.weight * fraction
        total += awarded
        per[dimension.key] = {
            "score": given.score,
            "weight": dimension.weight,
            "awarded": round(awarded, 2),
            "rationale": given.rationale,
        }

    normalised = 0
    if rubric.total_weight:
        normalised = int(round(100.0 * total / rubric.total_weight))
    return Scored(
        total=normalised,
        verdict=verdict_for(normalised, rubric),
        per_dimension=per,
        problems=problems,
    )


def default_rubric() -> Rubric:
    """The rubric used for UK business writing tasks.

    Weights sum to 100 so the total reads as a percentage without normalisation
    surprises. Accuracy carries the most weight because a fluent answer that is
    wrong is worse than a clumsy one that is right.
    """
    return Rubric(
        name="UK business writing, LLM output",
        pass_mark=70,
        revise_mark=50,
        dimensions=(
            Dimension(
                key="accuracy",
                name="Factual accuracy",
                weight=30,
                question="Is every claim, figure and name traceable to the source?",
                anchors={
                    1: "Contradicts the source or invents key facts",
                    2: "One material error that a reader would act on",
                    3: "Accurate but adds a detail the source does not support",
                    4: "Accurate; every claim traceable",
                    5: "Accurate and correctly qualified where the source is uncertain",
                },
            ),
            Dimension(
                key="adherence",
                name="Instruction adherence",
                weight=25,
                question="Does it do what the brief asked, in the format asked for?",
                anchors={
                    1: "Ignores the task or the format",
                    2: "Misses a major instruction or the format",
                    3: "Follows the brief but drifts in part",
                    4: "Follows every instruction",
                    5: "Follows every instruction and handles the edge case the brief implied",
                },
            ),
            Dimension(
                key="style",
                name="House style and voice",
                weight=20,
                question="Would this pass an editor without a rewrite?",
                anchors={
                    1: "Machine cadence, banned phrasing, dashes",
                    2: "Several tells; reads as generated",
                    3: "Clean but flat",
                    4: "Reads as written by the named author",
                    5: "Reads as written by the named author and is better than the source",
                },
            ),
            Dimension(
                key="concision",
                name="Concision",
                weight=15,
                question="Is anything here that the reader does not need?",
                anchors={
                    1: "Padding dominates the answer",
                    2: "Noticeably padded",
                    3: "Acceptable length, some filler",
                    4: "Tight; nothing extraneous",
                    5: "Tighter than the word limit required, with nothing lost",
                },
            ),
            Dimension(
                key="safety",
                name="Safety and honesty",
                weight=10,
                question="Does it avoid overclaiming, and flag what it cannot know?",
                anchors={
                    1: "Confidently asserts something it cannot know",
                    2: "Overclaims in a way that could mislead",
                    3: "Mostly careful, one unqualified claim",
                    4: "Careful and appropriately hedged",
                    5: "Careful, and names the limit of its own answer",
                },
            ),
        ),
    )

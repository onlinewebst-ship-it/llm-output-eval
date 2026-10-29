"""Deterministic checks for one model output against one evaluation case.

Every check is a pure function of (output text, case rules). Nothing here calls
a model, the network or the clock, so a run is reproducible and a disagreement
about a score can be settled by re-running the same text.

Checks answer only the questions that can be settled mechanically. Judgement
questions - is the tone right, is the summary actually useful - belong to the
rubric dimensions in :mod:`evalkit.rubric`, scored by a person or a judge model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

# Phrases that mark text as machine-written filler rather than communication.
# The list is deliberately short and defensible: every entry is a phrase a UK
# editor would strike. Adding to it is a style decision for the user, not a
# universal rule.
BANNED_PHRASES: Sequence[str] = (
    "delve into",
    "in today's fast-paced",
    "it's important to note",
    "it is important to note",
    "navigate the landscape",
    "unlock the power",
    "game-changer",
    "game changer",
    "seamless integration",
    "revolutionise",
    "revolutionize",
    "leverage the power",
    "in the ever-evolving",
    "tapestry of",
    "testament to",
)

# House style: no em dash or en dash. They survive LLM output by default and
# are the single most reliable tell in otherwise clean copy.
DASH_CHARS = ("\u2014", "\u2013")

PLACEHOLDER_RE = re.compile(r"(\[[A-Za-z][^\]]{0,40}\]|\bTBD\b|\bTODO\b|lorem ipsum)", re.I)
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]")
NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")


@dataclass
class CheckResult:
    """One mechanical check and its outcome."""

    name: str
    passed: bool
    detail: str = ""
    evidence: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "evidence": list(self.evidence),
        }


def words(text: str) -> List[str]:
    return WORD_RE.findall(text or "")


def _find_phrases(text: str, phrases: Iterable[str]) -> List[str]:
    haystack = " ".join(str(text or "").lower().split())
    return [p for p in phrases if p and p.lower() in haystack]


def check_banned_phrases(text: str, phrases: Sequence[str] = BANNED_PHRASES) -> CheckResult:
    hits = _find_phrases(text, phrases)
    return CheckResult(
        "banned_phrases",
        not hits,
        "no machine-filler phrasing" if not hits else "banned phrasing present",
        hits,
    )


def check_dashes(text: str) -> CheckResult:
    hits = [char for char in DASH_CHARS if char in (text or "")]
    return CheckResult(
        "no_em_or_en_dash",
        not hits,
        "no dashes" if not hits else "contains em/en dash",
        ["U+{:04X}".format(ord(c)) for c in hits],
    )


def check_length(text: str, max_words: Optional[int] = None, min_words: Optional[int] = None) -> CheckResult:
    count = len(words(text))
    problems: List[str] = []
    if max_words is not None and count > max_words:
        problems.append("{} words, limit is {}".format(count, max_words))
    if min_words is not None and count < min_words:
        problems.append("{} words, minimum is {}".format(count, min_words))
    return CheckResult(
        "word_count",
        not problems,
        "; ".join(problems) if problems else "{} words".format(count),
    )


def check_must_include(text: str, required: Sequence[str]) -> CheckResult:
    missing = [phrase for phrase in required if not _contains_phrase(text, phrase)]
    return CheckResult(
        "required_content",
        not missing,
        "all required content present" if not missing else "missing required content",
        missing,
    )


def check_must_not_include(text: str, forbidden: Sequence[str]) -> CheckResult:
    present = [phrase for phrase in forbidden if _contains_phrase(text, phrase)]
    return CheckResult(
        "forbidden_content",
        not present,
        "no forbidden content" if not present else "forbidden content present",
        present,
    )


def check_no_invented_numbers(text: str, source_facts: Sequence[str], allowed: Sequence[str] = ()) -> CheckResult:
    """Numbers in the output must appear in the supplied source material.

    This is the mechanical guard against a model inventing a statistic, a date
    or a figure. It cannot prove the number is used correctly, only that it was
    not made up.
    """
    source_blob = " ".join(list(source_facts) + list(allowed)).lower()
    invented: List[str] = []
    for match in NUMBER_RE.findall(text or ""):
        cleaned = match.replace(",", "")
        if cleaned not in source_blob.replace(",", ""):
            invented.append(match)
    return CheckResult(
        "no_invented_numbers",
        not invented,
        "every figure traces to the source" if not invented else "figures not present in the source",
        sorted(set(invented)),
    )


def check_no_placeholders(text: str) -> CheckResult:
    hits = PLACEHOLDER_RE.findall(text or "")
    return CheckResult(
        "no_placeholders",
        not hits,
        "no placeholders" if not hits else "unfinished placeholder text",
        [str(h) for h in hits[:5]],
    )


def check_sentence_length(text: str, max_words: int = 35) -> CheckResult:
    over: List[str] = []
    for sentence in SENTENCE_RE.findall(text or ""):
        count = len(words(sentence))
        if count > max_words:
            over.append("{} words: {}".format(count, " ".join(sentence.split())[:60]))
    return CheckResult(
        "sentence_length",
        not over,
        "all sentences within {} words".format(max_words) if not over else "long sentences",
        over,
    )


def _has_key(payload: Any, key: str) -> bool:
    """True when ``key`` appears anywhere in the JSON structure.

    Action lists are a normal shape (``{"actions": [{...}]}``), so a required
    key must be found nested as well as at the top level. Looking only at the
    outermost object would reject correct output.
    """
    if isinstance(payload, dict):
        if key in payload:
            return True
        return any(_has_key(value, key) for value in payload.values())
    if isinstance(payload, list):
        return any(_has_key(value, key) for value in payload)
    return False


def check_json_shape(text: str, required_keys: Sequence[str] = ()) -> CheckResult:
    import json

    try:
        payload = json.loads(text or "")
    except ValueError as exc:
        return CheckResult("json_valid", False, "not valid JSON: {}".format(exc))
    if required_keys:
        if not isinstance(payload, (dict, list)):
            return CheckResult("json_valid", False, "JSON is not an object or array")
        missing = [k for k in required_keys if not _has_key(payload, k)]
        return CheckResult(
            "json_valid",
            not missing,
            "valid JSON" if not missing else "missing keys: {}".format(", ".join(missing)),
        )
    return CheckResult("json_valid", True, "valid JSON")


def _contains_phrase(haystack: str, phrase: str) -> bool:
    haystack_l = " ".join(str(haystack or "").lower().split())
    phrase_l = " ".join(str(phrase or "").lower().split())
    if not phrase_l:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(phrase_l) + r"(?![a-z0-9])"
    return re.search(pattern, haystack_l) is not None


def run_checks(text: str, case: Dict[str, Any]) -> List[CheckResult]:
    """Run every check the case asks for, in a fixed order."""
    results: List[CheckResult] = [
        check_banned_phrases(text, case.get("banned_phrases", BANNED_PHRASES)),
        check_dashes(text),
        check_length(text, case.get("max_words"), case.get("min_words")),
        check_must_include(text, case.get("must_include", ())),
        check_must_not_include(text, case.get("must_not_include", ())),
        check_no_placeholders(text),
        check_sentence_length(text, int(case.get("max_sentence_words", 35))),
    ]
    if case.get("source_facts") is not None:
        results.append(
            check_no_invented_numbers(
                text,
                case.get("source_facts", ()),
                case.get("allowed_numbers", ()),
            )
        )
    if case.get("expect_json") or case.get("required_json_keys"):
        results.append(
            check_json_shape(text, case.get("required_json_keys", ()))
        )
    return results

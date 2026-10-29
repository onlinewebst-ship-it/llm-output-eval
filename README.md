# llm-output-eval

A small, dependency-free harness for scoring LLM output against an explicit
rubric and a set of mechanical checks. Python 3.9+, standard library only.

The point is not to produce a number. The point is that every number can be
explained: which check failed, on what evidence, and which anchor of which
dimension a human applied.

```sh
python3 -m evalkit run --cases cases/uk-writing.json --outputs outputs \
    --scores scores.json --markdown RESULTS.md
```

```
12 cases, 8 clean, 4 with failing checks
```

## Why this exists

"Does the model do a good job?" is answered in most teams by reading a few
outputs and forming an impression. That impression is unrepeatable, and it
cannot survive a disagreement.

This tool splits the question in two:

- **Mechanical checks** settle everything that can be settled by inspecting text:
  banned phrasing, em dashes, word limits, required content, forbidden claims,
  invented numbers, unfinished placeholders, JSON shape. These are pure
  functions of the output and the case, so two runs of the same text on
  different days give the same result.
- **A rubric** settles everything that needs judgement: accuracy, instruction
  adherence, house style, concision, and safety. Five dimensions, weighted to
  100, each with written anchors at 1, 2, 3, 4 and 5 so a score can be argued
  from the anchor rather than from taste.

The harness never generates the text it grades. That is deliberate: an evaluator
that writes the answer and then awards itself the mark is measuring nothing.

## What is in the box

| Path | What it is |
| --- | --- |
| `evalkit/checks.py` | Nine deterministic checks, each returning pass/fail plus evidence |
| `evalkit/rubric.py` | Dimensions, anchors, weighted scoring, verdict thresholds |
| `evalkit/runner.py` | Case loading, output loading, one results object per case |
| `evalkit/report.py` | Markdown and JSON rendering |
| `cases/uk-writing.json` | Twelve UK business-writing cases with per-case rules |
| `outputs/` | The twelve outputs being evaluated |
| `scores.json` | Rubric scores and rationales for those twelve |
| `RESULTS.md` | Generated report |
| `tests/` | 32 tests, all offline |

## The rubric

| Dimension | Weight | The question it asks |
| --- | --- | --- |
| Accuracy | 30 | Is every claim, figure and name traceable to the source? |
| Instruction adherence | 25 | Does it do what the brief asked, in the format asked for? |
| House style and voice | 20 | Would this pass an editor without a rewrite? |
| Concision | 15 | Is anything here that the reader does not need? |
| Safety and honesty | 10 | Does it avoid overclaiming and flag what it cannot know? |

A 1 anchor earns 20% of the dimension's weight, a 5 earns 100%. Accuracy carries
the most weight because a fluent answer that is wrong is worse than a clumsy one
that is right. `python3 -m evalkit rubric` prints the full anchors as JSON.

## The checks

| Check | Catches |
| --- | --- |
| `banned_phrases` | Machine filler: "delve into", "it is important to note", "game-changer" |
| `no_em_or_en_dash` | The most reliable tell in otherwise clean copy |
| `word_count` | Over-long or clipped answers |
| `required_content` | A missing date, figure or obligation the brief demanded |
| `forbidden_content` | Claims the brief ruled out |
| `no_invented_numbers` | A figure that does not appear in the supplied source |
| `no_placeholders` | `[insert colour]`, `TBD`, lorem ipsum shipped as finished copy |
| `sentence_length` | The 60-word sentence that hides a missing argument |
| `json_valid` | Invalid JSON, or a missing key anywhere in the structure |

## Results on the sample set

Twelve UK business-writing cases. Four outputs carry a seeded defect, and each
one is caught by the check designed for it:

| Case | Seeded defect | Caught by |
| --- | --- | --- |
| `c03` | Invents a 30-day refund window; the regulations give 14 | `no_invented_numbers` |
| `c06` | Em dash and "it is important to note" | `no_em_or_en_dash`, `banned_phrases` |
| `c09` | Ships `[insert colour]` as finished copy | `no_placeholders` |
| `c12` | Invents a fundraising total, and a ticket price, for a charity post | `no_invented_numbers` |

Rubric results separate from that: `c03` scores 53 (revise) and `c12` scores 55
(revise), while the two strongest outputs, the overdue-invoice chase and the
IR35 explanation, score 92 and 90.

## What this does and does not establish

Stated plainly, because an evaluation that overstates itself is worthless:

- **The outputs were written by an AI assistant, and scored by the same
  assistant.** That is a single rater with a shared blind spot. It demonstrates
  the method and the tooling; it is not evidence that any model is good or bad.
- **Twelve cases is a demonstration, not a benchmark.** It is enough to show the
  checks fire on the defects they target. It is nowhere near enough to rank
  models, and no such claim is made.
- **The rubric weights are an opinion**, chosen for UK business writing. Change
  them for your context; the arithmetic will follow.
- **`no_invented_numbers` proves only that a figure was not made up.** It cannot
  tell whether a real figure was used correctly.
- **Passing every check is not a pass.** A text can clear all nine mechanical
  checks and still be the wrong answer. That is what the rubric is for.

## Design decisions worth knowing

- **Missing outputs are an error, not a skip.** An evaluator who reports "8 of
  12 passed" without mentioning that four outputs were missing has misled the
  reader. The runner refuses to run on a partial set.
- **An unscored dimension scores zero and raises a problem.** Missing judgement
  is not neutral judgement.
- **Exit code 2 when any check fails**, so the tool can gate a CI step.
- **Required JSON keys are searched at any depth**, because `{"actions": [{...}]}`
  is a normal shape and a top-level-only check would reject correct output.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

32 tests, offline, no fixtures beyond the case set itself. They cover each
check, the rubric arithmetic (including the 20/100 floor and the missing-dimension
rule), the loader's refusal to skip, and an end-to-end run that asserts the four
seeded defects are the only failures.

## Licence

MIT. See `LICENSE`.

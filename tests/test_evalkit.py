"""Tests for the checks, the rubric arithmetic and the runner."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evalkit import checks, rubric
from evalkit.runner import load_cases, load_outputs, run


class BannedPhraseTests(unittest.TestCase):
    def test_clean_text_passes(self):
        result = checks.check_banned_phrases("We will empty your bin every two weeks.")
        self.assertTrue(result.passed)

    def test_phrase_detected_case_insensitively(self):
        result = checks.check_banned_phrases("It's Important To Note that the bin is late.")
        self.assertFalse(result.passed)
        self.assertIn("it's important to note", result.evidence)

    def test_word_boundary_is_respected(self):
        # "ai" must not match inside "said" - the same trap as the job-search tool.
        self.assertFalse(checks._contains_phrase("she said nothing", "ai"))
        self.assertTrue(checks._contains_phrase("we use ai daily", "ai"))
        self.assertFalse(checks._contains_phrase("she said something", "said something else"))


class DashTests(unittest.TestCase):
    def test_em_dash_fails(self):
        result = checks.check_dashes("Late \u2014 and late again.")
        self.assertFalse(result.passed)
        self.assertIn("U+2014", result.evidence)

    def test_hyphen_is_fine(self):
        self.assertTrue(checks.check_dashes("a part-time role").passed)


class LengthTests(unittest.TestCase):
    def test_over_limit_fails(self):
        result = checks.check_length("word " * 20, max_words=10)
        self.assertFalse(result.passed)
        self.assertIn("20 words", result.detail)

    def test_under_minimum_fails(self):
        self.assertFalse(checks.check_length("two words", min_words=5).passed)

    def test_within_bounds_passes(self):
        self.assertTrue(checks.check_length("three whole words", min_words=2, max_words=5).passed)


class ContentTests(unittest.TestCase):
    def test_required_content_missing(self):
        result = checks.check_must_include("The bin will be emptied weekly.", ["3 November"])
        self.assertFalse(result.passed)
        self.assertEqual(result.evidence, ["3 November"])

    def test_required_content_present(self):
        self.assertTrue(checks.check_must_include("From 3 November 2026 it changes.", ["3 November"]).passed)

    def test_forbidden_content(self):
        self.assertFalse(checks.check_must_not_include("A young and energetic team.", ["young and energetic"]).passed)


class InventedNumberTests(unittest.TestCase):
    def test_number_in_source_passes(self):
        result = checks.check_no_invented_numbers(
            "The rate rises 4.2 per cent from 1 January 2027.",
            ["4.2 per cent", "1 January 2027"],
        )
        self.assertTrue(result.passed)

    def test_number_not_in_source_fails(self):
        result = checks.check_no_invented_numbers("You have 30 days to return it.", ["14 days"])
        self.assertFalse(result.passed)
        self.assertEqual(result.evidence, ["30"])

    def test_thousands_separator_is_normalised(self):
        result = checks.check_no_invented_numbers("Total raised: £12,480.", ["12,480"])
        self.assertTrue(result.passed)

    def test_rounded_variant_is_still_caught(self):
        result = checks.check_no_invented_numbers("Total raised: £12,480.", ["£12,000"])
        self.assertFalse(result.passed)


class PlaceholderAndShapeTests(unittest.TestCase):
    def test_placeholder_caught(self):
        self.assertFalse(checks.check_no_placeholders("Finish: [insert colour].").passed)

    def test_tbd_caught(self):
        self.assertFalse(checks.check_no_placeholders("Date: TBD").passed)

    def test_invalid_json_caught(self):
        self.assertFalse(checks.check_json_shape("{not json").passed)

    def test_nested_required_keys_are_found(self):
        payload = json.dumps({"actions": [{"owner": "Sam", "action": "Chase", "due": "Friday"}]})
        self.assertTrue(checks.check_json_shape(payload, ["owner", "action", "due"]).passed)

    def test_missing_nested_key_caught(self):
        payload = json.dumps({"actions": [{"owner": "Sam"}]})
        result = checks.check_json_shape(payload, ["owner", "due"])
        self.assertFalse(result.passed)
        self.assertIn("due", result.detail)

    def test_long_sentence_caught(self):
        sentence = " ".join(["word"] * 40) + "."
        self.assertFalse(checks.check_sentence_length(sentence, 35).passed)


class RubricArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.rubric = rubric.default_rubric()

    def test_default_rubric_is_valid_and_sums_to_100(self):
        self.assertEqual(self.rubric.validate(), [])
        self.assertEqual(self.rubric.total_weight, 100)

    def test_perfect_scores_give_100(self):
        scores = [rubric.DimensionScore(d.key, 5) for d in self.rubric.dimensions]
        self.assertEqual(rubric.apply(self.rubric, scores).total, 100)

    def test_lowest_scores_give_20(self):
        # A 1 anchor is 20% of the weight, so every dimension at 1 is 20/100.
        scores = [rubric.DimensionScore(d.key, 1) for d in self.rubric.dimensions]
        self.assertEqual(rubric.apply(self.rubric, scores).total, 20)

    def test_missing_dimension_scores_zero_and_warns(self):
        scores = [rubric.DimensionScore(d.key, 5) for d in self.rubric.dimensions if d.key != "accuracy"]
        result = rubric.apply(self.rubric, scores)
        self.assertLess(result.total, 100)
        self.assertTrue(any("accuracy" in problem for problem in result.problems))

    def test_out_of_range_score_is_a_problem(self):
        scores = [rubric.DimensionScore(d.key, 5) for d in self.rubric.dimensions]
        scores[0] = rubric.DimensionScore(scores[0].key, 9)
        result = rubric.apply(self.rubric, scores)
        self.assertTrue(result.problems)

    def test_verdict_thresholds(self):
        self.assertEqual(rubric.verdict_for(70, self.rubric), "pass")
        self.assertEqual(rubric.verdict_for(69, self.rubric), "revise")
        self.assertEqual(rubric.verdict_for(49, self.rubric), "fail")

    def test_anchor_validation(self):
        bad = rubric.Dimension(key="x", name="X", weight=10, question="?", anchors={1: "a", 2: "b"})
        self.assertTrue(bad.validate())


class RunnerTests(unittest.TestCase):
    def _write(self, root, name, payload):
        path = Path(root) / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "cases.json", {"cases": [{"id": "a"}, {"id": "a"}]})
            with self.assertRaises(ValueError):
                load_cases(path)

    def test_missing_output_is_an_error_not_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = self._write(tmp, "cases.json", {"cases": [{"id": "c1", "title": "T"}]})
            outdir = Path(tmp) / "out"
            outdir.mkdir()
            with self.assertRaises(ValueError) as caught:
                run(cases, outdir)
            self.assertIn("c1", str(caught.exception))

    def test_outputs_loader_ignores_non_text_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "c1.md").write_text("hello", encoding="utf-8")
            (Path(tmp) / "notes.bin").write_bytes(b"\x00\x01")
            self.assertEqual(list(load_outputs(Path(tmp))), ["c1"])

    def test_end_to_end_on_the_repository_case_set(self):
        root = Path(__file__).resolve().parents[1]
        result = run(root / "cases" / "uk-writing.json", root / "outputs", root / "scores.json")
        self.assertEqual(result.total, 12)
        # The four seeded defects are the only cases with failing checks.
        failing = sorted(r.case_id for r in result.results if not r.checks_passed)
        self.assertEqual(failing, ["c03", "c06", "c09", "c12"])
        self.assertEqual(len(result.scored), 12)


if __name__ == "__main__":
    unittest.main()

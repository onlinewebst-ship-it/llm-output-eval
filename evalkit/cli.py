"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import render_json, render_markdown
from .rubric import default_rubric
from .runner import run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m evalkit",
        description=(
            "Score model outputs against an explicit rubric and a set of "
            "deterministic checks. Bring your own outputs: this tool does not "
            "generate them, so it cannot grade its own work."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("rubric", help="print the default rubric as JSON")

    run_parser = sub.add_parser("run", help="evaluate a directory of outputs")
    run_parser.add_argument("--cases", required=True, metavar="PATH", help="case set JSON")
    run_parser.add_argument("--outputs", required=True, metavar="DIR", help="directory of <case id>.md outputs")
    run_parser.add_argument("--scores", metavar="PATH", default=None, help="optional rubric scores JSON")
    run_parser.add_argument("--markdown", metavar="PATH", default=None, help="write a Markdown report")
    run_parser.add_argument("--json", metavar="PATH", default=None, help="write a JSON report")
    run_parser.add_argument("--note", metavar="TEXT", default="", help="note printed under the summary")

    args = parser.parse_args(argv)

    if args.command == "rubric":
        print(json.dumps(default_rubric().as_dict(), indent=2, ensure_ascii=False))
        return 0

    cases_path = Path(args.cases)
    for path, label in ((cases_path, "cases"), (Path(args.outputs), "outputs")):
        if not path.exists():
            print("error: {} path does not exist: {}".format(label, path), file=sys.stderr)
            return 1

    try:
        result = run(
            cases_path,
            Path(args.outputs),
            Path(args.scores) if args.scores else None,
        )
    except ValueError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1

    markdown = render_markdown(result, note=args.note)
    if args.markdown:
        Path(args.markdown).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json:
        Path(args.json).write_text(render_json(result), encoding="utf-8")

    print(
        "{} cases, {} clean, {} with failing checks".format(
            result.total, result.clean, result.total - result.clean
        ),
        file=sys.stderr,
    )
    # Non-zero exit when any deterministic check fails, so a pipeline can gate.
    return 0 if result.clean == result.total else 2


if __name__ == "__main__":
    raise SystemExit(main())

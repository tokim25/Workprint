from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import InvestigationEngine, InvestigationError
from .render import render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workprint",
        description="Build a Workprint investigation from normalized evidence JSON.",
    )
    parser.add_argument("input", type=Path, help="Path to investigation input JSON")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument("--output", type=Path, help="Write output to this path")
    parser.add_argument(
        "--session-gap",
        type=int,
        default=30,
        help="Maximum minutes between events in an inferred session (default: 30)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report = InvestigationEngine(args.session_gap).investigate(payload)
        output = (
            json.dumps(report, indent=2, ensure_ascii=False)
            if args.format == "json"
            else render_markdown(report)
        )
        if args.output:
            args.output.write_text(output + ("\n" if not output.endswith("\n") else ""), encoding="utf-8")
        else:
            print(output)
        return 0
    except (OSError, json.JSONDecodeError, InvestigationError) as exc:
        print(f"workprint: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters import ClaudeAdapter, ClaudeAdapterError
from .engine import InvestigationEngine, InvestigationError
from .render import render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workprint",
        description="Ingest project evidence and build Workprint investigations.",
    )
    subparsers = parser.add_subparsers(dest="command")

    investigate = subparsers.add_parser(
        "investigate",
        help="Build an investigation from normalized evidence JSON.",
    )
    _add_investigation_arguments(investigate)

    ingest = subparsers.add_parser(
        "ingest",
        help="Convert a supported source export into canonical observations.",
    )
    ingest_subparsers = ingest.add_subparsers(dest="adapter", required=True)
    claude = ingest_subparsers.add_parser(
        "claude", help="Ingest a Claude conversation export."
    )
    claude.add_argument("input", type=Path, help="Path to Claude export JSON")
    claude.add_argument("--output", type=Path, help="Write observations to this file")

    return parser


def _add_investigation_arguments(parser: argparse.ArgumentParser) -> None:
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


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)

    # Preserve the original v0.1 command shape:
    #   workprint input.json --output report.md
    # New commands use explicit subcommands.
    if args_list and args_list[0] not in {"investigate", "ingest", "-h", "--help"}:
        args_list.insert(0, "investigate")

    args = build_parser().parse_args(args_list)
    try:
        if args.command == "ingest" and args.adapter == "claude":
            observations = ClaudeAdapter().ingest(args.input)
            output = json.dumps(
                [observation.to_dict() for observation in observations],
                indent=2,
                ensure_ascii=False,
            )
            _write_or_print(output, args.output)
            return 0

        if args.command == "investigate":
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            report = InvestigationEngine(args.session_gap).investigate(payload)
            output = (
                json.dumps(report, indent=2, ensure_ascii=False)
                if args.format == "json"
                else render_markdown(report)
            )
            _write_or_print(output, args.output)
            return 0

        build_parser().print_help()
        return 2
    except (
        OSError,
        json.JSONDecodeError,
        InvestigationError,
        ClaudeAdapterError,
    ) as exc:
        print(f"workprint: {exc}", file=sys.stderr)
        return 2


def _write_or_print(output: str, destination: Path | None) -> None:
    if destination:
        destination.write_text(
            output + ("\n" if not output.endswith("\n") else ""),
            encoding="utf-8",
        )
    else:
        print(output)


if __name__ == "__main__":
    raise SystemExit(main())

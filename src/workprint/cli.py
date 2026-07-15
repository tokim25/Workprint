from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from workprint.adapters import available_adapters, get_adapter
from workprint.discovery import discover_project, render_discovery
from workprint.engine import build_investigation
from workprint.extractor import extract_observations
from workprint.guided import GuidedOptions, run_guided
from workprint.multisource import load_observations, parse_evidence_spec
from workprint.reports import render_markdown


def _write(path: str | None, content: str) -> None:
    if path:
        Path(path).write_text(content, encoding="utf-8")
    else:
        print(content)


def _read_source(source: str, path: str):
    adapter = get_adapter(source)
    records = adapter.read(path)
    return extract_observations(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workprint",
        description="Reconstruct how work gets made from evidence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser(
        "import",
        help="Normalize source evidence into observations.",
    )
    import_parser.add_argument("source", choices=available_adapters())
    import_parser.add_argument("input")
    import_parser.add_argument("--output")

    investigate_parser = subparsers.add_parser(
        "investigate",
        help="Create an investigation report from source evidence.",
    )
    investigate_parser.add_argument("source", choices=available_adapters())
    investigate_parser.add_argument("input")
    investigate_parser.add_argument("--project", required=True)
    investigate_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    investigate_parser.add_argument("--output")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate that a supported export can be read.",
    )
    validate_parser.add_argument("source", choices=available_adapters())
    validate_parser.add_argument("input")

    guide_parser = subparsers.add_parser(
        "guide",
        help="Start a guided investigation workflow.",
    )
    guide_parser.add_argument("--path", help="Project folder to scan.")
    guide_parser.add_argument(
        "--include",
        help=(
            "Evidence selection, for example all, 1,3, chatgpt, "
            "or -google-docs."
        ),
    )
    guide_parser.add_argument("--project", help="Project name for reports.")
    guide_parser.add_argument(
        "--output-dir",
        help="Output directory for default report paths.",
    )
    guide_parser.add_argument("--markdown", help="Markdown report path.")
    guide_parser.add_argument("--json", help="JSON report path.")
    guide_parser.add_argument(
        "--yes",
        action="store_true",
        help="Accept defaults, final confirmation, and overwrites.",
    )

    discover_parser = subparsers.add_parser(
        "discover",
        help="Preview supported evidence in a project directory.",
    )
    discover_parser.add_argument("path", nargs="?", default=".")

    multi_parser = subparsers.add_parser(
        "investigate-multi",
        help="Create one investigation from multiple evidence inputs.",
    )
    multi_parser.add_argument(
        "--evidence",
        action="append",
        required=True,
        metavar="SOURCE=PATH",
        help=(
            "Repeat for each source, for example "
            "--evidence chatgpt=chatgpt.json --evidence claude=claude.json"
        ),
    )
    multi_parser.add_argument("--project", required=True)
    multi_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
    )
    multi_parser.add_argument("--output")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "guide":
        options = GuidedOptions(
            path=args.path,
            include=args.include,
            project=args.project,
            output_dir=args.output_dir,
            markdown=args.markdown,
            json=args.json,
            yes=args.yes,
        )
        return run_guided(options=options)

    if args.command == "discover":
        try:
            discovery = discover_project(args.path)
        except ValueError as exc:
            parser.error(str(exc))
        print(render_discovery(discovery))
        return 0

    if args.command == "investigate-multi":
        try:
            evidence_inputs = [parse_evidence_spec(spec) for spec in args.evidence]
            observations = load_observations(evidence_inputs)
        except ValueError as exc:
            parser.error(str(exc))

        investigation = build_investigation(
            project=args.project,
            source_files=[item.path for item in evidence_inputs],
            observations=observations,
        )
        if args.format == "json":
            output = json.dumps(
                investigation.to_dict(),
                indent=2,
                ensure_ascii=False,
            ) + "\n"
        else:
            output = render_markdown(investigation)

        _write(args.output, output)
        return 0

    try:
        observations = _read_source(args.source, args.input)
    except ValueError as exc:
        parser.error(str(exc))

    if args.command == "validate":
        print(
            json.dumps(
                {
                    "valid": True,
                    "source": args.source,
                    "observations": len(observations),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "import":
        payload = json.dumps(
            [item.to_dict() for item in observations],
            indent=2,
            ensure_ascii=False,
        )
        _write(args.output, payload + "\n")
        return 0

    investigation = build_investigation(
        project=args.project,
        source_files=[args.input],
        observations=observations,
    )
    if args.format == "json":
        output = json.dumps(
            investigation.to_dict(),
            indent=2,
            ensure_ascii=False,
        ) + "\n"
    else:
        output = render_markdown(investigation)

    _write(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

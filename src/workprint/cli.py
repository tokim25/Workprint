from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from workprint.adapters import available_adapters, get_adapter
from workprint.engine import build_investigation
from workprint.extractor import extract_observations
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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

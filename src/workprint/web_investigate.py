from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from workprint.ai_fluency import build_playbook_worksheet_markdown
from workprint.discovery import discover_project
from workprint.engine import build_investigation
from workprint.guided import evidence_files_from_discovery, select_evidence_files
from workprint.multisource import EvidenceInput, load_observations
from workprint.reports import render_json_dict, render_markdown


MAX_PATH_LENGTH = 4096
DESKTOP_CHAT_DEEP_PARSE_ENV = "WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE"


@dataclass(frozen=True)
class WebInvestigateError(Exception):
    code: str
    message: str


def build_web_investigation(
    project_path: str,
    *,
    include: str | None = None,
    project_name: str | None = None,
    include_desktop_chat_deep_parse: bool = False,
) -> dict[str, Any]:
    """Run a full Workprint investigation and return both report formats.

    Unlike mcp_server.py's investigate_project, this is for a one-time
    file download, not a conversational tool result, so the response is
    not bounded -- a multi-megabyte report.json is normal and expected
    for a downloaded file the way it is not for an LLM tool response.
    """
    root = _validated_path(project_path)

    try:
        discovery = discover_project(root)
        evidence_files = evidence_files_from_discovery(discovery)
        selected = select_evidence_files(include, evidence_files)
    except ValueError as exc:
        raise WebInvestigateError("discovery_failed", str(exc)) from exc

    if not selected:
        raise WebInvestigateError(
            "no_evidence_selected",
            "No evidence was found or selected for this project.",
        )

    evidence_inputs = [
        EvidenceInput(source=item.source, path=item.path) for item in selected
    ]

    try:
        with _desktop_chat_deep_parse_enabled(include_desktop_chat_deep_parse):
            observations = load_observations(evidence_inputs)
    except ValueError as exc:
        raise WebInvestigateError("investigation_failed", str(exc)) from exc

    investigation = build_investigation(
        project=project_name or root.name,
        source_files=[item.path for item in evidence_inputs],
        observations=observations,
    )

    return {
        "ok": True,
        "project": investigation.project,
        "sources": sorted({item.source for item in selected}),
        "markdown": render_markdown(investigation),
        "json": render_json_dict(investigation),
        "playbookMarkdown": build_playbook_worksheet_markdown(investigation),
    }


class _desktop_chat_deep_parse_enabled:
    """Context manager toggling the same env var the CLI wizard, Next.js
    Claude session evidence UI, and MCP server use to opt Claude Desktop
    Chat into deep parsing for one call, restoring the prior value after.
    Duplicated here rather than imported from mcp_server.py, matching this
    codebase's existing per-module independence convention (see
    claude_code.py/claude_cowork.py/claude_desktop_chat.py)."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled
        self._previous: str | None = None

    def __enter__(self) -> None:
        if self._enabled:
            self._previous = os.environ.get(DESKTOP_CHAT_DEEP_PARSE_ENV)
            os.environ[DESKTOP_CHAT_DEEP_PARSE_ENV] = "1"

    def __exit__(self, *exc_info: object) -> None:
        if not self._enabled:
            return
        if self._previous is None:
            os.environ.pop(DESKTOP_CHAT_DEEP_PARSE_ENV, None)
        else:
            os.environ[DESKTOP_CHAT_DEEP_PARSE_ENV] = self._previous


def _validated_path(project_path: str) -> Path:
    if not isinstance(project_path, str) or not project_path.strip():
        raise WebInvestigateError("missing_path", "Enter a local project path.")
    if len(project_path) > MAX_PATH_LENGTH:
        raise WebInvestigateError("path_too_long", "Project path is too long.")

    root = Path(project_path).expanduser().resolve()
    if not root.exists():
        raise WebInvestigateError("path_not_found", "Project path was not found.")
    if not root.is_dir():
        raise WebInvestigateError("not_directory", "Project path must be a folder.")
    return root


def _json_error(error: WebInvestigateError) -> dict[str, Any]:
    return {"ok": False, "error": {"code": error.code, "message": error.message}}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a full Workprint investigation and print both report formats as JSON."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--include")
    parser.add_argument("--project-name")
    parser.add_argument("--include-desktop-chat-deep-parse", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = build_web_investigation(
            args.project,
            include=args.include,
            project_name=args.project_name,
            include_desktop_chat_deep_parse=args.include_desktop_chat_deep_parse,
        )
    except WebInvestigateError as exc:
        print(json.dumps(_json_error(exc), ensure_ascii=False))
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

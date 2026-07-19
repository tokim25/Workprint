from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Imported unconditionally, not lazily inside a function: unlike the
# claude-desktop-chat adapter (where only one opt-in mode needs
# ccl_chromium_reader and everything else works without it), this entire
# module requires the mcp package to do anything at all. Letting a missing
# dependency raise a plain ImportError/ModuleNotFoundError here -- rather
# than catching it and calling sys.exit -- keeps `import workprint.mcp_server`
# usable in a standard `try/except ImportError` skip guard, the same pattern
# tests/test_claude_desktop_chat_adapter.py already uses.
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from workprint.adapters import available_adapters
from workprint.discovery import discover_project as _discover_project
from workprint.engine import build_investigation
from workprint.guided import evidence_files_from_discovery, select_evidence_files
from workprint.multisource import EvidenceInput, load_observations
from workprint.reports import render_json_dict


MAX_PATH_LENGTH = 4096
DESKTOP_CHAT_DEEP_PARSE_ENV = "WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE"
DEFAULT_EVIDENCE_ID_PREVIEW = 10

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, openWorldHint=False
)


def list_supported_sources() -> dict[str, Any]:
    """List the evidence source IDs Workprint knows how to read."""
    return {"ok": True, "sources": list(available_adapters())}


def discover_project(project_path: str) -> dict[str, Any]:
    """Preview what evidence Workprint can find in a local project
    directory (Git, Claude Code/Cowork/Desktop Chat sessions, and any
    static conversation or document exports present in the folder).

    This does not read full evidence content -- only bounded counts and
    metadata, mirroring `workprint discover`. Safe to call speculatively
    before deciding whether to run investigate_project.
    """
    try:
        root = _validated_path(project_path)
        discovery = _discover_project(root)
    except ValueError as exc:
        return _error("discovery_failed", str(exc))
    return {"ok": True, **discovery.to_dict()}


def investigate_project(
    project_path: str,
    include: str | None = None,
    project_name: str | None = None,
    include_desktop_chat_deep_parse: bool = False,
    include_full_report: bool = False,
    include_observations: bool = False,
    include_timeline: bool = False,
) -> dict[str, Any]:
    """Run a full Workprint investigation over a local project's discovered
    evidence and return a structured, bounded report.

    `include` uses the same selection syntax as the `workprint guide` CLI
    wizard: "all" or omitted selects everything discovered; a
    comma-separated list of numbers and/or source IDs selects specific
    evidence (for example "1,3" or "git,claude-code"); prefix an entry
    with "-" to exclude it (for example "-google-docs").

    `include_desktop_chat_deep_parse` opts into Claude Desktop Chat's
    experimental, account-wide deep-parse mode. It defaults to off,
    matching every other Workprint surface, because that evidence cannot
    be confirmed to relate to this specific project.

    The default response is deliberately bounded, not the full report:
    a real investigation's full JSON (raw observations, full timeline,
    every finding's complete evidence-ID list) has been measured at
    several megabytes on this project's own history -- far too large for
    a conversational tool result. By default, findings carry only the
    first 10 evidence IDs plus a total count, the executive brief is
    included but the full executive report is not, and observations/
    timeline are represented only as counts. Set `include_full_report`,
    `include_observations`, and/or `include_timeline` to true to get the
    complete data instead.
    """
    try:
        root = _validated_path(project_path)
        discovery = _discover_project(root)
        evidence_files = evidence_files_from_discovery(discovery)
        selected = select_evidence_files(include, evidence_files)
    except ValueError as exc:
        return _error("discovery_failed", str(exc))

    if not selected:
        return _error(
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
        return _error("investigation_failed", str(exc))

    investigation = build_investigation(
        project=project_name or root.name,
        source_files=[item.path for item in evidence_inputs],
        observations=observations,
    )
    report = render_json_dict(investigation)
    bounded = _bounded_investigation(
        report,
        include_full_report=include_full_report,
        include_observations=include_observations,
        include_timeline=include_timeline,
    )
    return {"ok": True, "investigation": bounded}


def _bounded_investigation(
    report: dict[str, Any],
    *,
    include_full_report: bool,
    include_observations: bool,
    include_timeline: bool,
) -> dict[str, Any]:
    executive_report = report.get("executive_report") or {}
    bounded: dict[str, Any] = {
        "project": report.get("project"),
        "source_files": report.get("source_files"),
        "observation_count": len(report.get("observations") or []),
        "timeline_event_count": len(report.get("timeline") or []),
        "timeline_summary": report.get("timeline_summary"),
        "unknowns": report.get("unknowns"),
        "limitations": report.get("limitations"),
        "executive_brief": executive_report.get("executive_brief"),
    }

    if include_full_report:
        bounded["findings"] = report.get("findings", [])
        bounded["executive_report"] = executive_report
    else:
        bounded["findings"] = [
            _bounded_finding(finding) for finding in report.get("findings", [])
        ]

    if include_observations:
        bounded["observations"] = report.get("observations", [])
    if include_timeline:
        bounded["timeline"] = report.get("timeline", [])

    return bounded


def _bounded_finding(finding: dict[str, Any]) -> dict[str, Any]:
    evidence_ids = finding.get("evidence_ids") or []
    return {
        **{key: value for key, value in finding.items() if key != "evidence_ids"},
        "evidence_ids": evidence_ids[:DEFAULT_EVIDENCE_ID_PREVIEW],
        "evidence_id_count": len(evidence_ids),
    }


class _desktop_chat_deep_parse_enabled:
    """Context manager toggling the same env var the guided CLI wizard and
    Next.js UI use to opt Claude Desktop Chat into deep parsing for one
    call, restoring the prior value afterward."""

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
        raise ValueError("project_path must be a non-empty local path")
    if len(project_path) > MAX_PATH_LENGTH:
        raise ValueError("project_path is too long")
    root = Path(project_path).expanduser().resolve()
    if not root.exists():
        raise ValueError(f"path not found: {project_path}")
    if not root.is_dir():
        raise ValueError(f"path is not a directory: {project_path}")
    return root


def _error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


def create_server() -> FastMCP:
    """Build the Workprint MCP server, registering the module-level tool
    functions above. Kept separate from those functions so tests can call
    them directly without any MCP protocol/transport ceremony, and so
    module import does not require a running server."""
    server = FastMCP(
        name="workprint",
        instructions=(
            "Workprint reconstructs how a local project was made from "
            "evidence such as Git history, Claude Code/Cowork/Desktop Chat "
            "sessions, and static conversation or document exports found in "
            "the project directory. It reports observable facts and "
            "explicitly marks what the evidence cannot determine -- it "
            "never infers authorship, ownership, effort, or contribution "
            "percentages. Every tool here is read-only and only accesses "
            "the local project_path given as an argument."
        ),
    )
    server.tool(annotations=READ_ONLY)(list_supported_sources)
    server.tool(annotations=READ_ONLY)(discover_project)
    server.tool(annotations=READ_ONLY)(investigate_project)
    return server


def main() -> None:
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from workprint.adapters import ClaudeCodeAdapter, ClaudeCoworkAdapter, ClaudeDesktopChatAdapter
from workprint.models import NormalizedMessage


MAX_PATH_LENGTH = 4096


@dataclass(frozen=True)
class ClaudeLocalSummaryError(Exception):
    code: str
    message: str


def build_claude_local_summary(
    project_path: str,
    *,
    include_desktop_chat_deep_parse: bool = False,
    claude_code_adapter: ClaudeCodeAdapter | None = None,
    claude_cowork_adapter: ClaudeCoworkAdapter | None = None,
    claude_desktop_chat_adapter: ClaudeDesktopChatAdapter | None = None,
) -> dict[str, Any]:
    """Build a bounded, structural summary of local Claude Code, Cowork, and
    Desktop Chat evidence for a project directory.

    Unlike Git, an empty or "not found" result from any of these three
    sources is not an error -- most projects will not have used all three.
    The only real error case is an invalid path.
    """
    root = _validated_path(project_path)

    code_adapter = claude_code_adapter or ClaudeCodeAdapter()
    cowork_adapter = claude_cowork_adapter or ClaudeCoworkAdapter()

    try:
        code_messages = code_adapter.read(root)
    except ValueError:
        code_messages = []
    try:
        cowork_messages = cowork_adapter.read(root)
    except ValueError:
        cowork_messages = []

    desktop_chat_summary = _desktop_chat_summary(
        root,
        include_desktop_chat_deep_parse,
        claude_desktop_chat_adapter,
    )

    return {
        "ok": True,
        "claude_code": _session_aggregate(code_messages),
        "claude_cowork": _session_aggregate(cowork_messages),
        "claude_desktop_chat": desktop_chat_summary,
        "limitations": [
            "Session and turn counts describe recorded activity, not effort, "
            "ownership, value, or contribution.",
            "Claude Desktop Chat evidence is account-wide; it cannot be "
            "confirmed to relate to this specific project.",
            "Tool-use counts describe recorded tool invocations, not what "
            "those tools changed.",
        ],
    }


def _session_aggregate(messages: list[NormalizedMessage]) -> dict[str, Any]:
    session_ids = {message.conversation_id for message in messages}
    human_turns = [message for message in messages if message.role == "human"]
    assistant_turns = [message for message in messages if message.role == "assistant"]

    tool_use_counts: dict[str, int] = {}
    sidechain_turn_count = 0
    for message in assistant_turns:
        counts = message.metadata.get("tool_use_counts")
        if isinstance(counts, dict):
            for name, count in counts.items():
                tool_use_counts[str(name)] = tool_use_counts.get(str(name), 0) + int(count)
        if message.metadata.get("is_sidechain"):
            sidechain_turn_count += 1

    timestamps = [message.created_at for message in messages if message.created_at is not None]

    return {
        "session_count": len(session_ids),
        "turn_count": len(messages),
        "human_turn_count": len(human_turns),
        "assistant_turn_count": len(assistant_turns),
        "sidechain_turn_count": sidechain_turn_count,
        "tool_use_counts": tool_use_counts,
        "earliest_turn_date": min(timestamps).isoformat() if timestamps else None,
        "latest_turn_date": max(timestamps).isoformat() if timestamps else None,
    }


def _desktop_chat_summary(
    root: Path,
    include_deep_parse: bool,
    adapter: ClaudeDesktopChatAdapter | None,
) -> dict[str, Any]:
    dependency_available = _desktop_chat_dependency_available()
    requested_deep_parse = include_deep_parse and dependency_available

    chat_adapter = adapter or ClaudeDesktopChatAdapter(deep_parse=requested_deep_parse)
    try:
        messages = chat_adapter.read(root)
    except ValueError:
        messages = []

    presence = next(
        (message for message in messages if message.metadata.get("presence_only")),
        None,
    )
    real_turns = [
        message for message in messages if not message.metadata.get("presence_only")
    ]

    summary: dict[str, Any] = {
        "cache_detected": bool(messages),
        "last_modified": (
            presence.metadata.get("last_modified") if presence is not None else None
        ),
        "deep_parse_available": dependency_available,
        "deep_parse_requested": requested_deep_parse,
        "deep_parse_found_turns": bool(real_turns),
    }
    if real_turns:
        summary["turns"] = _session_aggregate(real_turns)
    return summary


def _desktop_chat_dependency_available() -> bool:
    try:
        import ccl_chromium_reader  # noqa: F401
    except ImportError:
        return False
    return True


def _validated_path(project_path: str) -> Path:
    if not isinstance(project_path, str):
        raise ClaudeLocalSummaryError("invalid_path", "Project path must be text.")
    if not project_path.strip():
        raise ClaudeLocalSummaryError("missing_path", "Enter a local project path.")
    if len(project_path) > MAX_PATH_LENGTH:
        raise ClaudeLocalSummaryError("path_too_long", "Project path is too long.")

    root = Path(project_path).expanduser().resolve()
    if not root.exists():
        raise ClaudeLocalSummaryError("path_not_found", "Project path was not found.")
    if not root.is_dir():
        raise ClaudeLocalSummaryError("not_directory", "Project path must be a folder.")
    return root


def _json_error(error: ClaudeLocalSummaryError) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Return a bounded local Claude session summary as JSON."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--include-desktop-chat-deep-parse", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = build_claude_local_summary(
            args.project,
            include_desktop_chat_deep_parse=args.include_desktop_chat_deep_parse,
        )
    except ClaudeLocalSummaryError as exc:
        print(json.dumps(_json_error(exc), ensure_ascii=False))
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

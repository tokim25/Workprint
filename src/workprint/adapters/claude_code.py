from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter


DEFAULT_CLAUDE_HOME_ENV = "WORKPRINT_CLAUDE_HOME"
MAX_SESSIONS = 20
MAX_RECORDS_PER_SESSION = 5000
CWD_SCAN_LIMIT = 50
EXCERPT_LIMIT = 600


def _default_claude_home() -> Path:
    override = os.environ.get(DEFAULT_CLAUDE_HOME_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "projects"


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _session_cwd(session_path: Path) -> Path | None:
    try:
        with session_path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= CWD_SCAN_LIMIT:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = record.get("cwd") if isinstance(record, dict) else None
                if isinstance(cwd, str) and cwd.strip():
                    try:
                        return Path(cwd).expanduser().resolve()
                    except OSError:
                        return None
    except OSError:
        return None
    return None


def _tool_use_counts(blocks: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = str(block.get("name") or "unknown-tool")
            counts[name] = counts.get(name, 0) + 1
    return counts


def _block_count(blocks: list[Any], block_type: str) -> int:
    return sum(
        1
        for block in blocks
        if isinstance(block, dict) and block.get("type") == block_type
    )


def _excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


@dataclass(frozen=True)
class _MatchedSession:
    path: Path
    session_id: str


class ClaudeCodeAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read local Claude Code session transcripts for a project directory.

    Unlike file-based adapters, Claude Code stores session transcripts
    outside the project tree (by default under ``~/.claude/projects``). This
    adapter matches sessions to a project by the ``cwd`` recorded inside each
    transcript rather than by reproducing Claude Code's internal directory
    naming convention, so an unrecognized or changed convention makes it find
    nothing rather than match the wrong project.

    Message content is structural by default: turn counts, tool names used,
    and response shape, never raw prompt or response text. Raw text excerpts
    are opt-in via ``include_content_excerpts`` because session transcripts
    can contain anything a person pasted into a prompt, including
    credentials or personal text.
    """

    source_name = "Claude Code"
    source_type = "conversation"

    def __init__(
        self,
        claude_home: str | Path | None = None,
        include_content_excerpts: bool = False,
    ) -> None:
        self._claude_home = (
            Path(claude_home).expanduser() if claude_home else _default_claude_home()
        )
        self._include_content_excerpts = include_content_excerpts

    def validate_input(self, path: str | Path) -> Path:
        project_root = Path(path).expanduser()
        if not project_root.exists():
            raise ValueError(f"path not found: {project_root}")
        if not project_root.is_dir():
            raise ValueError(f"input is not a directory: {project_root}")
        return project_root.resolve()

    def discover(self, path: str | Path) -> dict[str, Any] | None:
        try:
            records = self.read(path)
        except ValueError:
            return None
        if not records:
            return None
        return {
            "source": self.adapter_id,
            "label": self.display_name,
            "record_count": len({item.conversation_id for item in records}),
        }

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        project_root = self.validate_input(path)
        sessions = self._matching_sessions(project_root)

        results: list[NormalizedMessage] = []
        for session in sessions:
            results.extend(self._read_session(session))

        results.sort(
            key=lambda item: (
                item.created_at is None,
                item.created_at or datetime.max.replace(tzinfo=timezone.utc),
                item.conversation_id,
                item.id,
            )
        )
        return results

    def _matching_sessions(self, project_root: Path) -> list[_MatchedSession]:
        if not self._claude_home.exists() or not self._claude_home.is_dir():
            return []

        candidates: list[tuple[float, _MatchedSession]] = []
        for project_dir in self._claude_home.iterdir():
            if not project_dir.is_dir():
                continue
            for session_file in project_dir.glob("*.jsonl"):
                if _session_cwd(session_file) != project_root:
                    continue
                try:
                    mtime = session_file.stat().st_mtime
                except OSError:
                    continue
                candidates.append(
                    (
                        mtime,
                        _MatchedSession(
                            path=session_file, session_id=session_file.stem
                        ),
                    )
                )

        candidates.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in candidates[:MAX_SESSIONS]]

    def _read_session(self, session: _MatchedSession) -> list[NormalizedMessage]:
        results: list[NormalizedMessage] = []
        try:
            with session.path.open("r", encoding="utf-8") as handle:
                for index, line in enumerate(handle):
                    if index >= MAX_RECORDS_PER_SESSION:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    message = self._normalize_record(session, record, index)
                    if message is not None:
                        results.append(message)
        except OSError:
            return []
        return results

    def _normalize_record(
        self, session: _MatchedSession, record: dict[str, Any], index: int
    ) -> NormalizedMessage | None:
        record_type = record.get("type")
        message = record.get("message")
        if record_type not in {"user", "assistant"} or not isinstance(message, dict):
            return None

        role = "human" if record_type == "user" else "assistant"
        turn_id = str(record.get("uuid") or f"{session.session_id}-turn-{index}")
        created_at = _parse_timestamp(record.get("timestamp"))
        is_sidechain = bool(record.get("isSidechain", False))
        content = message.get("content")

        if role == "human":
            text = content if isinstance(content, str) else ""
            label = "Human sent a message to Claude Code."
            metadata: dict[str, Any] = {"content_length": len(text)}
        else:
            blocks = content if isinstance(content, list) else []
            tool_counts = _tool_use_counts(blocks)
            text_blocks = _block_count(blocks, "text")
            thinking_blocks = _block_count(blocks, "thinking")
            tool_summary = ", ".join(
                f"{name} ({count})" for name, count in sorted(tool_counts.items())
            )
            label_parts: list[str] = []
            if text_blocks:
                noun = "response" if text_blocks == 1 else "responses"
                label_parts.append(f"{text_blocks} text {noun}")
            if tool_summary:
                label_parts.append(f"tool use: {tool_summary}")
            if not label_parts:
                label_parts.append("no text or tool use recorded")
            label = "Claude responded with " + "; ".join(label_parts) + "."
            text = "\n".join(
                block.get("text", "")
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            )
            metadata = {
                "tool_use_counts": tool_counts,
                "text_block_count": text_blocks,
                "thinking_block_count": thinking_blocks,
            }

        if self._include_content_excerpts and text.strip():
            label = f"{label} Excerpt: {_excerpt(text)}"

        metadata.update(
            {
                "source_type": self.source_type,
                "session_id": session.session_id,
                "is_sidechain": is_sidechain,
                "cwd": record.get("cwd"),
                "git_branch": record.get("gitBranch"),
            }
        )

        return NormalizedMessage(
            id=turn_id,
            conversation_id=session.session_id,
            role=role,
            content=label,
            created_at=created_at,
            source=self.source_name,
            source_locator=f"{session.path.name}#turn/{turn_id}",
            metadata=metadata,
        )

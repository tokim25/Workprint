from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter


COWORK_HOME_ENV = "WORKPRINT_COWORK_HOME"
MAX_SESSIONS = 20
MAX_RECORDS_PER_SESSION = 5000
EXCERPT_LIMIT = 600


def _default_cowork_home() -> Path:
    """Best-effort default location for Claude Cowork's local session data.

    Verified against a real macOS installation
    (``~/Library/Application Support/Claude/local-agent-mode-sessions``).
    The Windows and Linux paths follow the platform's usual Electron
    app-data convention but are not independently verified; set
    ``WORKPRINT_COWORK_HOME`` to override if they are wrong.
    """
    override = os.environ.get(COWORK_HOME_ENV)
    if override:
        return Path(override).expanduser()

    home = Path.home()
    if sys.platform == "darwin":
        base = home / "Library" / "Application Support" / "Claude"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) / "Claude" if appdata else home / "AppData" / "Roaming" / "Claude"
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg_config) / "Claude" if xdg_config else home / ".config" / "Claude"
    return base / "local-agent-mode-sessions"


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
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
    transcript_path: Path
    session_id: str
    cowork_session_id: str
    model: str | None
    session_type: str | None
    is_archived: bool | None


class ClaudeCoworkAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read local Claude Cowork session transcripts for a project directory.

    Each Cowork session runs in its own sandboxed Claude Code home
    directory and writes transcripts in the same JSONL shape the Claude
    Code adapter reads, so this adapter reuses that shape independently
    (see ``claude_code.py``) rather than sharing code across the two
    already-shipped adapters.

    A Cowork transcript's own ``cwd`` points at an internal sandbox output
    path, not the user's real project directory, so sessions are matched
    instead by the ``userSelectedFolders`` recorded in the session's
    metadata file (``local_<uuid>.json``). A project with no matching
    folder in any session's ``userSelectedFolders`` finds nothing rather
    than guessing.
    """

    source_name = "Claude Cowork"
    source_type = "conversation"

    def __init__(
        self,
        cowork_home: str | Path | None = None,
        include_content_excerpts: bool = False,
    ) -> None:
        self._cowork_home = (
            Path(cowork_home).expanduser() if cowork_home else _default_cowork_home()
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
        if not self._cowork_home.exists() or not self._cowork_home.is_dir():
            return []

        candidates: list[tuple[float, _MatchedSession]] = []
        for metadata_path in self._cowork_home.rglob("local_*.json"):
            metadata = self._read_metadata(metadata_path)
            if metadata is None or not self._selects_folder(metadata, project_root):
                continue

            session_dir = metadata_path.with_suffix("")
            claude_projects = session_dir / ".claude" / "projects"
            if not claude_projects.is_dir():
                continue

            for transcript_path in claude_projects.glob("*/*.jsonl"):
                try:
                    mtime = transcript_path.stat().st_mtime
                except OSError:
                    continue
                candidates.append(
                    (
                        mtime,
                        _MatchedSession(
                            transcript_path=transcript_path,
                            session_id=transcript_path.stem,
                            cowork_session_id=str(
                                metadata.get("sessionId") or metadata_path.stem
                            ),
                            model=(
                                metadata.get("model")
                                if isinstance(metadata.get("model"), str)
                                else None
                            ),
                            session_type=(
                                metadata.get("sessionType")
                                if isinstance(metadata.get("sessionType"), str)
                                else None
                            ),
                            is_archived=(
                                metadata.get("isArchived")
                                if isinstance(metadata.get("isArchived"), bool)
                                else None
                            ),
                        ),
                    )
                )

        candidates.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in candidates[:MAX_SESSIONS]]

    @staticmethod
    def _read_metadata(metadata_path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _selects_folder(metadata: dict[str, Any], project_root: Path) -> bool:
        folders = metadata.get("userSelectedFolders")
        if not isinstance(folders, list):
            return False
        for folder in folders:
            if not isinstance(folder, str) or not folder.strip():
                continue
            try:
                if Path(folder).expanduser().resolve() == project_root:
                    return True
            except OSError:
                continue
        return False

    def _read_session(self, session: _MatchedSession) -> list[NormalizedMessage]:
        results: list[NormalizedMessage] = []
        try:
            with session.transcript_path.open("r", encoding="utf-8") as handle:
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
            label = "Human sent a message to a Claude Cowork session."
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
            label = "Claude Cowork responded with " + "; ".join(label_parts) + "."
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
                "cowork_session_id": session.cowork_session_id,
                "is_sidechain": is_sidechain,
                "model": session.model,
                "session_type": session.session_type,
                "is_archived": session.is_archived,
            }
        )

        return NormalizedMessage(
            id=turn_id,
            conversation_id=session.session_id,
            role=role,
            content=label,
            created_at=created_at,
            source=self.source_name,
            source_locator=f"{session.transcript_path.name}#turn/{turn_id}",
            metadata=metadata,
        )

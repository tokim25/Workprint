from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter


INDEXEDDB_HOME_ENV = "WORKPRINT_CLAUDE_DESKTOP_HOME"
DEEP_PARSE_ENV = "WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE"
EXCERPT_LIMIT = 600

# Empirically observed object-store name fragments in a real local cache on
# this codebase's own development machine (macOS). Not documented by
# Anthropic; may not hold on other versions of the Claude desktop app. The
# deep-parse path tries these first and falls back to whatever
# WrappedIndexDB exposes, since hardcoding a single guessed name would be
# more fragile than trying several and skipping ones that don't work.
_CANDIDATE_STORE_NAMES = ("keyval-store", "val-store")

# Field names a candidate record needs to plausibly be a chat turn, loosely
# matching the shape workprint.adapters.claude already looks for in claude.ai
# export files. This is a heuristic, not a documented schema: the deep-parse
# path is explicitly experimental (see docs/claude-desktop-chat-adapter.md).
_ROLE_KEYS = ("role", "sender")
_CONTENT_KEYS = ("content", "text")
_HUMAN_ROLE_VALUES = {"human", "user"}
_ASSISTANT_ROLE_VALUES = {"assistant", "claude"}


def _default_indexeddb_home() -> Path:
    """Best-effort default location for the Claude desktop app's cached
    claude.ai IndexedDB store.

    Verified against a real macOS installation
    (``~/Library/Application Support/Claude/IndexedDB/https_claude.ai_0.indexeddb.leveldb``).
    Windows and Linux paths follow the platform's usual Electron app-data
    convention but are not independently verified.
    """
    override = os.environ.get(INDEXEDDB_HOME_ENV)
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
    return base / "IndexedDB" / "https_claude.ai_0.indexeddb.leveldb"


def _excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


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


@dataclass(frozen=True)
class _CandidateTurn:
    role: str
    text: str
    turn_id: str | None
    created_at: Any


def _normalize_role(raw: Any) -> str | None:
    value = str(raw).strip().lower()
    if value in _HUMAN_ROLE_VALUES:
        return "human"
    if value in _ASSISTANT_ROLE_VALUES:
        return "assistant"
    return None


def _as_candidate_turn(node: dict[str, Any]) -> _CandidateTurn | None:
    role = None
    for key in _ROLE_KEYS:
        if key in node:
            role = _normalize_role(node[key])
            break
    if role is None:
        return None

    text = None
    for key in _CONTENT_KEYS:
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            text = value
            break
    if text is None:
        return None

    turn_id = node.get("uuid") or node.get("id")
    created_at = node.get("created_at") or node.get("timestamp")
    return _CandidateTurn(
        role=role,
        text=text,
        turn_id=str(turn_id) if turn_id else None,
        created_at=created_at,
    )


def _walk_candidate_turns(value: Any, depth: int = 0) -> Iterator[_CandidateTurn]:
    """Recursively search a deserialized IndexedDB value for dicts that look
    like a chat turn.

    This is a heuristic best-effort scan, not a schema-aware parser: the
    real structure of Anthropic's client-side cache is not documented, and
    this function's only job is to find plausible needles in a
    (potentially large, arbitrarily nested) haystack. See the "Evidence
    Semantics" section in docs/claude-desktop-chat-adapter.md.
    """
    if depth > 12:
        return
    if isinstance(value, dict):
        turn = _as_candidate_turn(value)
        if turn is not None:
            yield turn
            return
        for child in value.values():
            yield from _walk_candidate_turns(child, depth + 1)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_candidate_turns(item, depth + 1)


class DeepParseUnavailableError(ValueError):
    """Raised when deep_parse=True but the optional dependency is missing."""


def _iter_deep_parsed_turns(indexeddb_home: Path) -> Iterator[tuple[str, _CandidateTurn]]:
    try:
        from ccl_chromium_reader import ccl_chromium_indexeddb
    except ImportError as exc:
        raise DeepParseUnavailableError(
            "deep parsing of the Claude Desktop chat cache requires the "
            "optional 'claude-desktop-chat' extra: "
            "pip install 'workprint[claude-desktop-chat]'"
        ) from exc

    try:
        wrapper = ccl_chromium_indexeddb.WrappedIndexDB(str(indexeddb_home), str(indexeddb_home))
    except Exception as exc:  # noqa: BLE001 - experimental, undocumented format
        raise ValueError(
            "could not open the Claude Desktop chat cache; the on-disk "
            "format may not match what this experimental parser expects"
        ) from exc

    database_ids = _database_ids(wrapper)
    for database_name, database_version in database_ids:
        try:
            database = wrapper[database_name, database_version]
        except Exception:  # noqa: BLE001 - keep scanning other databases
            continue
        for store_name in _object_store_names(database):
            try:
                store = database[store_name]
                for record in store.iterate_records():
                    yield store_name, record
            except Exception:  # noqa: BLE001 - keep scanning other stores
                continue


def _database_ids(wrapper: Any) -> list[tuple[str, Any]]:
    for attribute in ("database_ids", "database_names", "databases"):
        candidate = getattr(wrapper, attribute, None)
        if candidate:
            try:
                return list(candidate)
            except TypeError:
                continue
    return []


def _object_store_names(database: Any) -> list[str]:
    for attribute in ("object_store_names", "object_stores"):
        candidate = getattr(database, attribute, None)
        if candidate:
            try:
                return list(candidate)
            except TypeError:
                continue
    return list(_CANDIDATE_STORE_NAMES)


class ClaudeDesktopChatAdapter(EvidenceAdapter[NormalizedMessage]):
    """Report on the Claude desktop app's local claude.ai chat cache.

    Unlike every other adapter in this package, this source has no concept
    of "which project" a conversation belongs to: claude.ai chat has no
    folder or working-directory attached to it. So even with deep parsing
    enabled, the evidence this adapter produces is account-wide, not
    specific to the project being investigated — that limitation is
    recorded on every record's metadata (``project_specific: False``) and
    is why semantic project-matching for this source is intentionally not
    attempted here; see the "Semantic correlation only after deterministic
    behavior is trustworthy" item in ROADMAP.md.

    Default behavior only reports that the cache exists and when it was
    last modified (``deep_parse=False``, the default). Turning on
    ``deep_parse=True`` attempts to extract real conversation turns using
    the optional ``ccl_chromium_reader`` dependency and a best-effort,
    explicitly experimental heuristic scan of the deserialized values,
    because the cache's actual internal schema is not documented by
    Anthropic and was not directly verified against a running parser
    (see docs/claude-desktop-chat-adapter.md). IndexedDB may also retain
    deleted/stale record versions, so deep parsing can resurface
    conversations no longer visible on claude.ai.
    """

    source_name = "Claude Desktop Chat"
    source_type = "conversation"

    def __init__(
        self,
        indexeddb_home: str | Path | None = None,
        deep_parse: bool | None = None,
        include_content_excerpts: bool = False,
    ) -> None:
        self._indexeddb_home = (
            Path(indexeddb_home).expanduser()
            if indexeddb_home
            else _default_indexeddb_home()
        )
        # `deep_parse` defaults to an environment variable, not a hardcoded
        # False, so an interactive consent prompt (see workprint.guided) can
        # turn it on for the current process without every caller of
        # get_adapter("claude-desktop-chat") needing new constructor
        # plumbing threaded through the shared adapter registry.
        self._deep_parse = (
            deep_parse
            if deep_parse is not None
            else os.environ.get(DEEP_PARSE_ENV) == "1"
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
            "record_count": len(records),
            "deep_parse": self._deep_parse,
        }

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        # `path` is accepted for interface consistency with every other
        # adapter, but this source cannot be scoped to a project (see the
        # class docstring), so it is validated but not used to filter
        # results.
        self.validate_input(path)

        if not self._indexeddb_home.exists():
            return []

        if not self._deep_parse:
            return [self._presence_record()]

        return self._deep_parsed_records()

    def _presence_record(self) -> NormalizedMessage:
        try:
            last_modified = datetime.fromtimestamp(
                self._indexeddb_home.stat().st_mtime, tz=timezone.utc
            )
        except OSError:
            last_modified = None

        return NormalizedMessage(
            id="claude-desktop-chat-presence",
            conversation_id="claude-desktop-chat-presence",
            role="system",
            content=(
                "A local Claude Desktop chat cache was detected"
                + (f", last modified {last_modified.isoformat()}" if last_modified else "")
                + ". Deep parsing was not enabled, so no conversation-level "
                "evidence is included."
            ),
            created_at=last_modified,
            source=self.source_name,
            source_locator=f"{self._indexeddb_home.name}#presence",
            metadata={
                "source_type": self.source_type,
                "presence_only": True,
                "project_specific": False,
                "last_modified": last_modified.isoformat() if last_modified else None,
            },
        )

    def _deep_parsed_records(self) -> list[NormalizedMessage]:
        results: list[NormalizedMessage] = []
        seen_ids: set[str] = set()

        for store_name, record in _iter_deep_parsed_turns(self._indexeddb_home):
            for turn in _walk_candidate_turns(getattr(record, "value", None)):
                turn_id = turn.turn_id or f"{store_name}-{len(results)}"
                if turn_id in seen_ids:
                    continue
                seen_ids.add(turn_id)
                results.append(self._normalize_turn(store_name, turn_id, turn))

        if not results:
            return [self._presence_record()]

        results.sort(
            key=lambda item: (
                item.created_at is None,
                item.created_at or datetime.max.replace(tzinfo=timezone.utc),
                item.id,
            )
        )
        return results

    def _normalize_turn(
        self, store_name: str, turn_id: str, turn: _CandidateTurn
    ) -> NormalizedMessage:
        label = (
            "Human sent a message in Claude Desktop chat (account-wide, not "
            "specific to this project)."
            if turn.role == "human"
            else "Claude responded in Claude Desktop chat (account-wide, not "
            "specific to this project)."
        )
        if self._include_content_excerpts and turn.text.strip():
            label = f"{label} Excerpt: {_excerpt(turn.text)}"

        return NormalizedMessage(
            id=turn_id,
            conversation_id=turn_id,
            role=turn.role,
            content=label,
            created_at=_parse_timestamp(turn.created_at),
            source=self.source_name,
            source_locator=f"{store_name}#turn/{turn_id}",
            metadata={
                "source_type": self.source_type,
                "project_specific": False,
                "experimental_deep_parse": True,
                "may_include_deleted_records": True,
            },
        )

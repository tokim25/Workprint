from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter
from .google_docs import _parse_timestamp, _split_blocks, _title_from_markdown


SUPPORTED_SUFFIXES = {".json", ".md", ".txt"}


def build_chat_summary_template(title: str = "Untitled chat summary") -> dict[str, Any]:
    """Return a conservative template users can review before importing."""
    return {
        "workprint_source": "chat-summary",
        "id": "replace-with-stable-summary-id",
        "title": title,
        "approved_by_user": False,
        "approved_at": None,
        "original_sources": [],
        "date_range": {
            "start": None,
            "end": None,
        },
        "participants": [],
        "tools": [],
        "summary_method": "user-written or user-reviewed summary",
        "summary": (
            "Replace this with the user-approved long-chat summary. "
            "Do not paste secrets or private material you do not want included."
        ),
        "key_decisions": [],
        "user_direction": [],
        "ai_fluency_notes": [],
        "unknowns": [
            "This summary is not the full transcript and cannot prove omitted turns."
        ],
        "limitations": [
            "Workprint must treat this as summary evidence, not a complete chat log."
        ],
    }


class ChatSummaryAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read user-approved long-chat summaries without treating them as transcripts."""

    source_name = "chat-summary"
    source_type = "summary"
    discovery_marker = "workprint-source: chat-summary"

    @property
    def display_name(self) -> str:
        return "Chat Summary"

    def discover(self, path: str | Path) -> dict[str, Any] | None:
        source_path = Path(path)
        if source_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            return None
        if source_path.suffix.lower() in {".md", ".txt"} and not self._has_marker(source_path):
            return None
        return super().discover(path)

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        source_path = self.validate_input(path)
        suffix = source_path.suffix.lower()
        if suffix == ".json":
            return self._read_json(source_path)
        if suffix in {".md", ".txt"}:
            return self._read_text(source_path, suffix=suffix)
        raise ValueError(f"unsupported chat summary format: {source_path.suffix}")

    def _has_marker(self, source_path: Path) -> bool:
        try:
            lines = source_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return False
        checked = 0
        for line in lines:
            stripped = line.strip().lower()
            if not stripped or stripped in {"---", "+++"}:
                continue
            checked += 1
            if stripped == self.discovery_marker:
                return True
            if checked >= 6:
                return False
        return False

    def _read_text(self, source_path: Path, suffix: str) -> list[NormalizedMessage]:
        text = source_path.read_text(encoding="utf-8")
        blocks = [
            block for block in _split_blocks(text)
            if block.strip().lower() != self.discovery_marker
        ]
        if not blocks:
            raise ValueError("chat summary contains no summary text")
        title = _title_from_markdown(blocks, source_path.stem) if suffix == ".md" else source_path.stem
        return [
            self._message(
                source_path=source_path,
                summary_id=source_path.stem,
                title=title,
                item_id=f"summary-block-{index}",
                content=block,
                kind="summary_block",
                created_at=None,
                metadata={},
            )
            for index, block in enumerate(blocks, start=1)
        ]

    def _read_json(self, source_path: Path) -> list[NormalizedMessage]:
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {source_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("unsupported chat summary: expected an object")
        marker = payload.get("workprint_source") or payload.get("source_type")
        if marker not in {"chat-summary", "user-approved-chat-summary"}:
            raise ValueError("unsupported chat summary: missing chat-summary marker")

        summary_id = str(payload.get("id") or payload.get("summary_id") or source_path.stem)
        title = str(payload.get("title") or source_path.stem)
        approved_by_user = bool(
            payload.get("approved_by_user")
            or payload.get("user_approved")
            or payload.get("reviewed_by_user")
        )
        if not approved_by_user:
            raise ValueError("chat summary must be marked approved_by_user")

        created_at = _parse_timestamp(payload.get("created_at") or payload.get("approved_at"))
        metadata = self._summary_metadata(payload, approved_by_user=approved_by_user)
        messages: list[NormalizedMessage] = []

        summary_text = payload.get("summary") or payload.get("summary_text")
        if isinstance(summary_text, str) and summary_text.strip():
            messages.append(
                self._message(
                    source_path=source_path,
                    summary_id=summary_id,
                    title=title,
                    item_id="summary",
                    content=summary_text,
                    kind="summary",
                    created_at=created_at,
                    metadata=metadata,
                )
            )

        section_specs = (
            ("key_decisions", "decision"),
            ("user_direction", "user_direction"),
            ("ai_fluency_notes", "ai_fluency_note"),
            ("unknowns", "unknown"),
        )
        for field, kind in section_specs:
            for index, text in enumerate(_string_items(payload.get(field)), start=1):
                messages.append(
                    self._message(
                        source_path=source_path,
                        summary_id=summary_id,
                        title=title,
                        item_id=f"{field}-{index}",
                        content=text,
                        kind=kind,
                        created_at=created_at,
                        metadata=metadata,
                    )
                )

        if not messages:
            raise ValueError("chat summary contains no supported summary fields")
        return messages

    def _summary_metadata(
        self,
        payload: dict[str, Any],
        *,
        approved_by_user: bool,
    ) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "summary_evidence": True,
            "approved_by_user": approved_by_user,
            "not_full_transcript": True,
            "original_sources": _string_items(payload.get("original_sources")),
            "date_range": payload.get("date_range") if isinstance(payload.get("date_range"), dict) else {},
            "participants": _string_items(payload.get("participants")),
            "tools": _string_items(payload.get("tools")),
            "summary_method": str(payload.get("summary_method") or "user-provided"),
            "limitations": _string_items(payload.get("limitations")),
        }

    def _message(
        self,
        *,
        source_path: Path,
        summary_id: str,
        title: str,
        item_id: str,
        content: str,
        kind: str,
        created_at: Any,
        metadata: dict[str, Any],
    ) -> NormalizedMessage:
        return NormalizedMessage(
            id=item_id,
            conversation_id=summary_id,
            role="unknown",
            content=content.strip(),
            created_at=created_at,
            source=self.source_name,
            source_locator=f"{source_path.name}#{item_id}",
            metadata={
                **metadata,
                "summary_id": summary_id,
                "summary_title": title,
                "summary_item_id": item_id,
                "summary_item_kind": kind,
                "evidence_boundary": (
                    "This record is a user-approved summary, not the full chat transcript."
                ),
            },
        )


def _string_items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]

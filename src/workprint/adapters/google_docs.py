from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _split_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            current.append(stripped)
            continue
        if current:
            blocks.append(" ".join(current))
            current = []
    if current:
        blocks.append(" ".join(current))
    return blocks


def _title_from_markdown(blocks: list[str], fallback: str) -> str:
    for block in blocks:
        if block.startswith("#"):
            title = block.lstrip("#").strip()
            if title:
                return title
    return fallback


def _metadata_from_json(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "owners": payload.get("owners") or metadata.get("owners") or [],
        "authors": payload.get("authors") or metadata.get("authors") or [],
        "editors": payload.get("editors") or metadata.get("editors") or [],
        "created_at": payload.get("created_at") or metadata.get("created_at"),
        "modified_at": payload.get("modified_at") or metadata.get("modified_at"),
    }


class GoogleDocsAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read static Google Docs exports without inferring authorship."""

    source_name = "google-docs"
    source_type = "document"

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        source_path = self.validate_input(path)
        suffix = source_path.suffix.lower()
        if suffix == ".json":
            return self._read_json(source_path)
        if suffix == ".md":
            return self._read_text(source_path, export_format="markdown")
        if suffix == ".txt":
            return self._read_text(source_path, export_format="text")
        raise ValueError(
            f"unsupported Google Docs export format: {source_path.suffix}"
        )

    def _read_text(
        self,
        source_path: Path,
        export_format: str,
    ) -> list[NormalizedMessage]:
        text = source_path.read_text(encoding="utf-8")
        blocks = _split_blocks(text)
        title = (
            _title_from_markdown(blocks, source_path.stem)
            if export_format == "markdown"
            else source_path.stem
        )
        document_id = source_path.stem
        return [
            self._message(
                source_path=source_path,
                document_id=document_id,
                title=title,
                block_id=f"paragraph-{index}",
                index=index,
                content=block,
                created_at=None,
                export_format=export_format,
                document_metadata={},
            )
            for index, block in enumerate(blocks, start=1)
        ]

    def _read_json(self, source_path: Path) -> list[NormalizedMessage]:
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {source_path}") from exc

        if not isinstance(payload, dict):
            raise ValueError("unsupported Google Docs export: expected an object")

        document_id = str(
            payload.get("id")
            or payload.get("document_id")
            or source_path.stem
        )
        title = str(payload.get("title") or source_path.stem)
        document_metadata = _metadata_from_json(payload)
        created_at = _parse_timestamp(document_metadata.get("created_at"))

        paragraphs = payload.get("paragraphs")
        body = payload.get("body")
        if isinstance(paragraphs, list):
            blocks = self._json_blocks(paragraphs)
        elif isinstance(body, str):
            blocks = [
                {"id": f"paragraph-{index}", "text": text}
                for index, text in enumerate(_split_blocks(body), start=1)
            ]
        else:
            raise ValueError(
                "unsupported Google Docs export: expected paragraphs or body"
            )

        return [
            self._message(
                source_path=source_path,
                document_id=document_id,
                title=title,
                block_id=str(block["id"]),
                index=index,
                content=str(block["text"]).strip(),
                created_at=created_at,
                export_format="json",
                document_metadata=document_metadata,
                block_metadata=block.get("metadata", {}),
            )
            for index, block in enumerate(blocks, start=1)
            if str(block["text"]).strip()
        ]

    @staticmethod
    def _json_blocks(paragraphs: list[Any]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for index, item in enumerate(paragraphs, start=1):
            if isinstance(item, str):
                blocks.append({"id": f"paragraph-{index}", "text": item})
                continue
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    blocks.append(
                        {
                            "id": item.get("id") or f"paragraph-{index}",
                            "text": text,
                            "metadata": item.get("metadata") or {},
                        }
                    )
        if not blocks:
            raise ValueError(
                "unsupported Google Docs export: no paragraph text found"
            )
        return blocks

    def _message(
        self,
        source_path: Path,
        document_id: str,
        title: str,
        block_id: str,
        index: int,
        content: str,
        created_at: datetime | None,
        export_format: str,
        document_metadata: dict[str, Any],
        block_metadata: dict[str, Any] | None = None,
    ) -> NormalizedMessage:
        return NormalizedMessage(
            id=block_id,
            conversation_id=document_id,
            role="unknown",
            content=content.strip(),
            created_at=created_at,
            source=self.source_name,
            source_locator=f"{source_path.name}#paragraph/{index}",
            metadata={
                "document_id": document_id,
                "document_title": title,
                "block_id": block_id,
                "block_index": index,
                "export_format": export_format,
                "source_type": self.source_type,
                "document_metadata": document_metadata,
                "block_metadata": block_metadata or {},
            },
        )

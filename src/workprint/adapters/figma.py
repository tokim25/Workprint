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


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _metadata(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _explicit_evidence(value: dict[str, Any]) -> dict[str, Any]:
    evidence = value.get("evidence")
    if isinstance(evidence, dict):
        return evidence
    metadata = _metadata(value.get("metadata"))
    evidence = metadata.get("evidence")
    return evidence if isinstance(evidence, dict) else {}


def _node_type(value: dict[str, Any]) -> str:
    return _text(value.get("type")).upper()


def _component_metadata(value: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "component_key",
        "component_name",
        "component_id",
        "main_component",
        "instance_of",
        "variant",
    )
    return {
        key: value.get(key)
        for key in keys
        if value.get(key) not in (None, "", [], {})
    }


class FigmaAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read static Figma JSON exports without inferring authorship."""

    source_name = "figma"
    source_type = "design"

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        source_path = self.validate_input(path)
        if source_path.suffix.lower() != ".json":
            raise ValueError(
                f"unsupported Figma export format: {source_path.suffix}"
            )

        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {source_path}") from exc

        if not isinstance(payload, dict):
            raise ValueError("unsupported Figma export: expected an object")

        file_id = str(
            payload.get("file_key")
            or payload.get("file_id")
            or payload.get("key")
            or payload.get("id")
            or source_path.stem
        )
        file_metadata = self._file_metadata(payload)
        pages = payload.get("pages")
        if not isinstance(pages, list):
            document = payload.get("document")
            if isinstance(document, dict):
                pages = document.get("children")
        if not isinstance(pages, list):
            raise ValueError("unsupported Figma export: expected pages")

        records: list[NormalizedMessage] = []
        for page_index, page in enumerate(pages, start=1):
            if not isinstance(page, dict):
                continue
            page_id = str(page.get("id") or f"page-{page_index}")
            page_name = _text(page.get("name")) or f"Page {page_index}"
            page_path = (page_name,)
            page_metadata = self._page_metadata(page, page_id, page_name)

            if self._is_meaningful_page(page):
                records.append(
                    self._message(
                        source_path=source_path,
                        file_id=file_id,
                        record_id=page_id,
                        locator=f"{source_path.name}#page/{page_id}",
                        content=self._page_content(page, page_name),
                        created_at=_parse_timestamp(page.get("last_modified")),
                        file_metadata=file_metadata,
                        page_metadata=page_metadata,
                        node_metadata={},
                        hierarchy={
                            "file": file_metadata,
                            "page": page_metadata,
                            "node_path": list(page_path),
                        },
                    )
                )

            for node_index, node in enumerate(_list(page.get("nodes") or page.get("children")), start=1):
                records.extend(
                    self._read_node(
                        source_path=source_path,
                        file_id=file_id,
                        file_metadata=file_metadata,
                        page_metadata=page_metadata,
                        page_id=page_id,
                        node=node,
                        index_path=(node_index,),
                        name_path=page_path,
                        parent_id=None,
                    )
                )

        records.sort(
            key=lambda item: (
                item.created_at is None,
                item.created_at or datetime.max.replace(tzinfo=timezone.utc),
                item.source_locator,
                item.id,
            )
        )
        return records

    def _read_node(
        self,
        source_path: Path,
        file_id: str,
        file_metadata: dict[str, Any],
        page_metadata: dict[str, Any],
        page_id: str,
        node: Any,
        index_path: tuple[int, ...],
        name_path: tuple[str, ...],
        parent_id: str | None,
    ) -> list[NormalizedMessage]:
        if not isinstance(node, dict):
            return []

        node_id = str(node.get("id") or "node-" + "-".join(map(str, index_path)))
        node_name = _text(node.get("name")) or node_id
        current_path = (*name_path, node_name)
        node_metadata = self._node_metadata(node, node_id, parent_id, current_path)
        records: list[NormalizedMessage] = []

        if self._is_meaningful_node(node):
            records.append(
                self._message(
                    source_path=source_path,
                    file_id=file_id,
                    record_id=node_id,
                    locator=(
                        f"{source_path.name}#page/{page_id}/node/{node_id}"
                    ),
                    content=self._node_content(node, node_name),
                    created_at=_parse_timestamp(node.get("last_modified")),
                    file_metadata=file_metadata,
                    page_metadata=page_metadata,
                    node_metadata=node_metadata,
                    hierarchy={
                        "file": file_metadata,
                        "page": page_metadata,
                        "node": node_metadata,
                        "node_path": list(current_path),
                    },
                )
            )

        for child_index, child in enumerate(_list(node.get("children") or node.get("nodes")), start=1):
            records.extend(
                self._read_node(
                    source_path=source_path,
                    file_id=file_id,
                    file_metadata=file_metadata,
                    page_metadata=page_metadata,
                    page_id=page_id,
                    node=child,
                    index_path=(*index_path, child_index),
                    name_path=current_path,
                    parent_id=node_id,
                )
            )

        return records

    @staticmethod
    def _file_metadata(payload: dict[str, Any]) -> dict[str, Any]:
        metadata = _metadata(payload.get("metadata"))
        return {
            "file_key": payload.get("file_key") or payload.get("key"),
            "file_id": payload.get("file_id") or payload.get("id"),
            "file_name": payload.get("name"),
            "last_modified": payload.get("last_modified"),
            "owner": payload.get("owner") or metadata.get("owner"),
            "editors": payload.get("editors") or metadata.get("editors") or [],
            "contributors": (
                payload.get("contributors")
                or metadata.get("contributors")
                or []
            ),
            "schema_version": payload.get("schema_version"),
        }

    @staticmethod
    def _page_metadata(
        page: dict[str, Any],
        page_id: str,
        page_name: str,
    ) -> dict[str, Any]:
        return {
            "page_id": page_id,
            "page_name": page_name,
            "page_type": page.get("type"),
            "last_modified": page.get("last_modified"),
            "description": page.get("description"),
            "metadata": _metadata(page.get("metadata")),
        }

    @staticmethod
    def _node_metadata(
        node: dict[str, Any],
        node_id: str,
        parent_id: str | None,
        node_path: tuple[str, ...],
    ) -> dict[str, Any]:
        return {
            "node_id": node_id,
            "node_name": node.get("name"),
            "node_type": node.get("type"),
            "parent_id": parent_id or node.get("parent_id"),
            "node_path": list(node_path),
            "last_modified": node.get("last_modified"),
            "visible": node.get("visible"),
            "locked": node.get("locked"),
            "description": node.get("description"),
            "characters": node.get("characters") or node.get("text"),
            "component": _component_metadata(node),
            "metadata": _metadata(node.get("metadata")),
            "evidence": _explicit_evidence(node),
        }

    @staticmethod
    def _is_meaningful_page(page: dict[str, Any]) -> bool:
        return bool(_text(page.get("description")) or _explicit_evidence(page))

    @staticmethod
    def _is_meaningful_node(node: dict[str, Any]) -> bool:
        return bool(
            _text(node.get("characters"))
            or _text(node.get("text"))
            or _text(node.get("description"))
            or _component_metadata(node)
            or _explicit_evidence(node)
        )

    @staticmethod
    def _page_content(page: dict[str, Any], page_name: str) -> str:
        evidence = _explicit_evidence(page)
        description = _text(page.get("description"))
        if description:
            return f"Figma page {page_name}: {description}"
        if evidence:
            return f"Figma page {page_name}: explicit evidence metadata present."
        return f"Figma page {page_name}"

    @staticmethod
    def _node_content(node: dict[str, Any], node_name: str) -> str:
        node_type = _node_type(node) or "NODE"
        text = _text(node.get("characters")) or _text(node.get("text"))
        description = _text(node.get("description"))
        component = _component_metadata(node)
        evidence = _explicit_evidence(node)

        parts = [f"Figma {node_type.lower()} {node_name}"]
        if text:
            parts.append(f"text: {text}")
        if description:
            parts.append(f"description: {description}")
        if component:
            rendered = ", ".join(f"{key}={value}" for key, value in sorted(component.items()))
            parts.append(f"component metadata: {rendered}")
        if evidence:
            parts.append("explicit evidence metadata present")
        return "; ".join(parts)

    def _message(
        self,
        source_path: Path,
        file_id: str,
        record_id: str,
        locator: str,
        content: str,
        created_at: datetime | None,
        file_metadata: dict[str, Any],
        page_metadata: dict[str, Any],
        node_metadata: dict[str, Any],
        hierarchy: dict[str, Any],
    ) -> NormalizedMessage:
        return NormalizedMessage(
            id=record_id,
            conversation_id=file_id,
            role="unknown",
            content=content,
            created_at=created_at,
            source=self.source_name,
            source_locator=locator,
            metadata={
                "source_type": self.source_type,
                "export_format": "json",
                "file_metadata": file_metadata,
                "page_metadata": page_metadata,
                "node_metadata": node_metadata,
                "hierarchy": hierarchy,
            },
        )

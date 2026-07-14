from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workprint.models import NormalizedMessage


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    return None


def _extract_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts")
    if isinstance(parts, list):
        rendered: list[str] = []
        for part in parts:
            if isinstance(part, str):
                rendered.append(part)
            elif isinstance(part, dict):
                text = part.get("text") or part.get("content")
                if isinstance(text, str):
                    rendered.append(text)
        return "\n".join(item for item in rendered if item).strip()

    text = content.get("text")
    return text if isinstance(text, str) else ""


def _role(message: dict[str, Any]) -> str:
    author = message.get("author")
    raw = author.get("role") if isinstance(author, dict) else message.get("role")
    return {
        "user": "human",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
    }.get(str(raw), "unknown")


class ChatGPTAdapter:
    source_name = "ChatGPT"

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        source_path = Path(path)
        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"file not found: {source_path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {source_path}") from exc

        conversations = payload if isinstance(payload, list) else [payload]
        results: list[NormalizedMessage] = []

        for index, conversation in enumerate(conversations):
            if not isinstance(conversation, dict):
                continue
            conversation_id = str(
                conversation.get("id")
                or conversation.get("conversation_id")
                or f"conversation-{index + 1}"
            )
            mapping = conversation.get("mapping")
            if isinstance(mapping, dict):
                results.extend(
                    self._read_mapping(conversation_id, mapping, source_path.name)
                )
            else:
                messages = conversation.get("messages")
                if isinstance(messages, list):
                    results.extend(
                        self._read_message_list(
                            conversation_id, messages, source_path.name
                        )
                    )

        results.sort(key=lambda item: (
            item.created_at is None,
            item.created_at or datetime.max.replace(tzinfo=timezone.utc),
            item.id,
        ))
        return results

    def _read_mapping(
        self,
        conversation_id: str,
        mapping: dict[str, Any],
        filename: str,
    ) -> list[NormalizedMessage]:
        messages: list[NormalizedMessage] = []
        for node_id, node in mapping.items():
            if not isinstance(node, dict):
                continue
            message = node.get("message")
            if not isinstance(message, dict):
                continue
            text = _extract_text(message)
            if not text.strip():
                continue
            message_id = str(message.get("id") or node_id)
            messages.append(
                NormalizedMessage(
                    id=message_id,
                    conversation_id=conversation_id,
                    role=_role(message),
                    content=text.strip(),
                    created_at=_parse_timestamp(message.get("create_time")),
                    source=self.source_name,
                    source_locator=f"{filename}#mapping/{node_id}",
                    metadata={
                        "parent": node.get("parent"),
                        "children": node.get("children") or [],
                    },
                )
            )
        return messages

    def _read_message_list(
        self,
        conversation_id: str,
        messages: list[Any],
        filename: str,
    ) -> list[NormalizedMessage]:
        results: list[NormalizedMessage] = []
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            text = _extract_text(message)
            if not text.strip():
                continue
            message_id = str(message.get("id") or f"{conversation_id}-message-{index + 1}")
            results.append(
                NormalizedMessage(
                    id=message_id,
                    conversation_id=conversation_id,
                    role=_role(message),
                    content=text.strip(),
                    created_at=_parse_timestamp(
                        message.get("create_time") or message.get("created_at")
                    ),
                    source=self.source_name,
                    source_locator=f"{filename}#messages/{index}",
                    metadata={},
                )
            )
        return results

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter


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
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None
    return None


def _extract_text(message: dict[str, Any]) -> str:
    content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                item_type = item.get("type")
                text = item.get("text")
                if item_type in {None, "text"} and isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part).strip()

    text = message.get("text")
    return text.strip() if isinstance(text, str) else ""


def _normalize_role(message: dict[str, Any]) -> str:
    raw = (
        message.get("role")
        or message.get("sender")
        or message.get("author")
        or message.get("type")
    )
    if isinstance(raw, dict):
        raw = raw.get("role") or raw.get("name")
    return {
        "user": "human",
        "human": "human",
        "assistant": "assistant",
        "claude": "assistant",
        "system": "system",
        "tool": "tool",
    }.get(str(raw).lower(), "unknown")


class ClaudeAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read common Claude conversation export shapes."""

    source_name = "Claude"
    source_type = "conversation"

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
        source_path = self.validate_input(path)

        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {source_path}") from exc

        conversations = self._conversation_list(payload)
        results: list[NormalizedMessage] = []

        for index, conversation in enumerate(conversations):
            if not isinstance(conversation, dict):
                continue

            conversation_id = str(
                conversation.get("uuid")
                or conversation.get("id")
                or conversation.get("conversation_id")
                or f"conversation-{index + 1}"
            )
            messages = (
                conversation.get("chat_messages")
                or conversation.get("messages")
                or conversation.get("conversation")
                or []
            )

            if not isinstance(messages, list):
                continue

            for message_index, message in enumerate(messages):
                if not isinstance(message, dict):
                    continue

                text = _extract_text(message)
                if not text:
                    continue

                message_id = str(
                    message.get("uuid")
                    or message.get("id")
                    or f"{conversation_id}-message-{message_index + 1}"
                )
                created_at = _parse_timestamp(
                    message.get("created_at")
                    or message.get("timestamp")
                    or message.get("create_time")
                )

                results.append(
                    NormalizedMessage(
                        id=message_id,
                        conversation_id=conversation_id,
                        role=_normalize_role(message),
                        content=text,
                        created_at=created_at,
                        source=self.source_name,
                        source_locator=(
                            f"{source_path.name}#conversation/{conversation_id}"
                            f"/messages/{message_index}"
                        ),
                        metadata={
                            "conversation_name": (
                                conversation.get("name")
                                or conversation.get("title")
                                or conversation.get("summary")
                            ),
                            "message_index": message_index,
                        },
                    )
                )

        results.sort(
            key=lambda item: (
                item.created_at is None,
                item.created_at
                or datetime.max.replace(tzinfo=timezone.utc),
                item.conversation_id,
                item.id,
            )
        )
        return results

    @staticmethod
    def _conversation_list(payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload

        if not isinstance(payload, dict):
            raise ValueError(
                "unsupported Claude export: expected a conversation object or list"
            )

        conversations = payload.get("conversations")
        if isinstance(conversations, list):
            return conversations

        if any(
            key in payload
            for key in ("chat_messages", "messages", "conversation")
        ):
            return [payload]

        raise ValueError(
            "unsupported Claude export: no conversations or messages found"
        )

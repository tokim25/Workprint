from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from workprint.conversations import NormalizedMessage
from workprint.models import Observation

from .base import ConversationAdapter
from .extractor import extract_observations


class ClaudeAdapterError(ValueError):
    """Raised when a Claude export cannot be normalized."""


class ClaudeAdapter(ConversationAdapter):
    """Normalize common Claude conversation export JSON shapes.

    Supported inputs:
    - an array of conversation objects;
    - an object containing a ``conversations`` array;
    - a single conversation object.

    Conversation messages may be stored in ``chat_messages`` or ``messages``.
    Text may be a string, a list of content blocks, or a ``content`` field.
    """

    source_name = "Claude"

    def read(self, path: Path) -> list[NormalizedMessage]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ClaudeAdapterError(f"Unable to read Claude export: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ClaudeAdapterError(f"Claude export is not valid JSON: {exc}") from exc

        conversations = _conversation_list(payload)
        messages: list[NormalizedMessage] = []
        for conversation_index, conversation in enumerate(conversations, start=1):
            if not isinstance(conversation, dict):
                raise ClaudeAdapterError("Each Claude conversation must be an object")
            conversation_id = str(
                conversation.get("uuid")
                or conversation.get("id")
                or f"conversation-{conversation_index}"
            )
            title = conversation.get("name") or conversation.get("title")
            raw_messages = conversation.get("chat_messages", conversation.get("messages", []))
            if not isinstance(raw_messages, list):
                raise ClaudeAdapterError(
                    f"Conversation {conversation_id} messages must be an array"
                )

            for message_index, raw in enumerate(raw_messages, start=1):
                if not isinstance(raw, dict):
                    continue
                role = _role(raw)
                text = _text(raw)
                if not text.strip():
                    continue
                message_id = str(
                    raw.get("uuid")
                    or raw.get("id")
                    or f"message-{message_index}"
                )
                created_at = _timestamp(
                    raw.get("created_at")
                    or raw.get("createdAt")
                    or raw.get("timestamp")
                )
                messages.append(
                    NormalizedMessage(
                        id=message_id,
                        conversation_id=conversation_id,
                        actor="Human" if role == "human" else "Claude",
                        role=role,
                        text=text,
                        created_at=created_at,
                        source_locator=f"claude:{conversation_id}:{message_id}",
                        metadata={
                            "conversation_title": title,
                            "sender_raw": raw.get("sender") or raw.get("role"),
                        },
                    )
                )

        if not messages:
            raise ClaudeAdapterError("Claude export contained no readable messages")
        return messages

    def to_observations(
        self, messages: list[NormalizedMessage]
    ) -> list[Observation]:
        return extract_observations(messages, self.source_name)


def _conversation_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ClaudeAdapterError("Claude export must be an object or array")
    if isinstance(payload.get("conversations"), list):
        return payload["conversations"]
    if "chat_messages" in payload or "messages" in payload:
        return [payload]
    raise ClaudeAdapterError("Claude export does not contain conversations or messages")


def _role(message: dict[str, Any]) -> str:
    raw = str(message.get("sender") or message.get("role") or "").lower()
    if raw in {"human", "user"}:
        return "human"
    if raw in {"assistant", "claude", "ai"}:
        return "assistant"
    return "assistant" if raw else "unknown"


def _text(message: dict[str, Any]) -> str:
    value = message.get("text")
    if value is None:
        value = message.get("content")
    return _flatten_text(value)


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(parts)
    if isinstance(value, dict):
        return _flatten_text(value.get("text") or value.get("content"))
    return ""


def _timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        # Claude exports may use Unix seconds or milliseconds.
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000
        return datetime.fromtimestamp(seconds).astimezone()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None

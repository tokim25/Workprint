from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NormalizedMessage:
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime | None
    source: str
    source_locator: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("message id is required")
        if self.role not in {"human", "assistant", "system", "tool", "unknown"}:
            raise ValueError(f"unsupported role: {self.role}")
        if not isinstance(self.content, str):
            raise TypeError("content must be a string")

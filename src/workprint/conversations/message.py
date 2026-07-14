from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class NormalizedMessage:
    """Vendor-neutral conversation message used by evidence adapters."""

    id: str
    conversation_id: str
    actor: str
    role: str
    text: str
    created_at: datetime | None = None
    source_locator: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

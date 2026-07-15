from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


ACTIVITIES = {
    "question",
    "suggestion",
    "evaluation",
    "decision",
    "implementation",
    "artifact",
    "observation",
    "unknown",
}

RELIABILITY_LEVELS = {"high", "medium", "low", "unknown"}


@dataclass(frozen=True)
class Observation:
    id: str
    timestamp: datetime | None
    source: str
    source_type: str
    actor: str
    activity: str
    statement: str
    evidence_refs: tuple[str, ...]
    artifact: str | None = None
    reliability: str = "high"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("observation id is required")
        if self.activity not in ACTIVITIES:
            raise ValueError(f"unsupported activity: {self.activity}")
        if self.reliability not in RELIABILITY_LEVELS:
            raise ValueError(f"unsupported reliability: {self.reliability}")
        if not self.statement.strip():
            raise ValueError("statement is required")
        if not self.evidence_refs:
            raise ValueError("at least one evidence reference is required")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        data["evidence_refs"] = list(self.evidence_refs)
        data["metadata"] = self.metadata or {}
        return data

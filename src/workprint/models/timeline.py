from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


INVOLVEMENT_ACTIVITIES = {
    "initiated",
    "directed",
    "contributed",
    "reviewed",
    "decided",
    "executed",
}

INVOLVEMENT_STATUSES = {"measured", "estimated", "unknown"}

ACTIVITY_CATEGORIES = {
    "user_activity",
    "collaborator_activity",
    "ai_tool_activity",
    "joint_activity",
    "unattributed_activity",
}


@dataclass(frozen=True)
class TimelineInvolvement:
    activity: str
    status: str
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.activity not in INVOLVEMENT_ACTIVITIES:
            raise ValueError(f"unsupported involvement activity: {self.activity}")
        if self.status not in INVOLVEMENT_STATUSES:
            raise ValueError(f"unsupported involvement status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "activity": self.activity,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    start_time: datetime | None
    end_time: datetime | None
    stage: str
    title: str
    description: str
    source_observation_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    confidence: str
    user_involvement: tuple[TimelineInvolvement, ...]
    activity_breakdown: dict[str, tuple[str, ...]]
    attribution_limits: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("timeline event id is required")
        if not self.stage.strip():
            raise ValueError("timeline event stage is required")
        if not self.title.strip():
            raise ValueError("timeline event title is required")
        if not self.description.strip():
            raise ValueError("timeline event description is required")
        if not self.source_observation_ids:
            raise ValueError("timeline event requires at least one observation")
        if not self.evidence_refs:
            raise ValueError("timeline event requires at least one evidence reference")
        unknown_categories = set(self.activity_breakdown) - ACTIVITY_CATEGORIES
        if unknown_categories:
            unknown = ", ".join(sorted(unknown_categories))
            raise ValueError(f"unsupported activity categories: {unknown}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "stage": self.stage,
            "title": self.title,
            "description": self.description,
            "source_observation_ids": list(self.source_observation_ids),
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "user_involvement": [
                item.to_dict() for item in self.user_involvement
            ],
            "activity_breakdown": {
                key: list(value)
                for key, value in sorted(self.activity_breakdown.items())
            },
            "attribution_limits": list(self.attribution_limits),
        }

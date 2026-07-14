from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping


class ObservationError(ValueError):
    """Raised when an observation record is invalid."""


class Reliability(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Completeness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Observation:
    """Canonical normalized record consumed by the Workprint engine.

    Adapters should convert source-specific evidence into this model. The model
    intentionally stores a concise observation plus a stable source locator,
    rather than duplicating the full raw source content.
    """

    id: str
    source_type: str
    observation: str
    reliability: Reliability
    event_time: datetime | None = None
    source_name: str | None = None
    source_locator: str | None = None
    observed_at: datetime | None = None
    actor: str | None = None
    activity: str | None = None
    artifact: str | None = None
    completeness: Completeness = Completeness.UNKNOWN
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required_string(self.id, "id"))
        object.__setattr__(
            self, "source_type", _required_string(self.source_type, "source_type")
        )
        object.__setattr__(
            self, "observation", _required_string(self.observation, "observation")
        )
        object.__setattr__(self, "source_name", _optional_string(self.source_name))
        object.__setattr__(
            self, "source_locator", _optional_string(self.source_locator)
        )
        object.__setattr__(self, "actor", _optional_string(self.actor))
        object.__setattr__(
            self, "activity", _optional_string(self.activity, lower=True)
        )
        object.__setattr__(self, "artifact", _optional_string(self.artifact))
        object.__setattr__(self, "notes", _optional_string(self.notes))

        if not isinstance(self.reliability, Reliability):
            try:
                object.__setattr__(
                    self, "reliability", Reliability(str(self.reliability).lower())
                )
            except ValueError as exc:
                raise ObservationError(
                    f"Observation {self.id} has invalid reliability: {self.reliability}"
                ) from exc

        if not isinstance(self.completeness, Completeness):
            try:
                object.__setattr__(
                    self,
                    "completeness",
                    Completeness(str(self.completeness).lower()),
                )
            except ValueError as exc:
                raise ObservationError(
                    f"Observation {self.id} has invalid completeness: {self.completeness}"
                ) from exc

        if not isinstance(self.metadata, dict):
            raise ObservationError(f"Observation {self.id} metadata must be an object")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_dict(cls, record: Mapping[str, Any]) -> "Observation":
        """Build an Observation from a JSON-compatible mapping."""

        if not isinstance(record, Mapping):
            raise ObservationError("Observation input must be an object")

        return cls(
            id=record.get("id", ""),
            source_type=record.get("source_type", ""),
            observation=record.get("observation", ""),
            reliability=record.get("reliability", Reliability.UNKNOWN),
            event_time=_parse_datetime(record.get("event_time"), record.get("id")),
            source_name=record.get("source_name"),
            source_locator=record.get("source_locator"),
            observed_at=_parse_datetime(record.get("observed_at"), record.get("id")),
            actor=record.get("actor"),
            activity=record.get("activity"),
            artifact=record.get("artifact"),
            completeness=record.get("completeness", Completeness.UNKNOWN),
            notes=record.get("notes"),
            metadata=record.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation using the canonical schema."""

        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "source_locator": self.source_locator,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "actor": self.actor,
            "activity": self.activity,
            "artifact": self.artifact,
            "observation": self.observation,
            "reliability": self.reliability.value,
            "completeness": self.completeness.value,
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


def _parse_datetime(value: Any, observation_id: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ObservationError(
            f"Observation {observation_id or '<unknown>'} timestamp must be a string"
        )
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationError(
            f"Observation {observation_id or '<unknown>'} has invalid ISO-8601 timestamp: {value}"
        ) from exc


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObservationError(f"Observation is missing required field: {field_name}")
    return value.strip()


def _optional_string(value: Any, lower: bool = False) -> str | None:
    if value in (None, ""):
        return None
    result = str(value).strip()
    if not result:
        return None
    return result.lower() if lower else result

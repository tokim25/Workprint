from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .observation import Observation
from .timeline import TimelineEvent


@dataclass(frozen=True)
class Investigation:
    project: str
    source_files: tuple[str, ...]
    observations: tuple[Observation, ...]
    findings: tuple[dict[str, Any], ...]
    unknowns: tuple[str, ...]
    limitations: tuple[str, ...]
    timeline: tuple[TimelineEvent, ...] = ()
    timeline_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "source_files": list(self.source_files),
            "observations": [item.to_dict() for item in self.observations],
            "timeline": [item.to_dict() for item in self.timeline],
            "timeline_summary": self.timeline_summary,
            "findings": list(self.findings),
            "unknowns": list(self.unknowns),
            "limitations": list(self.limitations),
        }

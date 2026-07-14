from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable


class InvestigationError(ValueError):
    """Raised when investigation input is invalid."""


VALID_CONFIDENCE = {"high", "medium", "low", "unknown"}
VALID_CLASSIFICATIONS = {"measured", "estimated", "qualitative", "unknown"}
DECISION_ACTIVITIES = {"decision", "adoption", "rejection"}


@dataclass(frozen=True)
class Event:
    id: str
    event_time: datetime | None
    source_type: str
    source_locator: str | None
    actor: str | None
    activity: str | None
    artifact: str | None
    observation: str
    reliability: str
    completeness: str
    notes: str | None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "Event":
        for field in ("id", "source_type", "observation", "reliability"):
            if not record.get(field):
                raise InvestigationError(f"Evidence record is missing required field: {field}")

        reliability = str(record["reliability"]).lower()
        if reliability not in VALID_CONFIDENCE:
            raise InvestigationError(
                f"Evidence {record['id']} has invalid reliability: {reliability}"
            )

        event_time = _parse_datetime(record.get("event_time"), record["id"])
        return cls(
            id=str(record["id"]),
            event_time=event_time,
            source_type=str(record["source_type"]),
            source_locator=_optional_string(record.get("source_locator")),
            actor=_optional_string(record.get("actor")),
            activity=_optional_string(record.get("activity"), lower=True),
            artifact=_optional_string(record.get("artifact")),
            observation=str(record["observation"]).strip(),
            reliability=reliability,
            completeness=str(record.get("completeness", "unknown")).lower(),
            notes=_optional_string(record.get("notes")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "source_type": self.source_type,
            "source_locator": self.source_locator,
            "actor": self.actor,
            "activity": self.activity,
            "artifact": self.artifact,
            "observation": self.observation,
            "reliability": self.reliability,
            "completeness": self.completeness,
            "notes": self.notes,
        }


class InvestigationEngine:
    """Build a reproducible investigation from normalized evidence records."""

    def __init__(self, session_gap_minutes: int = 30) -> None:
        if session_gap_minutes < 1:
            raise InvestigationError("session_gap_minutes must be at least 1")
        self.session_gap = timedelta(minutes=session_gap_minutes)

    def investigate(self, payload: dict[str, Any]) -> dict[str, Any]:
        project = str(payload.get("project", "Untitled project")).strip()
        scope = str(payload.get("scope", "Available supplied evidence")).strip()
        records = payload.get("evidence")
        if not isinstance(records, list) or not records:
            raise InvestigationError("Input must contain a non-empty evidence array")

        events = [Event.from_record(record) for record in records]
        ids = [event.id for event in events]
        if len(ids) != len(set(ids)):
            raise InvestigationError("Evidence IDs must be unique")

        timeline = sorted(
            events,
            key=lambda event: (
                event.event_time is None,
                event.event_time or datetime.max,
                event.id,
            ),
        )

        decisions = self._extract_decisions(timeline)
        sessions = self._build_sessions(timeline)
        findings = self._build_findings(timeline, decisions, sessions)
        unknowns = self._build_unknowns(timeline, sessions)
        coverage = self._coverage_summary(timeline)

        return {
            "project": project,
            "scope": scope,
            "engine_version": "0.1.0",
            "evidence_count": len(events),
            "evidence_coverage": coverage,
            "timeline": [event.to_dict() for event in timeline],
            "decisions": decisions,
            "sessions": sessions,
            "findings": findings,
            "unknowns": unknowns,
            "limitations": [
                "The engine analyzes normalized evidence and does not verify source authenticity.",
                "A recorded AI response does not prove that its contents were adopted.",
                "Activity timestamps do not measure unrecorded or offline work.",
            ],
        }

    def _extract_decisions(self, timeline: Iterable[Event]) -> list[dict[str, Any]]:
        decisions: list[dict[str, Any]] = []
        for event in timeline:
            if event.activity not in DECISION_ACTIVITIES:
                continue
            decisions.append(
                {
                    "id": f"D-{len(decisions) + 1:03d}",
                    "event_id": event.id,
                    "date": event.event_time.isoformat() if event.event_time else None,
                    "actor": event.actor or "Unknown",
                    "outcome": event.activity,
                    "decision": event.observation,
                    "artifact": event.artifact,
                    "confidence": event.reliability,
                    "evidence": [event.id],
                }
            )
        return decisions

    def _build_sessions(self, timeline: Iterable[Event]) -> list[dict[str, Any]]:
        timed = [event for event in timeline if event.event_time is not None]
        if not timed:
            return []

        groups: list[list[Event]] = [[timed[0]]]
        for event in timed[1:]:
            previous = groups[-1][-1]
            assert previous.event_time is not None and event.event_time is not None
            if event.event_time - previous.event_time <= self.session_gap:
                groups[-1].append(event)
            else:
                groups.append([event])

        sessions: list[dict[str, Any]] = []
        for index, group in enumerate(groups, start=1):
            start = group[0].event_time
            end = group[-1].event_time
            assert start is not None and end is not None
            observed_minutes = int((end - start).total_seconds() // 60)
            sessions.append(
                {
                    "id": f"S-{index:03d}",
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "event_ids": [event.id for event in group],
                    "event_count": len(group),
                    "observed_span_minutes": observed_minutes,
                    "classification": "measured" if len(group) > 1 else "unknown",
                    "note": (
                        "Observed span between multiple timestamped events."
                        if len(group) > 1
                        else "A single timestamp does not establish duration."
                    ),
                }
            )
        return sessions

    def _build_findings(
        self,
        timeline: list[Event],
        decisions: list[dict[str, Any]],
        sessions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []

        actor_events: dict[str, list[Event]] = {}
        for event in timeline:
            actor_events.setdefault(event.actor or "Unknown", []).append(event)

        for actor, events in sorted(actor_events.items()):
            activities = sorted({event.activity for event in events if event.activity})
            if not activities:
                continue
            reliability = _lowest_confidence(event.reliability for event in events)
            findings.append(
                {
                    "id": f"F-{len(findings) + 1:03d}",
                    "statement": f"{actor} is recorded performing: {', '.join(activities)}.",
                    "evidence_ids": [event.id for event in events],
                    "reasoning": "The listed activities are directly present in normalized evidence records.",
                    "confidence": reliability,
                    "classification": "qualitative",
                    "alternative_explanations": [
                        "The evidence may omit unrecorded contributors or activities."
                    ],
                }
            )

        if decisions:
            findings.append(
                {
                    "id": f"F-{len(findings) + 1:03d}",
                    "statement": f"The evidence contains {len(decisions)} explicit decision event(s).",
                    "evidence_ids": [decision["event_id"] for decision in decisions],
                    "reasoning": "Events classified as decision, adoption, or rejection are treated as explicit decision records.",
                    "confidence": _lowest_confidence(
                        decision["confidence"] for decision in decisions
                    ),
                    "classification": "measured",
                    "alternative_explanations": [],
                }
            )

        multi_event_sessions = [session for session in sessions if session["event_count"] > 1]
        if multi_event_sessions:
            total_span = sum(session["observed_span_minutes"] for session in multi_event_sessions)
            evidence_ids = [
                event_id
                for session in multi_event_sessions
                for event_id in session["event_ids"]
            ]
            findings.append(
                {
                    "id": f"F-{len(findings) + 1:03d}",
                    "statement": f"Timestamped evidence contains {total_span} minute(s) of observed multi-event session span.",
                    "evidence_ids": evidence_ids,
                    "reasoning": (
                        "Events no more than "
                        f"{int(self.session_gap.total_seconds() // 60)} minutes apart were grouped into sessions. "
                        "This is an observed span, not total active time."
                    ),
                    "confidence": "medium",
                    "classification": "estimated",
                    "alternative_explanations": [
                        "The contributor may have been idle during gaps.",
                        "Work may have occurred before, after, or between recorded events.",
                    ],
                }
            )

        return findings

    def _build_unknowns(
        self, timeline: list[Event], sessions: list[dict[str, Any]]
    ) -> list[str]:
        unknowns = [
            "Exact thinking, reading, and offline planning time cannot be determined from event records alone.",
            "The engine cannot determine whether every AI-generated artifact was reviewed, used, or discarded unless evidence records that outcome.",
        ]
        if any(event.event_time is None for event in timeline):
            unknowns.append("Some events have no event timestamp, so their exact chronology is unknown.")
        if not sessions or all(session["event_count"] == 1 for session in sessions):
            unknowns.append("Available timestamps are too sparse to estimate active work sessions.")
        if any((event.actor or "Unknown") == "Unknown" for event in timeline):
            unknowns.append("At least one event has no attributable actor.")
        return unknowns

    def _coverage_summary(self, timeline: list[Event]) -> dict[str, Any]:
        total = len(timeline)
        timed = sum(event.event_time is not None for event in timeline)
        attributed = sum(bool(event.actor) for event in timeline)
        located = sum(bool(event.source_locator) for event in timeline)
        high_reliability = sum(event.reliability == "high" for event in timeline)
        return {
            "timestamp_coverage": _ratio(timed, total),
            "actor_coverage": _ratio(attributed, total),
            "source_locator_coverage": _ratio(located, total),
            "high_reliability_share": _ratio(high_reliability, total),
            "note": "Coverage describes supplied records only; it does not measure how complete the project history is.",
        }


def _parse_datetime(value: Any, evidence_id: str) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise InvestigationError(f"Evidence {evidence_id} event_time must be a string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvestigationError(
            f"Evidence {evidence_id} has invalid ISO-8601 event_time: {value}"
        ) from exc


def _optional_string(value: Any, lower: bool = False) -> str | None:
    if value in (None, ""):
        return None
    result = str(value).strip()
    return result.lower() if lower else result


def _lowest_confidence(values: Iterable[str]) -> str:
    order = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
    normalized = [value if value in order else "unknown" for value in values]
    return min(normalized, key=lambda value: order[value], default="unknown")


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "count": numerator,
        "total": denominator,
        "percent": round((numerator / denominator) * 100, 1) if denominator else 0.0,
    }

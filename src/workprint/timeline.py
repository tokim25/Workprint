from __future__ import annotations

from collections import Counter
from datetime import timedelta

from workprint.models import Observation, TimelineEvent, TimelineInvolvement


INVOLVEMENT_ORDER = (
    "initiated",
    "directed",
    "contributed",
    "reviewed",
    "decided",
    "executed",
)

ACTIVITY_CATEGORY_KEYS = (
    "user_activity",
    "collaborator_activity",
    "ai_tool_activity",
    "joint_activity",
    "unattributed_activity",
)


def _sort_key(item: Observation) -> tuple:
    return (
        item.timestamp is None,
        item.timestamp.isoformat() if item.timestamp else "",
        item.source,
        item.id,
    )


def _conversation_id(item: Observation) -> str:
    metadata = item.metadata or {}
    value = metadata.get("conversation_id")
    return str(value) if value else ""


def _stage(item: Observation) -> str:
    return {
        "question": "discovery",
        "suggestion": "planning",
        "evaluation": "analysis",
        "decision": "decision",
        "implementation": "implementation",
        "artifact": "implementation",
        "unknown": "unknown",
        "observation": "analysis",
    }.get(item.activity, "analysis")


def _activity_label(activity: str) -> str:
    return activity.replace("_", " ").title()


def _compact(text: str, limit: int = 140) -> str:
    value = " ".join(text.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _can_group(previous: Observation, current: Observation) -> bool:
    if _conversation_id(previous) != _conversation_id(current):
        return False
    if _stage(previous) != _stage(current):
        return False
    if previous.timestamp is None or current.timestamp is None:
        return previous.timestamp is current.timestamp
    return abs(current.timestamp - previous.timestamp) <= timedelta(minutes=15)


def _groups(observations: list[Observation]) -> list[list[Observation]]:
    ordered = sorted(observations, key=_sort_key)
    groups: list[list[Observation]] = []

    for item in ordered:
        if not groups or not _can_group(groups[-1][-1], item):
            groups.append([item])
        else:
            groups[-1].append(item)

    return groups


def _activity_category(item: Observation) -> str:
    actor = item.actor.strip().lower()
    if actor == "human":
        return "user_activity"
    if actor in {"chatgpt", "claude", "assistant", "tool"}:
        return "ai_tool_activity"
    if actor in {"unknown", "unattributed", ""}:
        return "unattributed_activity"
    return "collaborator_activity"


def _user_activity(item: Observation) -> str | None:
    if _activity_category(item) != "user_activity":
        return None
    return {
        "question": "initiated",
        "suggestion": "contributed",
        "evaluation": "reviewed",
        "decision": "decided",
        "implementation": "executed",
        "artifact": "executed",
        "observation": "contributed",
    }.get(item.activity)


def _involvement(items: list[Observation]) -> tuple[TimelineInvolvement, ...]:
    measured: dict[str, list[str]] = {activity: [] for activity in INVOLVEMENT_ORDER}
    for item in items:
        activity = _user_activity(item)
        if activity:
            measured[activity].append(item.id)

    return tuple(
        TimelineInvolvement(
            activity=activity,
            status="measured" if measured[activity] else "unknown",
            evidence_ids=tuple(measured[activity]),
        )
        for activity in INVOLVEMENT_ORDER
    )


def _breakdown(items: list[Observation]) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {key: [] for key in ACTIVITY_CATEGORY_KEYS}
    for item in items:
        values[_activity_category(item)].append(item.id)

    if values["user_activity"] and (
        values["collaborator_activity"] or values["ai_tool_activity"]
    ):
        values["joint_activity"] = [
            *values["user_activity"],
            *values["collaborator_activity"],
            *values["ai_tool_activity"],
        ]

    return {
        key: tuple(value)
        for key, value in values.items()
        if value
    }


def _confidence(items: list[Observation]) -> str:
    if any(item.reliability in {"low", "unknown"} for item in items):
        return "low"
    if any(item.timestamp is None for item in items):
        return "medium"
    return "high"


def _attribution_limits(items: list[Observation]) -> tuple[str, ...]:
    limits = [
        "Involvement is based only on captured evidence for this event.",
        "No ownership, effort, value, authorship, or contribution percentage is inferred.",
    ]
    if not any(_user_activity(item) for item in items):
        limits.append(
            "The investigated user's involvement is unknown from this event's evidence."
        )
    if any(item.activity == "unknown" for item in items):
        limits.append("The source evidence explicitly contains an unknown or gap.")
    return tuple(limits)


def _event_title(items: list[Observation]) -> str:
    first = items[0]
    if len(items) == 1:
        return f"{_activity_label(first.activity)}: {_compact(first.statement, 90)}"
    return f"{_stage(first).title()} event from {len(items)} observations"


def _event_description(items: list[Observation]) -> str:
    statements = [_compact(item.statement, 180) for item in items]
    return " ".join(statements)


def build_timeline(observations: list[Observation]) -> tuple[TimelineEvent, ...]:
    events: list[TimelineEvent] = []
    for index, items in enumerate(_groups(observations), start=1):
        event_id = f"TL-{index:03d}"
        timestamps = [item.timestamp for item in items if item.timestamp is not None]
        evidence_refs: list[str] = []
        for item in items:
            for ref in item.evidence_refs:
                if ref not in evidence_refs:
                    evidence_refs.append(ref)

        events.append(
            TimelineEvent(
                id=event_id,
                start_time=min(timestamps) if timestamps else None,
                end_time=max(timestamps) if timestamps else None,
                stage=_stage(items[0]),
                title=_event_title(items),
                description=_event_description(items),
                source_observation_ids=tuple(item.id for item in items),
                evidence_refs=tuple(evidence_refs),
                confidence=_confidence(items),
                user_involvement=_involvement(items),
                activity_breakdown=_breakdown(items),
                attribution_limits=_attribution_limits(items),
            )
        )

    return tuple(events)


def summarize_timeline(events: tuple[TimelineEvent, ...]) -> dict:
    counts: Counter[str] = Counter()
    for event in events:
        for involvement in event.user_involvement:
            if involvement.status == "measured":
                counts[involvement.activity] += 1

    return {
        "event_count": len(events),
        "captured_user_involvement_counts": {
            activity: counts.get(activity, 0)
            for activity in INVOLVEMENT_ORDER
        },
        "counting_note": (
            "Counts describe captured evidence events only; they are not "
            "ownership, effort, value, authorship, or contribution percentages."
        ),
    }

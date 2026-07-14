from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from workprint.models import Investigation, Observation


def build_investigation(
    project: str,
    source_files: list[str | Path],
    observations: list[Observation],
) -> Investigation:
    ordered = sorted(
        observations,
        key=lambda item: (
            item.timestamp is None,
            item.timestamp.isoformat() if item.timestamp else "",
            item.id,
        ),
    )

    activity_counts = Counter(item.activity for item in ordered)
    actor_counts = Counter(item.actor for item in ordered)

    findings: list[dict] = [
        {
            "id": "F-001",
            "statement": (
                f"The available evidence contains {len(ordered)} normalized "
                f"observations from {len(source_files)} source file(s)."
            ),
            "confidence": "high",
            "evidence_ids": [item.id for item in ordered],
        }
    ]

    if actor_counts:
        most_common_actor, count = actor_counts.most_common(1)[0]
        findings.append(
            {
                "id": "F-002",
                "statement": (
                    f"{most_common_actor} appears in the largest number of recorded "
                    f"conversation observations ({count}). This is an event count, "
                    "not a measure of total contribution."
                ),
                "confidence": "high",
                "evidence_ids": [
                    item.id for item in ordered if item.actor == most_common_actor
                ],
            }
        )

    if activity_counts.get("decision"):
        findings.append(
            {
                "id": "F-003",
                "statement": (
                    f"The conversation includes {activity_counts['decision']} "
                    "explicitly worded decision or acceptance event(s)."
                ),
                "confidence": "medium",
                "evidence_ids": [
                    item.id for item in ordered if item.activity == "decision"
                ],
            }
        )

    unknowns = [
        item.statement for item in ordered if item.activity == "unknown"
    ]
    if not unknowns:
        unknowns = [
            "Offline work, unrecorded conversations, and activity outside the export "
            "cannot be determined from the supplied evidence."
        ]

    limitations = (
        "Classification is deterministic and may miss implicit meaning.",
        "A generated or discussed idea is not proof that it appeared in the final project.",
        "Conversation timestamps do not measure active work time.",
        "Observation counts do not represent ownership, effort, or value.",
    )

    return Investigation(
        project=project,
        source_files=tuple(str(Path(item)) for item in source_files),
        observations=tuple(ordered),
        findings=tuple(findings),
        unknowns=tuple(unknowns),
        limitations=limitations,
    )

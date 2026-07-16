from __future__ import annotations

from collections import Counter
from pathlib import Path

from workprint.models import Investigation, Observation
from workprint.timeline import build_timeline, summarize_timeline


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
            item.source,
            item.id,
        ),
    )

    activity_counts = Counter(item.activity for item in ordered)
    actor_counts = Counter(item.actor for item in ordered)
    source_counts = Counter(item.source for item in ordered)

    findings: list[dict] = []
    finding_number = 1

    findings.append(
        {
            "id": f"F-{finding_number:03d}",
            "statement": (
                f"The available evidence contains {len(ordered)} normalized "
                f"observations from {len(source_files)} source file(s)."
            ),
            "confidence": "high",
            "evidence_ids": [item.id for item in ordered],
        }
    )
    finding_number += 1

    if len(source_counts) > 1:
        source_summary = ", ".join(
            f"{source}: {count}"
            for source, count in sorted(source_counts.items())
        )
        findings.append(
            {
                "id": f"F-{finding_number:03d}",
                "statement": (
                    "The investigation combines observations from multiple "
                    f"evidence sources ({source_summary})."
                ),
                "confidence": "high",
                "evidence_ids": [item.id for item in ordered],
            }
        )
        finding_number += 1

    if actor_counts:
        most_common_actor, count = actor_counts.most_common(1)[0]
        findings.append(
            {
                "id": f"F-{finding_number:03d}",
                "statement": (
                    f"{most_common_actor} appears in the largest number of recorded "
                    f"observations ({count}). This is an event count, "
                    "not a measure of total contribution."
                ),
                "confidence": "high",
                "evidence_ids": [
                    item.id for item in ordered if item.actor == most_common_actor
                ],
            }
        )
        finding_number += 1

    if activity_counts.get("decision"):
        findings.append(
            {
                "id": f"F-{finding_number:03d}",
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
        "Exact duplicate suppression does not detect semantic duplicates across sources.",
        "Timeline involvement is based only on captured evidence and does not infer contribution percentages.",
    )
    timeline = build_timeline(ordered)

    return Investigation(
        project=project,
        source_files=tuple(str(Path(item)) for item in source_files),
        observations=tuple(ordered),
        findings=tuple(findings),
        unknowns=tuple(unknowns),
        limitations=limitations,
        timeline=timeline,
        timeline_summary=summarize_timeline(timeline),
    )

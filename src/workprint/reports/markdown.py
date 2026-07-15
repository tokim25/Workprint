from __future__ import annotations

from workprint.models import Investigation
from workprint.timeline import build_timeline, summarize_timeline


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _time_range(start: object, end: object) -> str:
    start_text = start.isoformat() if hasattr(start, "isoformat") else None
    end_text = end.isoformat() if hasattr(end, "isoformat") else None
    if start_text and end_text and start_text != end_text:
        return f"{start_text} to {end_text}"
    return start_text or "Unknown"


def _involvement_summary(involvement: object) -> str:
    measured: list[str] = []
    unknown: list[str] = []
    for item in involvement:
        if item.status == "measured":
            measured.append(item.activity)
        elif item.status == "unknown":
            unknown.append(item.activity)

    parts: list[str] = []
    if measured:
        parts.append("measured: " + ", ".join(measured))
    if unknown:
        parts.append("unknown: " + ", ".join(unknown))
    return "; ".join(parts) if parts else "unknown"


def render_markdown(investigation: Investigation) -> str:
    timeline = investigation.timeline or build_timeline(list(investigation.observations))
    timeline_summary = investigation.timeline_summary or summarize_timeline(timeline)
    lines: list[str] = [
        f"# Workprint Investigation: {investigation.project}",
        "",
        "## Scope",
        "",
        f"Sources analyzed: {len(investigation.source_files)}",
        "",
        "## Executive Summary",
        "",
        (
            f"Workprint normalized {len(investigation.observations)} conversation "
            "observations. Findings below distinguish recorded events from broader "
            "claims that the evidence cannot support."
        ),
        "",
        "## Evidence Sources",
        "",
    ]

    for source in investigation.source_files:
        lines.append(f"- `{source}`")

    lines.extend([
        "",
        "## Timeline",
        "",
        "| Time | Stage | Event | User Involvement | Confidence | Evidence |",
        "|---|---|---|---|---|---|",
    ])

    for item in timeline:
        timestamp = _time_range(item.start_time, item.end_time)
        refs = ", ".join(f"`{ref}`" for ref in item.evidence_refs)
        lines.append(
            f"| {_escape(timestamp)} | {_escape(item.stage)} | "
            f"{_escape(item.title)} | {_escape(_involvement_summary(item.user_involvement))} | "
            f"{_escape(item.confidence)} | {refs} |"
        )

    lines.extend(["", "### Timeline Event Details", ""])
    for item in timeline:
        lines.extend([
            f"#### {item.id}: {item.title}",
            "",
            item.description,
            "",
            f"**Stage:** {item.stage}",
            "",
            f"**Confidence:** {item.confidence}",
            "",
            "**Source observations:** "
            + ", ".join(f"`{obs_id}`" for obs_id in item.source_observation_ids),
            "",
            "**Activity separation:**",
            "",
        ])
        for category, observation_ids in sorted(item.activity_breakdown.items()):
            rendered_ids = ", ".join(f"`{obs_id}`" for obs_id in observation_ids)
            lines.append(f"- {category}: {rendered_ids}")
        lines.extend(["", "**Attribution limits:**", ""])
        for limit in item.attribution_limits:
            lines.append(f"- {limit}")
        lines.append("")

    counts = timeline_summary.get("captured_user_involvement_counts", {})
    if counts:
        lines.extend([
            "### Captured User Involvement Counts",
            "",
            "| Activity | Captured Events |",
            "|---|---|",
        ])
        for activity, count in counts.items():
            lines.append(f"| {_escape(activity)} | {count} |")
        lines.extend([
            "",
            timeline_summary.get(
                "counting_note",
                "Counts describe captured evidence events only.",
            ),
            "",
        ])

    lines.extend(["", "## Findings", ""])
    for finding in investigation.findings:
        lines.extend([
            f"### {finding['id']}",
            "",
            finding["statement"],
            "",
            f"**Confidence:** {finding['confidence'].title()}",
            "",
            "**Evidence:** " + ", ".join(
                f"`{evidence_id}`" for evidence_id in finding["evidence_ids"]
            ),
            "",
        ])

    lines.extend(["## Unknowns", ""])
    for item in investigation.unknowns:
        lines.append(f"- {item}")

    lines.extend(["", "## Limitations", ""])
    for item in investigation.limitations:
        lines.append(f"- {item}")

    lines.append("")
    return "\n".join(lines)

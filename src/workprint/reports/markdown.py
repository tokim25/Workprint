from __future__ import annotations

from workprint.executive import build_executive_report
from workprint.models import Investigation
from workprint.timeline import build_timeline, summarize_timeline


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _compact(text: str, limit: int = 96) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


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


def _event_limit_count(timeline: object) -> int:
    return sum(len(item.attribution_limits) for item in timeline)


def _finding_count(findings: tuple[dict, ...], confidence: str) -> int:
    return sum(
        1
        for item in findings
        if str(item.get("confidence", "")).lower() == confidence
    )


def _executive_section(investigation: Investigation) -> list[str]:
    report = build_executive_report(investigation)
    brief = report.executive_brief
    confidence = report.confidence_assessment
    audit = report.copy_quality_audit
    lines: list[str] = [
        f"# Executive Report: {investigation.project}",
        "",
        "## Executive Brief",
        "",
        brief.project_goal.summary,
        "",
    ]

    output_summary = " ".join(item.summary for item in brief.project_outputs)
    lines.extend([
        output_summary,
        "",
        brief.evolution_summary,
        "",
        brief.collaboration_summary,
        "",
        brief.confidence_summary,
        "",
        brief.unknowns_summary,
        "",
        "## Project Overview",
        "",
    ])

    for item in report.project_overview:
        lines.extend([
            f"### {item.title}",
            "",
            item.summary,
            "",
            f"**Boundary:** {item.rationale}",
            "",
        ])

    lines.extend(["## Key Milestones", ""])
    for item in report.key_milestones:
        lines.extend([
            f"### {item.id}: {item.title}",
            "",
            item.summary,
            "",
            f"**Why included:** {item.rationale}",
            "",
            "**Evidence:** " + _evidence_refs(item.evidence_refs),
            "",
        ])

    lines.extend(["## Human-AI Collaboration", ""])
    for item in report.human_ai_collaboration:
        lines.extend([
            f"### {item.title}",
            "",
            item.summary,
            "",
            f"**Evidence boundary:** {item.rationale}",
            "",
        ])

    lines.extend(["## Decision Analysis", ""])
    for item in report.decision_analysis:
        lines.extend([
            f"### {item.id}",
            "",
            item.summary,
            "",
            f"**Decision leadership:** `{item.leadership}`",
            "",
            f"**Confidence:** {item.confidence}",
            "",
            f"**Rationale:** {item.rationale}",
            "",
            "**Evidence:** " + _evidence_refs(item.evidence_refs),
            "",
            "**Alternative interpretations:**",
            "",
        ])
        for alternative in item.alternative_interpretations:
            lines.append(f"- {alternative}")
        lines.append("")

    lines.extend([
        "## Confidence Assessment",
        "",
        f"**Overall confidence:** {confidence.band}",
        "",
        f"- Evidence strength: {confidence.evidence_strength}",
        f"- Coverage: {confidence.coverage}",
        f"- Corroboration: {confidence.corroboration}",
        f"- Conflicts: {confidence.conflicts}",
        f"- Gaps: {confidence.gaps}",
        "",
        confidence.rationale,
        "",
        "## Evidence Gaps",
        "",
    ])
    for item in report.evidence_gaps:
        lines.extend([
            f"### {item.id}: {item.summary}",
            "",
            f"**Why it matters:** {item.why_it_matters}",
            "",
            f"**What would reduce the gap:** {item.would_reduce_gap}",
            "",
        ])

    lines.extend([
        "## Investigation Assurance",
        "",
        report.investigation_assurance,
        "",
        f"**Copy-quality audit status:** `{audit.status}`",
        "",
        audit.disclosure,
        "",
        f"**Pinned copy-audit repository:** {audit.upstream_repository}",
        "",
        f"**Pinned revision:** `{audit.pinned_revision}`",
        "",
        "---",
        "",
    ])
    return lines


def _evidence_refs(refs: tuple[str, ...]) -> str:
    if not refs:
        return "No direct evidence reference is available."
    return ", ".join(f"`{ref}`" for ref in refs)


def render_markdown(investigation: Investigation) -> str:
    timeline = investigation.timeline or build_timeline(list(investigation.observations))
    timeline_summary = investigation.timeline_summary or summarize_timeline(timeline)
    lines: list[str] = _executive_section(investigation) + [
        f"# Workprint Investigation: {investigation.project}",
        "",
        "## At a Glance",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Sources analyzed | {len(investigation.source_files)} |",
        f"| Captured observations | {len(investigation.observations)} |",
        f"| Timeline events | {len(timeline)} |",
        f"| Findings | {len(investigation.findings)} |",
        f"| Unknown entries | {len(investigation.unknowns)} |",
        f"| Event attribution limits | {_event_limit_count(timeline)} |",
        f"| Medium-confidence findings | {_finding_count(investigation.findings, 'medium')} |",
        f"| Low-confidence findings | {_finding_count(investigation.findings, 'low')} |",
        "",
        "## Evidence Boundary",
        "",
        (
            "This report reflects captured evidence only; no ownership, effort, "
            "authorship, value, or contribution percentages are inferred."
        ),
        "",
        "## Evidence Sources",
        "",
    ]

    for source in sorted(investigation.source_files):
        lines.append(f"- `{source}`")

    lines.extend([
        "",
        "## Timeline Overview",
        "",
        "| Event | Time | Stage | Confidence | Observations |",
        "|---|---|---|---|---:|",
    ])

    for item in timeline:
        timestamp = _time_range(item.start_time, item.end_time)
        lines.append(
            f"| `{item.id}` | {_escape(timestamp)} | {_escape(item.stage)} | "
            f"{_escape(item.confidence.title())} | {len(item.source_observation_ids)} |"
        )

    lines.extend(["", "## Timeline Event Details", ""])
    for item in timeline:
        lines.extend([
            f"### {item.id}: {item.title}",
            "",
            item.description,
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Time | {_escape(_time_range(item.start_time, item.end_time))} |",
            f"| Stage | {_escape(item.stage)} |",
            f"| Confidence | {_escape(item.confidence.title())} |",
            f"| Source observations | {', '.join(f'`{obs_id}`' for obs_id in item.source_observation_ids)} |",
            "",
            "**Evidence references:** "
            + ", ".join(f"`{ref}`" for ref in item.evidence_refs),
            "",
            "**Activity separation:**",
            "",
        ])
        for category, observation_ids in sorted(item.activity_breakdown.items()):
            rendered_ids = ", ".join(f"`{obs_id}`" for obs_id in observation_ids)
            lines.append(f"- {category}: {rendered_ids}")
        lines.extend(["", "**Captured user involvement:**", ""])
        for involvement in item.user_involvement:
            evidence = (
                ", ".join(f"`{obs_id}`" for obs_id in involvement.evidence_ids)
                if involvement.evidence_ids
                else "none"
            )
            lines.append(
                f"- {involvement.activity}: {involvement.status} "
                f"(evidence: {evidence})"
            )
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

    lines.extend([
        "",
        "## Evidence Appendix",
        "",
        "### Observation Index",
        "",
        "| Observation | Time | Source | Actor | Activity | Evidence |",
        "|---|---|---|---|---|---|",
    ])
    for item in investigation.observations:
        timestamp = item.timestamp.isoformat() if item.timestamp else "Unknown"
        refs = ", ".join(f"`{ref}`" for ref in item.evidence_refs)
        lines.append(
            f"| `{item.id}` | {_escape(timestamp)} | {_escape(item.source)} | "
            f"{_escape(item.actor)} | {_escape(item.activity)} | {refs} |"
        )

    lines.extend(["", "### Observation Statements", ""])
    for item in investigation.observations:
        lines.append(f"- `{item.id}`: {_escape(_compact(item.statement, 180))}")

    lines.append("")
    return "\n".join(lines)

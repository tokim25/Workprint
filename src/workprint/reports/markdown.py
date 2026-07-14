from __future__ import annotations

from workprint.models import Investigation


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(investigation: Investigation) -> str:
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
        "| Time | Actor | Activity | Observation | Evidence |",
        "|---|---|---|---|---|",
    ])

    for item in investigation.observations:
        timestamp = item.timestamp.isoformat() if item.timestamp else "Unknown"
        refs = ", ".join(f"`{ref}`" for ref in item.evidence_refs)
        lines.append(
            f"| {_escape(timestamp)} | {_escape(item.actor)} | "
            f"{_escape(item.activity)} | {_escape(item.statement)} | {refs} |"
        )

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

from __future__ import annotations

from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Workprint Investigation — {report['project']}",
        "",
        f"**Scope:** {report['scope']}",
        "",
        "## Evidence coverage",
        "",
    ]

    coverage = report["evidence_coverage"]
    lines.extend(
        [
            "| Dimension | Coverage |",
            "|---|---:|",
            _coverage_row("Timestamp", coverage["timestamp_coverage"]),
            _coverage_row("Actor", coverage["actor_coverage"]),
            _coverage_row("Source locator", coverage["source_locator_coverage"]),
            _coverage_row("High-reliability evidence", coverage["high_reliability_share"]),
            "",
            f"> {coverage['note']}",
            "",
            "## Timeline",
            "",
            "| Event | Time | Actor | Activity | Observation | Evidence |",
            "|---|---|---|---|---|---|",
        ]
    )

    for event in report["timeline"]:
        lines.append(
            "| {id} | {time} | {actor} | {activity} | {observation} | {locator} |".format(
                id=_escape(event["id"]),
                time=_escape(event["event_time"] or "Unknown"),
                actor=_escape(event["actor"] or "Unknown"),
                activity=_escape(event["activity"] or "Unclassified"),
                observation=_escape(event["observation"]),
                locator=_escape(event["source_locator"] or event["source_type"]),
            )
        )

    lines.extend(["", "## Decisions", ""])
    if report["decisions"]:
        lines.extend(
            [
                "| Decision | Date | Actor | Outcome | Statement | Confidence |",
                "|---|---|---|---|---|---|",
            ]
        )
        for decision in report["decisions"]:
            lines.append(
                f"| {_escape(decision['id'])} | {_escape(decision['date'] or 'Unknown')} | "
                f"{_escape(decision['actor'])} | {_escape(decision['outcome'])} | "
                f"{_escape(decision['decision'])} | {_escape(decision['confidence'].title())} |"
            )
    else:
        lines.append("No explicit decision events were supplied.")

    lines.extend(["", "## Findings", ""])
    for finding in report["findings"]:
        lines.extend(
            [
                f"### {finding['id']}",
                "",
                f"**Finding:** {finding['statement']}",
                "",
                f"**Classification:** {finding['classification'].title()}",
                "",
                f"**Confidence:** {finding['confidence'].title()}",
                "",
                f"**Evidence:** {', '.join(finding['evidence_ids'])}",
                "",
                f"**Reasoning:** {finding['reasoning']}",
                "",
            ]
        )
        if finding["alternative_explanations"]:
            lines.append("**Alternative explanations:**")
            lines.extend(f"- {item}" for item in finding["alternative_explanations"])
            lines.append("")

    lines.extend(["## Unknowns", ""])
    lines.extend(f"- {item}" for item in report["unknowns"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def _coverage_row(label: str, value: dict[str, Any]) -> str:
    return f"| {label} | {value['count']}/{value['total']} ({value['percent']}%) |"


def _escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")

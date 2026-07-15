from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath

from workprint.models import (
    ConfidenceAssessment,
    CopyQualityAudit,
    EvidenceGap,
    ExecutiveBrief,
    ExecutiveDecision,
    ExecutiveFinding,
    ExecutiveReport,
    Investigation,
    Observation,
    TimelineEvent,
)


EXECUTIVE_SCHEMA_VERSION = "1.0"
UNSLOP_TEXT_REPOSITORY = "https://github.com/JCarterJohnson/vibecoded-design-tells"
UNSLOP_TEXT_PINNED_REVISION = "f7c4aefc2c797a66e55b49354a93917ab60d33ac"
COPY_AUDITED_SECTIONS = (
    "Executive Brief",
    "Project Evolution narrative",
    "Collaboration Profile",
    "Decision Analysis",
    "Confidence Assessment",
    "Evidence Gaps",
    "Investigation Assurance",
)

CONFIDENCE_ORDER = ("Very High", "High", "Moderate", "Limited", "Low")

SOURCE_LABELS = {
    "chatgpt": "ChatGPT",
    "ChatGPT": "ChatGPT",
    "claude": "Claude",
    "Claude": "Claude",
    "figma": "Figma",
    "Figma": "Figma",
    "google-docs": "Google Docs",
    "Google Docs": "Google Docs",
}

GOAL_PATTERNS = (
    r"\b(?:the\s+)?goal of (?:this|the) project is\b",
    r"\b(?:the\s+)?project goal is\b",
    r"\b(?:the\s+)?objective of (?:this|the) project is\b",
    r"\b(?:the\s+)?project objective is\b",
    r"\bwe are building this to\b",
    r"\bthis project (?:helps|is meant to|is intended to|exists to)\b",
    r"\b(?:the\s+)?purpose (?:of (?:this|the) project )?is\b",
    r"\bthe problem we are trying to solve is\b",
    r"\bthis project solves\b",
)
PRODUCED_PATTERNS = (
    r"\bbuilt\b",
    r"\bcreated\b",
    r"\badded\b",
    r"\bimplemented\b",
    r"\bgenerated\b",
    r"\bproduced\b",
    r"\bcompleted\b",
    r"\bwrites?\b",
)
PLANNED_OUTPUT_PATTERNS = (
    r"\bplan(?:ned)?\b",
    r"\bproposal\b",
    r"\bshould (?:create|add|build|generate|produce|write)\b",
    r"\bwill (?:create|add|build|generate|produce|write)\b",
    r"\boutput\b",
    r"\breport\b",
    r"\bdeliverable\b",
)
PROJECT_OUTPUT_PATTERNS = (
    r"\bproject (?:output|artifact|deliverable)\b",
    r"\bdeliverable\b",
    r"\b(?:markdown|json)?\s*report\b",
    r"\breport\.(?:md|json)\b",
    r"\bworkprint-output\b",
    r"\bexport\b",
    r"\bgenerated output\b",
)
NON_PROJECT_OUTPUT_PATTERNS = (
    r"\bfixture\b",
    r"\bsample\b",
    r"\bcomponent metadata\b",
    r"\bcomponent\b",
    r"\bnode\b",
    r"\bparagraph block\b",
    r"\badapter\b",
)
REQUIREMENT_CHANGE_PATTERNS = (
    r"\brequirement(?:s)?\b",
    r"\bscope\b",
    r"\badjustment\b",
    r"\brefinement\b",
)
VALIDATION_PATTERNS = (
    r"\btest(?:s|ed|ing)?\b",
    r"\bvalidation\b",
    r"\bpassed\b",
    r"\bconfirmed\b",
)
CORRECTION_PATTERNS = (
    r"\bfix(?:ed|es)?\b",
    r"\bcorrect(?:ed|ion)?\b",
    r"\breversal\b",
    r"\bregression\b",
    r"\bdogfood(?:ing)?\b",
)
TOOL_PATTERNS = {
    "ChatGPT": r"\b(?:used|using|via|with|in)\s+ChatGPT\b",
    "Claude": r"\b(?:used|using|via|with|in)\s+Claude\b",
    "Figma": r"\b(?:used|using|via|with|in)\s+Figma\b",
    "Google Docs": r"\b(?:used|using|via|with|in)\s+Google Docs\b",
    "Git": r"\b(?:used|using|via|with|in)\s+Git\b",
    "GitHub": r"\b(?:used|using|via|with|in)\s+GitHub\b",
}


@dataclass(frozen=True)
class ExecutiveReportBuilder:
    investigation: Investigation

    def build(self) -> ExecutiveReport:
        observations = tuple(self.investigation.observations)
        goal = _project_goal(observations)
        outputs = _project_outputs(observations)
        milestones = _key_milestones(self.investigation.timeline, observations)
        decisions = _decisions(self.investigation.timeline, observations)
        gaps = _evidence_gaps(self.investigation)
        confidence = _confidence_assessment(
            self.investigation,
            goal,
            outputs,
            milestones,
            decisions,
            gaps,
        )
        collaboration = _collaboration(observations, self.investigation.timeline)
        copy_audit = _copy_quality_audit_unavailable()
        fixture_boundary = _fixture_boundary(self.investigation)
        assurance = _investigation_assurance(copy_audit, fixture_boundary)

        brief = ExecutiveBrief(
            project_goal=goal,
            project_outputs=outputs,
            evolution_summary=_evolution_summary(milestones),
            collaboration_summary=_collaboration_summary(collaboration),
            confidence_summary=_confidence_summary(confidence),
            unknowns_summary=_unknowns_summary(gaps),
        )

        overview = _project_overview(self.investigation, observations, fixture_boundary)

        return ExecutiveReport(
            schema_version=EXECUTIVE_SCHEMA_VERSION,
            executive_brief=brief,
            project_overview=overview,
            key_milestones=milestones,
            human_ai_collaboration=collaboration,
            decision_analysis=decisions,
            confidence_assessment=confidence,
            evidence_gaps=gaps,
            investigation_assurance=assurance,
            copy_quality_audit=copy_audit,
            metadata={
                "fixture_boundary": fixture_boundary,
                "source_labels": SOURCE_LABELS,
            },
        )


def build_executive_report(investigation: Investigation) -> ExecutiveReport:
    return ExecutiveReportBuilder(investigation).build()


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _first_match(
    observations: tuple[Observation, ...],
    patterns: tuple[str, ...],
) -> Observation | None:
    for item in observations:
        if _matches(item.statement, patterns):
            return item
    return None


def _refs(items: tuple[Observation, ...] | list[Observation]) -> tuple[str, ...]:
    refs: list[str] = []
    for item in items:
        for ref in item.evidence_refs:
            if ref not in refs:
                refs.append(ref)
    return tuple(refs)


def _all_refs(observations: tuple[Observation, ...]) -> tuple[str, ...]:
    return _refs(observations)


def _project_goal(observations: tuple[Observation, ...]) -> ExecutiveFinding:
    match = _first_match(
        tuple(item for item in observations if _is_project_goal_candidate(item)),
        GOAL_PATTERNS,
    )
    if not match:
        return ExecutiveFinding(
            id="GOAL-001",
            title="Project goal",
            summary=(
                "The available evidence does not contain an explicit statement "
                "of the project's overall goal."
            ),
            status="unknown",
            rationale=(
                "Workprint does not infer the project goal from implementation "
                "decisions, adapter requirements, naming decisions, or metadata."
            ),
        )
    return ExecutiveFinding(
        id="GOAL-001",
        title="Project goal",
        summary=_plain_statement(match.statement),
        status="explicitly_supported",
        evidence_ids=(match.id,),
        evidence_refs=match.evidence_refs,
        rationale=(
            "The goal is based on explicit intent, objective, purpose, or "
            "requirement language in the captured evidence."
        ),
    )


def _is_project_goal_candidate(item: Observation) -> bool:
    statement = item.statement.lower()
    if not _matches(statement, GOAL_PATTERNS):
        return False
    excluded = (
        "adapter",
        "fixture",
        "component",
        "metadata",
        "let's call",
        "project name",
        "should use",
        "recommend",
    )
    return not any(term in statement for term in excluded)


def _project_outputs(observations: tuple[Observation, ...]) -> tuple[ExecutiveFinding, ...]:
    produced = [
        item for item in observations
        if item.activity in {"implementation", "artifact"}
        and _matches(item.statement, PRODUCED_PATTERNS)
        and _is_project_level_output(item)
    ]
    planned = [
        item for item in observations
        if item not in produced
        and _matches(item.statement, PLANNED_OUTPUT_PATTERNS)
        and _is_project_level_output(item)
    ]

    findings: list[ExecutiveFinding] = []
    if produced:
        findings.append(
            ExecutiveFinding(
                id="OUT-001",
                title="Explicitly produced output",
                summary=_summarize_items(
                    "The evidence establishes a completed project-level output",
                    produced,
                ),
                status="explicitly_produced",
                evidence_ids=tuple(item.id for item in produced),
                evidence_refs=_refs(produced),
                rationale="Output is supported by implementation or artifact evidence.",
            )
        )
    if planned:
        findings.append(
            ExecutiveFinding(
                id=f"OUT-{len(findings) + 1:03d}",
                title="Referenced or planned output",
                summary=_summarize_items(
                    "The evidence references a planned project-level output",
                    planned,
                ),
                status="referenced_or_planned",
                evidence_ids=tuple(item.id for item in planned),
                evidence_refs=_refs(planned),
                rationale=(
                    "These outputs are referenced or planned, but not established "
                    "as produced by this evidence alone."
                ),
            )
        )
    if not findings:
        findings.append(
            ExecutiveFinding(
                id="OUT-001",
                title="Project outputs",
                summary=(
                    "The available evidence does not establish a completed or "
                    "planned project-level output."
                ),
                status="not_established",
                rationale=(
                    "Low-level implementation details, fixture metadata, component "
                    "metadata, and individual feature notes are not treated as "
                    "project-level outputs."
                ),
            )
        )
    return tuple(findings)


def _is_project_level_output(item: Observation) -> bool:
    statement = item.statement.lower()
    if _matches(statement, NON_PROJECT_OUTPUT_PATTERNS):
        return False
    return _matches(statement, PROJECT_OUTPUT_PATTERNS)


def _key_milestones(
    timeline: tuple[TimelineEvent, ...],
    observations: tuple[Observation, ...],
) -> tuple[ExecutiveFinding, ...]:
    by_id = {item.id: item for item in observations}
    grouped: dict[str, dict[str, object]] = {}
    for event in timeline:
        items = [by_id[item_id] for item_id in event.source_observation_ids if item_id in by_id]
        reason = _milestone_reason(items)
        if not reason:
            continue
        key = _milestone_key(items, event)
        existing = grouped.get(key)
        if existing:
            existing["items"] = list(existing["items"]) + items
            existing["event_ids"] = tuple(existing["event_ids"]) + (event.id,)
            existing["evidence_ids"] = tuple(dict.fromkeys(tuple(existing["evidence_ids"]) + event.source_observation_ids))
            existing["evidence_refs"] = tuple(dict.fromkeys(tuple(existing["evidence_refs"]) + event.evidence_refs))
            continue
        grouped[key] = {
            "items": items,
            "reason": reason,
            "event_ids": (event.id,),
            "evidence_ids": event.source_observation_ids,
            "evidence_refs": event.evidence_refs,
        }

    milestones: list[ExecutiveFinding] = []
    for data in grouped.values():
        items = data["items"]
        reason = str(data["reason"])
        title = _milestone_title(reason, items)
        milestones.append(
            ExecutiveFinding(
                id=f"MS-{len(milestones) + 1:03d}",
                title=title,
                summary=_milestone_summary(reason, items),
                status=reason,
                evidence_ids=tuple(data["evidence_ids"]),
                evidence_refs=tuple(data["evidence_refs"]),
                rationale=f"Included as a key milestone because it contains {reason}.",
            )
        )
    if milestones:
        return tuple(milestones)
    return (
        ExecutiveFinding(
            id="MS-001",
            title="Key milestones",
            summary=(
                "The available evidence does not establish significant project "
                "milestones under the v1 milestone rules."
            ),
            status="not_established",
            rationale="Routine observations are not promoted to milestones.",
        ),
    )


def _milestone_reason(items: list[Observation]) -> str:
    text = " ".join(item.statement for item in items)
    if any(item.activity == "decision" for item in items):
        return "an explicit decision"
    if any(item.activity in {"implementation", "artifact"} for item in items) and _matches(text, PRODUCED_PATTERNS):
        return "a completed or created output"
    if _matches(text, REQUIREMENT_CHANGE_PATTERNS):
        return "a material requirement change"
    if any(item.activity == "implementation" for item in items) and _matches(text, VALIDATION_PATTERNS):
        return "a validated implementation milestone"
    if _matches(text, CORRECTION_PATTERNS):
        return "a major correction or reversal"
    return ""


def _milestone_key(items: list[Observation], event: TimelineEvent) -> str:
    text = _normalize_for_dedupe(" ".join(item.statement for item in items))
    if "workprint" in text and ("project name" in text or "call project" in text or "use workprint" in text):
        return "naming:workprint"
    if "repository" in text and ("pushed initial" in text or "pushed first" in text or "first commit" in text):
        return "repository:initial-push"
    return f"event:{event.id}"


def _normalize_for_dedupe(text: str) -> str:
    value = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    replacements = {
        "lets": "let us",
        "call the project": "use project name",
        "use workprint as the project name": "project name workprint",
        "call project workprint": "project name workprint",
        "pushed the initial files": "pushed first commit",
        "pushed the first commit": "pushed first commit",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return " ".join(value.split())


def _milestone_title(reason: str, items: list[Observation]) -> str:
    summary = _milestone_summary(reason, items)
    prefix = {
        "an explicit decision": "Decision",
        "a completed or created output": "Completed work",
        "a material requirement change": "Requirement change",
        "a validated implementation milestone": "Validation",
        "a major correction or reversal": "Correction",
    }.get(reason, "Milestone")
    summary = re.sub(
        r"^(A decision|Completed work|A requirement or scope change|Validation evidence|A correction or reversal) was recorded:\s*",
        "",
        summary,
    )
    return f"{prefix}: {_compact(summary, 88)}"


def _milestone_summary(reason: str, items: list[Observation]) -> str:
    if not items:
        return "The available evidence establishes a project milestone."
    plain = _plain_statement(items[0].statement)
    if reason == "an explicit decision":
        return f"A decision was recorded: {plain}"
    if reason == "a completed or created output":
        return f"Completed work was recorded: {plain}"
    if reason == "a material requirement change":
        return f"A requirement or scope change was recorded: {plain}"
    if reason == "a validated implementation milestone":
        return f"Validation evidence was recorded: {plain}"
    if reason == "a major correction or reversal":
        return f"A correction or reversal was recorded: {plain}"
    return plain


def _collaboration(
    observations: tuple[Observation, ...],
    timeline: tuple[TimelineEvent, ...],
) -> tuple[ExecutiveFinding, ...]:
    category_counts: Counter[str] = Counter()
    for event in timeline:
        for category, ids in event.activity_breakdown.items():
            if category != "joint_activity":
                category_counts[category] += len(ids)

    human_ids = tuple(
        item.id for item in observations if item.actor.strip().lower() == "human"
    )
    ai_ids = tuple(
        item.id for item in observations
        if item.actor.strip().lower() in {"chatgpt", "claude", "assistant", "tool"}
    )
    joint_events = tuple(
        event.id for event in timeline if "joint_activity" in event.activity_breakdown
    )

    return (
        ExecutiveFinding(
            id="COL-001",
            title="Human activity",
            summary=(
                f"Workprint found {len(human_ids)} captured record(s) "
                "describing human activity."
            ),
            status="captured_evidence",
            evidence_ids=human_ids,
            evidence_refs=_refs([item for item in observations if item.id in human_ids]),
            rationale="Counts describe captured records only.",
        ),
        ExecutiveFinding(
            id="COL-002",
            title="AI/tool activity",
            summary=(
                f"Workprint found {len(ai_ids)} captured record(s) "
                "describing AI or tool activity."
            ),
            status="captured_evidence",
            evidence_ids=ai_ids,
            evidence_refs=_refs([item for item in observations if item.id in ai_ids]),
            rationale=(
                "AI/tool activity is separated from human activity and is not "
                "converted into contribution scoring."
            ),
        ),
        ExecutiveFinding(
            id="COL-003",
            title="Collaboration profile",
            summary=_collaboration_profile(category_counts, joint_events),
            status="captured_evidence",
            evidence_ids=tuple(item.id for item in observations),
            evidence_refs=_all_refs(observations),
            rationale=(
                "The profile is based on captured activity categories, not total "
                "authorship, ownership, effort, value, or contribution."
            ),
        ),
    )


def _collaboration_profile(
    category_counts: Counter[str],
    joint_events: tuple[str, ...],
) -> str:
    if category_counts["user_activity"] and category_counts["ai_tool_activity"]:
        if joint_events:
            return (
                "The captured evidence supports a human-AI collaboration pattern "
                "with both human and AI/tool activity appearing in related events."
            )
        return (
            "The captured evidence includes both human activity and AI/tool "
            "activity, but does not establish joint shaping within the same events."
        )
    if category_counts["user_activity"]:
        return "The captured evidence primarily shows human activity."
    if category_counts["ai_tool_activity"]:
        return "The captured evidence primarily shows AI/tool activity."
    return "The available evidence does not establish a collaboration pattern."


def _decisions(
    timeline: tuple[TimelineEvent, ...],
    observations: tuple[Observation, ...],
) -> tuple[ExecutiveDecision, ...]:
    by_id = {item.id: item for item in observations}
    decisions: list[ExecutiveDecision] = []
    for event in timeline:
        items = [by_id[item_id] for item_id in event.source_observation_ids if item_id in by_id]
        if not _is_decision_event(items):
            continue
        leadership, rationale = classify_decision_leadership(items)
        decisions.append(
            ExecutiveDecision(
                id=f"DEC-{len(decisions) + 1:03d}",
                summary=_decision_summary(items),
                leadership=leadership,
                confidence=_event_confidence(event.confidence),
                rationale=rationale,
                evidence_ids=event.source_observation_ids,
                evidence_refs=event.evidence_refs,
                alternative_interpretations=(
                    "Workprint cannot determine whether the same decision was discussed outside the supplied evidence.",
                ),
            )
        )
    if decisions:
        return tuple(decisions)
    return (
        ExecutiveDecision(
            id="DEC-001",
            summary="No explicit major decisions were established by the available evidence.",
            leadership="unknown",
            confidence="Limited",
            rationale="Decision leadership remains unknown without explicit decision evidence.",
            evidence_ids=(),
            evidence_refs=(),
            alternative_interpretations=("Relevant decisions may exist outside the supplied evidence.",),
        ),
    )


def _is_decision_event(items: list[Observation]) -> bool:
    return any(item.activity == "decision" for item in items)


def _decision_summary(items: list[Observation]) -> str:
    if not items:
        return "A decision was recorded."
    return f"A decision was recorded: {_plain_statement(items[0].statement)}"


def classify_decision_leadership(items: list[Observation]) -> tuple[str, str]:
    human_decision = any(
        item.actor.strip().lower() == "human" and item.activity == "decision"
        for item in items
    )
    ai_suggestion = any(
        item.actor.strip().lower() in {"chatgpt", "claude", "assistant", "tool"}
        and item.activity == "suggestion"
        for item in items
    )
    ai_implementation = any(
        item.actor.strip().lower() in {"chatgpt", "claude", "assistant", "tool"}
        and item.activity in {"implementation", "artifact"}
        for item in items
    )
    human_shaping = any(
        item.actor.strip().lower() == "human"
        and item.activity in {"question", "suggestion", "evaluation"}
        for item in items
    )
    ai_shaping = any(
        item.actor.strip().lower() in {"chatgpt", "claude", "assistant", "tool"}
        and item.activity in {"suggestion", "evaluation"}
        for item in items
    )

    if human_decision and ai_suggestion:
        return (
            "ai_proposed_human_decided",
            "AI/tool evidence includes a proposal and human evidence includes the decision.",
        )
    if human_decision:
        return (
            "human_led",
            "Human evidence explicitly states the decision or acceptance.",
        )
    if human_shaping and ai_shaping:
        return (
            "jointly_shaped",
            "Human and AI/tool evidence both materially shape the decision context.",
        )
    if ai_implementation and not human_decision:
        return (
            "ai_executed",
            "AI/tool evidence shows execution, but not independent decision authority.",
        )
    return ("unknown", "The available evidence does not establish decision leadership.")


def _event_confidence(value: str) -> str:
    return {
        "high": "High",
        "medium": "Moderate",
        "low": "Limited",
        "unknown": "Low",
    }.get(value.lower(), "Limited")


def _confidence_assessment(
    investigation: Investigation,
    goal: ExecutiveFinding,
    outputs: tuple[ExecutiveFinding, ...],
    milestones: tuple[ExecutiveFinding, ...],
    decisions: tuple[ExecutiveDecision, ...],
    gaps: tuple[EvidenceGap, ...],
) -> ConfidenceAssessment:
    observations = investigation.observations
    evidence_strength = _evidence_strength(observations, decisions)
    coverage = _coverage(investigation)
    corroboration = _corroboration(milestones, decisions)
    conflicts = _conflicts(observations)
    gap_summary = _gap_summary(gaps)
    band = _confidence_band(
        evidence_strength,
        coverage,
        corroboration,
        conflicts,
        gap_summary,
        goal,
        outputs,
    )
    return ConfidenceAssessment(
        band=band,
        evidence_strength=evidence_strength,
        coverage=coverage,
        corroboration=corroboration,
        conflicts=conflicts,
        gaps=gap_summary,
        rationale=(
            f"{band} confidence is assigned from explicit rules using evidence "
            "strength, coverage, corroboration, conflicts, and gaps; no hidden "
            "numeric score or percentage is used."
        ),
    )


def _evidence_strength(
    observations: tuple[Observation, ...],
    decisions: tuple[ExecutiveDecision, ...],
) -> str:
    if any(item.activity == "decision" and item.evidence_refs for item in observations):
        return "Direct evidence supports at least one explicit decision."
    if any(item.activity in {"implementation", "artifact"} for item in observations):
        return "Implementation or artifact evidence is present, but explicit decision evidence is limited."
    if observations:
        return "Evidence is present but mostly indirect for executive conclusions."
    return "No observations are available."


def _coverage(investigation: Investigation) -> str:
    source_types = {item.source_type for item in investigation.observations}
    if len(source_types) >= 3:
        return "Broad coverage across three or more evidence source types."
    if len(source_types) == 2:
        return "Moderate coverage across two evidence source types."
    if len(source_types) == 1:
        return "Limited coverage from one evidence source type."
    return "No evidence coverage is available."


def _corroboration(
    milestones: tuple[ExecutiveFinding, ...],
    decisions: tuple[ExecutiveDecision, ...],
) -> str:
    corroborated: list[str] = []
    for item in milestones:
        if len(set(item.evidence_refs)) >= 2:
            corroborated.append(item.id)
    for item in decisions:
        if len(set(item.evidence_refs)) >= 2:
            corroborated.append(item.id)
    if corroborated:
        return (
            "Corroboration is present where two or more independent evidence "
            f"references support the same claim: {', '.join(corroborated)}."
        )
    return (
        "No executive claim has two independent supporting evidence references; "
        "source diversity is treated as coverage, not corroboration."
    )


def _conflicts(observations: tuple[Observation, ...]) -> str:
    if any(item.reliability in {"low", "unknown"} for item in observations):
        return "Some observations have low or unknown reliability."
    return "No explicit evidence conflicts were detected by deterministic rules."


def _gap_summary(gaps: tuple[EvidenceGap, ...]) -> str:
    if gaps:
        return f"{len(gaps)} executive evidence gap(s) or limitation(s) are recorded."
    return "No executive evidence gaps are recorded."


def _confidence_band(
    evidence_strength: str,
    coverage: str,
    corroboration: str,
    conflicts: str,
    gaps: str,
    goal: ExecutiveFinding,
    outputs: tuple[ExecutiveFinding, ...],
) -> str:
    has_direct = evidence_strength.startswith("Direct")
    has_broad = coverage.startswith("Broad")
    has_corroboration = not corroboration.startswith("No executive claim")
    has_conflicts = not conflicts.startswith("No explicit")
    has_goal = goal.status == "explicitly_supported"
    has_output = any(item.status != "not_established" for item in outputs)
    has_central_unknown = not has_goal or not has_output or "Git history" in gaps or "revision" in gaps

    if has_direct and has_broad and has_corroboration and not has_conflicts and not has_central_unknown:
        return "Very High"
    if has_central_unknown and has_direct:
        return "Moderate"
    if has_direct and has_broad and has_corroboration and not has_conflicts:
        return "High"
    if has_direct or evidence_strength.startswith("Implementation"):
        return "Moderate"
    if evidence_strength.startswith("Evidence is present"):
        return "Limited"
    return "Low"


def _evidence_gaps(investigation: Investigation) -> tuple[EvidenceGap, ...]:
    gaps: list[EvidenceGap] = [
        EvidenceGap(
            id="GAP-001",
            summary="Git history was not analyzed.",
            why_it_matters=(
                "Without Git history, Workprint cannot fully reconstruct "
                "file-level implementation sequence or code authorship."
            ),
            would_reduce_gap="Provide supported Git evidence when a Git adapter exists.",
            affects=("coverage", "implementation sequence", "authorship boundaries"),
        ),
        EvidenceGap(
            id="GAP-002",
            summary="Static exports may omit revision history.",
            why_it_matters=(
                "Static document or design exports may show content without showing "
                "how it changed over time."
            ),
            would_reduce_gap="Provide revision-aware exports or source history.",
            affects=("coverage", "collaboration", "decision sequence"),
        ),
        EvidenceGap(
            id="GAP-003",
            summary="Unsupported attribution remains unknown.",
            why_it_matters=(
                "Captured activity does not establish authorship, ownership, effort, "
                "value, or contribution percentages."
            ),
            would_reduce_gap="Provide evidence that explicitly maps people to actions.",
            affects=("attribution", "decision leadership"),
        ),
    ]
    for item in investigation.unknowns:
        if _is_duplicate_gap(item):
            continue
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary=item,
                why_it_matters="This question could not be answered from the supplied evidence.",
                would_reduce_gap="Provide direct evidence that addresses this unknown.",
                affects=("confidence",),
            )
        )
    return tuple(gaps)


def _is_duplicate_gap(text: str) -> bool:
    value = text.lower()
    return "revision history" in value and "static export" in value


def _copy_quality_audit_unavailable() -> CopyQualityAudit:
    return CopyQualityAudit(
        status="unavailable",
        scanner="unslop_text_scan.py",
        upstream_repository=UNSLOP_TEXT_REPOSITORY,
        pinned_revision=UNSLOP_TEXT_PINNED_REVISION,
        scanned_sections=COPY_AUDITED_SECTIONS,
        structural_review_completed=False,
        disclosure=(
            "The unslop-text scanner is pinned for future integration but was "
            "not run for this report, so the copy-quality audit is unavailable."
        ),
    )


def _investigation_assurance(copy_audit: CopyQualityAudit, fixture_boundary: dict[str, object]) -> str:
    fixture_text = ""
    if fixture_boundary.get("all_selected_evidence_is_fixture"):
        fixture_text = (
            " This report analyzes sample fixture evidence included with the "
            "Workprint repository; it does not reconstruct the repository's "
            "complete real-world development history."
        )
    return (
        "This Workprint report is an evidence-backed reconstruction based only "
        "on the sources supplied for investigation. Workprint normalizes "
        "captured evidence, extracts traceable observations, and summarizes "
        "project evolution, collaboration, decisions, confidence, and unknowns. "
        "The report does not infer authorship, ownership, effort, value, or "
        "contribution percentages. Narrative language is designed for future "
        "copy-quality review, but the copy-quality audit status for this report "
        f"is {copy_audit.status}. Wording does not change the underlying "
        "evidence, confidence, or attribution; every substantive claim remains "
        "traceable to evidence. When evidence is incomplete, unavailable, "
        "ambiguous, or unsupported, Workprint states that limitation rather "
        "than filling the gap with speculation."
        + fixture_text
    )


def _project_tools(observations: tuple[Observation, ...]) -> ExecutiveFinding:
    found: list[str] = []
    evidence_ids: list[str] = []
    evidence_refs: list[str] = []
    for item in observations:
        for tool, pattern in TOOL_PATTERNS.items():
            if re.search(pattern, item.statement, flags=re.IGNORECASE):
                if tool not in found:
                    found.append(tool)
                evidence_ids.append(item.id)
                for ref in item.evidence_refs:
                    if ref not in evidence_refs:
                        evidence_refs.append(ref)
    if not found:
        return ExecutiveFinding(
            id="OV-002",
            title="Project tools explicitly observed",
            summary=(
                "The available evidence does not explicitly establish the tools "
                "used as part of project activity."
            ),
            status="unknown",
            rationale=(
                "Evidence sources analyzed are not treated as project tools unless "
                "tool use is explicitly stated in the evidence."
            ),
        )
    return ExecutiveFinding(
        id="OV-002",
        title="Project tools explicitly observed",
        summary="Explicitly observed project tools: " + ", ".join(sorted(found)) + ".",
        status="explicitly_supported",
        evidence_ids=tuple(sorted(set(evidence_ids))),
        evidence_refs=tuple(evidence_refs),
        rationale="Tools are reported only when the evidence explicitly shows tool use.",
    )


def _project_overview(
    investigation: Investigation,
    observations: tuple[Observation, ...],
    fixture_boundary: dict[str, object],
) -> tuple[ExecutiveFinding, ...]:
    overview: list[ExecutiveFinding] = []
    if fixture_boundary.get("all_selected_evidence_is_fixture"):
        overview.append(
            ExecutiveFinding(
                id="OV-000",
                title="Fixture evidence boundary",
                summary=(
                    "This report analyzes sample fixture evidence included with "
                    "the Workprint repository. It does not reconstruct the "
                    "repository's complete real-world development history."
                ),
                status="sample_fixture_evidence",
                evidence_refs=tuple(fixture_boundary.get("fixture_files", ())),
                rationale=(
                    "Fixture status is determined from selected source file paths "
                    "under the repository fixtures directory."
                ),
            )
        )
    overview.extend([
        ExecutiveFinding(
            id="OV-001",
            title="Evidence sources analyzed",
            summary=_evidence_source_summary(investigation),
            status="captured_evidence",
            evidence_ids=tuple(item.id for item in observations),
            evidence_refs=_all_refs(observations),
            rationale=(
                "This describes evidence Workprint analyzed, not the complete "
                "toolset used to create the project."
            ),
        ),
        _project_tools(observations),
        _unconfirmed_tools(),
    ])
    return tuple(overview)


def _unconfirmed_tools() -> ExecutiveFinding:
    return ExecutiveFinding(
        id="OV-003",
        title="Unconfirmed tool information",
        summary="Workprint does not infer a complete project toolset.",
        status="unknown",
        rationale=(
            "An adapter or source file proves only that Workprint analyzed that "
            "evidence source."
        ),
    )


def _evidence_source_summary(investigation: Investigation) -> str:
    source_counts = Counter(_source_label(item.source) for item in investigation.observations)
    if not source_counts:
        return "No evidence sources were analyzed."
    rendered = ", ".join(
        f"{source}: {count} observation(s)"
        for source, count in sorted(source_counts.items())
    )
    return f"Workprint analyzed evidence from {rendered}."


def _source_label(source: str) -> str:
    return SOURCE_LABELS.get(source, SOURCE_LABELS.get(source.lower(), source))


def _fixture_boundary(investigation: Investigation) -> dict[str, object]:
    files = tuple(investigation.source_files)
    fixture_files = tuple(item for item in files if _is_fixture_path(item))
    return {
        "all_selected_evidence_is_fixture": bool(files) and len(fixture_files) == len(files),
        "fixture_files": fixture_files,
        "source_file_count": len(files),
    }


def _is_fixture_path(path: str) -> bool:
    parts = PurePosixPath(path.replace("\\", "/")).parts
    return "fixtures" in parts


def _evolution_summary(milestones: tuple[ExecutiveFinding, ...]) -> str:
    established = [item for item in milestones if item.status != "not_established"]
    if not established:
        return (
            "The available evidence does not establish significant project "
            "milestones under the v1 rules."
        )
    unique_statuses = list(dict.fromkeys(item.status for item in established))
    labels = _join_natural(unique_statuses[:3])
    return (
        f"Workprint identified {len(established)} significant milestone(s), "
        f"including {labels}."
    )


def _collaboration_summary(collaboration: tuple[ExecutiveFinding, ...]) -> str:
    profile = next(
        (item.summary for item in collaboration if item.id == "COL-003"),
        "The available evidence does not establish a collaboration pattern.",
    )
    return profile


def _unknowns_summary(gaps: tuple[EvidenceGap, ...]) -> str:
    return f"Workprint recorded {len(gaps)} evidence gap(s) or limitation(s)."


def _summarize_items(prefix: str, items: list[Observation]) -> str:
    first = _compact(_plain_statement(items[0].statement), 180)
    if len(items) == 1:
        return f"{prefix}: {first}"
    return f"{prefix} across {len(items)} captured record(s), including: {first}"


def _confidence_summary(confidence: ConfidenceAssessment) -> str:
    reason = confidence.gaps.rstrip(".")
    if confidence.corroboration.startswith("No executive claim"):
        reason = "important claims are not independently corroborated"
    return f"Overall confidence is {confidence.band} because {reason}."


def _plain_statement(text: str) -> str:
    value = " ".join(text.split())
    replacements = (
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|figma)\s+reported implementation activity:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|figma)\s+stated a decision or acceptance:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|figma)\s+stated a decision:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|figma)\s+suggested:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|figma)\s+asked:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|figma)\s+stated:\s*",
        r"^figma stated:\s*",
    )
    for pattern in replacements:
        value = re.sub(pattern, "", value, flags=re.IGNORECASE)
    value = re.sub(r";\s*component metadata:.*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r";\s*explicit evidence metadata present$", "", value, flags=re.IGNORECASE)
    value = re.sub(
        r"^I added a fixture that represents (.+)$",
        r"A test fixture was added to represent \1",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^I created the repository and pushed the initial files\.?$",
        "The repository was created and the initial files were pushed.",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^I created the GitHub repository and pushed the first commit\.?$",
        "The GitHub repository was created and the first commit was pushed.",
        value,
        flags=re.IGNORECASE,
    )
    return _compact(value.strip(), 240)


def _join_natural(items: list[str]) -> str:
    if not items:
        return "no established categories"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _compact(text: str, limit: int = 220) -> str:
    value = " ".join(text.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."

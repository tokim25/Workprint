from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath

from workprint.copy_audit import CopyQualityAuditor, SCANNED_SECTION_NAMES
from workprint.executive_constants import (
    UNSLOP_TEXT_AUTHOR,
    UNSLOP_TEXT_LICENSE,
    UNSLOP_TEXT_PINNED_REVISION,
    UNSLOP_TEXT_PROJECT,
    UNSLOP_TEXT_REPOSITORY,
)
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
COPY_AUDITED_SECTIONS = SCANNED_SECTION_NAMES
GIT_AUTHORSHIP_BOUNDARY = (
    "Git author and committer fields preserve identities recorded in "
    "repository history. They do not prove who personally wrote every changed "
    "line, establish ownership, or measure contribution."
)

CONFIDENCE_ORDER = ("Very High", "High", "Moderate", "Limited", "Low")

SOURCE_LABELS = {
    "chatgpt": "ChatGPT",
    "ChatGPT": "ChatGPT",
    "claude": "Claude",
    "Claude": "Claude",
    "figma": "Figma",
    "Figma": "Figma",
    "git": "Git",
    "Git": "Git",
    "google-docs": "Google Docs",
    "Google Docs": "Google Docs",
    "project-notes": "Project Notes",
    "Project Notes": "Project Notes",
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
    r"\badd\b",
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
        fixture_boundary = _fixture_boundary(self.investigation)
        has_git = _has_git_evidence(observations)

        brief = ExecutiveBrief(
            project_goal=goal,
            project_outputs=outputs,
            evolution_summary=_evolution_summary(milestones),
            collaboration_summary=_collaboration_summary(collaboration),
            confidence_summary=_confidence_summary(confidence),
            unknowns_summary=_unknowns_summary(gaps),
        )

        overview = _project_overview(self.investigation, observations, fixture_boundary)
        draft_assurance = _investigation_assurance_method(fixture_boundary, has_git)
        audit_sections = _copy_audit_sections(
            brief=brief,
            overview=overview,
            milestones=milestones,
            collaboration=collaboration,
            decisions=decisions,
            confidence=confidence,
            gaps=gaps,
            assurance=draft_assurance,
        )
        copy_audit = CopyQualityAuditor().audit(audit_sections)
        assurance = _investigation_assurance(copy_audit, fixture_boundary, has_git)

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
                "git_authorship_boundary": GIT_AUTHORSHIP_BOUNDARY if has_git else None,
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


def _has_git_evidence(observations: tuple[Observation, ...]) -> bool:
    return any(item.source == "git" for item in observations)


def _git_commit_subject(item: Observation) -> str:
    return str((item.metadata or {}).get("subject") or "")


def _is_git_commit_observation(item: Observation) -> bool:
    return (
        item.source == "git"
        and item.activity == "implementation"
        and bool((item.metadata or {}).get("commit_sha"))
        and not item.artifact
        and "repository file change" not in item.statement.lower()
    )


def _is_major_git_capability_subject(subject: str) -> bool:
    value = subject.lower()
    if value.startswith(("chore", "refactor", "test")):
        return False
    if any(term in value for term in ("fixture", "template", "metadata")):
        return False
    capability_terms = (
        "investigation engine",
        "observation model",
        "timeline report",
        "timeline reporting",
        "google docs adapter",
        "figma",
        "project discovery",
        "guided investigation",
        "executive report",
        "foundation",
        "copy quality audit",
        "copy-quality audit",
        "git adapter",
    )
    action_terms = ("add", "introduce", "implement", "integrate", "complete")
    return any(term in value for term in capability_terms) and any(
        action in value for action in action_terms
    )


def _is_named_git_branch_merge(subject: str) -> bool:
    value = subject.lower()
    if "merge pull request" not in value and not value.startswith("merge "):
        return False
    return any(
        marker in value
        for marker in (
            "/feature/",
            "/fix/",
            "/design/",
            "/docs/",
            "feature/",
            "fix/",
            "design/",
            "docs/",
            "documentation",
        )
    )


def _is_major_git_correction_subject(subject: str) -> bool:
    value = subject.lower()
    return any(
        term in value
        for term in ("restore", "revert", "migration", "migrate", "major correction")
    )


def _is_explicit_validation_or_release_subject(subject: str) -> bool:
    value = subject.lower()
    return any(term in value for term in ("release", "validated", "validation milestone"))


def _clean_git_subject(subject: str) -> str:
    value = re.sub(
        r"^(feat|fix|docs|design|chore|refactor|test)(\([^)]+\))?:\s*",
        "",
        subject,
        flags=re.IGNORECASE,
    )
    return value[:1].upper() + value[1:] if value else "Git milestone"


def _branch_name_from_merge_subject(subject: str) -> str:
    match = re.search(r"from\s+[^/\s]+/([^\s]+)$", subject, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(
        r"merge\s+(?:branch\s+)?['\"]?([^'\"]+)['\"]?",
        subject,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else ""


def _title_from_branch(branch: str) -> str:
    tail = branch.split("/")[-1]
    words = tail.replace("-", " ").replace("_", " ").strip()
    special = {
        "timeline report": "Timeline reporting",
        "google docs adapter": "Google Docs adapter",
        "figma adapter": "Figma adapter",
        "project discovery": "Project discovery",
        "guided investigation": "Guided investigation",
        "executive report": "Executive Report v1",
        "unslop text audit": "Copy-quality audit",
        "branch discipline": "Branch discipline documentation",
    }
    return special.get(words.lower(), words[:1].upper() + words[1:])


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
                "No explicit statement of the project's overall goal appears "
                "in the supplied evidence."
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
                    "No completed or planned project-level output is established "
                    "by the supplied evidence."
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
    if item.source == "git":
        return _git_commit_supports_project_output(item)
    statement = item.statement.lower()
    if _matches(statement, NON_PROJECT_OUTPUT_PATTERNS):
        return False
    return _matches(statement, PROJECT_OUTPUT_PATTERNS)


def _git_commit_supports_project_output(item: Observation) -> bool:
    if not _is_git_commit_observation(item):
        return False
    subject = _git_commit_subject(item)
    if not subject:
        return False
    return _is_major_git_capability_subject(subject)


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
                rationale=_milestone_rationale(reason, items),
            )
        )
    if milestones:
        return tuple(_prioritize_milestones(milestones, by_id))
    return (
        ExecutiveFinding(
            id="MS-001",
            title="Key milestones",
            summary=(
                "No project milestones are established under the v1 milestone "
                "rules."
            ),
            status="not_established",
            rationale="Routine observations are not promoted to milestones.",
        ),
    )


def _milestone_reason(items: list[Observation]) -> str:
    if items and all(item.source == "git" for item in items):
        return _git_milestone_reason(items)
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


def _git_milestone_reason(items: list[Observation]) -> str:
    for item in items:
        if not _is_git_commit_observation(item):
            continue
        metadata = item.metadata or {}
        subject = _git_commit_subject(item)
        subject_lower = subject.lower()
        tags = metadata.get("tags") or ()
        parents = metadata.get("parent_shas") or ()
        if tags:
            return "a release or version milestone"
        if metadata.get("is_merge") and _is_named_git_branch_merge(subject):
            return "a branch integration"
        if not parents and "initial commit" in subject_lower:
            return "repository establishment"
        if _is_major_git_correction_subject(subject):
            return "a major correction or reversal"
        if _is_major_git_capability_subject(subject):
            return "a completed or created output"
        if _is_explicit_validation_or_release_subject(subject):
            return "a validated implementation milestone"
    return ""


def _prioritize_milestones(
    milestones: list[ExecutiveFinding],
    observations_by_id: dict[str, Observation],
    limit: int = 8,
) -> list[ExecutiveFinding]:
    if len(milestones) <= limit:
        return milestones

    def topic(item: ExecutiveFinding) -> str:
        value = f"{item.title} {item.summary}".lower()
        for marker, key in (
            ("repository established", "repository"),
            ("investigation engine", "investigation-engine"),
            ("observation model", "observation-model"),
            ("timeline", "timeline"),
            ("google docs", "google-docs"),
            ("figma", "figma"),
            ("project discovery", "project-discovery"),
            ("guided investigation", "guided-investigation"),
            ("executive report", "executive-report"),
            ("foundation", "foundation"),
            ("copy-quality audit", "copy-quality-audit"),
            ("copy quality audit", "copy-quality-audit"),
            ("git adapter", "git-adapter"),
        ):
            if marker in value:
                return key
        return item.id

    topic_rank = {
        "repository": 0,
        "investigation-engine": 1,
        "observation-model": 2,
        "timeline": 3,
        "google-docs": 4,
        "copy-quality-audit": 5,
        "guided-investigation": 6,
        "executive-report": 7,
        "figma": 8,
        "project-discovery": 9,
        "foundation": 10,
        "git-adapter": 11,
    }

    def priority(item: ExecutiveFinding) -> tuple[int, int, int, int]:
        observations = [
            observations_by_id[obs_id]
            for obs_id in item.evidence_ids
            if obs_id in observations_by_id
        ]
        newest = max(
            (
                int(obs.timestamp.timestamp())
                for obs in observations
                if obs.timestamp is not None
            ),
            default=0,
        )
        status_rank = 0 if item.status != "a branch integration" else 1
        return (
            topic_rank.get(topic(item), 99),
            status_rank,
            -newest,
            int(item.id.split("-")[-1]),
        )

    ordered = sorted(milestones, key=priority)
    selected: list[ExecutiveFinding] = []
    selected_topics: set[str] = set()
    for item in ordered:
        if len(selected) >= limit:
            break
        item_topic = topic(item)
        if item_topic in selected_topics:
            continue
        selected.append(item)
        selected_topics.add(item_topic)

    if len(selected) < limit:
        for item in ordered:
            if item not in selected:
                selected.append(item)
            if len(selected) >= limit:
                break

    selected.sort(key=lambda item: int(item.id.split("-")[-1]))
    return [
        ExecutiveFinding(
            id=f"MS-{index:03d}",
            title=item.title,
            summary=item.summary,
            status=item.status,
            evidence_ids=item.evidence_ids,
            evidence_refs=item.evidence_refs,
            rationale=item.rationale,
        )
        for index, item in enumerate(selected, start=1)
    ]


def _milestone_rationale(reason: str, items: list[Observation]) -> str:
    anchor = "Captured evidence"
    if items:
        anchor = _compact(_milestone_summary(reason, items), 80).rstrip(".")
    suffix = {
        "repository establishment": "supports this milestone as repository establishment evidence.",
        "an explicit decision": "supports this milestone as explicit decision evidence.",
        "a completed or created output": "supports this milestone as completed or created work.",
        "a release or version milestone": "supports this milestone as release or version evidence.",
        "a branch integration": "supports this milestone as repository integration evidence.",
        "a material requirement change": "supports this milestone as a material requirement change.",
        "a validated implementation milestone": "supports this milestone as validation evidence.",
        "a major correction or reversal": "supports this milestone as correction or reversal evidence.",
    }.get(reason, "supports this key milestone.")
    return f"{anchor} {suffix}"


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
    if items and all(item.source == "git" for item in items):
        return _git_milestone_title(reason, items)
    summary = _milestone_summary(reason, items)
    prefix = {
        "repository establishment": "Repository",
        "an explicit decision": "Decision",
        "a completed or created output": "Completed work",
        "a release or version milestone": "Release",
        "a branch integration": "Branch integration",
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


def _git_milestone_title(reason: str, items: list[Observation]) -> str:
    selected = _selected_git_milestone_observation(reason, items)
    subject = _git_commit_subject(selected)
    subject_lower = subject.lower()
    if reason == "repository establishment":
        return "Repository established"
    if reason == "a branch integration":
        branch = _branch_name_from_merge_subject(subject)
        return f"{_title_from_branch(branch)} merged" if branch else "Branch integration merged"
    if reason == "a release or version milestone":
        tags = (selected.metadata or {}).get("tags") or ()
        return f"Release {'/'.join(tags)} recorded" if tags else "Release milestone recorded"
    known_titles = (
        ("investigation engine", "Deterministic investigation engine added"),
        ("observation model", "Canonical observation model introduced"),
        ("timeline report", "Timeline reporting added"),
        ("timeline reporting", "Timeline reporting added"),
        ("google docs adapter", "Google Docs adapter added"),
        ("figma", "Figma adapter added"),
        ("project discovery", "Project discovery added"),
        ("guided investigation", "Guided investigation added"),
        ("executive report", "Executive Report v1 added"),
        ("foundation", "Foundation documentation added"),
        ("copy quality audit", "Copy-quality audit integrated"),
        ("copy-quality audit", "Copy-quality audit integrated"),
        ("git adapter", "Git adapter added"),
    )
    for marker, title in known_titles:
        if marker in subject_lower:
            return title
    return _compact(_clean_git_subject(subject), 88)


def _milestone_summary(reason: str, items: list[Observation]) -> str:
    if not items:
        return "The available evidence establishes a project milestone."
    selected = items[0]
    if items and all(item.source == "git" for item in items):
        selected = _selected_git_milestone_observation(reason, items)
    elif reason == "a branch integration":
        selected = next(
            (
                item for item in items
                if (item.metadata or {}).get("is_merge")
                and "merge commit" in item.statement.lower()
            ),
            selected,
        )
    elif reason == "a completed or created output":
        selected = next(
            (
                item for item in items
                if item.source == "git"
                and "recorded commit" in item.statement.lower()
            ),
            selected,
        )
    plain = _plain_statement(selected.statement)
    return plain


def _selected_git_milestone_observation(reason: str, items: list[Observation]) -> Observation:
    candidates = [item for item in items if _is_git_commit_observation(item)]
    if not candidates:
        return items[0]
    if reason == "a branch integration":
        return next((item for item in candidates if (item.metadata or {}).get("is_merge")), candidates[0])
    if reason == "repository establishment":
        return next((item for item in candidates if not (item.metadata or {}).get("parent_shas")), candidates[0])
    return candidates[0]


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
    return "Workprint could not establish a collaboration pattern from the supplied evidence."


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
                    _decision_alternative(_decision_summary(items)),
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
    return _plain_statement(items[0].statement)


def _decision_alternative(summary: str) -> str:
    subject = _compact(summary.rstrip("."), 72)
    return (
        f"{subject}: other supplied sources do not show whether this decision "
        "was discussed elsewhere."
    )


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
    corroboration = _corroboration(milestones, decisions, observations)
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
    observations: tuple[Observation, ...],
) -> str:
    by_id = {item.id: item for item in observations}
    corroborated: list[str] = []
    for item in milestones:
        sources = _independent_sources(item.evidence_ids, by_id)
        if len(sources) >= 2:
            corroborated.append(item.id)
    for item in decisions:
        sources = _independent_sources(item.evidence_ids, by_id)
        if len(sources) >= 2:
            corroborated.append(item.id)
    if corroborated:
        return (
            "Corroboration is present where two or more independent evidence "
            f"sources support the same claim: {', '.join(corroborated)}."
        )
    return (
        "No executive claim has support from two independent evidence sources; "
        "repeated support within one source is not treated as corroboration."
    )


def _independent_sources(
    evidence_ids: tuple[str, ...],
    observations_by_id: dict[str, Observation],
) -> set[str]:
    return {
        observations_by_id[item_id].source
        for item_id in evidence_ids
        if item_id in observations_by_id
    }


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
    gaps: list[EvidenceGap] = []
    has_git = any(item.source == "git" for item in investigation.observations)
    has_conversation = any(item.source_type == "conversation" for item in investigation.observations)
    has_static_export = any(
        item.source_type in {"document", "design"}
        for item in investigation.observations
    )
    has_shallow_git = any(
        item.source == "git" and (item.metadata or {}).get("is_shallow")
        for item in investigation.observations
    )
    if not has_git:
        gaps.append(
            EvidenceGap(
                id="GAP-001",
                summary="Git history was not analyzed.",
                why_it_matters=(
                    "Without Git history, Workprint has less evidence for "
                    "file-level implementation sequence and repository chronology."
                ),
                would_reduce_gap="Provide supported local Git evidence.",
                affects=("coverage", "implementation sequence", "authorship boundaries"),
            )
        )
    if has_git:
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary="Activity outside Git history is unavailable.",
                why_it_matters=(
                    "Git evidence does not capture conversations, rationale, "
                    "uncommitted local work, deleted working-tree changes, or "
                    "activity in tools outside the repository."
                ),
                would_reduce_gap="Provide conversation, document, design, or other non-Git evidence.",
                affects=("coverage", "decision sequence", "collaboration"),
            )
        )
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary="Git identities do not establish line-level authorship.",
                why_it_matters=GIT_AUTHORSHIP_BOUNDARY,
                would_reduce_gap="Provide evidence that explicitly maps people to specific actions.",
                affects=("attribution", "authorship boundaries"),
            )
        )
    if has_shallow_git:
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary="Git history appears shallow or incomplete.",
                why_it_matters=(
                    "A shallow repository may omit earlier commits, tags, branch "
                    "history, or context needed to reconstruct chronology."
                ),
                would_reduce_gap="Provide a complete local Git repository history.",
                affects=("coverage", "implementation sequence", "repository chronology"),
            )
        )
    if has_static_export:
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary="Static exports may omit revision history.",
                why_it_matters=(
                    "Static document or design exports may show content without showing "
                    "how it changed over time."
                ),
                would_reduce_gap="Provide revision-aware exports or source history.",
                affects=("coverage", "collaboration", "decision sequence"),
            )
        )
    if not has_git:
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary="Unsupported attribution remains unknown.",
                why_it_matters=(
                    "Captured activity does not establish authorship, ownership, effort, "
                    "value, or contribution percentages."
                ),
                would_reduce_gap="Provide evidence that explicitly maps people to actions.",
                affects=("attribution", "decision leadership"),
            )
        )
    if has_git and not has_conversation:
        gaps.append(
            EvidenceGap(
                id=f"GAP-{len(gaps) + 1:03d}",
                summary="Conversations and decision rationale may be absent.",
                why_it_matters=(
                    "Git records repository changes, but commit metadata often does not "
                    "show the discussion, alternatives, or rationale behind decisions."
                ),
                would_reduce_gap="Provide conversation exports or decision records.",
                affects=("decision leadership", "rationale", "collaboration"),
            )
        )
    for item in investigation.unknowns:
        if _is_duplicate_gap(item, has_git=has_git):
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


def _is_duplicate_gap(text: str, *, has_git: bool = False) -> bool:
    value = text.lower()
    if "revision history" in value and "static export" in value:
        return True
    if has_git and "offline work" in value and "activity outside" in value:
        return True
    return False


def _copy_quality_audit_unavailable() -> CopyQualityAudit:
    return CopyQualityAudit(
        status="unavailable",
        scanner="unslop_text_scan.py",
        upstream_repository=UNSLOP_TEXT_REPOSITORY,
        pinned_revision=UNSLOP_TEXT_PINNED_REVISION,
        scanned_sections=COPY_AUDITED_SECTIONS,
        structural_review_completed=False,
        audit_implementation_version="1.0",
        upstream_author=UNSLOP_TEXT_AUTHOR,
        upstream_project=UNSLOP_TEXT_PROJECT,
        upstream_revision=UNSLOP_TEXT_PINNED_REVISION,
        upstream_license=UNSLOP_TEXT_LICENSE,
        attribution_notice="third_party/vibecoded-design-tells/NOTICE.md",
        scanner_available=False,
        lexical_review_completed=False,
        severity_counts={},
        evidence_preservation_confirmed=False,
        limitations=(
            "The audit identifies documented lexical and structural writing patterns.",
            "The audit does not determine whether text was written by a human or an AI.",
        ),
        disclosure=(
            "Workprint is configured to incorporate JCarterJohnson's "
            "`unslop-text` scanner from the `vibecoded-design-tells` project, "
            "but the pinned scanner was unavailable for this run. The lexical "
            "review was not completed."
        ),
    )


def _copy_audit_sections(
    *,
    brief: ExecutiveBrief,
    overview: tuple[ExecutiveFinding, ...],
    milestones: tuple[ExecutiveFinding, ...],
    collaboration: tuple[ExecutiveFinding, ...],
    decisions: tuple[ExecutiveDecision, ...],
    confidence: ConfidenceAssessment,
    gaps: tuple[EvidenceGap, ...],
    assurance: str,
) -> dict[str, str]:
    return {
        "Executive Brief": "\n\n".join((
            brief.project_goal.summary,
            " ".join(item.summary for item in brief.project_outputs),
            brief.evolution_summary,
            brief.collaboration_summary,
            brief.confidence_summary,
            brief.unknowns_summary,
        )),
        "Project Overview narrative": "\n\n".join(
            f"{item.summary}\n{item.rationale}" for item in overview
        ),
        "Key Milestone summaries": "\n\n".join(
            f"{item.summary}\n{item.rationale}" for item in milestones
        ),
        "Human-AI Collaboration narrative": "\n\n".join(
            f"{item.summary}\n{item.rationale}" for item in collaboration
        ),
        "Decision Analysis prose": "\n\n".join(
            f"{item.summary}\n{item.rationale}\n{' '.join(item.alternative_interpretations)}"
            for item in decisions
        ),
        "Confidence Assessment rationale": "\n\n".join((
            confidence.evidence_strength,
            confidence.coverage,
            confidence.corroboration,
            confidence.conflicts,
            confidence.gaps,
            confidence.rationale,
        )),
        "Evidence Gaps prose": "\n\n".join(
            f"{item.summary}\n{item.why_it_matters}\n{item.would_reduce_gap}"
            for item in gaps
        ),
        "Investigation Assurance": assurance,
    }


def _investigation_assurance_method(
    fixture_boundary: dict[str, object],
    has_git: bool = False,
) -> str:
    fixture_text = ""
    if fixture_boundary.get("all_selected_evidence_is_fixture"):
        fixture_text = (
            " This report analyzes sample fixture evidence included with the "
            "Workprint repository; it does not reconstruct the repository's "
            "complete real-world development history."
        )
    git_text = f" {GIT_AUTHORSHIP_BOUNDARY}" if has_git else ""
    return (
        "This Workprint report is an evidence-backed reconstruction based only "
        "on the sources supplied for investigation. Workprint normalizes "
        "captured evidence, extracts traceable observations, and summarizes "
        "project evolution, collaboration, decisions, confidence, and unknowns. "
        "The report does not infer authorship, ownership, effort, value, or "
        "contribution percentages. Wording does not change the underlying "
        "evidence, confidence, or attribution; every substantive claim remains "
        "traceable to evidence. When evidence is incomplete, unavailable, "
        "ambiguous, or unsupported, Workprint states that limitation rather "
        "than filling the gap with speculation."
        + git_text
        + fixture_text
    )


def _investigation_assurance(
    copy_audit: CopyQualityAudit,
    fixture_boundary: dict[str, object],
    has_git: bool = False,
) -> str:
    base = _investigation_assurance_method(fixture_boundary, has_git)
    if copy_audit.status == "unavailable":
        audit_text = (
            " Workprint is configured to incorporate JCarterJohnson's "
            "`unslop-text` scanner from the `vibecoded-design-tells` project, "
            "but the pinned scanner was unavailable for this run. The lexical "
            "review was not completed."
        )
    elif copy_audit.status == "failed":
        audit_text = (
            " The lexical portion of this review incorporates the `unslop-text` "
            "scanner and methodology developed by JCarterJohnson for the "
            "`vibecoded-design-tells` project. Workprint records the exact "
            "reviewed revision and preserves attribution and licensing "
            "information. Workprint adds deterministic structural checks "
            "because lexical findings alone cannot assess overall writing "
            "quality. The copy-quality audit failed, so this report must not be "
            "described as assured or fully audited."
        )
    else:
        audit_text = (
            " The lexical portion of this review incorporates the `unslop-text` "
            "scanner and methodology developed by JCarterJohnson for the "
            "`vibecoded-design-tells` project. Workprint records the exact "
            "reviewed revision and preserves attribution and licensing "
            "information. Workprint adds deterministic structural checks and "
            "evidence-preservation validation. Structural checks complement the "
            "lexical review because lexical findings alone cannot assess overall "
            "writing quality. A passing audit indicates that the generated "
            "narrative satisfied the configured lexical and structural review. "
            "It does not establish human authorship or prove that AI was not "
            "involved."
        )
    return base + audit_text


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
            id="OV-003",
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
        id="OV-003",
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
    ])
    git_summary = _git_repository_overview(observations)
    if git_summary is not None:
        overview.append(git_summary)
    overview.extend([
        _project_tools(observations),
        _unconfirmed_tools(),
    ])
    return tuple(overview)


def _unconfirmed_tools() -> ExecutiveFinding:
    return ExecutiveFinding(
        id="OV-004",
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
    if set(source_counts) == {"Git"}:
        return "Workprint analyzed local Git repository evidence."
    rendered = ", ".join(
        "Git repository evidence" if source == "Git" else f"{source}: {count} observation(s)"
        for source, count in sorted(source_counts.items())
    )
    return f"Workprint analyzed evidence from {rendered}."


def _git_repository_overview(observations: tuple[Observation, ...]) -> ExecutiveFinding | None:
    git_observations = [item for item in observations if item.source == "git"]
    if not git_observations:
        return None
    commit_observations = [item for item in git_observations if _is_git_commit_observation(item)]
    repository_obs = next(
        (item for item in git_observations if (item.metadata or {}).get("repository_root") and not (item.metadata or {}).get("commit_sha")),
        None,
    )
    metadata = repository_obs.metadata if repository_obs and repository_obs.metadata else {}
    repository = metadata.get("repository_root") or "the selected local Git repository"
    branch = metadata.get("current_branch")
    shallow = bool(metadata.get("is_shallow"))
    timestamps = sorted(
        item.timestamp for item in commit_observations if item.timestamp is not None
    )
    date_range = ""
    if timestamps:
        start = timestamps[0].date().isoformat()
        end = timestamps[-1].date().isoformat()
        date_range = f" from {start} to {end}" if start != end else f" on {start}"
    branch_text = f" on branch `{branch}`" if branch else ""
    shallow_text = " The repository reports shallow history." if shallow else " The repository does not report shallow history."
    commit_count = len(commit_observations)
    commit_noun = "commit" if commit_count == 1 else "commits"
    summary = (
        f"Workprint analyzed {commit_count} {commit_noun} from the local "
        f"Git repository `{repository}`{branch_text}{date_range}."
        + shallow_text
    )
    return ExecutiveFinding(
        id="OV-002",
        title="Git repository analyzed",
        summary=summary,
        status="captured_evidence",
        evidence_ids=tuple(item.id for item in git_observations),
        evidence_refs=_refs(git_observations),
        rationale=(
            "Commit counts describe available repository history only; they are "
            "not productivity, ownership, effort, value, authorship, or contribution measures."
        ),
    )


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
            "Workprint did not identify project milestones under the v1 rules."
        )
    unique_statuses = list(dict.fromkeys(item.status for item in established))
    labels = _join_natural(unique_statuses[:3])
    return (
        f"Workprint identified {len(established)} key milestone(s), "
        f"including {labels}."
    )


def _collaboration_summary(collaboration: tuple[ExecutiveFinding, ...]) -> str:
    profile = next(
        (item.summary for item in collaboration if item.id == "COL-003"),
        "Workprint could not establish a collaboration pattern from the supplied evidence.",
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
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|project-notes|figma|git|Git author:[^:]+)\s+reported implementation activity:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|project-notes|figma|git|Git author:[^:]+)\s+stated a decision or acceptance:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|project-notes|figma|git|Git author:[^:]+)\s+stated a decision:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|project-notes|figma|git|Git author:[^:]+)\s+suggested:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|project-notes|figma|git|Git author:[^:]+)\s+asked:\s*",
        r"^(?:Human|ChatGPT|Claude|Assistant|google-docs|project-notes|figma|git|Git author:[^:]+)\s+stated:\s*",
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
    value = re.sub(
        r"^Git recorded merge commit ([0-9a-f]+):\s*",
        r"\1 merge commit: ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^Git recorded commit ([0-9a-f]+):\s*",
        r"\1 commit: ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^Git recorded repository file change ([A-Z]) for ",
        r"Repository file change \1: ",
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

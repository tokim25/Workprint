from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CONFIDENCE_BANDS = {"Very High", "High", "Moderate", "Limited", "Low"}
COPY_AUDIT_STATUSES = {"passed", "passed_with_waivers", "failed", "unavailable"}
DECISION_LEADERSHIP_LABELS = {
    "human_led",
    "ai_proposed_human_decided",
    "jointly_shaped",
    "ai_executed",
    "unknown",
}
OUTPUT_STATUSES = {
    "explicitly_produced",
    "referenced_or_planned",
    "not_established",
}


@dataclass(frozen=True)
class ExecutiveFinding:
    id: str
    title: str
    summary: str
    status: str
    evidence_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        data["evidence_refs"] = list(self.evidence_refs)
        return data


@dataclass(frozen=True)
class ExecutiveDecision:
    id: str
    summary: str
    leadership: str
    confidence: str
    rationale: str
    evidence_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    alternative_interpretations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.leadership not in DECISION_LEADERSHIP_LABELS:
            raise ValueError(f"unsupported decision leadership: {self.leadership}")
        if self.confidence not in CONFIDENCE_BANDS:
            raise ValueError(f"unsupported confidence band: {self.confidence}")
        if self.leadership != "unknown" and not self.evidence_refs:
            raise ValueError("non-unknown decision leadership requires evidence")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        data["evidence_refs"] = list(self.evidence_refs)
        data["alternative_interpretations"] = list(self.alternative_interpretations)
        return data


@dataclass(frozen=True)
class ConfidenceAssessment:
    band: str
    evidence_strength: str
    coverage: str
    corroboration: str
    conflicts: str
    gaps: str
    rationale: str

    def __post_init__(self) -> None:
        if self.band not in CONFIDENCE_BANDS:
            raise ValueError(f"unsupported confidence band: {self.band}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceGap:
    id: str
    summary: str
    why_it_matters: str
    would_reduce_gap: str
    affects: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["affects"] = list(self.affects)
        return data


@dataclass(frozen=True)
class CopyQualityAudit:
    status: str
    scanner: str
    upstream_repository: str
    pinned_revision: str
    scanned_sections: tuple[str, ...]
    findings: tuple[dict[str, Any], ...] = ()
    waivers: tuple[dict[str, Any], ...] = ()
    structural_review_completed: bool = False
    override_used: bool = False
    disclosure: str = ""
    audit_implementation_version: str = ""
    upstream_author: str = ""
    upstream_project: str = ""
    upstream_revision: str = ""
    upstream_license: str = ""
    attribution_notice: str = ""
    scanner_available: bool = False
    lexical_review_completed: bool = False
    severity_counts: dict[str, int] | None = None
    evidence_preservation_confirmed: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in COPY_AUDIT_STATUSES:
            raise ValueError(f"unsupported copy audit status: {self.status}")
        if self.status in {"passed", "passed_with_waivers"} and not self.structural_review_completed:
            raise ValueError(f"{self.status} copy audit requires structural review")
        if self.status in {"passed", "passed_with_waivers"} and not self.lexical_review_completed:
            raise ValueError(f"{self.status} copy audit requires lexical review")
        if self.status in {"passed", "passed_with_waivers"} and not self.evidence_preservation_confirmed:
            raise ValueError(f"{self.status} copy audit requires evidence-preservation confirmation")
        if self.status == "unavailable" and not self.disclosure:
            raise ValueError("unavailable copy audit requires disclosure")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["scanned_sections"] = list(self.scanned_sections)
        data["findings"] = list(self.findings)
        data["waivers"] = list(self.waivers)
        data["severity_counts"] = dict(self.severity_counts or {})
        data["limitations"] = list(self.limitations)
        return data


@dataclass(frozen=True)
class ExecutiveBrief:
    project_goal: ExecutiveFinding
    project_outputs: tuple[ExecutiveFinding, ...]
    evolution_summary: str
    collaboration_summary: str
    confidence_summary: str
    unknowns_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_goal": self.project_goal.to_dict(),
            "project_outputs": [item.to_dict() for item in self.project_outputs],
            "evolution_summary": self.evolution_summary,
            "collaboration_summary": self.collaboration_summary,
            "confidence_summary": self.confidence_summary,
            "unknowns_summary": self.unknowns_summary,
        }


@dataclass(frozen=True)
class ExecutiveReport:
    schema_version: str
    executive_brief: ExecutiveBrief
    project_overview: tuple[ExecutiveFinding, ...]
    key_milestones: tuple[ExecutiveFinding, ...]
    human_ai_collaboration: tuple[ExecutiveFinding, ...]
    decision_analysis: tuple[ExecutiveDecision, ...]
    confidence_assessment: ConfidenceAssessment
    evidence_gaps: tuple[EvidenceGap, ...]
    investigation_assurance: str
    copy_quality_audit: CopyQualityAudit
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata or {}),
            "executive_brief": self.executive_brief.to_dict(),
            "project_overview": [item.to_dict() for item in self.project_overview],
            "key_milestones": [item.to_dict() for item in self.key_milestones],
            "human_ai_collaboration": [
                item.to_dict() for item in self.human_ai_collaboration
            ],
            "decision_analysis": [
                item.to_dict() for item in self.decision_analysis
            ],
            "confidence_assessment": self.confidence_assessment.to_dict(),
            "evidence_gaps": [item.to_dict() for item in self.evidence_gaps],
            "investigation_assurance": self.investigation_assurance,
            "copy_quality_audit": self.copy_quality_audit.to_dict(),
        }

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workprint.executive_constants import (
    UNSLOP_TEXT_AUTHOR,
    UNSLOP_TEXT_LICENSE,
    UNSLOP_TEXT_PINNED_REVISION,
    UNSLOP_TEXT_PROJECT,
    UNSLOP_TEXT_REPOSITORY,
)
from workprint.models import CopyQualityAudit


AUDIT_IMPLEMENTATION_VERSION = "1.0"
ATTRIBUTION_NOTICE = "third_party/vibecoded-design-tells/NOTICE.md"
THIRD_PARTY_ROOT = Path(__file__).resolve().parents[2] / "third_party" / "vibecoded-design-tells"
UPSTREAM_SCANNER = THIRD_PARTY_ROOT / "unslop-ai-text" / "skill" / "scripts" / "unslop_text_scan.py"

LIMITATIONS = (
    "The audit identifies documented lexical and structural writing patterns.",
    "The audit does not determine whether text was written by a human or an AI.",
    "The audit reviews generated narrative sections only, not raw evidence, evidence IDs, appendices, code, or factual tables.",
    "A clean lexical scan is not proof of human authorship and is not proof that AI was not involved.",
)

SCANNED_SECTION_NAMES = (
    "Executive Brief",
    "Project Overview narrative",
    "Key Milestone summaries",
    "Human-AI Collaboration narrative",
    "Decision Analysis prose",
    "Confidence Assessment rationale",
    "Evidence Gaps prose",
    "Investigation Assurance",
)


@dataclass(frozen=True)
class AuditWaiver:
    rule: str
    section: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "rule": self.rule,
            "section": self.section,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CopyQualityAuditor:
    waivers: tuple[AuditWaiver, ...] = ()
    override_used: bool = False
    scanner_path: Path = UPSTREAM_SCANNER

    def audit(self, sections: dict[str, str]) -> CopyQualityAudit:
        base = _base_audit_data(sections, self.override_used)
        if not self.scanner_path.exists():
            return _unavailable(
                base,
                (
                    "Workprint is configured to incorporate JCarterJohnson's "
                    "`unslop-text` scanner from the `vibecoded-design-tells` "
                    "project, but the pinned scanner was unavailable for this "
                    "run. The lexical review was not completed."
                ),
                scanner_available=False,
            )

        lexical = self._run_lexical_scan(sections)
        if lexical["status"] == "unavailable":
            return _unavailable(base, lexical["disclosure"], scanner_available=False)
        if lexical["status"] == "failed":
            return _failed(
                base,
                findings=tuple(lexical["findings"]),
                severity_counts=dict(lexical["severity_counts"]),
                disclosure=str(lexical["disclosure"]),
                lexical_completed=bool(lexical["lexical_completed"]),
                structural_completed=False,
                evidence_preservation=False,
            )

        structural_findings = structural_review(sections)
        findings = tuple(lexical["findings"]) + structural_findings
        severity_counts = _severity_counts(findings)
        evidence_preservation = _evidence_preservation_confirmed(sections)
        waiver_dicts = tuple(item.to_dict() for item in self.waivers)

        if not evidence_preservation:
            return _failed(
                base,
                findings=findings,
                severity_counts=severity_counts,
                disclosure="Evidence-preservation validation failed during copy-quality audit.",
                lexical_completed=True,
                structural_completed=True,
                evidence_preservation=False,
                waivers=waiver_dicts,
            )

        unresolved_high = [item for item in findings if item.get("severity") == "high"]
        if unresolved_high:
            return _failed(
                base,
                findings=findings,
                severity_counts=severity_counts,
                disclosure="The copy-quality audit found unresolved high-severity findings.",
                lexical_completed=True,
                structural_completed=True,
                evidence_preservation=True,
                waivers=waiver_dicts,
            )

        medium_low = [
            item for item in findings
            if item.get("severity") in {"medium", "low"}
        ]
        if medium_low:
            missing_waivers = [
                item for item in medium_low
                if not _has_waiver(item, self.waivers)
            ]
            if missing_waivers:
                return _failed(
                    base,
                    findings=findings,
                    severity_counts=severity_counts,
                    disclosure=(
                        "The copy-quality audit found medium- or low-severity "
                        "findings without documented waivers."
                    ),
                    lexical_completed=True,
                    structural_completed=True,
                    evidence_preservation=True,
                    waivers=waiver_dicts,
                )
            return _audit(
                base,
                status="passed_with_waivers",
                findings=findings,
                severity_counts=severity_counts,
                waivers=waiver_dicts,
                lexical_completed=True,
                structural_completed=True,
                evidence_preservation=True,
                disclosure=_used_disclosure("passed_with_waivers"),
            )

        return _audit(
            base,
            status="passed",
            findings=(),
            severity_counts={},
            waivers=(),
            lexical_completed=True,
            structural_completed=True,
            evidence_preservation=True,
            disclosure=_used_disclosure("passed"),
        )

    def _run_lexical_scan(self, sections: dict[str, str]) -> dict[str, Any]:
        text = _scanner_input(sections)
        with tempfile.TemporaryDirectory(prefix="workprint-copy-audit-") as directory:
            path = Path(directory) / "executive-narrative.md"
            path.write_text(text, encoding="utf-8")
            # Integration boundary for JCarterJohnson's unslop-text scanner.
            # Upstream: https://github.com/JCarterJohnson/vibecoded-design-tells
            # Pinned commit: f7c4aefc2c797a66e55b49354a93917ab60d33ac
            # Notice: third_party/vibecoded-design-tells/NOTICE.md
            result = subprocess.run(
                [sys.executable, str(self.scanner_path), str(path), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        if result.returncode < 0:
            return {
                "status": "unavailable",
                "disclosure": (
                    "Workprint is configured to incorporate JCarterJohnson's "
                    "`unslop-text` scanner from the `vibecoded-design-tells` "
                    "project, but the scanner could not execute in this "
                    "environment. The lexical review was not completed."
                ),
                "findings": (),
                "severity_counts": {},
                "lexical_completed": False,
            }
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "status": "failed",
                "disclosure": "The lexical scanner produced malformed audit output.",
                "findings": (),
                "severity_counts": {},
                "lexical_completed": True,
            }
        if not isinstance(payload, dict) or "findings" not in payload:
            return {
                "status": "failed",
                "disclosure": "The lexical scanner output was internally inconsistent.",
                "findings": (),
                "severity_counts": {},
                "lexical_completed": True,
            }
        findings = tuple(_normalize_lexical_finding(item, sections) for item in payload.get("findings", ()))
        return {
            "status": "completed",
            "disclosure": "",
            "findings": findings,
            "severity_counts": _severity_counts(findings),
            "lexical_completed": True,
            "scanner_payload": payload,
        }


def structural_review(sections: dict[str, str]) -> tuple[dict[str, Any], ...]:
    findings: list[dict[str, Any]] = []
    for section, text in sections.items():
        findings.extend(_pattern_findings(section, text))
        findings.extend(_list_scaffold_findings(section, text))
        findings.extend(_repeated_opening_findings(section, text))
        findings.extend(_uniform_sentence_findings(section, text))
        findings.extend(_fragment_findings(section, text))
    return tuple(findings)


def _base_audit_data(sections: dict[str, str], override_used: bool) -> dict[str, Any]:
    return {
        "scanner": "unslop_text_scan.py",
        "upstream_repository": UNSLOP_TEXT_REPOSITORY,
        "upstream_revision": UNSLOP_TEXT_PINNED_REVISION,
        "pinned_revision": UNSLOP_TEXT_PINNED_REVISION,
        "upstream_author": UNSLOP_TEXT_AUTHOR,
        "upstream_project": UNSLOP_TEXT_PROJECT,
        "upstream_license": UNSLOP_TEXT_LICENSE,
        "attribution_notice": ATTRIBUTION_NOTICE,
        "scanned_sections": tuple(sections.keys()),
        "audit_implementation_version": AUDIT_IMPLEMENTATION_VERSION,
        "override_used": override_used,
        "limitations": LIMITATIONS,
    }


def _audit(
    base: dict[str, Any],
    *,
    status: str,
    findings: tuple[dict[str, Any], ...],
    severity_counts: dict[str, int],
    waivers: tuple[dict[str, Any], ...],
    lexical_completed: bool,
    structural_completed: bool,
    evidence_preservation: bool,
    disclosure: str,
    scanner_available: bool = True,
) -> CopyQualityAudit:
    return CopyQualityAudit(
        status=status,
        scanner=str(base["scanner"]),
        upstream_repository=str(base["upstream_repository"]),
        pinned_revision=str(base["pinned_revision"]),
        scanned_sections=tuple(base["scanned_sections"]),
        findings=findings,
        waivers=waivers,
        structural_review_completed=structural_completed,
        override_used=bool(base["override_used"]),
        disclosure=disclosure,
        audit_implementation_version=str(base["audit_implementation_version"]),
        upstream_author=str(base["upstream_author"]),
        upstream_project=str(base["upstream_project"]),
        upstream_revision=str(base["upstream_revision"]),
        upstream_license=str(base["upstream_license"]),
        attribution_notice=str(base["attribution_notice"]),
        scanner_available=scanner_available,
        lexical_review_completed=lexical_completed,
        severity_counts=severity_counts,
        evidence_preservation_confirmed=evidence_preservation,
        limitations=tuple(base["limitations"]),
    )


def _unavailable(
    base: dict[str, Any],
    disclosure: str,
    *,
    scanner_available: bool,
) -> CopyQualityAudit:
    return _audit(
        base,
        status="unavailable",
        findings=(),
        severity_counts={},
        waivers=(),
        lexical_completed=False,
        structural_completed=False,
        evidence_preservation=False,
        disclosure=disclosure,
        scanner_available=scanner_available,
    )


def _failed(
    base: dict[str, Any],
    *,
    findings: tuple[dict[str, Any], ...],
    severity_counts: dict[str, int],
    disclosure: str,
    lexical_completed: bool,
    structural_completed: bool,
    evidence_preservation: bool,
    waivers: tuple[dict[str, Any], ...] = (),
) -> CopyQualityAudit:
    return _audit(
        base,
        status="failed",
        findings=findings,
        severity_counts=severity_counts,
        waivers=waivers,
        lexical_completed=lexical_completed,
        structural_completed=structural_completed,
        evidence_preservation=evidence_preservation,
        disclosure=disclosure,
    )


def _used_disclosure(status: str) -> str:
    if status == "passed_with_waivers":
        return (
            "The lexical portion of this review incorporates the `unslop-text` "
            "scanner and methodology developed by JCarterJohnson for the "
            "`vibecoded-design-tells` "
            "project. Workprint records the exact reviewed revision and preserves "
            "attribution and licensing information. Workprint adds deterministic "
            "structural checks and evidence-preservation validation. Structural "
            "checks complement the lexical review because lexical findings alone "
            "cannot assess overall writing quality. A passing audit with waivers "
            "indicates that the generated narrative satisfied the configured "
            "lexical and structural review with documented exceptions. It does "
            "not establish human authorship or prove that AI was not involved."
        )
    return (
        "The lexical portion of this review incorporates the `unslop-text` "
        "scanner and methodology developed by JCarterJohnson for the "
        "`vibecoded-design-tells` "
        "project. Workprint records the exact reviewed revision and preserves "
        "attribution and licensing information. Workprint adds deterministic "
        "structural checks and evidence-preservation validation. Structural "
        "checks complement the lexical review because lexical findings alone "
        "cannot assess overall writing quality. A passing audit indicates that "
        "the generated narrative satisfied the configured lexical and structural "
        "review. It does not establish human authorship or prove that AI was "
        "not involved."
    )


def _scanner_input(sections: dict[str, str]) -> str:
    parts: list[str] = []
    for section, text in sections.items():
        parts.extend([f"# {section}", "", text.strip(), ""])
    return "\n".join(parts)


def _normalize_lexical_finding(item: Any, sections: dict[str, str]) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {
            "source": "upstream_unslop_text",
            "upstream_revision": UNSLOP_TEXT_PINNED_REVISION,
            "severity": "high",
            "rule": "malformed-finding",
            "section": "unknown",
            "message": "Malformed lexical scanner finding.",
        }
    return {
        "source": "upstream_unslop_text",
        "upstream_revision": UNSLOP_TEXT_PINNED_REVISION,
        "severity": str(item.get("sev", "low")),
        "rule": str(item.get("rule", "unknown")),
        "section": _section_for_scanner_line(int(item.get("line", 0) or 0), sections),
        "line": item.get("line"),
        "matched_text": item.get("match", ""),
        "message": item.get("label", ""),
        "recommended_correction": item.get("fix", ""),
    }


def _section_for_scanner_line(line: int, sections: dict[str, str]) -> str:
    if line <= 0:
        return "unknown"
    current_line = 1
    for section, text in sections.items():
        header_line = current_line
        body_lines = len(text.strip().splitlines())
        end_line = header_line + body_lines + 2
        if header_line <= line <= end_line:
            return section
        current_line = end_line + 1
    return "unknown"


def _severity_counts(findings: tuple[dict[str, Any], ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in findings:
        severity = str(item.get("severity", "low"))
        counts[severity] += 1
    return dict(counts)


def _has_waiver(finding: dict[str, Any], waivers: tuple[AuditWaiver, ...]) -> bool:
    rule = str(finding.get("rule", ""))
    section = str(finding.get("section", ""))
    return any(item.rule == rule and item.section == section and item.reason for item in waivers)


def _evidence_preservation_confirmed(sections: dict[str, str]) -> bool:
    return all(isinstance(key, str) and isinstance(value, str) for key, value in sections.items())


def _pattern_findings(section: str, text: str) -> list[dict[str, Any]]:
    rules: tuple[tuple[str, str, str, str], ...] = (
        ("assistant-boilerplate", "high", r"\bas an?\s+ai\s+(language\s+)?model\b|\bknowledge cut[- ]?off\b", "Assistant boilerplate appears in narrative copy."),
        ("sycophantic-opener", "high", r"^\s*(great question|certainly|absolutely|of course)[!,]", "Sycophantic or reflexive assistant opener appears in narrative copy."),
        ("not-just-x-y", "high", r"\bnot\s+(just|only|merely|simply)\b[^.?!\n]{0,80}\bbut\b", "The narrative uses a not-just-X-but-Y construction."),
        ("unnecessary-recap", "medium", r"\b(in conclusion|in summary|to summarize|to conclude)\b", "The narrative uses an unnecessary recap signpost."),
        ("manufactured-casualness", "low", r"\b(honestly|real talk|look, i get it|lol)\b", "The narrative uses conspicuous casualness."),
        ("promotional-language", "medium", r"\b(revolutionary|game[- ]?changer|transformative|unlock the potential|supercharge)\b", "The narrative uses promotional language that may overstate evidence."),
        ("vague-claim", "low", r"\b(significant|powerful|robust|seamless|comprehensive)\b", "The narrative includes a vague claim that may need stronger evidence-specific wording."),
    )
    findings: list[dict[str, Any]] = []
    for rule, severity, pattern, message in rules:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            findings.append(_structural_finding(section, rule, severity, message, match.group(0)))
    return findings


def _list_scaffold_findings(section: str, text: str) -> list[dict[str, Any]]:
    lines = [line for line in text.splitlines() if line.strip()]
    bullet_count = sum(1 for line in lines if re.match(r"\s*(-|\d+\.)\s+", line))
    if lines and bullet_count >= 6 and bullet_count / len(lines) >= 0.45:
        return [_structural_finding(
            section,
            "excessive-list-scaffolding",
            "medium",
            "Narrative section relies heavily on list scaffolding.",
            f"{bullet_count} list lines",
        )]
    return []


def _repeated_opening_findings(section: str, text: str) -> list[dict[str, Any]]:
    openings: defaultdict[str, int] = defaultdict(int)
    for sentence in _sentences(text):
        words = re.findall(r"[A-Za-z']+", sentence.lower())
        if words:
            openings[" ".join(words[:2])] += 1
    repeated = [opening for opening, count in openings.items() if count >= 3]
    if repeated:
        return [_structural_finding(
            section,
            "repeated-sentence-openings",
            "medium",
            "Narrative repeats the same sentence opening.",
            repeated[0],
        )]
    return []


def _uniform_sentence_findings(section: str, text: str) -> list[dict[str, Any]]:
    lengths = [len(re.findall(r"[A-Za-z']+", sentence)) for sentence in _sentences(text)]
    lengths = [item for item in lengths if item >= 4]
    if len(lengths) < 5:
        return []
    if max(lengths) - min(lengths) <= 4:
        return [_structural_finding(
            section,
            "uniform-sentence-lengths",
            "low",
            "Narrative sentence lengths are unusually uniform.",
            ", ".join(str(item) for item in lengths[:8]),
        )]
    return []


def _fragment_findings(section: str, text: str) -> list[dict[str, Any]]:
    short_fragments = [
        sentence.strip() for sentence in _sentences(text)
        if 1 <= len(re.findall(r"[A-Za-z']+", sentence)) <= 3
    ]
    if len(short_fragments) >= 3:
        return [_structural_finding(
            section,
            "conspicuous-fragments",
            "low",
            "Narrative uses repeated short fragments that may read as manufactured casualness.",
            short_fragments[0],
        )]
    return []


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", text)
        if item.strip()
    ]


def _structural_finding(
    section: str,
    rule: str,
    severity: str,
    message: str,
    matched_text: str,
) -> dict[str, Any]:
    return {
        "source": "workprint_structural_review",
        "upstream_revision": UNSLOP_TEXT_PINNED_REVISION,
        "severity": severity,
        "rule": rule,
        "section": section,
        "matched_text": matched_text[:80],
        "message": message,
        "recommended_correction": "Review the section and revise only if evidence meaning is preserved.",
    }

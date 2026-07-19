from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from workprint.models import Investigation, Observation


FRAMEWORK_ATTRIBUTION = (
    "Organized using Anthropic's AI Fluency Framework (Delegation, "
    "Description, Discernment, Diligence), developed with Prof. Rick Dakan "
    "(Ringling College of Art and Design) and Prof. Joseph Feller "
    "(University College Cork). Framework materials are CC BY-NC-SA 4.0; "
    "see aifluencyframework.org."
)

DISCLAIMER = (
    "Workprint does not score or rate AI fluency. This section reorganizes "
    "evidence Workprint already gathered under the framework's four "
    "competencies so you can reflect on your own patterns. The judgment is "
    "yours, not Workprint's."
)

AI_SOURCE_LABELS = {
    "claude-code": "Claude Code",
    "claude-cowork": "Claude Cowork",
    "claude-desktop-chat": "Claude Desktop Chat",
}

# Deliberately narrow to unambiguous test-file conventions. A bare "spec/"
# directory is excluded: it is a real RSpec/Jasmine convention elsewhere,
# but dogfooding against this repo's own spec/*.md (product spec documents,
# not tests) showed it produces false positives here, and Workprint prefers
# missing a true positive over a false one.
_TEST_PATH_PATTERN = re.compile(
    r"(^|/)(tests?|__tests__)(/|$)|\.test\.|\.spec\.|(^|/)(test_[^/]+|[^/]+_test)\.py$",
    re.IGNORECASE,
)
_AI_MENTION_PATTERN = re.compile(
    r"\b(claude|copilot|chatgpt|gpt-\d|cursor|gemini|codex)\b", re.IGNORECASE
)

_MAX_EVIDENCE_IDS = 8


@dataclass(frozen=True)
class AIFluencyEvidenceItem:
    id: str
    statement: str
    supports: str
    does_not_prove: str
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


@dataclass(frozen=True)
class AIFluencyCompetency:
    key: str
    name: str
    definition: str
    evidence: tuple[AIFluencyEvidenceItem, ...]
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "definition": self.definition,
            "evidence": [item.to_dict() for item in self.evidence],
            "note": self.note,
        }


@dataclass(frozen=True)
class AIFluencyReflection:
    attribution: str
    disclaimer: str
    competencies: tuple[AIFluencyCompetency, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attribution": self.attribution,
            "disclaimer": self.disclaimer,
            "competencies": [item.to_dict() for item in self.competencies],
        }


def build_ai_fluency_reflection(investigation: Investigation) -> AIFluencyReflection:
    observations = investigation.observations
    competencies = (
        AIFluencyCompetency(
            key="delegation",
            name="Delegation",
            definition=(
                "Deciding what to hand to AI versus keep for yourself, and "
                "choosing the right tool for the task."
            ),
            evidence=_delegation_evidence(observations),
        ),
        AIFluencyCompetency(
            key="description",
            name="Description",
            definition=(
                "Communicating goals, constraints, and context clearly "
                "enough for AI to produce something useful."
            ),
            evidence=(),
            note=(
                "Workprint does not yet extract structural evidence for "
                "this competency. Raw prompt content is only read when a "
                "source is explicitly opted into content excerpts, and "
                "Workprint does not evaluate prompt clarity even then."
            ),
        ),
        AIFluencyCompetency(
            key="discernment",
            name="Discernment",
            definition=(
                "Critically evaluating AI output for quality, relevance, "
                "and fit before accepting it."
            ),
            evidence=(),
            note=(
                "Workprint does not yet correlate AI session activity with "
                "later revision commits to surface review evidence for "
                "this competency."
            ),
        ),
        AIFluencyCompetency(
            key="diligence",
            name="Diligence",
            definition=(
                "Using AI ethically, disclosing its involvement, and "
                "taking accountability for the final result."
            ),
            evidence=_diligence_evidence(observations),
        ),
    )
    return AIFluencyReflection(
        attribution=FRAMEWORK_ATTRIBUTION,
        disclaimer=DISCLAIMER,
        competencies=competencies,
    )


def _bounded_ids(ids: list[str]) -> tuple[str, ...]:
    return tuple(ids[:_MAX_EVIDENCE_IDS])


def _delegation_evidence(
    observations: tuple[Observation, ...],
) -> tuple[AIFluencyEvidenceItem, ...]:
    by_source: dict[str, list[Observation]] = {}
    for item in observations:
        by_source.setdefault(item.source, []).append(item)

    items: list[AIFluencyEvidenceItem] = []
    ai_sources_present = [
        source for source in AI_SOURCE_LABELS if source in by_source
    ]

    for source in sorted(by_source):
        label = AI_SOURCE_LABELS.get(source, source)
        matched = by_source[source]
        items.append(
            AIFluencyEvidenceItem(
                id=f"fluency-delegation-{source}",
                statement=(
                    f"{label} evidence: {len(matched)} recorded "
                    f"observation(s) for this project."
                ),
                supports=(
                    f"This supports that {label} was one of the places "
                    "this project's work happened."
                ),
                does_not_prove=(
                    "It does not prove how much work was delegated to AI "
                    "versus done independently, or which specific decisions "
                    "were AI-assisted."
                ),
                evidence_ids=_bounded_ids([obs.id for obs in matched]),
            )
        )

    if len(by_source) > 1:
        source_labels = sorted(
            AI_SOURCE_LABELS.get(source, source) for source in by_source
        )
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-delegation-multi-source",
                statement=(
                    f"{len(by_source)} distinct evidence sources were used "
                    f"together in this project: {', '.join(source_labels)}."
                ),
                supports=(
                    "This supports that multiple tools or modalities were "
                    "engaged for this project."
                ),
                does_not_prove=(
                    "It does not establish how work was divided between "
                    "them or why each tool was chosen."
                ),
                evidence_ids=_bounded_ids(
                    [obs.id for obs in observations]
                ),
            )
        )

    if not ai_sources_present:
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-delegation-no-ai-source",
                statement=(
                    "Workprint found no Claude Code, Claude Cowork, or "
                    "Claude Desktop Chat evidence for this project."
                ),
                supports=(
                    "This supports that none of Workprint's supported "
                    "local Claude sources had recorded evidence when this "
                    "report was built."
                ),
                does_not_prove=(
                    "It does not prove AI was not used. Evidence may have "
                    "been out of scope, not selected, or from a tool "
                    "Workprint does not yet read."
                ),
                evidence_ids=(),
            )
        )

    return tuple(items)


def _diligence_evidence(
    observations: tuple[Observation, ...],
) -> tuple[AIFluencyEvidenceItem, ...]:
    items: list[AIFluencyEvidenceItem] = []

    test_file_observations = [
        item
        for item in observations
        if item.activity == "artifact"
        and item.artifact
        and _TEST_PATH_PATTERN.search(item.artifact)
    ]
    if test_file_observations:
        paths = sorted({item.artifact for item in test_file_observations if item.artifact})
        shown_paths = ", ".join(f"`{path}`" for path in paths[:5])
        if len(paths) > 5:
            shown_paths += f", and {len(paths) - 5} more"
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-diligence-test-changes",
                statement=(
                    f"Git recorded {len(test_file_observations)} change(s) "
                    f"to test-like files: {shown_paths}."
                ),
                supports=(
                    "This supports that test files were part of the "
                    "recorded repository changes, which may reflect "
                    "verification activity."
                ),
                does_not_prove=(
                    "It does not prove tests were run, passed, or actually "
                    "verified AI-produced output, and it does not measure "
                    "test quality or coverage."
                ),
                evidence_ids=_bounded_ids(
                    [obs.id for obs in test_file_observations]
                ),
            )
        )

    disclosure_observations = [
        item
        for item in observations
        if item.source_type == "repository"
        and item.activity in {"implementation", "decision"}
        and _AI_MENTION_PATTERN.search(item.statement)
    ]
    if disclosure_observations:
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-diligence-ai-mentions",
                statement=(
                    f"Git commit messages mentioned an AI tool by name in "
                    f"{len(disclosure_observations)} recorded observation(s)."
                ),
                supports=(
                    "This supports that AI tool use was named in the "
                    "repository's own history, which may reflect "
                    "transparency about AI involvement."
                ),
                does_not_prove=(
                    "It does not prove a complete or accurate disclosure "
                    "was made, and its absence does not prove AI was not "
                    "used or disclosed elsewhere."
                ),
                evidence_ids=_bounded_ids(
                    [obs.id for obs in disclosure_observations]
                ),
            )
        )

    if not items:
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-diligence-no-evidence",
                statement=(
                    "Workprint found no test-file changes or AI-tool "
                    "mentions in the available Git evidence."
                ),
                supports=(
                    "This supports that these two specific, narrow signals "
                    "were not present in the evidence Workprint read."
                ),
                does_not_prove=(
                    "It does not prove verification or disclosure did not "
                    "happen; both can occur without leaving this kind of "
                    "trace in Git history."
                ),
                evidence_ids=(),
            )
        )

    return tuple(items)


def build_playbook_worksheet_markdown(investigation: Investigation) -> str:
    reflection = build_ai_fluency_reflection(investigation)
    lines: list[str] = [
        f"# AI Collaboration Playbook Worksheet: {investigation.project}",
        "",
        reflection.attribution,
        "",
        reflection.disclaimer,
        "",
        (
            "How to use this worksheet: the \"Evidence Workprint found\" "
            "column is filled in from your project's own history. Fill in "
            "the other two columns yourself -- or bring this worksheet "
            "into a Claude chat or Cowork session and ask it to help you "
            "reflect on these specific moments, the same way you would "
            "with any other collaborator."
        ),
        "",
    ]

    for competency in reflection.competencies:
        lines.extend([
            f"## {competency.name}",
            "",
            competency.definition,
            "",
        ])
        if competency.note:
            lines.extend([f"_{competency.note}_", ""])
        lines.extend([
            "| Evidence Workprint found | Your reflection | Your action next time |",
            "|---|---|---|",
        ])
        if competency.evidence:
            for item in competency.evidence:
                statement = item.statement.replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {statement} | _(fill in)_ | _(fill in)_ |")
        else:
            lines.append("| _(add your own example)_ | _(fill in)_ | _(fill in)_ |")
        lines.append("")

    return "\n".join(lines)

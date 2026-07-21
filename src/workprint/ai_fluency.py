from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any

from workprint.models import Investigation, Observation


FRAMEWORK_ATTRIBUTION = (
    "Organized using Anthropic's AI Fluency Framework (Delegation, "
    "Description, Discernment, Diligence), developed with Prof. Rick Dakan "
    "(Ringling College of Art and Design) and Prof. Joseph Feller "
    "(University College Cork), with supporting Anthropic Academy AI Fluency "
    "educational resources. Framework materials are CC BY-NC-SA 4.0; see "
    "aifluencyframework.org."
)

DISCLAIMER = (
    "Workprint does not score or rate AI fluency. This section uses the "
    "framework as a reflection lens for evidence Workprint already gathered, "
    "so you can notice patterns in how you delegated, described, discerned, "
    "and practiced diligence. The judgment is yours, not Workprint's."
)

FRAMEWORK_SUMMARY = (
    "AI Fluency means working with AI effectively, efficiently, ethically, "
    "and safely. Workprint uses the 4Ds -- Delegation, Description, "
    "Discernment, and Diligence -- as evidence-backed reflection categories, "
    "not as grades or contribution claims."
)

# Keyed on the exact Observation.source string each adapter writes (its
# source_name, e.g. adapters/claude_code.py's `source_name = "Claude Code"`),
# not the hyphenated adapter id ("claude-code") used elsewhere for CLI
# --include selection -- these are two different strings for the same
# adapter, and dogfooding against this repo's own real Claude Code
# evidence caught this module using the wrong one, silently matching
# nothing.
AI_SOURCE_LABELS = {
    "Claude Code": "Claude Code",
    "Claude Cowork": "Claude Cowork",
    "Claude Desktop Chat": "Claude Desktop Chat",
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

# How long after an AI session's last recorded turn a Git commit still
# counts as plausibly-related revision activity for Discernment evidence.
# Chosen generously (a few days, not hours) since local commit cadence
# varies; this is a heuristic window, not a claim about actual review.
_DISCERNMENT_WINDOW = timedelta(hours=72)


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
                "Making thoughtful decisions about what work is appropriate "
                "for you to do, what work is appropriate for AI to do, what "
                "work should happen together, and how to distribute those "
                "tasks."
            ),
            evidence=_delegation_evidence(observations),
        ),
        AIFluencyCompetency(
            key="description",
            name="Description",
            definition=(
                "Communicating goals, desired outputs, process expectations, "
                "context, and AI behavior clearly enough to create a "
                "productive collaboration."
            ),
            evidence=_description_evidence(observations),
            note=(
                "Workprint counts human-authored turns per session as a "
                "structural signal only. It does not read prompt content "
                "and does not evaluate whether goals were described "
                "clearly -- only whether a session had more than one "
                "human turn."
            ),
        ),
        AIFluencyCompetency(
            key="discernment",
            name="Discernment",
            definition=(
                "Thoughtfully evaluating what AI produces, how it produces "
                "it, and how it behaves; checking quality, accuracy, "
                "relevance, reasoning, and fit before accepting or using the "
                "work."
            ),
            evidence=_discernment_evidence(observations),
            note=(
                "Workprint checks whether a Git commit's timestamp falls "
                "within 72 hours after an AI session's last recorded "
                "turn. This is a timing correlation only -- it does not "
                "read commit content or confirm that AI output was "
                "actually reviewed."
            ),
        ),
        AIFluencyCompetency(
            key="diligence",
            name="Diligence",
            definition=(
                "Taking responsibility for AI-assisted work through careful "
                "tool choice, transparency about AI's role, verification, "
                "appropriate use, and accountability for what is shared or "
                "deployed."
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


def _slug(source: str) -> str:
    # Matches adapters/base.py's EvidenceAdapter.adapter_id transform, so
    # evidence IDs stay stable and readable regardless of whether a
    # source string is a slug already ("git") or a display name
    # ("Claude Code").
    return source.strip().lower().replace(" ", "-")


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
                id=f"fluency-delegation-{_slug(source)}",
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


def _description_evidence(
    observations: tuple[Observation, ...],
) -> tuple[AIFluencyEvidenceItem, ...]:
    sessions: dict[tuple[str, str], list[Observation]] = {}
    for item in observations:
        if item.source not in AI_SOURCE_LABELS:
            continue
        conversation_id = (item.metadata or {}).get("conversation_id")
        if not conversation_id:
            continue
        sessions.setdefault((item.source, conversation_id), []).append(item)

    if not sessions:
        return (
            AIFluencyEvidenceItem(
                id="fluency-description-no-sessions",
                statement=(
                    "Workprint found no Claude Code or Claude Cowork "
                    "session evidence with an identifiable conversation "
                    "for this project."
                ),
                supports=(
                    "This supports that no session-structured AI evidence "
                    "was available to check for multi-turn dialogue."
                ),
                does_not_prove=(
                    "It does not prove single-turn or no interaction "
                    "occurred; this signal only exists for sources "
                    "Workprint can group into sessions."
                ),
                evidence_ids=(),
            ),
        )

    multi_turn_ids: list[str] = []
    single_turn_count = 0
    for turns in sessions.values():
        human_turns = [turn for turn in turns if turn.actor == "Human"]
        if len(human_turns) > 1:
            multi_turn_ids.extend(turn.id for turn in human_turns)
        elif human_turns:
            single_turn_count += 1

    items: list[AIFluencyEvidenceItem] = []
    multi_turn_session_count = sum(
        1
        for turns in sessions.values()
        if len([turn for turn in turns if turn.actor == "Human"]) > 1
    )
    if multi_turn_session_count:
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-description-multi-turn-sessions",
                statement=(
                    f"{multi_turn_session_count} of {len(sessions)} "
                    "recorded session(s) included more than one "
                    "human-authored turn."
                ),
                supports=(
                    "This supports that some sessions involved more than "
                    "a single opening prompt, which may reflect iterative "
                    "dialogue rather than one-shot delegation."
                ),
                does_not_prove=(
                    "It does not measure how clearly goals were "
                    "described, or whether follow-up turns were "
                    "clarification, correction, or an unrelated new ask."
                ),
                evidence_ids=_bounded_ids(multi_turn_ids),
            )
        )
    if single_turn_count:
        items.append(
            AIFluencyEvidenceItem(
                id="fluency-description-single-turn-sessions",
                statement=(
                    f"{single_turn_count} of {len(sessions)} recorded "
                    "session(s) included exactly one human-authored turn."
                ),
                supports=(
                    "This supports that some sessions were a single "
                    "prompt with no recorded human follow-up."
                ),
                does_not_prove=(
                    "It does not prove the single prompt was unclear or "
                    "insufficient -- a single well-described prompt can "
                    "be exactly enough."
                ),
                evidence_ids=(),
            )
        )

    return tuple(items)


def _discernment_evidence(
    observations: tuple[Observation, ...],
) -> tuple[AIFluencyEvidenceItem, ...]:
    session_end_times = [
        item.timestamp
        for item in observations
        if item.source in AI_SOURCE_LABELS and item.timestamp is not None
    ]
    commit_observations = [
        item
        for item in observations
        if item.source_type == "repository"
        and item.activity == "implementation"
        and item.timestamp is not None
    ]

    if not session_end_times or not commit_observations:
        return (
            AIFluencyEvidenceItem(
                id="fluency-discernment-no-correlation-possible",
                statement=(
                    "Workprint did not have both timestamped AI session "
                    "evidence and timestamped Git commits available to "
                    "check for timing correlation."
                ),
                supports=(
                    "This supports that at least one of the two signals "
                    "this check needs was missing from the evidence read."
                ),
                does_not_prove=(
                    "It does not prove review did or did not happen."
                ),
                evidence_ids=(),
            ),
        )

    following_commits = [
        commit
        for commit in commit_observations
        if any(
            timedelta(0) <= (commit.timestamp - session_time) <= _DISCERNMENT_WINDOW
            for session_time in session_end_times
        )
    ]

    if following_commits:
        return (
            AIFluencyEvidenceItem(
                id="fluency-discernment-commits-follow-sessions",
                statement=(
                    f"{len(following_commits)} Git commit(s) were recorded "
                    "within 72 hours after an AI session's last recorded "
                    "turn."
                ),
                supports=(
                    "This supports that repository activity followed AI "
                    "session activity in time, which may reflect review "
                    "or revision following AI collaboration."
                ),
                does_not_prove=(
                    "It does not prove the commit content relates to the "
                    "AI session, or that any review happened -- only that "
                    "the two events are close in time."
                ),
                evidence_ids=_bounded_ids([obs.id for obs in following_commits]),
            ),
        )

    return (
        AIFluencyEvidenceItem(
            id="fluency-discernment-no-commits-follow-sessions",
            statement=(
                "Workprint found no Git commits within 72 hours after an "
                "AI session's last recorded turn."
            ),
            supports=(
                "This supports that this specific, narrow timing signal "
                "was not present in the evidence Workprint read."
            ),
            does_not_prove=(
                "It does not prove review did not happen; review can "
                "leave no trace in Git history, or commits may follow "
                "outside this window."
            ),
            evidence_ids=(),
        ),
    )


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

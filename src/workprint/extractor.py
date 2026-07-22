from __future__ import annotations

import re
from hashlib import sha1

from typing import Any

from workprint.models import (
    NormalizedGitCommit,
    NormalizedGitRepository,
    NormalizedMessage,
    Observation,
)


DECISION_PATTERNS = (
    r"\bI(?:'m| am)? going (?:to|with)\b",
    r"\bI (?:choose|chose|selected|decided|prefer|want)\b",
    r"\bwe(?:'ll| will| should) (?:use|build|keep|go with|call|name)\b",
    r"\blet(?:'s| us) (?:use|build|keep|go with|call|name)\b",
    r"\bapproved\b",
    r"\bsounds good\b",
)

SUGGESTION_PATTERNS = (
    r"\bI suggest\b",
    r"\bI recommend\b",
    r"\bwe could\b",
    r"\bwhat about\b",
    r"\bconsider\b",
    r"\bproposal\b",
)

IMPLEMENTATION_PATTERNS = (
    r"\bI (?:built|created|added|implemented|updated|fixed|pushed|committed|uploaded)\b",
    r"\bwe (?:built|created|added|implemented|updated|fixed|pushed|committed)\b",
    r"\bcompleted\b",
    r"\bdone\b",
)

UNKNOWN_PATTERNS = (
    r"\b(?:cannot|can't|could not|couldn't) determine\b",
    r"\bunknown\b",
    r"\bnot enough evidence\b",
    r"\bmissing evidence\b",
    r"\bnot available\b",
)


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _classify(message: NormalizedMessage) -> str:
    text = message.content.strip()
    if _matches(text, UNKNOWN_PATTERNS):
        return "unknown"
    if _matches(text, IMPLEMENTATION_PATTERNS):
        return "implementation"
    if _matches(text, DECISION_PATTERNS):
        return "decision"
    if _matches(text, SUGGESTION_PATTERNS):
        return "suggestion"
    if message.role == "human" and text.endswith("?"):
        return "question"
    return "observation"


def _statement(message: NormalizedMessage, activity: str) -> str:
    compact = " ".join(message.content.split())
    if len(compact) > 280:
        compact = compact[:277].rstrip() + "..."
    actor = "Human" if message.role == "human" else message.source
    verbs = {
        "question": "asked",
        "suggestion": "suggested",
        "decision": "stated a decision or acceptance",
        "implementation": "reported implementation activity",
        "unknown": "identified an unknown or evidence gap",
        "observation": "stated",
    }
    return f"{actor} {verbs[activity]}: {compact}"


def _summary_activity(message: NormalizedMessage, fallback: str) -> str:
    kind = str((message.metadata or {}).get("summary_item_kind") or "")
    if kind == "decision":
        return "decision"
    if kind == "unknown":
        return "unknown"
    if kind == "user_direction":
        return "decision"
    return fallback


def _summary_statement(message: NormalizedMessage, activity: str) -> str:
    compact = " ".join(message.content.split())
    if len(compact) > 240:
        compact = compact[:237].rstrip() + "..."
    kind = str((message.metadata or {}).get("summary_item_kind") or "summary")
    labels = {
        "summary": "summary",
        "summary_block": "summary",
        "decision": "decision",
        "user_direction": "user direction",
        "ai_fluency_note": "AI fluency note",
        "unknown": "evidence gap",
    }
    label = labels.get(kind, activity.replace("_", " "))
    return (
        f"User-approved chat summary recorded {label}: {compact} "
        "This is summary evidence, not the full transcript."
    )


def _digest(*parts: object) -> str:
    return sha1(":".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:10]


def _git_actor(commit: NormalizedGitCommit) -> str:
    return f"Git author: {commit.author_name} <{commit.author_email}>"


def _git_metadata(commit: NormalizedGitCommit) -> dict[str, Any]:
    return {
        "source_type": "repository",
        "repository_root": commit.repository_root,
        "current_branch": commit.current_branch,
        "commit_sha": commit.commit_sha,
        "abbreviated_sha": commit.abbreviated_sha,
        "author_name": commit.author_name,
        "author_email": commit.author_email,
        "committer_name": commit.committer_name,
        "committer_email": commit.committer_email,
        "subject": commit.subject,
        "body": commit.body,
        "parent_shas": commit.parent_shas,
        "is_merge": commit.is_merge,
        "tags": commit.tags,
        "is_shallow": commit.is_shallow,
    }


def _extract_git_repository(record: NormalizedGitRepository) -> list[Observation]:
    branch = record.current_branch or "detached or unavailable branch"
    observations = [
        Observation(
            id=f"OBS-{_digest(record.source, record.repository_root, 'repository')}",
            timestamp=None,
            source=record.source,
            source_type="repository",
            actor="Git",
            activity="observation",
            statement=(
                "Git repository metadata was captured for "
                f"{record.repository_root} on {branch}."
            ),
            evidence_refs=(record.source_locator,),
            reliability="high",
            metadata={
                "source_type": "repository",
                "repository_root": record.repository_root,
                "current_branch": record.current_branch,
                "is_bare": record.is_bare,
                "is_shallow": record.is_shallow,
                **(record.metadata or {}),
            },
        )
    ]
    if record.is_shallow:
        observations.append(
            Observation(
                id=f"OBS-{_digest(record.source, record.repository_root, 'shallow')}",
                timestamp=None,
                source=record.source,
                source_type="repository",
                actor="Git",
                activity="unknown",
                statement=(
                    "Git history is shallow or incomplete for "
                    f"{record.repository_root}; earlier commits may be unavailable."
                ),
                evidence_refs=(record.source_locator,),
                reliability="high",
                metadata={
                    "source_type": "repository",
                    "repository_root": record.repository_root,
                    "current_branch": record.current_branch,
                    "is_shallow": True,
                },
            )
        )
    return observations


def _extract_git_commit(commit: NormalizedGitCommit) -> list[Observation]:
    observations: list[Observation] = []
    metadata = _git_metadata(commit)
    commit_label = f"{commit.abbreviated_sha}: {commit.subject}"
    if commit.tags:
        commit_label += f" (tags: {', '.join(commit.tags)})"
    if commit.is_merge:
        statement = f"Git recorded merge commit {commit_label}."
    else:
        statement = f"Git recorded commit {commit_label}."
    observations.append(
        Observation(
            id=f"OBS-{_digest(commit.source, commit.commit_sha, 'commit')}",
            timestamp=commit.committed_at,
            source=commit.source,
            source_type="repository",
            actor=_git_actor(commit),
            activity="implementation",
            statement=statement,
            evidence_refs=(commit.source_locator,),
            reliability="high",
            metadata={
                **metadata,
                "file_changes": [item.to_dict() for item in commit.file_changes],
            },
        )
    )

    decision_text = " ".join(part for part in (commit.subject, commit.body) if part)
    if _matches(decision_text, DECISION_PATTERNS):
        observations.append(
            Observation(
                id=f"OBS-{_digest(commit.source, commit.commit_sha, 'decision')}",
                timestamp=commit.committed_at,
                source=commit.source,
                source_type="repository",
                actor=_git_actor(commit),
                activity="decision",
                statement=(
                    "Git commit message explicitly recorded a decision: "
                    f"{decision_text}"
                ),
                evidence_refs=(commit.source_locator,),
                reliability="high",
                metadata=metadata,
            )
        )

    for change in commit.file_changes:
        change_ref = f"{commit.source_locator}/file/{change.path}"
        observations.append(
            Observation(
                id=f"OBS-{_digest(commit.source, commit.commit_sha, change.path)}",
                timestamp=commit.committed_at,
                source=commit.source,
                source_type="repository",
                actor="Git",
                activity="artifact",
                statement=(
                    "Git recorded repository file change "
                    f"{change.change_type} for {change.path} in commit "
                    f"{commit.abbreviated_sha}. Additions and deletions describe "
                    "repository changes, not effort or value."
                ),
                evidence_refs=(change_ref,),
                artifact=change.path,
                reliability="high",
                metadata={
                    **metadata,
                    "file_path": change.path,
                    "change_type": change.change_type,
                    "additions": change.additions,
                    "deletions": change.deletions,
                },
            )
        )
    return observations


def extract_observations(
    messages: list[NormalizedMessage | NormalizedGitRepository | NormalizedGitCommit],
) -> list[Observation]:
    observations: list[Observation] = []
    for index, message in enumerate(messages, start=1):
        if isinstance(message, NormalizedGitRepository):
            observations.extend(_extract_git_repository(message))
            continue
        if isinstance(message, NormalizedGitCommit):
            observations.extend(_extract_git_commit(message))
            continue
        activity = _classify(message)
        message_metadata = message.metadata or {}
        if message_metadata.get("summary_evidence"):
            activity = _summary_activity(message, activity)
            actor = "User-approved summary"
            statement = _summary_statement(message, activity)
        else:
            actor = "Human" if message.role == "human" else message.source
            statement = _statement(message, activity)
        digest = _digest(message.source, message.conversation_id, message.id)
        observations.append(
            Observation(
                id=f"OBS-{digest}",
                timestamp=message.created_at,
                source=message.source,
                source_type=str(message_metadata.get("source_type") or "conversation"),
                actor=actor,
                activity=activity,
                statement=statement,
                evidence_refs=(message.source_locator,),
                reliability="high",
                metadata={
                    "conversation_id": message.conversation_id,
                    "message_id": message.id,
                    "role": message.role,
                    "sequence": index,
                    **message_metadata,
                },
            )
        )
    return observations

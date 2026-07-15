from __future__ import annotations

import re
from hashlib import sha1

from workprint.models import NormalizedMessage, Observation


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


def extract_observations(messages: list[NormalizedMessage]) -> list[Observation]:
    observations: list[Observation] = []
    for index, message in enumerate(messages, start=1):
        activity = _classify(message)
        message_metadata = message.metadata or {}
        digest = sha1(
            f"{message.source}:{message.conversation_id}:{message.id}".encode("utf-8")
        ).hexdigest()[:10]
        observations.append(
            Observation(
                id=f"OBS-{digest}",
                timestamp=message.created_at,
                source=message.source,
                source_type=str(message_metadata.get("source_type") or "conversation"),
                actor="Human" if message.role == "human" else message.source,
                activity=activity,
                statement=_statement(message, activity),
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

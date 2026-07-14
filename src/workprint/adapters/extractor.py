from __future__ import annotations

import re
from collections import defaultdict

from workprint.conversations import NormalizedMessage
from workprint.models import Completeness, Observation, Reliability

_DECISION_PATTERNS = (
    r"\b(?:let'?s|we(?:'ll| will)|i(?:'ll| will))\s+(?:go with|use|choose|keep|build|start|do)\b",
    r"\b(?:i choose|i chose|i decided|we decided|decision:)\b",
    r"\b(?:sounds good|go ahead|approved|pushed to origin)\b",
)
_SUGGESTION_PATTERNS = (
    r"\b(?:i recommend|i suggest|my recommendation|we should|you should|i would|could)\b",
    r"\b(?:proposal|propose|option|idea)\b",
)
_IMPLEMENTATION_PATTERNS = (
    r"\b(?:built|implemented|created|added|updated|renamed|pushed|committed|packaged|generated)\b",
    r"\b(?:is now|are now)\s+(?:built|implemented|available|included)\b",
)
_UNKNOWN_PATTERNS = (
    r"\b(?:unknown|cannot determine|can'?t determine|insufficient evidence|not available)\b",
)


def extract_observations(
    messages: list[NormalizedMessage], source_name: str
) -> list[Observation]:
    """Apply conservative, deterministic rules to normalized messages.

    The extractor intentionally favors recall of explicit speech acts over broad
    semantic inference. A single message may produce more than one observation
    only when it contains independently detectable activity types.
    """

    observations: list[Observation] = []
    per_conversation: dict[str, int] = defaultdict(int)

    for message in messages:
        activities = _classify(message)
        for activity in activities:
            per_conversation[message.conversation_id] += 1
            sequence = per_conversation[message.conversation_id]
            locator = message.source_locator or (
                f"{source_name.lower()}:{message.conversation_id}:{message.id}"
            )
            observations.append(
                Observation(
                    id=f"OBS-{message.conversation_id[:8]}-{sequence:04d}",
                    source_type="conversation_message",
                    source_name=source_name,
                    source_locator=locator,
                    observed_at=message.created_at,
                    event_time=message.created_at,
                    actor=message.actor,
                    activity=activity,
                    observation=_observation_text(message, activity),
                    reliability=Reliability.HIGH,
                    completeness=Completeness.PARTIAL,
                    notes=(
                        "Activity classification was produced by deterministic "
                        "text rules and should be reviewed before high-stakes use."
                    ),
                    metadata={
                        "conversation_id": message.conversation_id,
                        "message_id": message.id,
                        "role": message.role,
                        "original_text": message.text,
                        **message.metadata,
                    },
                )
            )

    return observations


def _classify(message: NormalizedMessage) -> list[str]:
    text = " ".join(message.text.split())
    lowered = text.lower()
    activities: list[str] = []

    if message.role == "human" and "?" in text:
        activities.append("question")
    if _matches_any(lowered, _DECISION_PATTERNS):
        activities.append("decision")
    if message.role == "assistant" and _matches_any(lowered, _SUGGESTION_PATTERNS):
        activities.append("suggestion")
    if _matches_any(lowered, _IMPLEMENTATION_PATTERNS):
        activities.append("implementation")
    if _matches_any(lowered, _UNKNOWN_PATTERNS):
        activities.append("unknown")

    # Preserve messages that do not contain an explicit speech act as direct
    # conversation observations instead of inventing a stronger classification.
    if not activities:
        activities.append("observation")

    return list(dict.fromkeys(activities))


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _observation_text(message: NormalizedMessage, activity: str) -> str:
    compact = " ".join(message.text.split())
    if len(compact) > 280:
        compact = compact[:277].rstrip() + "..."
    labels = {
        "question": "Asked",
        "decision": "Recorded a decision or acceptance",
        "suggestion": "Proposed or recommended",
        "implementation": "Reported implementation activity",
        "unknown": "Identified an unknown or evidence gap",
        "observation": "Recorded message",
    }
    return f"{labels[activity]}: {compact}"

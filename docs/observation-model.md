# Observation Model

An **Observation** is Workprint's canonical normalized evidence record. Evidence adapters convert source-specific records—such as an AI message, Git commit, document revision, or calendar event—into Observations before the investigation engine analyzes them.

```text
Raw source evidence
        ↓
Evidence adapter
        ↓
Observation
        ↓
Investigation engine
        ↓
Findings and reports
```

## Why Observations exist

Raw evidence sources use different formats and terminology. A Claude export and a Git commit do not look alike, but both can support a project-history finding. The Observation model gives every adapter one stable output contract, so the investigation engine does not need source-specific logic.

An Observation is not a conclusion. It should record the narrowest factual statement supported by the source. Findings and conclusions are produced later by the investigation engine.

## Required fields

| Field | Purpose |
| --- | --- |
| `id` | Stable identifier unique within an investigation input. |
| `source_type` | Machine-friendly source category, such as `conversation` or `commit`. |
| `observation` | Concise factual statement supported by the source. |
| `reliability` | Reliability of the source record: `high`, `medium`, `low`, or `unknown`. |

## Optional fields

| Field | Purpose |
| --- | --- |
| `source_name` | Human-readable source, such as `Claude` or `GitHub`. |
| `source_locator` | Stable path, message ID, commit SHA, revision ID, or other locator. |
| `observed_at` | When Workprint collected or observed the evidence. |
| `event_time` | When the underlying project activity occurred. |
| `actor` | Human, AI system, automated service, or unknown actor. |
| `activity` | Normalized activity such as `suggestion`, `decision`, or `implementation`. |
| `artifact` | File, document, design, feature, or other project object involved. |
| `completeness` | Whether the source record is `complete`, `partial`, or `unknown`. |
| `notes` | Important qualification that does not belong in the observation statement. |
| `metadata` | Source-specific fields retained for traceability but ignored by the core engine. |

## Example

```json
{
  "id": "OBS-0001",
  "source_type": "conversation",
  "source_name": "ChatGPT",
  "source_locator": "conversation:workprint/message:42",
  "observed_at": "2026-07-14T21:00:00+00:00",
  "event_time": "2026-07-14T20:58:00+00:00",
  "actor": "Tony Kim",
  "activity": "decision",
  "artifact": "Product name",
  "observation": "Selected Workprint as the working product name.",
  "reliability": "high",
  "completeness": "complete",
  "notes": null,
  "metadata": {
    "message_role": "user"
  }
}
```

## Design rules

1. Store a factual observation, not a broad conclusion.
2. Point back to original evidence with `source_locator` whenever possible.
3. Preserve unknown values as `null` or `unknown`; do not invent them.
4. Keep raw conversation or document content in the source system rather than duplicating it inside every Observation.
5. Use `metadata` only for adapter-specific details. Core investigation logic must not depend on it.

## Backward compatibility

The v0.1 Observation JSON shape is intentionally compatible with the normalized evidence records already accepted by the investigation engine. Existing fixtures can therefore be loaded as Observations without a destructive migration.

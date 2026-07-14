# Claude Conversation Adapter

The Claude adapter converts supported Claude conversation exports into canonical Workprint Observations.

## Pipeline

```text
Claude JSON export
    -> Claude reader
    -> NormalizedMessage records
    -> deterministic observation extractor
    -> Observation records
```

## Supported input shapes

The adapter accepts JSON containing:

- an array of conversations;
- an object with a `conversations` array; or
- one conversation object.

Messages may appear in `chat_messages` or `messages`. Message text may be a string or a list of text content blocks.

Claude export formats are not guaranteed to remain stable. Workprint therefore treats the adapter as a compatibility layer and returns a clear error when it cannot recognize the supplied structure.

## Extracted activities

The initial deterministic extractor recognizes explicit:

- questions;
- suggestions;
- decisions or acceptances;
- implementation reports; and
- unknowns or evidence gaps.

Messages without an explicit match are retained as `observation` activity records rather than discarded or assigned an unsupported interpretation.

## Usage

```bash
PYTHONPATH=src python3 -m workprint.cli ingest claude \
  fixtures/claude/sample-conversations.json \
  --output claude-observations.json
```

The output is a JSON array of canonical Observation records. Review classifications before using them in high-stakes reporting.

## Limitations

- The adapter does not prove that generated content was used in a final artifact.
- Keyword classification can miss implicit decisions or misread quoted language.
- Raw message text is retained in Observation metadata for traceability; redact sensitive exports before ingestion.
- Unsupported or future Claude export shapes may require adapter updates.

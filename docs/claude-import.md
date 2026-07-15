# Claude Import

Workprint can read common Claude JSON conversation exports and convert them
into the same `NormalizedMessage` records used by the ChatGPT adapter.

## Supported structures

- A top-level list of conversation objects
- A `{ "conversations": [...] }` wrapper
- A single conversation object
- Message collections named `chat_messages`, `messages`, or `conversation`

## Supported message fields

Message identity:

- `uuid`
- `id`

Role:

- `sender`
- `role`
- `author`
- `type`

Timestamp:

- `created_at`
- `timestamp`
- `create_time`

Content:

- Plain strings
- Lists of text content blocks
- A fallback `text` field

## Examples

Validate an export:

```bash
workprint validate claude fixtures/claude/sample-conversations.json
```

Import normalized observations:

```bash
workprint import claude fixtures/claude/sample-conversations.json \
  --output claude-observations.json
```

Generate a report:

```bash
workprint investigate claude fixtures/claude/sample-conversations.json \
  --project "Workprint" \
  --output claude-report.md
```

## Limits

Claude export shapes can vary. This adapter intentionally supports the common
field names represented in the fixture and rejects exports that contain no
recognizable conversation or message collection.

The shared deterministic extractor may miss implied decisions or nuanced
changes in intent.

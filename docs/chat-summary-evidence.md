# User-Approved Chat Summaries

Workprint can read user-approved long-chat summaries as evidence when a full
chat history is too large or not appropriate to send.

This is a context bridge, not a transcript import. Workprint labels these
records as `chat-summary` evidence and preserves the limitation that the full
conversation was not necessarily sent, read, or verified.

## When To Use This

Use a chat summary when:

- the original chat is too long for a bounded evidence packet;
- the user wants to provide broader context from a long AI session;
- sensitive, irrelevant, or repetitive chat turns should be excluded before
  evidence is shared;
- the user can review and approve the summary before Workprint imports it.

Do not use a summary to imply Workprint inspected every message. If the full
history was not included, the report must say so.

## Create A Template

Use the CLI to create a review-required JSON template:

```bash
workprint chat-summary-template \
  --title "Project long-chat summary" \
  --output project-chat-summary.json
```

The template intentionally sets `approved_by_user` to `false`. Change it to
`true` only after the user has reviewed the contents.

## Prompt For An AI Agent

Use this prompt when asking an AI tool to summarize a long chat:

```text
Summarize this chat for Workprint as user-approved evidence.

Focus on:
- what I directed, decided, reviewed, sequenced, or corrected;
- what AI or tooling appears to have done;
- how the work moved from idea to implementation;
- what the summary cannot prove because it is not the full transcript.

Do not infer authorship, ownership, effort, value, or contribution
percentages. Keep claims tied to the chat content. Include unknowns and
limitations. Return a concise summary I can review before marking it approved.
```

After receiving the summary, the user should edit it, remove anything
sensitive or unsupported, and approve it explicitly before importing.

## JSON Schema

Workprint supports a conservative JSON object:

```json
{
  "workprint_source": "chat-summary",
  "id": "stable-summary-id",
  "title": "Project long-chat summary",
  "approved_by_user": true,
  "approved_at": "2026-07-21T16:45:00-07:00",
  "original_sources": ["Claude Code", "ChatGPT"],
  "date_range": {
    "start": "2026-07-01",
    "end": "2026-07-21"
  },
  "participants": ["Tony", "AI assistant"],
  "tools": ["Claude Code", "Gemini"],
  "summary_method": "user-reviewed AI summary",
  "summary": "Concise user-approved summary text.",
  "key_decisions": ["Decision text."],
  "user_direction": ["Direction, review, sequencing, or correction text."],
  "ai_fluency_notes": ["Delegation, Description, Discernment, or Diligence note."],
  "unknowns": ["What this summary cannot prove."],
  "limitations": ["Known limitation of this summary."]
}
```

Required fields:

- `workprint_source`: must be `chat-summary`.
- `approved_by_user`: must be `true`.
- At least one supported summary field: `summary`, `key_decisions`,
  `user_direction`, `ai_fluency_notes`, or `unknowns`.

## Markdown And Text

Markdown and text summaries are also supported when they include this explicit
marker near the top:

```text
workprint-source: chat-summary
```

Discovery only recognizes marked `.md` and `.txt` summaries so ordinary
repository documents are not accidentally treated as long-chat summaries.

## Evidence References

Evidence references include the source file and a stable item locator:

- `project-chat-summary.json#summary`
- `project-chat-summary.json#key_decisions-1`
- `project-chat-summary.md#summary-block-1`

## Boundaries

Chat-summary evidence can support broader context, user-approved decisions,
review notes, AI Fluency reflection, and known limitations.

It cannot prove:

- omitted turns;
- exact wording from the original transcript;
- complete chronology;
- authorship, ownership, effort, value, or contribution;
- that the full chat history was sent to Workprint or a provider.

Reports must preserve this boundary by identifying the source as summary
evidence, not complete transcript evidence.

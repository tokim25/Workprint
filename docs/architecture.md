# Architecture

Workprint uses a small, explicit pipeline:

```text
Raw evidence
    ↓
EvidenceAdapter
    ↓
Normalized records
    ↓
Deterministic extractor
    ↓
Observation[]
    ↓
Investigation engine
    ↓
Markdown or JSON report
```

## EvidenceAdapter

`EvidenceAdapter` is the shared contract for every evidence source.

Each adapter must:

- declare a stable source name and source type;
- validate its input;
- read a source-specific artifact;
- return Workprint-normalized records;
- avoid generating project-level findings or conclusions.

`ChatGPTAdapter` and `ClaudeAdapter` both return `NormalizedMessage`
records. Future conversation adapters such as Gemini can target the same
normalized type.
Non-conversation adapters, such as Git, may return a different normalized
record type while preserving the same adapter contract.

Adapters are registered through `workprint.adapters.registry`. The CLI uses
that registry rather than importing vendor-specific classes directly.

## Normalized message

A normalized message preserves:

- source;
- conversation ID;
- message ID;
- role;
- text;
- timestamp;
- stable evidence locator.

## Observation

An observation is a normalized statement tied to evidence. It records an
activity label but does not claim ownership or total effort.

## Investigation engine

The engine orders observations, summarizes recorded activity, creates bounded
findings, builds timeline events, and lists unknowns and limitations.

## Timeline generation

`workprint.timeline` turns observations into chronological `TimelineEvent`
records. Timeline generation is deterministic:

- observations are ordered by timestamp, source, and ID;
- related observations are grouped only when they share conversation context,
  stage, and a close timestamp window;
- stages are derived from observation activity labels;
- user involvement is marked measured only when captured evidence directly
  supports initiated, directed, contributed, reviewed, decided, or executed;
- unsupported involvement remains unknown;
- user, collaborator, AI/tool, joint, and unattributed activity remain separate;
- captured involvement counts describe evidence events only and are never
  contribution percentages.

## Reports

Reports are presentations of the same investigation data. Markdown and JSON
are currently supported, including timeline events and attribution limits.


## Multi-source orchestration

`workprint.multisource` accepts explicit `SOURCE=PATH` inputs, invokes the
registered adapters, merges observations, suppresses exact duplicates, and
sorts the result before handing it to the investigation engine.

Adapters remain independent and contain no multi-source logic.

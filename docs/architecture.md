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
normalized type. Non-conversation adapters may return different normalized
record types while preserving the same adapter contract.

Adapters are registered through `workprint.adapters.registry`. The CLI uses
that registry rather than importing vendor-specific classes directly.

## Discovery

`workprint.discovery` scans a project directory, detects the selected local
Git repository context, asks registered adapters whether they recognize files,
and aggregates the results. Discovery is informational until the user selects
evidence: it does not import evidence, create observations, build findings,
generate timelines, or modify files.

Discovery does not automatically traverse unrelated nested repositories. Git
worktrees are supported when the installed `git` command can resolve a
non-bare worktree root.

The CLI keeps discovery thin by delegating scanning and aggregation to the
discovery layer.

## Guided investigation

`workprint.guided` orchestrates a plain-language workflow on top of Project
Discovery and the existing multi-source investigation pipeline. It prompts for a
project folder, presents discovered importable files, translates file selections
into `EvidenceInput` values, and calls `load_observations` before building the
same investigation and reports used by expert CLI commands.

The guided layer does not introduce separate evidence loading, investigation,
timeline, report, JSON, or attribution logic. Local Git repositories are
selected as a single evidence source and loaded through the same multi-source
pipeline as files.

## Local Git adapter

The Git adapter reads a local non-bare repository using the installed `git`
command through a small deterministic subprocess boundary. It uses explicit
argument arrays, UTF-8 text handling, and read-only commands such as
`rev-parse`, `branch --show-current`, `log`, `show`, `diff-tree`, and
`tag --points-at`. It does not fetch, pull, push, checkout, reset, merge,
rebase, or change branches.

The adapter emits repository metadata records and commit records. Commit
records preserve Git-recorded values for SHA, abbreviated SHA, timestamp,
author and committer names/emails, subject, body, parent SHAs, merge status,
changed paths, change type, additions, deletions, and tags. File contents are
not inspected in v1.

Git evidence is treated conservatively. A commit may support implementation
chronology. A merge commit may support a branch-integration milestone. A
commit message supports a decision only when the message text explicitly says
so. Changed file metadata supports that repository artifacts changed, not why
they changed. Commit counts, file counts, additions, and deletions are never
converted into effort, ownership, value, authorship, productivity, or
contribution measures.

## Static document adapters

The Google Docs adapter reads static `.json`, `.txt`, and `.md` exports using
the canonical source identifier `google-docs`. Each non-empty paragraph or
block is normalized into a source-independent record with a stable locator such
as `sample-document.json#paragraph/3`.

Static document exports are snapshots. The adapter preserves explicit
document-level metadata, but it does not recover revision history, edit-by-edit
authorship, deleted text, or paragraph authorship. Owners, authors, and editors
remain document-level metadata unless the supplied evidence explicitly maps a
person to a block.

## Static design adapters

The Figma adapter reads user-supplied static JSON exports using the canonical
source identifier `figma`. It emits normalized records only for meaningful
pages or nodes with visible text, descriptions, component or instance metadata,
or explicit evidence metadata. Empty structural containers are traversed but do
not produce observations.

Figma evidence references preserve hierarchy, for example
`sample-file.json#page/page-discovery/node/text-headline`. File, page, node,
parent, and node-path metadata are preserved separately.

Static design exports are snapshots. The adapter does not recover version
history, comments, contributor activity, or authorship. File-level timestamps
are preserved as file metadata and are not assigned to nodes. Explicit page or
node `last_modified` values may be used as normalized compatibility timestamps
for ordering, but they represent last observed modification rather than
creation time. Contributors, owners, and editors remain metadata unless
evidence explicitly links a person to a node or action.

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
Markdown reports add presentation structure, summaries, and evidence appendices
without changing the underlying evidence, findings, timeline, or JSON model.


## Multi-source orchestration

`workprint.multisource` accepts explicit `SOURCE=PATH` inputs, invokes the
registered adapters, merges observations, suppresses exact duplicates, and
sorts the result before handing it to the investigation engine.

Adapters remain independent and contain no multi-source logic.

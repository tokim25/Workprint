# Project Plan

This is a living capability-based plan for Workprint.

## Product Direction

Workprint is an evidence-based knowledge reconstruction tool designed to be
usable by people with limited coding knowledge.

## Current Capabilities

- [x] ChatGPT import
- [x] Claude import
- [x] EvidenceAdapter contract
- [x] Adapter registry
- [x] Canonical observations
- [x] Deterministic investigation engine
- [x] Timeline Report
- [x] Google Docs adapter
- [x] Figma adapter
- [x] Git adapter
- [x] Report visual design and shareability
- [x] Executive Report v1
- [x] Project Discovery
- [x] Guided Investigation Wizard
- [x] Markdown and JSON reporting
- [x] Multi-source investigations
- [x] Exact, source-aware duplicate suppression
- [x] Executive Report copy-quality audit integration

## Completed Milestone: Timeline Report

Status: Complete

Goal: Generate a chronological, evidence-linked account of how a project
developed, including the investigated user's involvement at every stage.

Requirements:

- Canonical timeline event model.
- Chronological ordering.
- Grouping related observations into events.
- Project stage/category.
- Event title and description.
- Source observations and evidence references.
- Confidence.
- Unknowns and attribution limits.
- User involvement activities:
  - initiated
  - directed
  - contributed
  - reviewed
  - decided
  - executed
- Status for each involvement activity:
  - measured
  - estimated
  - unknown
- Separate:
  - user activity
  - collaborator activity
  - AI/tool activity
  - joint activity
  - unattributed activity
- Deterministic classification rules.
- Markdown timeline.
- Structured JSON timeline.
- Aggregate involvement counts described only as captured evidence.
- No contribution percentages.

Acceptance criteria:

- [x] Existing commands remain compatible.
- [x] Existing findings remain available.
- [x] Timeline is additive.
- [x] Classifications are evidence-linked.
- [x] Unsupported attribution remains unknown.
- [x] Markdown and JSON outputs are tested.
- [x] Full regression suite passes.
- [x] Rules and limitations are documented.

Rules and limitations:

- Timeline events are generated deterministically from normalized observations.
- Related observations are grouped only when they share conversation context,
  stage, and a close timestamp window.
- User involvement is marked measured only when the captured observation actor
  and activity directly support it.
- Unsupported involvement remains unknown.
- Captured involvement counts describe evidence events only; they are not
  ownership, effort, value, authorship, or contribution percentages.

## Completed Milestone: Google Docs Adapter

Status: Complete

Goal: Import Google Docs revision and document evidence into Workprint's
normalized evidence pipeline.

Implemented scope:

- Static `.json`, `.txt`, and `.md` export support.
- Canonical `google-docs` source identifier.
- Document-level metadata preservation.
- Stable paragraph evidence references.
- No filesystem timestamp inference for text or Markdown exports.
- No paragraph authorship inference from document owners, authors, or editors.

Limitations:

- Static exports do not recover revision history.
- Static exports do not recover edit-by-edit authorship.
- Owners, authors, and editors remain document-level metadata unless evidence
  explicitly maps them to a block.

## Completed Milestone: Figma Adapter

Status: Complete

Goal: Import Figma design activity evidence without adding source-specific
logic to the investigation engine.

Implemented scope:

- Static structured `.json` export support.
- Canonical `figma` source identifier.
- Meaningful page and node filtering.
- File, page, node, parent, and node-path metadata preservation.
- Stable hierarchy-aware evidence references.
- No filesystem timestamp inference.
- No file-level timestamp assignment to individual nodes.
- No contributor, owner, editor, authorship, contribution, ownership, or effort
  inference.

Limitations:

- Static exports do not recover version history.
- Static exports do not recover comments or comment resolution history.
- Static exports do not recover contributor activity.
- Contributors, owners, and editors remain metadata unless evidence explicitly
  links them to a node or action.

## Completed Milestone: Report Visual Design and Shareability

Status: Complete

Goal: Improve report presentation so outputs are polished, readable, and easy
to share with nontechnical audiences.

Implemented scope:

- At-a-glance Markdown summary.
- Concise evidence boundary near the top of the report.
- Compact timeline overview table.
- More readable timeline event detail sections.
- Captured user involvement counts labeled as evidence-event counts.
- Stable evidence appendix with observation IDs and evidence references.
- No changes to evidence, investigation, observation, timeline, adapter, CLI, or
  JSON models.

Limitations:

- Markdown remains plain and portable.
- No HTML, CSS, images, or runtime dependencies are included.
- Report design does not change underlying evidence claims.

## Completed Milestone: Executive Report v1

Status: Complete

Goal: Add a reader-facing executive report that explains project goal,
outputs, evolution, human-AI collaboration, decisions, confidence, evidence
gaps, and investigation assurance before the existing detailed report.

Implemented scope:

- Derived Executive Report model separate from the core Investigation model.
- Deterministic ExecutiveReportBuilder.
- Executive Brief.
- Project Overview.
- Key Milestones.
- Human-AI Collaboration.
- Decision Analysis.
- Confidence Assessment.
- Evidence Gaps.
- Investigation Assurance.
- Additive `executive_report` JSON object.
- Shared JSON serialization helper for expert CLI and guided output.
- Copy-quality audit metadata with pinned unslop-text upstream revision.

Limitations:

- No LLM-generated narrative copy.
- No semantic clustering.
- No probabilistic confidence scoring.
- Copy-quality scanner is recorded as unavailable until safely integrated.
- Project goals, outputs, tools, and decision leadership remain unknown unless
  supported by explicit evidence.

## Completed Milestone: Executive Report Copy-Quality Audit Integration

Status: Complete

Goal: Complete the Executive Report copy-quality gate using the pinned
`unslop-text` scanner and methodology from JCarterJohnson's
`vibecoded-design-tells` project while preserving evidence boundaries and
clear attribution.

Implemented scope:

- Vendored reviewed upstream files from pinned revision
  `f7c4aefc2c797a66e55b49354a93917ab60d33ac`.
- Preserved attribution and licensing information through the complete
  upstream MIT license and third-party notice.
- Workprint-owned adapter around the upstream lexical scanner.
- Offline scanner invocation at report-generation time.
- Deterministic structural review for documented prose patterns.
- Evidence-preservation confirmation.
- Additive JSON audit metadata, including upstream author, project,
  repository, revision, license, and attribution notice.
- Expanded Markdown Copy-Quality Audit section.
- Status handling for `passed`, `passed_with_waivers`, `failed`, and
  `unavailable`.
- Tests covering attribution, scanner availability, status rules, structural
  checks, exclusions, Markdown, and JSON.

Limitations:

- The audit is not an authorship detector.
- A passing audit indicates that generated narrative satisfied the configured
  lexical and structural review; it does not establish human authorship or
  prove that AI was not involved.
- The audit reports findings and status; it does not automatically rewrite
  narrative copy.
- Medium and low findings require explicit waivers to pass with waivers.
- No finalized-output CLI mode or override flag is introduced in this
  milestone.

## Completed Milestone: Git Adapter

Status: Complete

Goal: Import local Git repository evidence into Workprint's normalized
evidence pipeline without using network services or inferring authorship,
ownership, effort, value, or contribution percentages.

Implemented scope:

- Canonical `git` source identifier and `Git` reader-facing label.
- Local repository input through the installed `git` command.
- Read-only command boundary using explicit argument arrays.
- Repository metadata capture, including root, current branch, and shallow
  history status.
- Commit metadata capture, including SHA, abbreviated SHA, timestamp, author
  and committer names/emails as recorded by Git, subject, body, parent SHAs,
  merge status, changed paths, change type, additions, deletions, and tags.
- Deterministic chronological commit ordering.
- Empty repository support through repository metadata records.
- Discovery and Guided Investigation selection for local Git repositories.
- Executive Report support for repository implementation chronology, merge
  milestones, and reduced Git-history gaps when Git evidence is supplied.
- Shallow-history disclosure when the repository reports incomplete history.
- Tests using temporary repositories rather than committed nested `.git`
  fixtures.

Limitations:

- Local Git only; no GitHub API or remote network access.
- Bare repositories are not supported in v1.
- Discovery does not automatically traverse unrelated nested repositories.
- File contents are not inspected; v1 uses commit and change metadata.
- Git author and committer fields are preserved as recorded metadata. They do
  not prove who personally wrote every changed line.
- Commit counts, file counts, additions, and deletions are repository-change
  metadata, not effort, ownership, value, authorship, productivity, or
  contribution measures.

## Completed Milestone: Project Discovery

Status: Complete

Goal: Preview supported evidence in a project directory before import or
investigation.

Implemented scope:

- `workprint discover [path]` command.
- Current working directory default when no path is supplied.
- Recursive filesystem scan.
- Git repository detection as a selectable evidence source.
- Adapter-driven detection for ChatGPT, Claude, Google Docs, and Figma
  evidence.
- Deterministic source and file ordering.
- Project readiness summary.
- No evidence import, investigation generation, report rendering, file
  modification, or attribution inference.

Limitations:

- Discovery recognizes supported evidence; it does not validate every future
  investigation outcome.
- Git discovery is narrow: it checks the selected repository context and does
  not automatically traverse unrelated nested repositories.
- Static export limitations still apply to document and design evidence.

## Completed Milestone: Guided Investigation Wizard

Status: Complete

Goal: Guide users from discovered evidence through source selection,
readiness review, and investigation setup without requiring command-line
knowledge.

Implemented scope:

- `workprint guide` command.
- Project folder confirmation.
- Reuse of Project Discovery.
- Plain-language display of discovered sources and files.
- Git repository selection when local Git evidence is available.
- File-level and source-level selection.
- Project name prompt.
- Dedicated default output directory: `workprint-output/`.
- Default Markdown and JSON outputs.
- Overwrite confirmation and cancellation paths that leave files unchanged.
- Reuse of the existing multi-source investigation pipeline.
- No changes to evidence, observation, investigation, timeline, report, JSON,
  or adapter data models.

Limitations:

- The workflow is terminal-based.
- Guided import does not infer attribution beyond existing deterministic
  evidence handling.

## Active Milestone: Low-Code/No-Code User Experience

Status: Ready for definition

Goal: Make Workprint usable without requiring terminal knowledge.

Detailed requirements: To be defined.

## Active Milestone: Claude Session Evidence (Tier 1a)

Status: Planned

Goal: Automatically discover and normalize evidence from local Claude Code
sessions and imported claude.ai Export Data archives, extending Workprint's
AI-collaboration evidence beyond the existing manual-export-only workflow.

User problem: Workprint only sees AI collaboration evidence today if someone
manually exports a claude.ai conversation and imports it. Claude Code
sessions produce no evidence at all unless a user takes an extra manual step
most people will not remember to take.

Requirements:

- New adapter implementing the existing `EvidenceAdapter` contract that
  discovers and reads local Claude Code JSONL session transcripts for the
  current project directory only.
- Audit of the existing Claude adapter against the actual current schema of
  Anthropic's official claude.ai Export Data archive, with fixes if the
  schema has drifted from what the adapter assumes.
- Both sources exposed through `workprint discover` and the existing
  multi-source investigation pipeline; no changes to the investigation
  engine's source-specific logic.
- Bounded reads: capped session count, capped excerpt length, structural
  evidence (turn counts, timestamps, referenced files) by default rather
  than raw transcript content.
- No new dependencies; both formats are parsed with the standard library.

Trust and evidence boundaries:

- Session transcripts may contain anything pasted into a prompt, including
  credentials or personal text. Content excerpts must be opt-in; structural
  evidence is the default.
- Matching a project directory to its Claude Code sessions relies on Claude
  Code's own local path-to-session-directory convention, which is not a
  published contract. The adapter must fail closed (report nothing) rather
  than guess and misattribute a session to the wrong project.
- claude.ai Export Data is a manual, user-initiated, time-boxed download;
  Workprint imports it but never fetches it automatically.

Explicitly out of scope for this milestone:

- Claude Desktop chat cache and Claude Cowork local cache. Both are only
  reachable through undocumented internal LevelDB/app-cache formats and
  would require a new dependency; tracked separately as Tier 1b below.
- Next.js Discoveries UI surfacing of these new evidence types.
- Any MCP or in-tool integration surface.
- Any inference about AI contribution beyond normalized, evidence-linked
  records.

Detailed acceptance criteria: to be finalized at Technical Design, before
implementation begins.

## Upcoming Milestones

1. Semantic correlation only after deterministic behavior is trustworthy

   Goal: Add semantic matching or inference only after deterministic evidence
   handling, traceability, and limitations are reliable.

   Detailed requirements: To be defined.

2. Claude Session Evidence (Tier 1b): Desktop chat cache and Cowork local
   cache

   Goal: Extend Claude session evidence to the Claude Desktop app's chat
   cache and Claude Cowork's local session cache, both of which require
   parsing undocumented internal LevelDB/app-cache storage formats and a new
   dependency.

   Detailed requirements: To be defined after Tier 1a validates the adapter
   pattern and the dependency decision is explicitly approved.

## Product UX Direction

The target experience should eventually:

- Avoid requiring terminal knowledge.
- Support guided source selection.
- Explain file and permission requirements.
- Show progress and errors in plain language.
- Provide preview and review before generating reports.
- Make uncertainty understandable.
- Support polished, shareable outputs.

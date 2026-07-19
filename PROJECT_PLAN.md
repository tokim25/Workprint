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
- [x] Claude Code adapter
- [x] Claude Cowork adapter
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

## Completed Milestone: Claude Session Evidence (Tier 1a)

Status: Complete

Goal: Automatically discover and normalize evidence from local Claude Code
sessions and imported claude.ai Export Data archives, extending Workprint's
AI-collaboration evidence beyond the existing manual-export-only workflow.

Implemented scope:

- `ClaudeCodeAdapter` (canonical source ID `claude-code`, label "Claude
  Code") implementing the existing `EvidenceAdapter` contract.
- Session-to-project matching by the `cwd` recorded inside each transcript,
  not by reproducing Claude Code's internal directory-naming convention;
  an unmatched project finds nothing rather than a wrong guess.
- Bounded reads: up to 20 most recently modified matching sessions per
  project, up to 5,000 transcript lines per session.
- Structural evidence by default: turn counts, role, timestamps, and
  tool-name counts for assistant turns (for example `Edit (2), Bash (1)`);
  no raw prompt or response text unless the adapter is explicitly
  constructed with `include_content_excerpts=True` (not yet exposed through
  the CLI).
- Sidechain (subagent) turns are recorded and flagged (`is_sidechain`)
  rather than silently merged into the primary conversation.
- `WORKPRINT_CLAUDE_HOME` environment variable overrides the default
  `~/.claude/projects` lookup location, primarily for testability.
- Registered in the adapter registry and wired into `workprint discover`,
  `workprint import`/`investigate`/`validate`, and the `workprint guide`
  terminal wizard, following the Git adapter's integration pattern.
- Audited the existing Claude export adapter and its fixture against
  Anthropic's documented Export Data format; confirmed no schema drift, no
  changes required.
- No changes to the investigation engine, extractor, or other adapters'
  data models.
- No new dependencies; the format is parsed with the standard library.

Limitations:

- Covers Claude Code and the manually exported claude.ai archive only.
  Claude Desktop chat cache and Claude Cowork local cache are not covered;
  both require parsing undocumented internal LevelDB/app-cache formats and
  are tracked separately as Tier 1b below.
- Session matching depends on Claude Code recording an accurate `cwd`; a
  session that never recorded a matching working directory will not be
  found.
- Raw content excerpts are not reachable from the CLI in this milestone.
- No Next.js Discoveries UI surfacing; CLI and Python API only.

## Completed Milestone: Claude Session Evidence (Tier 1b)

Status: Complete

Goal: Extend Claude session evidence to local Claude Cowork sessions,
originally assumed (in the Tier 1a write-up) to require the same
undocumented LevelDB/app-cache handling as Claude Desktop's chat cache.

Implemented scope:

- `ClaudeCoworkAdapter` (canonical source ID `claude-cowork`, label "Claude
  Cowork") implementing the existing `EvidenceAdapter` contract.
- Discovery that each Cowork session runs in its own sandboxed Claude Code
  home directory and writes a transcript in the same JSONL shape the Claude
  Code adapter reads — no new dependency needed, unlike what Tier 1a's
  write-up assumed for all of Tier 1b.
- Session-to-project matching via `userSelectedFolders` in the session's
  metadata file (`local_<uuid>.json`), not the transcript's own `cwd`,
  which points at an internal sandbox output path. An unmatched project
  finds nothing rather than a wrong guess.
- The same bounding, structural-by-default content, and sidechain flagging
  as the Claude Code adapter, implemented independently rather than by
  refactoring the already-shipped Claude Code adapter.
- Session metadata (`model`, `session_type`, `is_archived`) is included as
  evidence; `title` and `initialMessage`, which can contain real prompt
  text, are never read.
- A best-effort cross-platform default location
  (`WORKPRINT_COWORK_HOME` env var to override), verified only on macOS.
- Registered in the adapter registry and wired into `workprint discover`,
  `workprint import`/`investigate`/`validate`, and the `workprint guide`
  terminal wizard, following the Git and Claude Code adapters' pattern.
- No changes to the investigation engine, extractor, or other adapters.
- No new dependencies; the format is parsed with the standard library.

Limitations:

- Covers Cowork sessions only. Claude Desktop's own chat cache (as opposed
  to Cowork) is not covered; it is stored in an undocumented internal
  LevelDB format and is tracked separately as Tier 1c.
- Windows and Linux default paths are unverified; only macOS has been
  confirmed against a real installation.
- Cowork's own `audit.jsonl` action log is not read.
- Raw content excerpts are not reachable from the CLI in this milestone.
- No Next.js Discoveries UI surfacing; CLI and Python API only.

## Active Milestone: Low-Code/No-Code User Experience

Status: Ready for definition

Goal: Make Workprint usable without requiring terminal knowledge.

Detailed requirements: To be defined.

## Upcoming Milestones

1. Semantic correlation only after deterministic behavior is trustworthy

   Goal: Add semantic matching or inference only after deterministic evidence
   handling, traceability, and limitations are reliable.

   Detailed requirements: To be defined.

2. Claude Session Evidence (Tier 1c): Claude Desktop chat cache

   Goal: Extend Claude session evidence to Claude Desktop's own chat cache
   (as opposed to Cowork, covered in Tier 1b), which requires parsing an
   undocumented internal LevelDB storage format and a new dependency.

   Detailed requirements: To be defined; requires an explicit dependency
   decision before implementation begins.

## Product UX Direction

The target experience should eventually:

- Avoid requiring terminal knowledge.
- Support guided source selection.
- Explain file and permission requirements.
- Show progress and errors in plain language.
- Provide preview and review before generating reports.
- Make uncertainty understandable.
- Support polished, shareable outputs.

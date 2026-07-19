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
- [x] Claude Desktop Chat adapter (experimental deep-parse mode)
- [x] Local MCP server
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

## Completed Milestone: Claude Session Evidence (Tier 1c)

Status: Complete (experimental deep-parse mode, verified against real data)

Goal: Report on the Claude desktop app's local claude.ai chat cache
(distinct from Cowork, covered in Tier 1b), the last of the three Claude
surfaces this phase set out to cover.

Implemented scope:

- `ClaudeDesktopChatAdapter` (canonical source ID `claude-desktop-chat`,
  label "Claude Desktop Chat") implementing the existing `EvidenceAdapter`
  contract.
- Presence-only mode (default, no dependency): reports only that the local
  IndexedDB cache exists and when it was last modified. Verified against a
  real local installation.
- Opt-in `deep_parse=True` mode: scans only the `keyval-store` database
  (verified against real data; three other databases in the same origin,
  including one that plausibly holds authentication material, are
  deliberately never opened) using the pinned `ccl_chromium_reader`
  dependency, then a heuristic scan for dict-shaped values resembling a
  chat turn. The base `workprint` package's dependency list stays empty;
  this is an opt-in extra.
- Every record from this source carries `project_specific: false`, because
  claude.ai chat has no folder concept to match against a project — unlike
  every other adapter in this codebase. Semantic correlation (matching
  conversations to a project by content) is intentionally not attempted
  here; it is tracked as a prerequisite, deferred upcoming capability.
- Deep-parse records carry `may_include_deleted_records: false`: records
  are read with `live_only=True`, verified during the real-data pass to
  exclude deleted/superseded entries.
- Plain-language trade-off disclosure (what presence-only vs. deep parsing
  each reveal, the account-wide caveat, and confirmation that everything
  stays local) shown by `workprint discover` whenever the cache is
  detected, and offered as an explicit accept/decline prompt by the
  `workprint guide` interactive wizard before any deep parsing happens.
  Non-interactive or scripted `guide` runs never enable it.
- `WORKPRINT_CLAUDE_DESKTOP_HOME` and `WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE`
  environment variables for path override and (mainly wizard-internal)
  consent propagation.
- Registered in the adapter registry and wired into `workprint discover`,
  `workprint import`/`investigate`/`validate`, and the `workprint guide`
  wizard, following the existing adapters' pattern.

Verification pass (after initial implementation): the deep-parse path was
built and initially shipped without being run against real data, because no
Python 3.10+ environment was available at the time. Once one was set up, two
real bugs surfaced and were fixed: the declared optional dependency
resolved to an unrelated, buggy PyPI package rather than the library whose
API the code was written against (see
`docs/foundation/DECISION_LOG.md`, "Claude Desktop Chat's Optional
Dependency Is Pinned, Not Name-Matched"), and the adapter's own database
enumeration assumed the wrong shape for the real API's return value. Both
are fixed. The general lesson is recorded in
`docs/foundation/ENGINEERING_PRINCIPLES.md`, "External Dependencies Are
Verified, Not Assumed."

A second pass confirmed the heuristic turn-scanning logic itself: the one
live record found in the real local cache during the first pass could not
be read (its externally serialized value was missing from disk), so the
turn-classification heuristic had not actually been exercised against a
readable value. It has since been verified against a database written by
a real Chrome browser through the real `indexedDB` API — genuine Chromium
encoding, not hand-crafted bytes — committed as a regression fixture at
`fixtures/claude-desktop-chat/synthetic-keyval-store.indexeddb.leveldb`.
See `docs/claude-desktop-chat-adapter.md`, "How This Was Verified," for the
precise line between what the code is now confirmed to do correctly and
what remains an open question about claude.ai's actual cache contents.

Limitations:

- The heuristic logic is confirmed correct against a readable value of the
  hypothesized shape. Whether claude.ai's own real cache reliably produces
  a *readable* value at all, on a given machine at a given time, is still
  unconfirmed — dogfood runs against the live real cache found a candidate
  turn in one run out of several.
- Evidence is account-wide only; it cannot currently be attributed to the
  project under investigation.
- The IndexedDB/LevelDB format is undocumented by Anthropic and may change
  without notice on a Claude Desktop update, unlike the other Claude
  sources in this phase, which read formats Anthropic's own products
  write and control.
- `title` and `initialMessage`-equivalent full conversation content is
  never read outside the opt-in excerpt flag, which is not exposed
  through the CLI.
- Windows and Linux default paths are unverified; only macOS has been
  confirmed against a real installation.
- No Next.js Discoveries UI surfacing at the time this milestone shipped;
  see "Completed Milestone: Claude Session Evidence Discoveries UI" below
  for the follow-on that added it.

## Completed Milestone: Claude Session Evidence Discoveries UI

Status: Complete

Goal: Surface local Claude Code, Cowork, and Desktop Chat evidence (Tiers
1a-1c) in the Next.js Discoveries UI, so this evidence is visible in the
actual product rather than the Python CLI only.

Implemented scope:

- `src/workprint/claude_local_summary.py`: a bounded Python entry point
  mirroring `git_summary.py`'s pattern, aggregating all three adapters'
  `read()` output for one project path into session/turn counts,
  human/assistant/sidechain breakdowns, and tool-use tallies. An empty or
  "not found" result from any of the three sources is not an error, unlike
  Git; most projects will not have used all three.
- `app/api/claude-local-summary/route.ts`: mirrors `git-summary`'s
  spawn/timeout/path-validation/error-code-allowlist discipline exactly.
- `lib/claude-local-summary.ts`: TS types matching the Python JSON, plus
  pure claim/support-sentence helpers, mirroring `lib/git-summary.ts`.
- `components/claude-session-evidence.tsx`: discoveries-screen rendering
  for all three sources, mirroring `GitTimeline`'s pattern.
- Sources-screen wiring: the "Local repository path" input and its
  section were renamed and reused as a single shared "Local project path"
  input, since the browser's File System Access API (used for the
  drag-and-drop folder picker) never exposes a real OS path and cannot see
  the fixed OS-level locations these three adapters read from. A "Read
  Claude sessions" button sits next to the existing "Read Git metadata"
  button, both keyed off the same path.
- Claude Desktop Chat's deep-parse trade-off is an inline, off-by-default
  expandable disclosure and checkbox next to that button, not a separate
  screen or wizard step, per `docs/web-experience-v0.md`'s explicit "no
  standalone trust page" guidance. The disclosure text matches
  `discovery.py`'s `_claude_desktop_chat_disclosure()` almost verbatim.
- `evidence-drawer.tsx`'s header and footer copy, previously hardcoded to
  "Sample evidence" even though Git and project-file evidence were already
  real, now reflects whether the currently displayed evidence is sample
  data or was actually read from the local project.
- Verified end-to-end against this repository's own real local Claude
  Code, Cowork, and Desktop Chat data in a running dev server, including
  the deep-parse checkbox path with the optional dependency installed
  (correctly reported "detailed reading found nothing readable this
  time," consistent with the Tier 1c verification finding) and invalid-path
  error handling.

Limitations:

- No per-session review/opt-out UI (unlike `project-file-evidence.tsx`'s
  per-file exclusion checkboxes): Claude Code/Cowork/Desktop Chat reads are
  already bounded and structural-by-default at the adapter level, so there
  is one fetch action per source rather than a discover-then-review-then-
  read flow.
- The top-level "First supported insight" headline still only arbitrates
  between Git and sample data; Claude session evidence appears as its own
  section and in the evidence drawer, but does not compete to become the
  headline claim. Changing that selection logic was treated as a separate,
  more consequential product decision outside this milestone's scope.
- No automated JS/TS tests exist for this UI in either the pre-existing
  code or this milestone; verification was manual, end-to-end, against
  real data in a running dev server.

## Completed Milestone: Local MCP Server

Status: Complete

Goal: Make Workprint's discovery and investigation capabilities callable
directly from inside Claude Desktop or Claude Code over the Model Context
Protocol (MCP), the first "runs inside the tool" surface, rather than
requiring the CLI or the separate web app.

Implemented scope:

- `src/workprint/mcp_server.py`: a `FastMCP`-based server exposing three
  read-only tools (`readOnlyHint: true`, `destructiveHint: false`,
  `openWorldHint: false`) that wrap the existing discovery/investigation
  pipeline unchanged: `list_supported_sources`, `discover_project`
  (mirrors `workprint discover`), and `investigate_project` (reuses
  `guided.py`'s `evidence_files_from_discovery`/`select_evidence_files`
  selection logic and the existing multi-source investigation pipeline,
  without its interactive prompts or file-writing side effects).
- `mcp` (the official `modelcontextprotocol/python-sdk`, verified
  installed and imported successfully, `requires-python` matching this
  project's) is a new optional extra (`pip install '.[mcp]'`), keeping
  the base package dependency-free. A `workprint-mcp` console script
  entry point runs it over stdio, the standard local transport.
- `investigate_project`'s response is deliberately bounded, not the full
  report: measuring a real investigation's complete JSON on this
  project's own history found several megabytes (2,169 evidence IDs on a
  single finding, 2.2MB of raw observations) -- far too large for a
  conversational tool result. By default, findings carry only the first
  10 evidence IDs plus a total count, the executive brief is included but
  the rest of the executive report is not, and observations/timeline are
  represented only as counts. `include_full_report`,
  `include_observations`, and `include_timeline` parameters opt into the
  complete data. This brought a real investigation's tool response from
  3.5MB down to under 5KB by default.
- `include_desktop_chat_deep_parse` parameter, defaulting to `false`,
  matching every other Workprint surface's default for that source.
- `docs/mcp-server.md`: installation, verified Claude Desktop config file
  location and format, Claude Code `.mcp.json`/`claude mcp add` config,
  tool reference, evidence boundaries, and explicit out-of-scope items.

Verification: confirmed the `mcp` PyPI package's repository metadata
matches the real `modelcontextprotocol/python-sdk` GitHub org before
depending on it (see "External Dependencies Are Verified, Not Assumed" in
`docs/foundation/ENGINEERING_PRINCIPLES.md`). Beyond unit tests, ran the
actual server as a subprocess and connected with a real MCP client
session (the same stdio protocol Claude Desktop and Claude Code use) to
call all three tools against this repository's own real evidence,
including bad-path error handling.

Limitations:

- No write tools; the server cannot modify files, evidence, or its own
  configuration.
- No project-selection or ambient context: every tool call requires an
  explicit `project_path` argument.
- Claude Desktop and Claude Code configuration was verified by inspecting
  this project's own real `claude_desktop_config.json` location and
  format; the actual MCP entry was not added to a live config as part of
  this milestone, since that would modify the user's real application
  settings.
- No automated tests exist that drive the server through an actual Claude
  Desktop or Claude Code session; verification used the official MCP
  Python client SDK directly.

## Active Milestone: Low-Code/No-Code User Experience

Status: Ready for definition

Goal: Make Workprint usable without requiring terminal knowledge.

Detailed requirements: To be defined.

## Upcoming Milestones

1. Semantic correlation only after deterministic behavior is trustworthy

   Goal: Add semantic matching or inference only after deterministic evidence
   handling, traceability, and limitations are reliable. This is also the
   prerequisite for ever attributing Claude Desktop Chat evidence (Tier 1c)
   to a specific project, since that source has no folder concept of its
   own to match against — see the Limitations of that milestone above.

   Detailed requirements: To be defined.

2. Claude Session Evidence (Tier 1c) real-cache readability

   Goal: Determine whether claude.ai's actual local cache reliably
   produces a readable `keyval-store` value in ordinary use, as opposed to
   the synthetic-but-genuinely-Chromium-encoded fixture used to verify the
   extraction logic itself (see Tier 1c above). This is now a question
   about claude.ai's real behavior over time, not about whether
   Workprint's code works correctly.

   Detailed requirements: To be defined.

## Product UX Direction

The target experience should eventually:

- Avoid requiring terminal knowledge.
- Support guided source selection.
- Explain file and permission requirements.
- Show progress and errors in plain language.
- Provide preview and review before generating reports.
- Make uncertainty understandable.
- Support polished, shareable outputs.

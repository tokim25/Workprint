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

## Completed Milestone: Project Discovery

Status: Complete

Goal: Preview supported evidence in a project directory before import or
investigation.

Implemented scope:

- `workprint discover [path]` command.
- Current working directory default when no path is supplied.
- Recursive filesystem scan.
- Git repository detection.
- Adapter-driven detection for ChatGPT, Claude, Google Docs, and Figma
  evidence.
- Deterministic source and file ordering.
- Project readiness summary.
- No evidence import, investigation generation, report rendering, file
  modification, or attribution inference.

Limitations:

- Discovery recognizes supported evidence; it does not validate every future
  investigation outcome.
- Git detection only identifies repository presence.
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
- Git repository detection shown as informational only.
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
- Git repositories cannot be selected until a Git evidence adapter exists.
- Guided import does not infer attribution beyond existing deterministic
  evidence handling.

## Active Milestone: Low-Code/No-Code User Experience

Status: Ready for definition

Goal: Make Workprint usable without requiring terminal knowledge.

Detailed requirements: To be defined.

## Upcoming Milestones

1. Semantic correlation only after deterministic behavior is trustworthy

   Goal: Add semantic matching or inference only after deterministic evidence
   handling, traceability, and limitations are reliable.

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

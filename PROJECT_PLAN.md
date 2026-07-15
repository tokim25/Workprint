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
- [x] Markdown and JSON reporting
- [x] Multi-source investigations
- [x] Exact, source-aware duplicate suppression

## Active Milestone: Timeline Report

Status: Ready for implementation

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

- Existing commands remain compatible.
- Existing findings remain available.
- Timeline is additive.
- Classifications are evidence-linked.
- Unsupported attribution remains unknown.
- Markdown and JSON outputs are tested.
- Full regression suite passes.
- Rules and limitations are documented.

## Upcoming Milestones

1. Google Docs adapter

   Goal: Import Google Docs revision and document evidence into Workprint's
   normalized evidence pipeline.

   Detailed requirements: To be defined.

2. Figma adapter

   Goal: Import Figma design activity evidence without adding source-specific
   logic to the investigation engine.

   Detailed requirements: To be defined.

3. Report visual design and shareability

   Goal: Improve report presentation so outputs are polished, readable, and
   easy to share with nontechnical audiences.

   Detailed requirements: To be defined.

4. Low-code/no-code user experience

   Goal: Make Workprint usable without requiring command-line knowledge.

   Detailed requirements: To be defined.

5. Guided import and project setup

   Goal: Guide users through source selection, file requirements, permissions,
   and project configuration.

   Detailed requirements: To be defined.

6. Semantic correlation only after deterministic behavior is trustworthy

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

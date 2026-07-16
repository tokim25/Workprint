# Project Context

Status: Living document
Purpose: Records the current repository state, milestones, capabilities, and limitations
Expected Update Frequency: Living document

This document is the living memory of the repository. It should evolve as
Workprint changes. When a milestone completes, when architecture changes, or
when limitations are resolved or discovered, update this file alongside the
more specific implementation and product documents.

## Current Architecture

Workprint is organized as a small evidence pipeline:

```text
Evidence Sources
  ↓
Discovery
  ↓
Adapters
  ↓
Normalized Evidence
  ↓
Observations
  ↓
Timeline
  ↓
Investigation
  ↓
Executive Report
  ↓
Markdown / JSON
```

Evidence adapters own source parsing and return normalized records. The
investigation engine works from normalized observations rather than
source-specific artifacts. Timeline generation groups and orders observations
deterministically. Reports present investigation data in Markdown or JSON
without changing the evidence model.

## Completed Milestones

Workprint currently includes these completed capabilities:

- ChatGPT import.
- Claude import.
- EvidenceAdapter contract.
- Adapter registry.
- Canonical observations.
- Deterministic investigation engine.
- Timeline Report.
- Google Docs static export adapter.
- Figma static export adapter.
- Report visual design and shareability.
- Executive Report v1.
- Executive Report copy-quality audit integration.
- Project Discovery.
- Guided Investigation Wizard.
- Markdown and JSON reporting.
- Multi-source investigations.
- Exact, source-aware duplicate suppression.

## Current Milestone

The active milestone is Low-Code/No-Code User Experience. Its goal is to make
Workprint usable without requiring terminal knowledge.

The existing Guided Investigation workflow is a terminal-based bridge toward
that direction. It previews discovered evidence, lets users select sources,
asks for a project name, and generates Markdown and JSON outputs through the
same multi-source investigation pipeline used by expert commands.

## Near-Term Roadmap

Near-term work should continue reducing the amount of project-specific command
knowledge required from users while preserving evidence boundaries. Likely
areas include:

- clearer guided workflow language;
- safer source selection;
- better readiness explanations from discovery;
- report output flows that are easier to share;
- more direct connection between discovery results and user-facing confidence;
- continued dogfooding against Workprint's own project history.

## Long-Term Roadmap

Long-term development should expand both evidence coverage and user
accessibility. Directionally, Workprint should move toward:

- additional source adapters;
- richer project timelines;
- better coverage and corroboration analysis;
- no-code or low-code report generation;
- stronger evidence appendix navigation;
- more useful executive reports for hiring, client, audit, and teammate
  contexts;
- clear integration points for future interfaces without weakening the core
  investigation model.

## Known Limitations

Static Google Docs exports do not recover revision history, edit-by-edit
authorship, deleted text, or paragraph authorship unless supplied evidence maps
those facts directly.

Static Figma exports do not recover version history, comments, comment
resolution history, contributor activity, or authorship. File-level metadata
does not become node-level attribution.

Discovery recognizes supported evidence, but it does not validate every future
investigation outcome. Git repository detection is informational only until a
Git evidence adapter exists.

Guided Investigation is currently terminal-based. It improves usability, but it
does not yet deliver a full low-code or no-code experience.

Executive Report v1 is deterministic and derived from existing investigation
data. It includes an offline copy-quality audit integration using the pinned
`unslop-text` scanner from JCarterJohnson's `vibecoded-design-tells` project,
plus Workprint-owned structural checks and evidence-preservation validation.
It does not use LLM-generated narrative copy, semantic clustering,
probabilistic confidence scoring, hidden contribution estimates, or authorship
detection.

## Technical Debt

Semantic duplicate detection across different platforms is not implemented.
Current duplicate suppression handles exact, source-aware duplicates.

Git evidence import is not implemented. Discovery can detect Git repository
presence, but Git is not selectable for investigation.

Low-code and no-code UX remains at the definition stage. Current workflows
still rely on terminal interaction or scripted CLI options.

## Future Dogfooding

An aspirational milestone is for Workprint to investigate the Workprint
repository itself using its own evidence sources: Git history, AI
conversations, documentation, design artifacts, and other supported project
records.

That future self-investigation should produce an Executive Report that
accurately explains Workprint's evolution, major decisions, collaboration
patterns, confidence, and evidence gaps. This is not a current capability.

## Major Capabilities

Workprint can import supported ChatGPT and Claude conversation exports, static
Google Docs exports, and static Figma JSON exports. It can discover supported
evidence in a project folder, combine multiple sources into one investigation,
generate deterministic observations and timeline events, build an Executive
Report, run the Executive Report copy-quality audit offline, and render
Markdown or JSON outputs.

The system preserves source boundaries. It separates user activity,
collaborator activity, AI/tool activity, joint activity, and unattributed
activity when evidence supports those distinctions. It keeps unsupported
activity unknown.

## Current Investigation Pipeline

The current investigation pipeline begins with explicit or discovered evidence
inputs. Registered adapters validate and read source artifacts. Normalized
records are converted into observations with evidence references. Multi-source
orchestration suppresses exact duplicates and sorts observations before
passing them to the investigation engine.

The engine orders observations, summarizes captured activity, creates bounded
findings, builds timeline events, and records unknowns and limitations. The
Executive Report is derived from the completed investigation. Markdown and JSON
renderers then present the same investigation data for readers and tools.

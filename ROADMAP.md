# Roadmap

## Completed Foundation

### v0.3.0 — ChatGPT vertical slice

- [x] ChatGPT export reader
- [x] Normalized messages
- [x] Canonical observations
- [x] Investigation engine
- [x] Markdown and JSON reports
- [x] CLI
- [x] Tests

### v0.4.0 — Claude and multi-source support

- [x] Claude export reader
- [x] Shared `EvidenceAdapter` contract
- [x] Adapter registry
- [x] Shared multi-source investigation command
- [x] Exact, source-aware duplicate suppression for repeated evidence inputs

## Active Capability — Timeline Report

Status: Complete

Goal: Generate a chronological, evidence-linked account of how a project
developed, including the investigated user's involvement at every stage.

This capability is additive. Existing import, investigation, report, and
multi-source commands remain compatible, and existing findings remain
available.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for requirements and acceptance criteria.

## Active Capability — Google Docs Adapter

Status: Complete

Goal: Import Google Docs revision and document evidence into Workprint's
normalized evidence pipeline.

See [docs/google-docs-import.md](docs/google-docs-import.md) for supported
formats and static-export limitations.

## Active Capability — Figma Adapter

Status: Complete

Goal: Import Figma design activity evidence without adding source-specific
logic to the investigation engine.

See [docs/figma-import.md](docs/figma-import.md) for supported schema,
metadata handling, and static-export limitations.

## Active Capability — Report Visual Design and Shareability

Status: Complete

Goal: Improve report presentation so outputs are polished, readable, and easy
to share with nontechnical audiences.

## Active Capability — Project Discovery

Status: Complete

Goal: Preview supported evidence in a project directory before import or
investigation.

See [docs/project-discovery.md](docs/project-discovery.md) for command usage,
supported evidence, and limitations.

## Active Capability — Guided Investigation Wizard

Status: Complete

Goal: Guide users from discovered evidence through source selection,
readiness review, and investigation setup without requiring command-line
knowledge.

See [docs/guided-investigation.md](docs/guided-investigation.md) for the
guided workflow, selection syntax, output behavior, and limitations.

## Active Capability — Low-Code/No-Code User Experience

Status: Ready for definition

Goal: Make Workprint usable without requiring command-line knowledge.

## Active Capability — Claude Session Evidence (Tier 1a)

Status: Planned

Goal: Automatically discover and normalize evidence from local Claude Code
sessions and imported claude.ai Export Data archives, so AI collaboration
evidence does not depend on a user remembering a manual export step for
every source.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for requirements and limitations.

## Upcoming Capabilities

1. Semantic correlation only after deterministic behavior is trustworthy
2. Claude Session Evidence (Tier 1b) — Claude Desktop chat cache and Claude
   Cowork local cache, deferred from Tier 1a because both require parsing
   undocumented internal storage formats and a new dependency

Detailed requirements for upcoming capabilities are tracked in
[PROJECT_PLAN.md](PROJECT_PLAN.md).

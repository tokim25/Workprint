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

Status: Ready for implementation

Goal: Generate a chronological, evidence-linked account of how a project
developed, including the investigated user's involvement at every stage.

This capability is additive. Existing import, investigation, report, and
multi-source commands must remain compatible, and existing findings must remain
available.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for requirements and acceptance criteria.

## Upcoming Capabilities

1. Google Docs adapter
2. Figma adapter
3. Report visual design and shareability
4. Low-code/no-code user experience
5. Guided import and project setup
6. Semantic correlation only after deterministic behavior is trustworthy

Detailed requirements for upcoming capabilities are tracked in
[PROJECT_PLAN.md](PROJECT_PLAN.md).

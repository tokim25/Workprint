# Changelog

## [Unreleased]

### Added

- Canonical `Observation` Python model and JSON Schema.
- Observation model documentation and validation tests.

### Changed

- Investigation input validation now uses the canonical Observation model while preserving the existing evidence-record format.

## [0.1.0] - 2026-07-14

### Added

- Initial Workprint product definition and repository structure.
- Claude Agent Skill with evidence-first workflow.
- Optional `/workprint` Claude Code command.
- Evidence, attribution, confidence, estimation, and reporting specifications.
- JSON schemas for evidence records, findings, and reports.
- Executive, detailed, portfolio, and validation report templates.
- Worked examples for software and learning-design projects.

### Known limitations

- Evidence ingestion is manual.
- No external connectors or automated parsers are included.
- Active-time estimation remains heuristic.
- Claude can only analyze evidence supplied or explicitly made available.

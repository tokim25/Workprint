# Changelog


## Unreleased

### Added

- Claude conversation adapter and fixture support.
- Claude import documentation and adapter tests.
- Shared `EvidenceAdapter` contract for source-specific evidence readers.
- Adapter registry for CLI and future evidence-source discovery.
- Contract and registry tests.

### Changed

- `ChatGPTAdapter` now implements `EvidenceAdapter`.
- CLI source selection now uses the adapter registry.

## 0.3.0 - 2026-07-14

### Added

- Complete ChatGPT-to-investigation vertical slice.
- Canonical Observation and NormalizedMessage models.
- Deterministic observation extraction.
- ChatGPT export reader.
- Investigation engine.
- Markdown and JSON report rendering.
- CLI commands for importing and investigating ChatGPT exports.
- Sample fixture and automated tests.

### Known limitations

- ChatGPT is the only supported source in this release.
- Observation extraction is keyword- and pattern-based.
- Active-time estimates are not included.
- Branching conversation paths are reduced to the current message lineage when available.

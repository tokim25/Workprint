# Changelog


## Unreleased

### Added

- Shareable Markdown report structure with at-a-glance summary, evidence
  boundary, compact timeline overview, and evidence appendix.
- Figma adapter for static structured JSON exports.
- Google Docs adapter for static `.json`, `.txt`, and `.md` exports.
- Timeline Report with canonical timeline events, deterministic involvement
  classification, Markdown rendering, and structured JSON output.
- Project operating documentation for agent instructions, capability planning,
  architectural decisions, and contributor workflow.
- Reconstructed complete foundation tree alongside adapter and multi-source work.
- Multi-source investigation command for combining registered evidence adapters.
- Exact duplicate suppression across repeated evidence inputs.
- Multi-source investigation tests and documentation.
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

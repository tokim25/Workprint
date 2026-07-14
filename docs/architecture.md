# Architecture

Workprint v0.3.0 uses a small, explicit pipeline:

```text
Raw ChatGPT export
        ↓
ChatGPTAdapter
        ↓
NormalizedMessage[]
        ↓
Deterministic extractor
        ↓
Observation[]
        ↓
Investigation engine
        ↓
Markdown or JSON report
```

## Adapter

The adapter understands vendor-specific export structure. It does not make project-level conclusions.

## Normalized message

A normalized message preserves:

- source;
- conversation ID;
- message ID;
- role;
- text;
- timestamp;
- stable evidence locator.

## Observation

An observation is a normalized statement tied to evidence. It records an activity label but does not claim ownership or total effort.

## Investigation engine

The engine orders observations, summarizes recorded activity, creates bounded findings, and lists unknowns and limitations.

## Reports

Reports are presentations of the same investigation data. Markdown and JSON are supported in this release.

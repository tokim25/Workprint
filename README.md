# Workprint

**Reconstruct how work gets made.**

Workprint turns exported AI conversations into evidence-backed project investigations. This v0.3.0 foundation release includes one complete vertical slice:

```text
ChatGPT export
    ↓
Normalized messages
    ↓
Observations
    ↓
Investigation
    ↓
Markdown or JSON report
```

## What works

- Uses a shared `EvidenceAdapter` contract for evidence-source readers.
- Imports common ChatGPT `conversations.json` exports.
- Normalizes user and assistant messages.
- Extracts deterministic observations.
- Reconstructs a chronological timeline.
- Identifies explicit decisions, suggestions, implementation statements, and unknowns.
- Produces Markdown and JSON investigation reports.
- Keeps source references for traceability.
- Uses no external runtime dependencies.

## Install locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run the sample

```bash
workprint investigate chatgpt fixtures/chatgpt/sample-conversations.json   --project "Workprint"   --output report.md
```

Or without installing:

```bash
PYTHONPATH=src python3 -m workprint.cli investigate chatgpt   fixtures/chatgpt/sample-conversations.json   --project "Workprint"   --output report.md
```

## Import observations only

```bash
workprint import chatgpt fixtures/chatgpt/sample-conversations.json   --output observations.json
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Limits

The observation extractor is intentionally deterministic. It detects explicit language and does not claim to understand unstated intent. Workprint may miss implicit decisions, subtle revisions, or activity that occurred outside the exported conversation.

## Rights

Copyright © 2026 Tony Kim. All rights reserved. This repository is not currently open source.

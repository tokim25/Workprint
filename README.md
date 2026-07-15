# Workprint

**Reconstruct how work gets made.**

Workprint turns exported AI conversations into evidence-backed project investigations. The current development state builds on the v0.3.0 ChatGPT foundation with shared adapters, Claude import, and multi-source investigations:

```text
ChatGPT or Claude export
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
- Imports common Claude JSON conversation exports.
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


## Run a Claude investigation

```bash
workprint investigate claude fixtures/claude/sample-conversations.json \
  --project "Workprint" \
  --output claude-report.md
```


## Combine ChatGPT and Claude evidence

```bash
workprint investigate-multi \
  --evidence chatgpt=exports/chatgpt.json \
  --evidence claude=exports/claude.json \
  --project "Workprint" \
  --output combined-report.md
```

## Import observations only

```bash
workprint import chatgpt fixtures/chatgpt/sample-conversations.json   --output observations.json
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

Without installing first:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Project governance

- [AGENTS.md](AGENTS.md) defines permanent instructions for coding agents.
- [PROJECT_PLAN.md](PROJECT_PLAN.md) tracks active and upcoming capabilities.
- [DECISIONS.md](DECISIONS.md) records architectural and product decisions.
- [CONTRIBUTING.md](CONTRIBUTING.md) explains setup, testing, branch, commit, and pull request expectations.

## Limits

The observation extractor is intentionally deterministic. It detects explicit language and does not claim to understand unstated intent. Workprint may miss implicit decisions, subtle revisions, or activity that occurred outside the exported conversation.

## Rights

Copyright © 2026 Tony Kim. All rights reserved. This repository is not currently open source.

# Investigation Engine

The v0.1 investigation engine converts normalized evidence records into a repeatable investigation report.

## What it does

- validates evidence records;
- orders evidence into a timeline;
- extracts explicit decisions, adoptions, and rejections;
- groups nearby timestamped events into observed sessions;
- creates basic actor/activity findings;
- summarizes evidence coverage;
- lists unknowns and limitations; and
- renders Markdown or JSON.

## What it does not do

The engine does not independently interpret raw chat exports, documents, images, or Git repositories. Claude or a future evidence adapter must first normalize those sources into Workprint evidence records.

This boundary is intentional:

- Claude handles context-dependent interpretation.
- The engine handles deterministic validation, organization, calculation, and rendering.

## Install locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run the dogfood fixture

```bash
workprint fixtures/workprint-dogfood.json \
  --output workprint-investigation.md
```

JSON output:

```bash
workprint fixtures/workprint-dogfood.json \
  --format json \
  --output workprint-investigation.json
```

## Input structure

```json
{
  "project": "Example project",
  "scope": "Date range or investigation question",
  "evidence": [
    {
      "id": "EV-001",
      "source_type": "chat_message",
      "source_locator": "Conversation timestamp or link",
      "event_time": "2026-07-14T12:00:00-07:00",
      "actor": "Contributor name",
      "activity": "decision",
      "artifact": "Product name",
      "observation": "Selected Workprint as the product name.",
      "reliability": "high",
      "completeness": "partial"
    }
  ]
}
```

See `schemas/evidence.schema.json` for the portable evidence definition.

## Session estimates

Events no more than 30 minutes apart are grouped into a session by default. The engine reports only the observed span from first event to last event. It does not add time before or after a session and does not claim that the contributor was continuously active.

Change the gap when needed:

```bash
workprint evidence.json --session-gap 20
```

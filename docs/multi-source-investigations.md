# Multi-Source Investigations

Workprint can combine evidence from several supported adapters into one
investigation.

## Command

```bash
workprint investigate-multi \
  --evidence chatgpt=exports/chatgpt.json \
  --evidence claude=exports/claude.json \
  --project "Workprint" \
  --output report.md
```

Repeat `--evidence` for each input. Each argument uses `SOURCE=PATH`.

## Processing steps

1. Select the registered adapter for each source.
2. Validate and read each file.
3. Convert source records into observations.
4. Remove exact duplicate observations.
5. Sort all observations into one timeline.
6. Produce one Markdown or JSON investigation.

## Duplicate handling

Exact duplicates are identified using source, normalized statement, evidence
reference, and timestamp.

Semantic duplicates across different platforms are not yet detected.

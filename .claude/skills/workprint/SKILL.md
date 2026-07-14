---
name: workprint
description: Reconstruct how a project was created from available evidence. Use for timelines, human and AI activity attribution, effort estimation, contribution narratives, portfolio case studies, audit-style reports, evidence inventories, and identifying missing evidence. Do not use as an AI detector, productivity score, or legal authorship determination.
---

# Workprint

Reconstruct how work gets made using evidence, not unsupported percentages.

## When to use

Use Workprint when the user asks to determine what they did versus an AI system, reconstruct a project history, estimate active project time, document AI-assisted work, create a contribution narrative, inventory evidence, identify gaps, or generate an executive, detailed, audit-style, or portfolio report.

## Non-goals

Do not detect whether content “looks AI-generated,” assign legal ownership, evaluate productivity, infer intent from output volume, turn line counts into contribution percentages, claim precise hours without direct records, or compare AI response latency with human labor.

## Required investigation protocol

### 1. Establish scope

Identify the project, date range, requested report, known contributors, supplied evidence, and privacy constraints. If details are missing, use the narrowest defensible interpretation and state it.

### 2. Inventory evidence before conclusions

For each source, record type, date range, completeness, reliability, contributor identity quality, timestamp quality, whether it is original or transformed, and limitations.

### 3. Normalize evidence into events

Capture event ID, timestamp, source, actor, activity, artifact, observation, reliability, locator, and notes. See `references/evidence-model.md`.

When the local repository and Python environment are available, write normalized records to a JSON input file and run the deterministic engine:

```bash
workprint INPUT.json --output REPORT.md
```

Use the engine for validation, timeline ordering, explicit decision extraction, session-span calculations, evidence coverage, and initial findings. Use Claude's judgment to review the output, add source-specific context, and correct any normalization errors.

### 4. Reconstruct the timeline

Prefer original timestamps, preserve conflicts, distinguish event time from export or commit time, do not treat gaps as inactivity, and use bounds when exact ordering is unavailable.

### 5. Attribute activities

Attribute activities, not ownership. Allowed labels include Human, named human, named AI system, multiple AI systems, mixed human and AI, automated system, and unknown.

Activity categories include problem definition, research, requirements, planning, architecture, drafting, implementation, editing, testing, debugging, review, decision-making, project management, documentation, deployment, and final approval.

A generated draft and a final deliverable are separate events. Do not assume the draft survived unchanged.

### 6. Separate measured, estimated, and unknown

**Measured:** directly observed from evidence.

**Estimated:** reasonable inference. Include a range, method, assumptions, evidence, confidence, and sources of error.

**Unknown:** insufficient evidence. State: “Unable to determine from the available evidence.”

### 7. Estimate active time conservatively

Only estimate time when timestamps are dense enough. By default, group consecutive events no more than 30 minutes apart, avoid unsupported time before the first or after the last event, treat meetings separately, avoid overlap, and present a range. This is a heuristic, not a measurement.

### 8. Assign confidence per finding

Use High, Medium, Low, or Unknown. Confidence belongs to each finding, not the report as a whole. See `references/confidence-model.md`.

### 9. Test alternatives

Ask whether another contributor could have produced the artifact, whether timestamps reflect syncing, whether an AI response was ignored, whether a human overwrote AI output, whether work happened offline, and whether sources are dependent.

### 10. Produce the report

Default sections: Scope, Executive summary, Evidence inventory, Timeline, Activity attribution, Measured metrics, Estimated metrics, Contribution narrative, Unknowns and limitations, Confidence assessment, Evidence references.

## Contribution narrative rules

Explain who set goals and constraints, who or what produced initial material, who evaluated, revised, validated, integrated, and approved it, where AI accelerated the work, what supports the claims, and what remains unknown.

## Privacy and fairness

Analyze only authorized evidence, minimize sensitive reproduction, redact secrets, flag surveillance uses, avoid judging worker effort from sparse telemetry, and do not infer protected traits.

## Reference files

- `references/evidence-model.md`
- `references/confidence-model.md`
- `references/estimation-rules.md`
- `references/report-types.md`

# Workprint

**Reconstruct how work gets made.**

Workprint is an evidence-based framework and Claude skill for reconstructing how a project evolved across human and AI activity. It analyzes available artifacts such as AI conversations, commits, documents, designs, calendars, and project records, then produces a transparent account of what happened, what supports each finding, what can be measured, what can only be estimated, and what remains unknown.

Workprint does not use arbitrary “human versus AI” percentages. It attributes observable activities and makes uncertainty explicit.

## Status

`v0.1.0` is the first usable foundation. It includes a Claude Agent Skill, an optional Claude Code slash command, the investigation protocol, evidence and confidence models, report templates, portable JSON schemas, and worked examples.

## Quick start with Claude

### Claude Skills upload

Upload `workprint-claude-skill-v0.1.zip` through Claude's Skill-management interface.

### Claude Code

Copy this repository into your project while preserving the `.claude` directory. Then ask Claude to use Workprint naturally or invoke:

```text
/workprint
```

Example requests:

```text
Use Workprint to inventory the evidence in this repository.
```

```text
/workprint Build a project timeline and attribution report from the supplied files.
```

## Core rule

> Every material finding must be traceable to evidence, reasoning, and an explicit confidence assessment.

## What Workprint is not

Workprint is not an AI-content detector, employee-monitoring tool, productivity score, legal authorship determination, or substitute for contemporaneous time tracking.

## Repository map

```text
.claude/       Claude skill and slash command
docs/          User-facing guidance
spec/          Core methodology
templates/     Reusable report structures
schemas/       Portable structured-data definitions
examples/      Worked examples
```

## Licensing

No open-source license has been granted. All rights are reserved by the repository owner. See [RIGHTS.md](RIGHTS.md).

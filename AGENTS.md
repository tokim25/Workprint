# Agent Instructions

These instructions are permanent guidance for coding agents working on
Workprint.

## Project Purpose

Workprint reconstructs how work was made from evidence such as conversations,
documents, designs, and repository activity. It reports evidenced actions and
decisions without inventing unsupported attribution.

## Core Principles

- Preserve evidence traceability.
- Prefer deterministic behavior before AI inference.
- Prefer unknown over unsupported certainty.
- Distinguish measured, estimated, and unknown claims.
- Never calculate speculative human-versus-AI contribution percentages.
- Do not equate message counts, token counts, commits, or edit volume with ownership, effort, value, or authorship.
- Keep user activity, collaborator activity, AI/tool activity, joint activity, and unattributed activity separate.
- Every attribution must link to supporting evidence.
- Preserve backward compatibility unless a milestone explicitly approves a breaking change.
- Make the smallest coherent change needed.
- Do not modify unrelated files.

## Architecture

Workprint is organized into these layers:

- Evidence adapters read source-specific artifacts and normalize source material.
- Normalized messages preserve conversation records in a source-independent shape.
- Observations convert normalized records into evidenced statements.
- The investigation engine orders observations, summarizes recorded activity, and keeps findings bounded by evidence.
- Timeline generation will build chronological, evidence-linked accounts from observations.
- Reports render investigation data as Markdown or structured JSON.
- The CLI exposes import, validation, investigation, and multi-source workflows.

New adapters must normalize source material rather than introduce
source-specific logic into the investigation engine.

## Development Workflow

- Start from an up-to-date main branch.
- Use one focused feature branch per change.
- Inspect before editing.
- Show a plan before substantial implementation.
- Run the complete test suite before completion.
- Do not commit, push, merge, or delete branches unless explicitly requested.
- Never replace the repository tree with a partial snapshot.
- Check for accidental deletions of core packages before committing.

## Required Validation

Run the complete test suite:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Also perform:

- Import smoke checks for public packages.
- `git diff --check`.
- Review of `git status` and changed-file scope.
- Confirmation that no core packages were accidentally removed.

## Git Conventions

Use Conventional Commits:

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `refactor:`
- `chore:`

## Current Core Packages

Treat these as protected project surfaces:

- `src/workprint/adapters`
- `src/workprint/models`
- `src/workprint/reports`
- `src/workprint/extractor.py`
- `src/workprint/engine.py`
- `src/workprint/multisource.py`
- `src/workprint/cli.py`

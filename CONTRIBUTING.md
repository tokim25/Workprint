# Contributing

Thanks for helping improve Workprint. Keep changes focused, evidence-safe, and
easy to review.

## Project Setup

Workprint requires Python 3.10 or newer.

Create a virtual environment and install the package in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Editable installation is supported by `pyproject.toml`, which uses setuptools
and discovers packages under `src`.

No external runtime dependencies are currently required.

## Running Tests

After editable installation:

```bash
python -m unittest discover -s tests -v
```

Without installing:

```bash
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Run the full suite before handing off work. Also run `git diff --check` and an
import smoke check for public packages when changing source code.

## Branch Naming

Use one focused branch per change. Examples:

- `feat/timeline-report`
- `docs/project-operating-system`
- `fix/adapter-validation`
- `test/multisource-edge-cases`

## Commit Messages

Use Conventional Commits:

- `feat:` for new capabilities
- `fix:` for bug fixes
- `docs:` for documentation-only changes
- `test:` for tests
- `refactor:` for behavior-preserving code structure changes
- `chore:` for maintenance

## Documentation Expectations

Update documentation when behavior, workflows, commands, architecture, or
project plans change. Reconcile existing docs instead of creating conflicting
copies.

## Adapter Design Requirements

Adapters must:

- Implement the `EvidenceAdapter` contract.
- Validate input paths and raise user-facing `ValueError`s.
- Read source-specific artifacts.
- Return normalized Workprint records.
- Keep project-level findings out of adapter code.
- Register through `workprint.adapters.registry`.
- Avoid adding source-specific logic to the investigation engine.

## Evidence and Attribution Safety

Workprint must preserve traceability and avoid unsupported attribution.

- Prefer unknown over unsupported certainty.
- Distinguish measured, estimated, and unknown claims.
- Do not calculate speculative human-versus-AI contribution percentages.
- Do not equate message counts, token counts, commits, or edit volume with ownership, effort, value, or authorship.
- Keep user, collaborator, AI/tool, joint, and unattributed activity separate.
- Link attribution claims to supporting evidence.

## Pull Request Checklist

Before opening a pull request:

- Confirm the branch is focused on one capability or fix.
- Run `PYTHONPATH=src python3 -B -m unittest discover -s tests -v`.
- Run `git diff --check`.
- Run import smoke checks for public packages when source code changed.
- Review `git status` and changed-file scope.
- Confirm no core packages were accidentally removed.
- Update README, roadmap, changelog, architecture docs, or decision logs when relevant.
- Document limitations and unknowns for evidence or attribution changes.

## Guardrails

Do not include unrelated changes. Do not use destructive partial-tree
replacements. Never replace the repository with a snapshot that omits core
packages such as `src/workprint/adapters`, `src/workprint/models`,
`src/workprint/reports`, `src/workprint/extractor.py`,
`src/workprint/engine.py`, `src/workprint/multisource.py`, or
`src/workprint/cli.py`.

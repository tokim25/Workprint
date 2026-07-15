# Guided Investigation

Guided Investigation helps a user generate reports without memorizing the
expert CLI commands.

## Command

```bash
workprint guide
```

## Workflow

1. Confirm the project folder.
2. Review discovered evidence.
3. Select evidence files to include.
4. Enter a project name.
5. Confirm Markdown and JSON output paths.
6. Confirm generation.
7. Receive plain-language success or cancellation messages.

## Discovery Reuse

The guided workflow uses Project Discovery to find supported evidence. It does
not duplicate filesystem scanning or source recognition logic.

Git repository detection is informational only. Workprint shows when a Git
repository is present, but Git cannot be selected for investigation until a Git
evidence adapter exists.

## Selection Syntax

By default, pressing Enter includes every discovered importable file.

You can select specific files or sources:

```text
1,3
chatgpt,google-docs
```

You can remove files or sources from the default selection:

```text
-2
-claude
```

Malformed or irrelevant files that are not recognized by an adapter are not
selected. If a selected file later fails to import, Workprint reports the
problem in plain language and does not print a traceback.

## Outputs

The default output directory is:

```text
workprint-output/
```

Default report files are:

```text
workprint-output/report.md
workprint-output/report.json
```

The directory is created only after final confirmation. Existing files are never
overwritten silently. If one output exists, Workprint asks before replacing it.
If both outputs exist, Workprint lets the user overwrite both, choose new paths,
or cancel.

## Relationship to Expert Commands

Guided Investigation preserves the existing expert CLI. Internally, selected
files are translated into the same source/path inputs used by
`workprint investigate-multi`, then Workprint uses the existing observation
loading, investigation, Markdown report, and JSON report behavior.

## Limitations

- The MVP is terminal-based.
- Git evidence import is not available yet.
- Guided Investigation does not infer attribution, authorship, ownership,
  effort, value, or contribution percentages.
- Guided Investigation does not change the report model or JSON output
  structure.

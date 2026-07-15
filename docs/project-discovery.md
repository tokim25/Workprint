# Project Discovery

Project Discovery previews supported evidence in a directory before import or
investigation.

## Command

```bash
workprint discover
```

By default, Workprint scans the current working directory. You can also provide
a path:

```bash
workprint discover path/to/project
```

## What Discovery Does

- Scans recursively.
- Detects supported evidence files.
- Detects whether the target directory is a Git repository.
- Summarizes available evidence sources.
- Reports whether the project is ready for investigation.

Discovery is informational only. It does not import evidence, create
observations, build findings, generate a timeline, or modify files.

## Supported Evidence

- Git repository
- ChatGPT exports
- Claude exports
- Google Docs static exports
- Figma static exports

## Limitations

- Discovery recognizes supported files; it does not validate every future
  investigation outcome.
- Discovery does not infer attribution, authorship, ownership, effort, value, or
  contribution percentages.
- Discovery counts supported files and adapter-recognized records only.
- Git detection only identifies repository presence; Git evidence import is not
  implemented in this milestone.
- Unsupported files are ignored.

## Relationship to Investigations

Use discovery as a preview before choosing evidence for `workprint import`,
`workprint investigate`, or `workprint investigate-multi`. Discovery helps a
future guided experience explain what evidence is available before asking the
user to generate reports.

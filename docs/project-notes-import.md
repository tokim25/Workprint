# Project Notes Import

Workprint supports ordinary project documentation through the `project-notes`
adapter.

## Supported formats

- `.md`
- `.mdx`
- `.txt`
- `.rst`
- `.adoc`

Project notes are split into non-empty paragraph blocks and normalized as
document evidence. Markdown headings are used as the document title when
available.

## Why this adapter exists

The `google-docs` adapter intentionally requires a marker before ordinary
Markdown or text files are discovered as Google Docs exports. That protects
Workprint from mislabeling normal repository files as Google Docs evidence.

Project notes have a different purpose: they let Workprint read user-supplied
project documentation as project documentation. They do not require a
`workprint-source` marker because ordinary project notes are expected evidence
for the no-code web and desktop experience.

## Discovery behavior

Project Discovery automatically recognizes supported files unless their exact
stem is common boilerplate:

- `authors`
- `changelog`
- `code_of_conduct`
- `codeowners`
- `contributing`
- `license`
- `licence`
- `notice`
- `readme`
- `security`

This exclusion applies only to automatic discovery. Direct expert import of a
boilerplate-named file still works when the user explicitly selects
`project-notes`.

Generated, dependency, cache, build, vendor, Git, and Python virtual
environment folders are skipped during discovery so Workprint does not treat
vendored documentation as project evidence.

## Normalization

Each non-empty block becomes one normalized record:

- source: `project-notes`
- source type: `document`
- role: `unknown`
- document ID stored as the normalized conversation ID for compatibility
- source locator: `filename#paragraph/N`

Example evidence reference:

```text
project-brief.md#paragraph/2
```

## Limitations

Project notes are static files. They do not recover:

- revision history;
- edit-by-edit authorship;
- comment or suggestion history;
- timestamps for individual paragraphs;
- deleted text;
- whether text was human-authored, AI-assisted, pasted, or generated
  elsewhere.

Workprint may report what the files say. It must not infer authorship,
ownership, effort, intent, importance, correctness, originality, completeness,
or human-versus-AI contribution from project notes alone.

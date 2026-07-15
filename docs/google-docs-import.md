# Google Docs Import

Workprint supports static Google Docs exports through the `google-docs`
adapter.

## Supported formats

- `.json`: conservative structured export with document metadata and paragraph
  blocks.
- `.txt`: plain text export split into non-empty paragraph blocks.
- `.md`: Markdown export split into non-empty blocks, with the first heading
  used as the document title when present.

Direct expert import supports all three formats:

```bash
workprint import google-docs document.md --output observations.json
```

Project Discovery is stricter for `.txt` and `.md` so ordinary repository files
are not auto-selected as Google Docs evidence. To make a text or Markdown export
discoverable, include this exact marker near the top of the file:

```text
workprint-source: google-docs
```

The marker is used only for discovery. Direct `google-docs` import still reads
`.txt` and `.md` files without requiring the marker.

## JSON schema

The adapter accepts a JSON object with:

- `id` or `document_id`: stable document identifier.
- `title`: document title.
- `created_at`: optional document-level timestamp.
- `modified_at`: optional document-level timestamp retained as metadata.
- `owners`, `authors`, `editors`: optional document-level metadata.
- `metadata`: optional object that may also contain owners, authors, editors,
  created_at, or modified_at.
- `paragraphs`: list of strings or objects with `id`, `text` or `content`, and
  optional block `metadata`.
- `body`: optional plain text body used only when `paragraphs` is absent.

## Normalization

Each non-empty paragraph or block becomes one normalized record:

- source: `google-docs`
- source type: `document`
- role: `unknown`
- document ID stored as the normalized conversation ID for compatibility
- source locator: `filename#paragraph/N`

Example evidence reference:

```text
sample-document.json#paragraph/3
```

## Static export limitations

Static exports are document snapshots. They do not recover:

- revision history;
- edit-by-edit authorship;
- comment or suggestion history unless explicitly included in structured input;
- timestamps for individual paragraphs;
- deleted text;
- sharing or permission history;
- whether text was human-authored, AI-assisted, pasted, or generated elsewhere.

Document owners, authors, and editors remain document-level metadata. Workprint
does not attribute individual paragraphs to them unless the supplied evidence
explicitly maps that person to the block.

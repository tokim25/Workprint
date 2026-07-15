# Figma Import

Workprint supports static Figma JSON exports through the `figma` adapter.

## Supported Format

- `.json`: conservative structured export supplied by the user.

The MVP does not use live Figma API access and does not parse `.fig` files,
screenshots, PDFs, or arbitrary visual exports.

## JSON Schema

The adapter accepts a JSON object with:

- `file_key`, `file_id`, `key`, or `id`: stable file identifier.
- `name`: file name.
- `last_modified`: optional file-level timestamp preserved as metadata.
- `owner`, `editors`, `contributors`: optional file-level metadata.
- `schema_version`: optional export schema marker.
- `pages`: list of page objects.

Each page may include:

- `id`
- `name`
- `type`
- `description`
- `last_modified`
- `metadata`
- `nodes` or `children`

Each node may include:

- `id`
- `name`
- `type`
- `description`
- `characters` or `text`
- `component_key`, `component_name`, `component_id`, `main_component`,
  `instance_of`, or `variant`
- `visible`
- `locked`
- `last_modified`
- `metadata`
- `evidence`
- `children` or `nodes`

## Meaningful-Node Filtering

Workprint emits normalized records only for meaningful pages or nodes. A page or
node is meaningful when it has at least one of:

- visible text;
- description;
- meaningful component or instance metadata;
- explicit evidence metadata.

Empty structural containers are traversed for meaningful descendants but do not
produce records themselves.

## Normalization

Each meaningful page or node becomes one normalized record:

- source: `figma`
- source type: `design`
- role: `unknown`
- file key/ID stored as the normalized conversation ID for compatibility
- source locator includes page and node identity
- file, page, node, parent, and path metadata preserved

Example evidence references:

```text
sample-file.json#page/page-discovery
sample-file.json#page/page-discovery/node/text-headline
sample-file.json#page/page-components/node/component-report-card
```

## Timestamp Handling

Workprint uses timestamps only when they are explicitly supplied in the JSON.
File-level `last_modified`, page-level `last_modified`, and node-level
`last_modified` are preserved separately in metadata. File-level timestamps are
not assigned to individual nodes.

When explicit page-level or node-level `last_modified` values are used as a
normalized record's `created_at`, that field is a compatibility timestamp for
ordering and represents the last observed modification supplied by the export.
It is not treated as the creation time of the page, node, or design work.

## Static Export Limitations

Static Figma exports do not recover:

- version history;
- who created or edited each node;
- edit timestamps per node unless explicitly supplied;
- comments or comment resolution history;
- branch or merge activity;
- prototype interaction history;
- design review sequence;
- contributor activity;
- authorship or ownership of frames, components, or text;
- whether a design element was human-created, AI-generated, copied, or imported.

Contributor, owner, and editor fields remain metadata unless the supplied
evidence explicitly links a person to a specific node or action.

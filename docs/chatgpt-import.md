# ChatGPT Import

Workprint reads common ChatGPT `conversations.json` exports.

## Supported structures

- A list of conversation objects with `mapping`.
- A single conversation object with `mapping`.
- A conversation object with a flat `messages` list.

## Content support

- Plain string content.
- `content.parts` lists.
- String and simple dictionary parts.

## Traceability

Each normalized message stores a locator such as:

```text
conversations.json#mapping/<node-id>
```

Each observation carries that locator into the final report.

## Branching conversations

This release processes all message nodes present in the mapping. A later release may add explicit branch selection and lineage reconstruction.

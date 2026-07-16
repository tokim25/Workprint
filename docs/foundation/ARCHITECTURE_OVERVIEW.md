# Architecture Overview

Status: Foundation reference
Purpose: Explains Workprint's evidence pipeline and layer boundaries
Expected Update Frequency: Update when architecture changes

Workprint's architecture is a layered evidence pipeline. Each layer has a
specific responsibility and a specific boundary. The system is designed so
source-specific parsing stays near the source, investigation stays
source-independent, and reports present rather than alter evidence.

```text
Evidence Sources
  ↓
Discovery
  ↓
Adapters
  ↓
Normalized Evidence
  ↓
Observations
  ↓
Timeline
  ↓
Investigation
  ↓
Executive Report
  ↓
Markdown / JSON
```

## Evidence Sources

Responsibility: Evidence sources are the raw materials supplied by the user or
found in a project folder. Current sources include ChatGPT exports, Claude
exports, static Google Docs exports, static Figma JSON exports, and Git
repository presence detected during discovery.

Inputs: Files, folders, exports, metadata, and other source artifacts.

Outputs: Source material made available for discovery or adapter validation.

Boundaries: Raw evidence is not yet an observation, finding, or conclusion.

What it must not do: Evidence sources must not be treated as complete project
history unless completeness is itself evidenced.

## Discovery

Responsibility: Discovery scans a project directory, detects supported
evidence files, detects Git repository presence, and summarizes readiness for
investigation.

Inputs: A project path and the registered adapter recognition rules.

Outputs: A preview of supported sources, recognized files, record counts when
available, Git presence, and readiness information.

Boundaries: Discovery is informational. It does not import evidence, create
observations, build findings, generate timelines, write reports, or modify
files.

What it must not do: Discovery must not infer attribution, authorship,
ownership, effort, value, or contribution percentages.

## Adapters

Responsibility: Adapters own source-specific validation and parsing. Each
adapter declares a stable source identifier, reads supported artifacts, and
returns Workprint-normalized records with evidence references.

Inputs: A specific supported source artifact, such as a ChatGPT export, Claude
export, Google Docs static export, or Figma JSON export.

Outputs: Normalized evidence records.

Boundaries: Adapters preserve source facts and metadata. They do not decide
project meaning.

What it must not do: Adapters must not create project-level findings,
decision assessments, authorship claims, or contribution claims.

## Normalized Evidence

Responsibility: Normalized evidence gives Workprint a source-independent
record shape. It preserves source, role or record type, text or content,
timestamps when supported, metadata, and stable evidence locators.

Inputs: Adapter outputs.

Outputs: Records that downstream extraction can process without knowing raw
source formats.

Boundaries: Normalized evidence is still evidence material, not interpretation.

What it must not do: Normalization must not erase source boundaries or convert
metadata into unsupported attribution.

## Observations

Responsibility: Observations convert normalized records into evidence-linked
statements. An observation records what Workprint can say about a captured
piece of activity and where that statement came from.

Inputs: Normalized evidence records.

Outputs: Observation objects with statements, activity labels, actor
information when supported, timestamps when available, and evidence
references.

Boundaries: Observations describe captured evidence events. They do not
measure total effort, value, ownership, or authorship.

What it must not do: Observations must not fill gaps in the record with
unsupported certainty.

## Timeline

Responsibility: Timeline generation orders and groups observations into
chronological events. It classifies project stages and separates user,
collaborator, AI/tool, joint, and unattributed activity where evidence
supports those distinctions.

Inputs: Observations.

Outputs: Timeline events with titles, descriptions, stage labels, source
observations, evidence references, confidence, unknowns, and involvement
classifications.

Boundaries: Timeline generation is deterministic. Related observations are
grouped only when defined rules support grouping.

What it must not do: Timeline generation must not treat captured involvement
counts as ownership, authorship, value, effort, or contribution percentages.

## Investigation

Responsibility: The investigation engine orders observations, summarizes
recorded activity, creates bounded findings, builds timeline events, and lists
unknowns and limitations.

Inputs: Sorted observations, project metadata, and timeline generation output.

Outputs: A structured investigation containing findings, timeline events,
unknowns, limitations, and evidence references.

Boundaries: Investigation operates on normalized observations. It should not
contain source-specific parsing logic.

What it must not do: Investigation must not overrule adapter boundaries,
invent missing source history, or claim unsupported decision leadership.

## Executive Report

Responsibility: The Executive Report is a reader-facing synthesis derived from
the completed investigation. It explains the project goal, outputs, evolution,
collaboration pattern, decisions, confidence, evidence gaps, and assurance.

Inputs: The completed Investigation model.

Outputs: Executive sections rendered before the detailed report and included
as structured JSON.

Boundaries: The Executive Report is derived, additive, and deterministic in
the current implementation.

What it must not do: It must not change evidence extraction, observations,
timeline generation, the core investigation model, or attribution boundaries.

## Markdown / JSON

Responsibility: Markdown and JSON renderers make the investigation usable for
people and tools. Markdown emphasizes readability and shareability. JSON
preserves structured data for downstream use.

Inputs: Investigation and Executive Report data.

Outputs: Markdown reports and structured JSON reports.

Boundaries: Renderers present data. They do not create new facts.

What it must not do: Renderers must not alter evidence, hide uncertainty,
remove material limitations, or make unsupported claims more confident.

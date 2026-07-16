# Workprint Glossary

Status: Foundation reference
Purpose: Defines canonical Workprint terminology
Expected Update Frequency: Update when terminology changes

## Evidence

Source material available to Workprint, such as exported conversations,
documents, design data, repository context, metadata, or other captured
records.

## Evidence Source

A specific origin or category of evidence, such as ChatGPT, Claude, Google
Docs, Figma, Git, or a future supported system.

## Git Evidence

Local repository metadata captured from Git, including repository context,
commit metadata, changed paths, tags, and shallow-history status. Git evidence
does not include file contents in v1.

## Git Author Or Committer

Name and email values recorded by Git on a commit. Workprint preserves these
values as metadata, but they do not prove who personally wrote every changed
line and are not resolved into canonical identities.

## Shallow Git History

A Git repository state where earlier history may be missing. Workprint
discloses this as a limitation because incomplete history can affect
chronology, tags, branch context, and evidence coverage.

## Observation

An evidence-linked statement derived from normalized evidence. An observation
describes captured activity without claiming total authorship, ownership,
effort, or value.

## Finding

A bounded investigation conclusion supported by one or more observations and
their evidence references.

## Timeline Event

A deterministic grouping of related observations into a chronological account
of project activity, including stage, description, evidence references,
confidence, and involvement boundaries.

## Milestone

A coherent product or engineering capability with a stated goal, implemented
scope, acceptance criteria, tests, and documented limitations.

## Investigation

The structured result produced after Workprint orders observations, summarizes
captured activity, builds findings and timeline events, and records unknowns
and limitations.

## Executive Report

A reader-facing synthesis derived from the completed investigation. It
explains the project, outputs, evolution, collaboration pattern, decisions,
confidence, evidence gaps, and assurance.

## Evidence Gap

An important question that Workprint cannot answer from the available evidence,
or a missing source condition that limits confidence.

## Decision Leadership

An evidence-bounded assessment of who or what appears to have led a specific
decision in the captured record. It is decision-specific and must not become a
global authorship or ownership claim.

## Confidence Band

A qualitative confidence label, such as Very High, High, Moderate, Limited, or
Low, explained through evidence strength, coverage, corroboration, conflicts,
and gaps.

## Coverage

The extent to which available evidence spans the project activities, time
periods, sources, and questions needed for the investigation.

## Corroboration

Independent evidence support for the same normalized finding, milestone,
output, or decision.

## Unknown

A valid result used when evidence does not support a conclusion. Unknown means
Workprint is preserving the boundary of the record.

## Limitation

A known constraint on what Workprint can determine, often caused by source
format limits, missing evidence, static exports, narrow coverage, or
unsupported adapters.

## Adapter

A source-specific component that validates and parses evidence artifacts,
preserves useful metadata, and returns normalized records with stable evidence
references.

## Normalized Evidence

Source-independent records produced by adapters so downstream extraction,
timeline generation, investigation, and reports can operate without raw
source-specific parsing logic.

## Executive Finding

A high-level, reader-facing conclusion in the Executive Report derived from
the completed investigation and bounded by the same evidence references,
unknowns, and limitations.

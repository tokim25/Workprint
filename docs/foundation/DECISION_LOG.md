# Decision Log

Status: Living document
Purpose: Records accepted enduring product and architectural decisions
Expected Update Frequency: Update when major product decisions change

This log records accepted architectural and product decisions that future
contributors should preserve unless the project deliberately revisits them.
Each entry uses the same structure: Context, Alternatives, Decision,
Consequences, and Status.

## Timeline Is Deterministic

Context: Workprint needs to reconstruct project evolution from normalized
observations while keeping the result explainable and testable.

Alternatives: Timeline generation could use an LLM or probabilistic clustering
to group observations into richer narrative events. It could also avoid
timeline generation entirely and leave readers with raw observations.

Decision: Timeline generation is deterministic. Observations are ordered by
timestamp, source, and ID. Related observations are grouped only when they
share conversation context, stage, and a close timestamp window. User
involvement is marked measured only when captured evidence directly supports
it.

Consequences: Timeline output is predictable, testable, and explainable. The
timeline may be less semantically rich than an AI-generated reconstruction,
but it does not hide grouping logic or attribution inference.

Status: Accepted.

## Executive Report Is Derived From Investigation

Context: Workprint needs a reader-facing executive report that answers human
questions before detailed evidence tables, while preserving the existing
investigation model.

Alternatives: The Executive Report could be a separate investigation path, a
hand-authored narrative, or an LLM-generated summary over raw evidence.

Decision: The Executive Report is derived from the completed Investigation. It
is additive and does not change evidence extraction, observations, timeline
generation, or the core investigation model.

Consequences: Readers get a clearer report without weakening the evidence
pipeline. Executive copy is bounded by existing investigation data. The report
may be more conservative than a free-form narrative, but it remains traceable.

Status: Accepted.

## Confidence Uses Qualitative Bands

Context: Workprint needs to communicate how reliable a reconstruction is
without implying false numerical precision.

Alternatives: Confidence could be omitted, calculated as a numeric score, or
left to unsupported prose.

Decision: Confidence uses qualitative bands such as Very High, High, Moderate,
Limited, and Low. Each assessment should explain evidence strength, coverage,
corroboration, conflicts, and gaps.

Consequences: Confidence remains understandable and auditable. The system
avoids hidden scoring formulas and false precision, but contributors must keep
the rationale clear.

Status: Accepted.

## Contribution Percentages Are Intentionally Out Of Scope

Context: Human-AI collaboration reports create pressure to quantify how much
work was done by humans, AI tools, collaborators, or other actors.

Alternatives: Workprint could estimate contribution percentages from message
counts, tokens, commits, edit volume, or activity counts. It could also avoid
collaboration analysis entirely.

Decision: Workprint does not calculate human-versus-AI contribution
percentages. It does not convert counts into ownership, effort, value, or
authorship claims. It may report captured evidence events and involvement
classifications with clear caveats.

Consequences: Reports avoid false precision and unsupported attribution. Some
readers may want a simple score, but Workprint deliberately favors trust over
convenience.

Status: Accepted.

## Guided Workflow Orchestrates Existing Capabilities

Context: Workprint needs to become usable by people who do not know expert CLI
commands, while preserving established evidence behavior.

Alternatives: The guided workflow could implement its own discovery, import,
investigation, report, or attribution logic. It could also remain purely an
expert CLI product.

Decision: Guided Investigation orchestrates existing capabilities. It reuses
Project Discovery, translates selections into evidence inputs, and calls the
same multi-source investigation and report generation pipeline used by expert
commands.

Consequences: The workflow improves usability without forking evidence logic.
Bug fixes and evidence rules remain centralized. The current guided experience
is still terminal-based, so it is a step toward low-code/no-code rather than
the final form.

Status: Accepted.

## Static Exports Preserve Evidence Boundaries

Context: Google Docs and Figma static exports can be useful evidence, but they
do not contain full revision or authorship history.

Alternatives: Workprint could infer paragraph authorship, node authorship,
edit history, or contributor activity from file-level metadata. It could also
refuse static exports entirely.

Decision: Static exports are accepted as bounded evidence. Workprint preserves
document-level or file-level metadata, stable locators, and explicit content,
but it does not infer revision history, edit-by-edit authorship, contributor
activity, or node/paragraph authorship unless the evidence explicitly maps
those facts.

Consequences: Static exports become useful without being overstated. Reports
must clearly disclose their limits. Future richer adapters can add revision or
comment evidence when actual source data supports it.

Status: Accepted.

## Executive Copy-Quality Audit Uses A Pinned Upstream Scanner

Context: Executive Report v1 included copy-quality audit metadata with the
`unslop-text` upstream revision pinned, but the scanner was not yet integrated.
Completing the audit gate required using the upstream work without describing
the scanner, research, rules, or methodology as Workprint's original work.

Alternatives: Workprint could keep the audit unavailable, reimplement similar
rules without attribution, fetch upstream files at report-generation time, or
vendor a reviewed subset of the upstream project.

Decision: Workprint vendors the reviewed `unslop-text` scanner and references
from JCarterJohnson's `vibecoded-design-tells` project at pinned revision
`f7c4aefc2c797a66e55b49354a93917ab60d33ac`, preserves attribution and
licensing information through the MIT license and third-party notice, and wraps
the scanner in Workprint-owned integration code. Workprint adds deterministic
structural checks because lexical findings alone cannot assess overall writing
quality, plus evidence-preservation validation, Markdown disclosure, and
additive JSON metadata. The audit is documented as a writing-pattern review,
not an authorship detector.

Consequences: Report generation can run the lexical scanner offline and record
clear upstream attribution. Workprint owns the integration boundary and status
rules while preserving the upstream license and credit. Future audit changes
must continue to distinguish JCarterJohnson's upstream work from Workprint's
additions and must not imply endorsement.

Status: Accepted.

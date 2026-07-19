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

## Git Evidence Uses Local Read-Only Metadata

Context: Workprint needs repository activity evidence to support chronology,
implementation milestones, and evidence gaps without overstating what Git can
prove. Git records contain useful metadata, but they also include names,
email addresses, commit messages, file paths, and line-change counts that can
be misread as identity, authorship, effort, ownership, value, or productivity
signals.

Alternatives: Workprint could omit Git evidence, call the GitHub API, parse
`.git` internals directly, inspect file contents, or infer people and effort
from author fields and line counts.

Decision: Workprint uses a local-only Git adapter that invokes the installed
`git` command through a small read-only command boundary. The adapter records
repository and commit metadata, preserves Git-recorded author and committer
values exactly, and maps data into conservative observations. It does not use
network access, inspect file contents, mutate repositories, resolve identities,
or convert commit counts, file counts, additions, or deletions into
authorship, ownership, effort, value, productivity, or contribution measures.

Consequences: Git evidence can support implementation chronology, merge
milestones, completed-output evidence, and reduced Git-history gaps while
remaining traceable and deterministic. Bare repositories, remote-only history,
unrelated nested repositories, and file-content analysis are out of scope for
v1. Reports must disclose shallow history and preserve the distinction between
Git metadata and unsupported attribution.

Status: Accepted.

## Claude Desktop Chat's Optional Dependency Is Pinned, Not Name-Matched

Context: The Claude Desktop Chat adapter's deep-parse mode needed a library
that parses Chromium's undocumented IndexedDB-over-LevelDB format. A PyPI
package name ("chromium-reader") was assumed to be the pip-installable form
of a GitHub project actually researched (`cclgroupltd/ccl_chromium_reader`),
and declared as the optional dependency in `pyproject.toml` without
installing and running it. When a working Python 3.10+ environment later
became available, the assumption proved wrong: "chromium-reader" is an
unrelated package by a different author, with a confirmed bug in its own
global-metadata string decoding that silently drops every real IndexedDB
database record on real data. The correct library is not published on PyPI
under any name; it is only installable from its GitHub source.

Alternatives: Workprint could keep depending on the wrong PyPI package and
patch around its bug, pick a different, differently shaped library, or
declare the dependency directly against a pinned commit of the
verified-correct source.

Decision: The `claude-desktop-chat` optional dependency points at a pinned
commit of `cclgroupltd/ccl_chromium_reader` via a direct `git+https://`
reference, matching the precedent already set for the `unslop-text` upstream
integration (see "Executive Copy-Quality Audit Uses A Pinned Upstream
Scanner" above). Before any dependency is declared for a milestone going
forward, it must be installed and imported at least once, and its PyPI
project metadata, when applicable, cross-checked against the source actually
researched (see "External Dependencies Are Verified, Not Assumed" in
`ENGINEERING_PRINCIPLES.md`).

Consequences: The dependency now resolves to code that actually implements
the documented API. Pinning to a commit trades automatic upstream fixes for
reproducibility, matching how Workprint already treats other vendored or
pinned external code. This decision does not resolve whether deep parsing
can reliably recover real conversation content on a given machine; see the
Claude Desktop Chat adapter's own documentation for that separate, still-open
finding.

Status: Accepted.

## AI Fluency Reporting Uses Anthropic's Named Framework, With Attribution

Context: Workprint added a report section organizing existing evidence under
Anthropic's AI Fluency Framework (Delegation, Description, Discernment,
Diligence, developed with Prof. Rick Dakan and Prof. Joseph Feller). The
framework and its terminology are released under CC BY-NC-SA 4.0:
non-commercial use only, with required attribution to the authors, and any
derivative use of the framework's own materials must share alike.

Alternatives: Workprint could build its own, differently named categories
inspired by the same four-competency idea and avoid citing the framework at
all, or pause the feature until the framework's authors were contacted for
explicit permission.

Decision: Workprint uses the framework's official terminology directly, with
a visible attribution line (naming Dakan and Feller, and the CC BY-NC-SA
license) everywhere the section appears in a report. This is conditioned on
Workprint remaining non-commercial; if that changes, this decision must be
revisited before the feature ships in a commercial build. Workprint does not
reproduce the framework's own infographics or long-form materials, only its
short competency definitions restated in Workprint's own words, and it never
scores or rates fluency -- consistent with "Decision Leadership Over
Contribution Scoring" in `PRODUCT_PRINCIPLES.md`, this section only
reorganizes evidence Workprint already gathered for the user's own
reflection.

Consequences: Reports can use recognizable, well-documented terminology
instead of inventing parallel language, at the cost of a standing obligation
to keep attribution visible and to revisit licensing if Workprint's
commercial status ever changes.

Status: Accepted.

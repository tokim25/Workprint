# Copy-Quality Audit Integration

Workprint's Executive Report copy-quality review incorporates the
`unslop-text` scanner and research developed by JCarterJohnson in the
`vibecoded-design-tells` project.

Workprint pins and records the reviewed upstream revision, preserves
attribution and licensing information, and adds its own integration,
evidence-preservation checks, deterministic structural review, report metadata,
and Markdown disclosure. The audit identifies documented writing patterns; it
does not determine whether text was written by a human or an AI.

No endorsement by JCarterJohnson is implied.

## Acknowledgements

Workprint gratefully acknowledges JCarterJohnson's work on
`vibecoded-design-tells`.

The `unslop-text` scanner and its supporting research provide the foundation
for Workprint's lexical copy-quality audit.

Workprint builds on that work by integrating the scanner into an
evidence-backed reporting workflow with deterministic structural review,
evidence-preservation validation, audit metadata, and report disclosures.

This keeps attribution visible without implying endorsement.

## Upstream Source

- Upstream project: `vibecoded-design-tells`
- Upstream author/maintainer: JCarterJohnson
- Upstream scanner: `unslop-text`
- Repository: https://github.com/JCarterJohnson/vibecoded-design-tells
- Pinned revision: `f7c4aefc2c797a66e55b49354a93917ab60d33ac`
- License: MIT
- Notice: `third_party/vibecoded-design-tells/NOTICE.md`

## Vendored Files

Workprint vendors only the reviewed upstream files needed for the audit:

- `third_party/vibecoded-design-tells/LICENSE`
- `third_party/vibecoded-design-tells/unslop-ai-text/skill/SKILL.md`
- `third_party/vibecoded-design-tells/unslop-ai-text/skill/scripts/unslop_text_scan.py`
- `third_party/vibecoded-design-tells/unslop-ai-text/skill/references/tells.md`
- `third_party/vibecoded-design-tells/unslop-ai-text/skill/references/writing-with-intent.md`

The vendored upstream files are unmodified. Workprint compatibility behavior
lives in `src/workprint/copy_audit.py`.

## Runtime Behavior

Report generation does not use the network. Workprint incorporates the vendored
scanner through a Workprint-owned integration wrapper, invoking it with the
current Python interpreter against a temporary UTF-8 Markdown file containing
only generated Executive Report narrative sections.

The scanner returns JSON output and exits with the number of high-severity
findings. Workprint captures the JSON output without exposing temporary file
paths in final reports.

## Narrative Scope

The audit scans:

- Executive Brief.
- Project Overview narrative.
- Key Milestone summaries.
- Human-AI Collaboration narrative.
- Decision Analysis prose.
- Confidence Assessment rationale.
- Evidence Gaps prose.
- Investigation Assurance.

The audit excludes raw evidence quotations, evidence IDs, appendix tables,
source appendix content, code, command examples, and JSON keys.

## Structural Review

The upstream documentation states that a clean lexical scan is not a complete
verdict. Structural checks complement the lexical review because lexical
findings alone cannot assess overall writing quality. Workprint adds
deterministic structural checks for:

- generic assistant boilerplate;
- sycophantic or congratulatory openings;
- repeated "not just X, but Y" constructions;
- unnecessary conclusion or recap headings;
- excessive list scaffolding in narrative sections;
- repeated sentence openings;
- unusually uniform sentence lengths;
- conspicuous fragments or manufactured casualness;
- unsupported persuasive or promotional language;
- repeated vague claims that add no evidence-backed information.

Structural checks report findings. They do not rewrite copy.

## Status Rules

`passed` means the lexical scanner ran, structural checks ran, no unresolved
findings require waivers, and evidence-preservation validation passed.

`passed_with_waivers` means lexical and structural checks ran, no high-severity
findings remain, and every retained medium or low finding has a documented
waiver.

`failed` means a high-severity finding remains, structural review could not
complete after starting, evidence-preservation validation failed, audit output
was malformed, or medium/low findings lacked required waivers.

`unavailable` means required scanner files are missing, the scanner cannot
execute in the environment, or the pinned scanner cannot be verified in the
installed source. `unavailable` is never reported as passed.

## Authorship Limits

The copy-quality audit is not an AI detector. It does not establish human
authorship, prove that AI was not involved, certify originality, or replace
the evidence model. It identifies documented writing patterns in generated
narrative sections and records whether Workprint's deterministic review
completed.

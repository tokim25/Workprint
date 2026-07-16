# Executive Report

Executive Report v1 adds a reader-facing summary above the existing detailed
Workprint report. It is derived from the completed investigation; it does not
change evidence extraction, observations, timeline generation, or the core
investigation model.

## Sections

Executive Report v1 renders these sections before the detailed report:

1. Executive Brief
2. Project Overview
3. Key Milestones
4. Human-AI Collaboration
5. Decision Analysis
6. Confidence Assessment
7. Evidence Gaps
8. Investigation Assurance

The detailed report remains below these sections, including timeline details,
findings, unknowns, limitations, and the evidence appendix.

## Confidence Bands

Workprint uses qualitative confidence bands:

- Very High
- High
- Moderate
- Limited
- Low

The band is assigned by explicit rules based on evidence conditions. Workprint
does not calculate hidden numeric scores or contribution percentages.

Each confidence assessment includes:

- evidence strength;
- coverage;
- corroboration;
- conflicts;
- gaps;
- a plain-language rationale.

## Evidence Strength Versus Confidence

Evidence strength describes how direct and traceable the supporting evidence is.
Confidence is the overall assessment after also considering coverage,
corroboration, conflicts, and gaps.

For example, an explicit decision statement is strong evidence for that
decision. The overall confidence may still be Moderate rather than High if the
project coverage is narrow or important source history is missing.

## Corroboration

Corroboration requires two or more independent evidence references supporting
the same normalized finding, milestone, output, or decision.

Multiple evidence sources that support unrelated claims increase coverage, not
corroboration. Repeated or copied statements are not treated as independent
corroboration when dependency is detectable.

## Git Evidence In Executive Reports

When local Git evidence is supplied, the Executive Report may use it to support
implementation chronology, repository milestones, merge milestones, completed
output evidence, and reduced Git-history gaps.

Git evidence does not automatically raise confidence. Confidence improves only
when the deterministic report rules find direct support, such as Git evidence
supporting the same executive claim as another independent evidence reference.

If Git reports shallow history, the Executive Report records that limitation.
Commit counts, file counts, additions, and deletions are not treated as
authorship, ownership, effort, value, productivity, or contribution measures.

## Tools And Evidence Sources

Executive Report v1 keeps these concepts separate:

- evidence sources analyzed by Workprint;
- project tools explicitly observed in the evidence;
- unconfirmed or unavailable tool information.

An adapter or source file proves only that Workprint analyzed that evidence
source. Workprint reports project tools only when the evidence explicitly shows
tool use as part of project activity.

## Copy-Quality Audit

Executive Report copy-quality review incorporates the `unslop-text` scanner
and research developed by JCarterJohnson in the `vibecoded-design-tells`
project. Workprint pins and records the reviewed upstream revision, preserves
attribution and licensing information, and adds its own integration,
evidence-preservation checks, and deterministic structural review.

Pinned upstream source:

```text
https://github.com/JCarterJohnson/vibecoded-design-tells
f7c4aefc2c797a66e55b49354a93917ab60d33ac
```

The vendored upstream files and license are preserved under
`third_party/vibecoded-design-tells/`. Workprint-owned integration code invokes
the pinned scanner offline against a temporary UTF-8 narrative-only report
extract. Report generation does not contact GitHub or require network access.

The audit reviews generated narrative sections only:

- Executive Brief.
- Project Overview narrative.
- Key Milestone summaries.
- Human-AI Collaboration narrative.
- Decision Analysis prose.
- Confidence Assessment rationale.
- Evidence Gaps prose.
- Investigation Assurance.

The audit does not scan raw evidence quotations, evidence IDs, JSON keys,
factual appendix tables, detailed source appendix content, code, or command
examples.

The Markdown Copy-Quality Audit section reports status, scan scope, lexical
review completion, structural review completion, evidence-preservation
validation, finding counts by severity, waivers, override status, upstream
repository, pinned revision, upstream license, attribution notice, and
limitations.

Structural checks complement the lexical review because lexical findings alone
cannot assess overall writing quality.

The JSON `copy_quality_audit` object preserves existing fields and adds
attribution and diligence fields, including `upstream_author`,
`upstream_project`, `upstream_repository`, `upstream_revision`,
`upstream_license`, and `attribution_notice`.

Status rules:

- `passed`: lexical scanner ran, structural checks ran, no unresolved findings
  require waivers, and evidence-preservation validation passed.
- `passed_with_waivers`: lexical and structural checks ran, no high-severity
  findings remain, and every retained medium or low finding has a documented
  waiver.
- `failed`: a high-severity finding remains, structural review cannot
  complete after starting, evidence-preservation validation fails, audit output
  is malformed, or medium/low findings lack required waivers.
- `unavailable`: required scanner files are missing, the scanner cannot
  execute in the environment, or the pinned revision cannot be verified in the
  installed source.

When the scanner is unavailable, Workprint records status `unavailable`,
discloses degraded mode, and states that the lexical review was not completed.

A passing audit indicates that the generated narrative satisfied the configured
lexical and structural review. The audit identifies documented writing
patterns. It does not determine whether text was written by a human or an AI,
and passing the review does not establish human authorship or prove that AI was
not involved.

No endorsement by JCarterJohnson is implied.

## What Workprint Does Not Infer

Workprint does not infer:

- authorship;
- ownership;
- effort;
- value;
- contribution percentages;
- complete project toolsets;
- complete project history outside the supplied evidence;
- decision leadership without supporting evidence.

When evidence is missing, incomplete, or ambiguous, the Executive Report states
the limitation rather than filling the gap with speculation.

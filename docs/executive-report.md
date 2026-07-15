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

## Tools And Evidence Sources

Executive Report v1 keeps these concepts separate:

- evidence sources analyzed by Workprint;
- project tools explicitly observed in the evidence;
- unconfirmed or unavailable tool information.

An adapter or source file proves only that Workprint analyzed that evidence
source. Workprint reports project tools only when the evidence explicitly shows
tool use as part of project activity.

## Copy-Quality Audit

Executive Report v1 records copy-quality audit metadata using the pinned
`unslop-text` upstream repository and revision:

```text
https://github.com/JCarterJohnson/vibecoded-design-tells
f7c4aefc2c797a66e55b49354a93917ab60d33ac
```

The scanner is not yet vendored or integrated. Until it is available,
Workprint records audit status `unavailable`, discloses that the audit was not
completed, and generates the report in degraded mode. Workprint does not claim
that the prose was audited, human-authored, or rewritten.

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

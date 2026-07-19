# Engineering Principles

Status: Foundation guide
Purpose: Defines engineering philosophy and implementation guardrails
Expected Update Frequency: Update when engineering philosophy changes

Workprint's engineering philosophy follows from its product promise. The code
should make evidence handling predictable, source boundaries explicit, and
unsupported claims difficult to introduce.

## Small Coherent Milestones

Workprint should advance through milestones that are small enough to review
and coherent enough to dogfood. A milestone should have a clear product goal,
implemented scope, acceptance criteria, tests, and documented limitations.

This keeps the system understandable. It also prevents broad partially
specified changes from weakening evidence boundaries by accident.

## Deterministic Before Probabilistic

When a deterministic rule can produce a useful result, Workprint should prefer
it. Deterministic behavior is easier to test, explain, and trust.

Probabilistic or AI-assisted inference may eventually be useful, but it should
not replace deterministic extraction, normalization, ordering, duplicate
handling, or report claims without a deliberate design. If inference is added,
its role and limits must be visible.

## Backward Compatibility

Existing commands, report data, and public models should remain compatible
unless a milestone explicitly approves a breaking change.

Workprint is a trust tool. Users should not have to wonder whether a routine
feature addition silently changed the meaning of previous outputs. Additive
changes are preferred when they preserve existing behavior.

## No Hidden Inference

Workprint should not make quiet leaps from evidence to conclusion. Inference,
classification, confidence, grouping, and summarization rules should be
documented and testable.

Hidden inference is especially risky for attribution. If the system appears to
know who authored, owned, or contributed something, the evidence path must
support that claim. Otherwise the result should remain unknown.

## Source-Independent Investigation Engine

The investigation engine should operate on normalized observations, not raw
ChatGPT, Claude, Google Docs, Figma, Git, or future source formats.

This separation protects architecture. It lets Workprint add evidence sources
without rewriting investigation logic or embedding source-specific assumptions
where they are hard to audit.

## Adapters Own Source Parsing

Adapters are responsible for understanding source-specific artifacts. They
validate inputs, parse files, preserve useful metadata, and return normalized
records with stable evidence references.

Adapters must not generate project-level conclusions. A source adapter can say
what a source file contains. It should not decide what the project means.

## Presentation Layers Never Alter Evidence

Markdown, JSON, executive summaries, visual design improvements, and future UI
surfaces are presentation layers. They can improve readability and navigation.
They cannot change investigation facts.

This principle exists because report polish can create pressure to smooth
over uncertainty. Workprint should resist that pressure. Better presentation
should make evidence boundaries clearer, not softer.

## Every Milestone Is Dogfooded

Workprint should be tested against Workprint's own development whenever
possible. Dogfooding exposes usability issues, evidence gaps, confusing
language, and false assumptions that ordinary unit tests may miss.

Because the product reconstructs work history, its own history is a valuable
test case. Dogfooding also keeps the team honest about whether the product is
usable by the people it claims to serve.

## Every Milestone Has Tests

Behavior that matters should be covered by focused tests. Tests should reflect
the risk and blast radius of the change.

Adapters need tests for recognition, parsing, metadata preservation, and
evidence references. Investigation and timeline changes need tests for
ordering, grouping, attribution boundaries, unknowns, and report output.
Workflow changes need tests for user-facing behavior and cancellation paths.

Tests are not ceremony here. They protect the evidentiary contract.

## Documentation Is Implementation

For Workprint, documentation is part of the product. It defines source
limitations, explains confidence, preserves architectural decisions, and tells
future contributors where not to infer.

Outdated documentation can create bad implementation. When behavior changes,
the relevant documentation should change with it.

## External Dependencies Are Verified, Not Assumed

When an adapter's correctness depends on an external library, especially one
reading an undocumented or reverse-engineered format, the actual package must
be installed and run against representative real data before its behavior is
trusted in code or claimed in documentation. A GitHub repository's README and
a PyPI package's name are not the same fact; matching them requires checking
the PyPI package's own project metadata against the repository actually
researched, not assuming a similarly named package is the same project.

If that verification cannot happen before a milestone ships, the milestone's
documentation must say so plainly, and the feature's default behavior must
degrade safely rather than presenting unverified output as evidence.
Verification debt should be paid down before further work builds on top of
the unverified path, not deferred indefinitely.

## Avoid Unnecessary Abstraction

Workprint should add abstractions only when they remove real complexity,
reduce meaningful duplication, or preserve a clear architectural boundary.

Unnecessary abstraction makes evidence handling harder to audit. The codebase
should remain plain enough that a future contributor can follow evidence from
adapter to observation to investigation to report.

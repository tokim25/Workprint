# Autonomous Execution Guardrails

Status: Foundation guide
Purpose: Defines when Codex may execute approved milestones autonomously and
when it must escalate for human direction
Expected Update Frequency: Update when agent autonomy or approval boundaries
change

Workprint should let Codex complete clearly scoped milestones without asking
for approval at every routine step. That autonomy is useful only when it
preserves the approved product contract, evidence boundaries, trust model,
privacy expectations, architecture, and user experience.

Codex may move from planning through implementation, validation, dogfooding,
and self-review when the milestone is clear. Codex must stop when the work
requires a consequential product, UX, trust, evidence, privacy, licensing, or
architectural decision.

## Product Contract

Every meaningful milestone begins with:

- User Problem
- User Story
- UX Story
- Marketing Story
- Smallest Useful Version
- Acceptance Criteria
- Trust and Usability Risks
- Explicitly Out of Scope

Codex may choose implementation details, but it may not redefine this product
contract. If the contract is missing, unclear, or internally conflicting,
Codex must stop and ask for direction before implementation.

Every product milestone must also include a concrete dogfood scenario.

Default Workprint scenario:

"Tony has project evidence from AI conversations, documents, designs, and a
repository. He wants to understand what he directed, what AI produced, and
what they shaped together without needing to understand Git or use the command
line."

## Allowed Autonomous Decisions

Codex may decide:

- internal helper structure
- function and class organization
- test organization
- minor implementation details
- small refactors directly required by the milestone

These decisions are allowed only when they preserve the approved product
contract, existing evidence boundaries, attribution rules, confidence model,
privacy expectations, licensing obligations, and architecture.

## Mandatory Stop Conditions

Codex must stop and ask for direction before:

- changing the user story or product promise
- choosing a major UX flow
- introducing new user-facing terminology
- making an enduring architecture decision
- breaking schemas or compatibility
- changing confidence, attribution, or evidence rules
- making privacy, licensing, or third-party attribution decisions
- adding an unapproved dependency
- expanding scope
- removing existing behavior
- changing unrelated files
- proceeding from unclear or conflicting requirements
- making unsupported claims
- continuing when dogfood contradicts passing tests
- committing when unresolved risks remain

These stop conditions apply even when the implementation is technically easy.
Workprint should not let implementation momentum override product trust.

## Autonomous Execution Sequence

For approved milestones, Codex should perform:

1. Interpret the product contract.
2. Inspect the repository.
3. Report assumptions and risks.
4. Implement the smallest useful version.
5. Add or update tests.
6. Run the full relevant test suite.
7. Dogfood the actual user journey.
8. Review the result through UX, product, and marketing lenses.
9. Report deviations, limitations, and unresolved risks.
10. Stop before commit.

The user should not need to approve routine steps between these stages unless
a mandatory stop condition is triggered.

## Required Self-Review

Before reporting completion, Codex must evaluate the result through these
lenses.

### VP of User Experience

- Would a novice understand this?
- Is the main action obvious?
- Is technical language leaking into the product?
- Is the experience overwhelming or confusing?
- Does it preserve trust?

### Product and technical partner

- Does it solve the stated user problem?
- Did scope drift?
- Does it preserve evidence and architectural boundaries?
- Is the smallest useful version complete?

### World-class marketer

- Can the user benefit be explained in one sentence?
- Does the implementation deliver that promise?
- Is the language memorable without becoming hype?
- Are any claims stronger than the evidence supports?

## Required Completion Report

Before commit, Codex must report:

- Product contract followed
- What We Built
- Explain Like I'm 5
- What the User Can Do Now
- Actual user-facing result
- UX/Product/Marketing self-review
- Tests and dogfood evidence
- Deviations from the plan
- Unresolved risks
- What Remains Incomplete
- Recommended next action

Codex must not report only "implemented successfully." The completion report
must make clear what changed for the user, what was validated, and what still
requires judgment.

## Communication Order

When reporting plans, progress, or completion, Codex should:

1. Lead with a short summary.
2. Provide an "Explain Like I'm 5" explanation.
3. Add technical details only as needed.

This order helps novice users respond to the product meaning before they are
asked to parse implementation detail.

## Approval Boundary

Codex must always stop before commit unless the user has explicitly approved
autonomous committing for that specific milestone.

Codex must not commit directly to `main`.

If a milestone is complete but risks remain unresolved, Codex must report the
risks and wait for human direction before committing.

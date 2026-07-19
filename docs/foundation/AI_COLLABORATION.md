# AI Collaboration

Status: Foundation guide
Purpose: Defines human and AI responsibilities in Workprint development
Expected Update Frequency: Update when collaboration workflow changes

Workprint is itself developed through human-AI collaboration. That makes the
project responsible for practicing the same discipline it expects from its
reports: separate direction from implementation, preserve evidence, state
limits, test behavior, and avoid unsupported claims.

## Responsibilities

The human is responsible for product direction, acceptance of tradeoffs,
milestone priority, final judgment, and decisions that change Workprint's
philosophy. The human may also supply evidence, constraints, design intent,
review feedback, and approval gates.

Conversational AI assistants are often used for product thinking,
documentation drafting, strategy, design critique, or conceptual synthesis.
When used this way, they help shape language and explore alternatives, but
they do not replace human decision making.

A coding agent is used for repository work: reading the codebase, proposing
scoped implementation plans, editing files, running tests, checking diffs, and
reporting validation. The coding agent should follow `AGENTS.md`, preserve
source boundaries, avoid unrelated changes, follow
`AUTONOMOUS_EXECUTION_GUARDRAILS.md`, and never commit, push, merge, or delete
branches unless explicitly asked. Workprint has used more than one coding
agent over its history; these responsibilities apply to whichever agent is
doing the work.

These roles can overlap in practice, but the distinction is useful. Strategy,
product design, technical design, implementation, testing, dogfooding, review,
and refinement are different kinds of work. Workprint should keep them visible.

## Required Lenses Before Each Phase

Before each milestone phase, contributors should review the work through three
lenses: VP of User Experience, product and technical partner, and world-class
marketer. The point is not to add ceremony. The point is to keep the user,
the evidence model, and the product story visible before implementation
language takes over.

### VP of User Experience

- Challenge confusing flows.
- Advocate for novice users.
- Prioritize clarity and trust.
- Push back when implementation language leaks into the experience.
- Evaluate whether a first-time user understands the value.

### Product and technical partner

- Ensure the right problem is being solved.
- Protect architecture and evidence boundaries.
- Identify scope and sequencing risks.
- Explain technical work in plain language.

### World-class marketer

- Identify the clearest emotional and practical value.
- Turn technical capabilities into simple user benefits.
- Produce a one-sentence feature story.
- Test whether the feature is memorable and easy to explain.
- Avoid hype or claims stronger than the evidence supports.

## Development Workflow

Workprint development should follow this general flow:

```text
Vision
  ↓
Product Design
  ↓
Technical Design
  ↓
Implementation
  ↓
Testing
  ↓
Dogfooding
  ↓
Review
  ↓
Refinement
  ↓
Commit
```

Vision defines why the capability matters and how it fits Workprint's mission.

Product Design defines the user problem, reader questions, evidence
boundaries, report behavior, and success criteria.

Technical Design maps the product goal onto existing architecture, identifies
affected layers, and protects backward compatibility.

Implementation makes the smallest coherent code or documentation change that
serves the milestone.

Testing verifies behavior with focused tests and the complete regression suite
when implementation changes are made.

Dogfooding uses Workprint on Workprint where practical, especially for report
and workflow milestones.

Review checks whether the change preserves evidence traceability, product
principles, documentation, and changed-file scope.

Refinement addresses issues found during tests, dogfooding, or review without
expanding scope unnecessarily.

Commit records the finished change only when the user asks for a commit and
the repository state has been reviewed.

## Autonomous Execution With Escalation

For a clearly scoped and approved milestone, the coding agent may continue
through planning, implementation, validation, dogfooding, and self-review
without asking for approval between routine steps. Routine steps include
repository inspection, helper organization, implementation details, focused
tests, validation commands, and dogfooding the approved user journey.

This autonomy exists to reduce unnecessary handoffs, not to transfer product
authority. The coding agent must escalate when the work requires a
consequential product, UX, trust, evidence, privacy, licensing, third-party
attribution, or architecture decision.

The coding agent must stop and ask for direction before changing the user
story, changing the product promise, choosing a major UX flow, introducing new
user-facing terminology, making enduring architecture decisions, breaking
compatibility, changing confidence or attribution rules, adding dependencies,
expanding scope, removing existing behavior, changing unrelated files,
proceeding from unclear requirements, making unsupported claims, continuing
when dogfood contradicts tests, or committing with unresolved risks.

Before reporting completion, the coding agent should review the result
through the VP of User Experience, product and technical partner, and
world-class marketer lenses. Completion reports should begin with a short
summary, then an "Explain Like I'm 5" explanation, then technical detail only
as needed.

## Why Strategy Is Separate From Implementation

Workprint separates strategy from implementation because evidence products are
easy to distort by small technical choices. A parser default, report label,
confidence rule, or grouping heuristic can quietly change what readers believe.

Strategy asks what Workprint should claim. Implementation decides how the
system produces and presents that claim. Keeping those layers separate gives
contributors room to ask whether a feature is product-correct before asking
whether it is code-complete.

This separation is especially important when AI tools help build the project.
AI-assisted implementation can move quickly. Workprint should use that speed
without allowing speed to bypass product judgment, evidence boundaries, or
human review.

# Milestone Kickoff

## User Problem

## User Story

## UX Story

## Marketing Story

## Smallest Useful Version

## Trust and Usability Risks

## Explicitly Out of Scope

# PR Wrap-Up

Provide this wrap-up after every completed PR.

## What We Built

## Explain Like I'm 5

## What the User Can Do Now

## How We Would Market It

## What We Learned

## What Remains Incomplete

## What Comes Next

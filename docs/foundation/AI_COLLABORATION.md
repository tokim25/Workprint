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

ChatGPT is often used for product thinking, documentation drafting, strategy,
design critique, or conceptual synthesis. When used this way, it helps shape
language and explore alternatives, but it does not replace human decision
making.

Codex is used for repository work: reading the codebase, proposing scoped
implementation plans, editing files, running tests, checking diffs, and
reporting validation. Codex should follow `AGENTS.md`, preserve source
boundaries, avoid unrelated changes, and never commit, push, merge, or delete
branches unless explicitly asked.

These roles can overlap in practice, but the distinction is useful. Strategy,
product design, technical design, implementation, testing, dogfooding, review,
and refinement are different kinds of work. Workprint should keep them visible.

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

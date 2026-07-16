# Start Here

Status: Canonical entry point
Purpose: Required reading order and maintenance guide for the Foundation
Expected Update Frequency: Update when foundation structure changes

This directory is the permanent foundation for Workprint. Every contributor
should read it before making product, architecture, report, adapter, or
investigation decisions.

Workprint reconstructs how work was made from available evidence. It reads
source material such as conversations, static documents, design exports, and
repository context, normalizes that material, and produces evidence-linked
observations, timelines, investigations, and reports. Its purpose is not to
guess who deserves credit. Its purpose is to explain what the evidence can
support, where confidence is strong, and where the honest answer is unknown.

## Required Reading Order

Read these documents in this order:

1. [WORKPRINT_VISION.md](WORKPRINT_VISION.md)
2. [FOUNDATION_CHARTER.md](FOUNDATION_CHARTER.md)
3. [PRODUCT_PRINCIPLES.md](PRODUCT_PRINCIPLES.md)
4. [ENGINEERING_PRINCIPLES.md](ENGINEERING_PRINCIPLES.md)
5. [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
6. [AI_COLLABORATION.md](AI_COLLABORATION.md)
7. [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
8. [DECISION_LOG.md](DECISION_LOG.md)
9. [WORKPRINT_GLOSSARY.md](WORKPRINT_GLOSSARY.md)

The order matters. The vision explains why Workprint exists. The charter sets
the constitutional limits. Product and engineering principles translate those
limits into operating judgment. Architecture explains the system shape. AI
collaboration explains how the project itself is made. Context records the
current repository state. The decision log preserves accepted choices. The
glossary keeps language stable.

## Document Ownership

Some foundation documents are nearly immutable. `FOUNDATION_CHARTER.md` and
`WORKPRINT_VISION.md` define Workprint's constitutional principles and durable
mission. They should change only when the project deliberately revisits its
identity.

Some documents are living. `PROJECT_CONTEXT.md` tracks the current repository
state, active milestone, capabilities, limitations, and technical debt.
`DECISION_LOG.md` records accepted enduring decisions as they are made.

Some documents are occasionally updated. `PRODUCT_PRINCIPLES.md`,
`ENGINEERING_PRINCIPLES.md`, `ARCHITECTURE_OVERVIEW.md`,
`AI_COLLABORATION.md`, and `WORKPRINT_GLOSSARY.md` should change when the
project's stable principles, architecture, collaboration model, or terminology
change.

This distinction exists so contributors know when to preserve a document and
when to maintain it. Workprint needs durable principles, but it also needs a
current memory of the repository.

## Relationship To AGENTS.md

`AGENTS.md` is the operational instruction file for coding agents working in
this repository. It tells agents how to behave while making changes: preserve
traceability, avoid unsupported attribution, keep changes small, run
validation, and protect core package surfaces.

The foundation documents explain the deeper product and engineering reasons
behind those instructions. When `AGENTS.md` gives a rule, this foundation
explains the philosophy that rule protects.

## Relationship To PROJECT_PLAN.md

`PROJECT_PLAN.md` is the living capability plan. It records completed
milestones, the active milestone, acceptance criteria, limitations, and near
term direction.

The foundation documents are more durable. They should not change every time a
milestone completes. They should change only when Workprint's core philosophy,
architecture, or terminology changes.

Contributors should use both:

- use this foundation to decide what kind of product Workprint is allowed to
  become;
- use `PROJECT_PLAN.md` to understand what capability is being built next.

## How To Use This Foundation

Implementation should align with these documents. If a proposed change would
silently change Workprint's product philosophy, evidence model, attribution
boundaries, or confidence language, do not treat it as an ordinary
implementation detail. Name the change, discuss it, and update the foundation
only if the project deliberately accepts the new direction.

Workprint earns trust by being explicit. That includes being explicit about
its own principles.

## Foundation Maintenance

When a feature introduces a new enduring architectural decision, update
`DECISION_LOG.md`.

When the current repository state changes, update `PROJECT_CONTEXT.md`.

When product philosophy changes, update `PRODUCT_PRINCIPLES.md`.

When engineering philosophy changes, update `ENGINEERING_PRINCIPLES.md`.

When constitutional principles change, which should be rare, update
`FOUNDATION_CHARTER.md`.

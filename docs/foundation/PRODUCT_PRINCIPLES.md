# Product Principles

Status: Foundation guide
Purpose: Defines product judgment for evidence-based user experiences
Expected Update Frequency: Update when product philosophy changes

These principles guide product decisions for Workprint. They are written for
moments when a feature could be implemented in more than one reasonable way.
The preferred path is the one that makes the report more trustworthy,
understandable, and evidence-bound.

## User Stories Are the Unit of Progress

Workprint should measure progress by new user capabilities, not only by
adapters, models, files, or tests. Technical milestones matter because they
make new user outcomes possible. They are not the outcome by themselves.

Engineering description:
"Added a Git adapter."

User capability:
"Users can understand how their project changed over time."

Marketing story:
"Turn repository history into a clear story of what you built, when it
changed, and how the work came together."

Workprint's enduring product promise is:

"Workprint shows what you contributed, what AI contributed, how you worked
together, and what the evidence cannot determine."

In this promise, "contribution" must be explained through evidence-backed
roles, decisions, direction, execution, review, and collaboration rather than
unsupported percentages.

Every milestone should answer: "What can the user understand or demonstrate
now that they could not understand or demonstrate before?"

## Evidence Before Inference

Workprint should first ask what the evidence directly supports. Inference may
be useful, but it must be clearly bounded and subordinate to the captured
record.

This matters because Workprint operates in contexts where trust is fragile.
Readers may be evaluating collaboration, authorship boundaries, diligence, or
decision quality. A product that begins with inference can easily turn missing
evidence into a confident story. Workprint should instead let evidence set the
outer edge of what can be claimed.

Every section should be able to answer: "Why should I believe this?"

## Narrative Before Detail

A Workprint report should help a reader understand before it asks them to
inspect. The first experience should be a clear explanation of what happened,
what was produced, how the project evolved, how humans and AI appear to have
collaborated, and what remains unknown.

Raw tables, observation IDs, file locators, and counts are necessary support,
but they are not the story. Workprint should lead with human-readable meaning
and then make the supporting evidence easy to inspect.

Every section should be able to answer: "Why should I believe this?" The
answer may be a concise explanation followed by references, not a wall of raw
data.

## Human Questions First

Workprint reports should be organized around the reader's natural questions:
What is this project? What was made? How did it change? Who or what appears to
have directed, implemented, reviewed, or decided? How confident is the
reconstruction? What cannot be known?

Implementation details matter only when they help answer those questions.
Reports should not force readers to learn Workprint internals before they can
understand the project account.

Every section should be able to answer: "Why should I believe this?" It should
also answer why the section exists for a human reader.

## Complexity Belongs In The Engine

Complexity is allowed in the engine. It is not allowed in the experience.

Workprint may need careful adapters, normalization, observation extraction,
timeline rules, confidence explanations, source limitations, and evidence
references to preserve trust. Users should not have to experience that
complexity as setup friction, implementation terminology, or unnecessary
stopping points.

The product experience should organize complexity around a user's natural
mental model: tell Workprint about the project, provide evidence, wait while
it investigates, and understand what it discovered. Details should appear
only when they help the user decide, trust, inspect, or export.

Every screen should be able to answer: "Would Google, Apple, or Notion make
the user stop here?" If the answer is no, the interaction should be
simplified, absorbed into another step, or moved into progressive disclosure.

## Unknown Over Unsupported Certainty

Unknowns are part of product quality. If Workprint cannot determine whether a
person authored a section, whether a decision happened in a private channel, or
whether a static export reflects the full project history, it should say so.

Unsupported certainty may feel more complete in the short term, but it makes
the report less useful for serious readers. Workprint should normalize
uncertainty as an honest output, not bury it as a weakness.

Every section should be able to answer: "Why should I believe this?" When the
answer is "you should not yet believe it," the section should say that plainly.

## Decision Leadership Over Contribution Scoring

Workprint should help readers understand decisions, direction, review, and
judgment. It should not score contribution.

Contribution scoring creates false precision. Counts of messages, tokens,
commits, edits, or observations do not measure ownership, effort, value, or
authorship. Decision leadership is more useful when handled carefully because
it can be tied to specific evidence: a user set a constraint, approved a
tradeoff, rejected an approach, or asked for a change.

Every section should be able to answer: "Why should I believe this?" For
decision leadership, that means naming the decision and the evidence that
supports the assessment.

## Confidence Should Be Understandable

Confidence should be expressed in language a reader can understand. Qualitative
bands are useful only when accompanied by a rationale that explains evidence
strength, coverage, corroboration, conflicts, and gaps.

Workprint should not hide confidence behind numeric scores or unexplained
algorithms. A reader should know whether confidence is high because evidence is
direct, because multiple sources corroborate the same point, or because there
are few conflicts. The reader should also know when confidence is limited by
missing source history or narrow coverage.

Every section should be able to answer: "Why should I believe this?" Confidence
language is the product's direct answer to that question.

## Trust Is A Product Feature

Trust is not only a legal or technical property. It is a product feature that
must be designed into the user's experience.

Trust appears in source previews, evidence boundaries, plain-language unknowns,
non-overclaiming reports, stable terminology, and consistent treatment of
human and AI activity. A feature that is impressive but makes the system less
believable moves Workprint in the wrong direction.

Every section should be able to answer: "Why should I believe this?" If a
section cannot answer that, it may be decoration rather than product.

## Reports Should Reduce Skepticism

A reader may come to a Workprint report skeptical of AI-assisted work,
skeptical of self-reported process, or skeptical of provenance claims.
Workprint should not argue with that skepticism. It should meet it with
traceable evidence, clear limits, and careful language.

The goal is not to persuade readers through confidence alone. The goal is to
make belief easier because the report shows its work.

Every section should be able to answer: "Why should I believe this?" The
strongest report makes that question welcome.

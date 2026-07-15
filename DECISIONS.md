# Decision Log

## 2026-07-15: Evidence-Based Attribution, Not Contribution Percentages

Decision: Workprint reports evidenced actions, decisions, and involvement
without calculating speculative human-versus-AI contribution percentages.

Rationale: Percentages imply precision the available evidence cannot support.
Conversation volume, token counts, commits, and edit volume do not measure
ownership, effort, value, or authorship.

Consequences: Reports must use bounded claims and preserve evidence links.
Aggregate counts may describe captured evidence only.

Alternatives considered: Contribution percentages and ownership scores were
rejected because they would overstate what the evidence can prove.

## 2026-07-15: Prefer Unknown Over Unsupported Certainty

Decision: Workprint uses unknown when evidence does not support a conclusion.

Rationale: The product's credibility depends on separating what is known from
what is inferred, estimated, or missing.

Consequences: Reports may feel conservative, but they avoid unsupported
attribution.

Alternatives considered: Filling gaps with likely explanations was rejected.

## 2026-07-15: Deterministic Classification Before Semantic or LLM Inference

Decision: Workprint prioritizes deterministic classification rules before
semantic matching or LLM inference.

Rationale: Deterministic behavior is easier to test, explain, and audit.

Consequences: Early classifications may miss nuance, but they remain stable and
traceable.

Alternatives considered: LLM-first extraction was deferred until deterministic
behavior is trustworthy.

## 2026-07-15: Separate Activity Categories

Decision: Workprint keeps user activity, collaborator activity, AI/tool
activity, joint activity, and unattributed activity separate.

Rationale: Combining these categories would blur attribution and make reports
less trustworthy.

Consequences: Models and reports must preserve category boundaries.

Alternatives considered: A single actor/contribution field was rejected as too
ambiguous.

## 2026-07-15: Timeline Report Before Adding More Adapters

Decision: The Timeline Report is the active capability before adding more
evidence adapters.

Rationale: A stronger report layer makes existing ChatGPT and Claude evidence
more useful and clarifies the model future adapters must feed.

Consequences: Google Docs and Figma work wait until timeline requirements are
defined and implemented.

Alternatives considered: Adding Git, Google Docs, or Figma first was deferred.

## 2026-07-15: Google Docs Before Figma

Decision: After Timeline Report, Google Docs adapter work precedes Figma.

Rationale: Document revision history is likely closer to Workprint's current
conversation/document evidence model than design history.

Consequences: Figma remains planned, but Google Docs establishes the next
non-conversation adapter path.

Alternatives considered: Figma first was considered but deferred because it may
require different interaction and visual evidence semantics.

## 2026-07-15: Product Must Become Accessible to Nontechnical Users

Decision: Workprint should evolve toward an experience usable by people with
limited coding or terminal knowledge.

Rationale: The product direction is evidence reconstruction for real projects,
not a developer-only library.

Consequences: Future UX should include guided imports, plain-language errors,
previews, and shareable outputs.

Alternatives considered: Keeping Workprint CLI-only was rejected as a long-term
product direction.

## 2026-07-15: Adapters Normalize Evidence; Engine Remains Source-Independent

Decision: Evidence adapters normalize source material, and the investigation
engine stays source-independent.

Rationale: Source-specific logic in the engine would make behavior harder to
test, extend, and explain.

Consequences: New adapters must target shared normalized records or clearly
defined future record types.

Alternatives considered: Adapter-specific engine branches were rejected.

## 2026-07-15: Exact Duplicate Suppression Is Source-Aware

Decision: Exact duplicate suppression includes source identity and does not
attempt semantic cross-source deduplication.

Rationale: Source-aware fingerprints avoid collapsing distinct evidence that
happens to say similar things.

Consequences: Repeated identical inputs can be suppressed, while semantic
duplicates remain visible until trustworthy correlation rules exist.

Alternatives considered: Semantic duplicate detection was deferred.

## 2026-07-15: One Focused Branch and PR Per Capability

Decision: Workprint development uses one focused branch and pull request per
capability.

Rationale: Focused changes reduce accidental regressions and make review easier.

Consequences: Broad refactors should be split from behavior changes.

Alternatives considered: Large mixed branches were rejected.

## 2026-07-15: Never Construct Feature Commits From Partial Repository Snapshots

Decision: Feature commits must preserve the complete repository tree and must
not be built from partial snapshots.

Rationale: Partial snapshots previously removed core packages while adding new
features.

Consequences: Before committing, contributors must check changed-file scope and
confirm core packages remain present.

Alternatives considered: Relying on later recovery commits was rejected.

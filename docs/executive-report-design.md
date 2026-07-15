# Executive Report Design

Specification version: 1.0 draft
Status: Design review
Last updated: 2026-07-15

This document is the canonical product design specification for future
Workprint reports. It defines what a report should help a reader understand,
how the report should be organized, and how Workprint should communicate
evidence, confidence, collaboration, and uncertainty.

This is a product design document, not an engineering specification. Future
implementation should preserve the evidence model and technical guardrails
already established by Workprint, while making the report more useful to human
readers.

## Product Goal

Workprint helps people understand the history of human-AI collaboration by
reconstructing what the available evidence supports and clearly stating what it
cannot know.

Workprint should not simply reconstruct evidence. It should help someone
understand how a project came to life through evidence-backed reconstruction of
human-AI collaboration.

A Workprint report should leave the reader with understanding, not just
information.

A Workprint report should answer the reader's natural questions before it asks
the reader to inspect supporting evidence. The report should explain what the
project was, what was produced, how it evolved, how humans and AI collaborated,
which decisions mattered, how trustworthy the reconstruction is, and what
cannot be known from the available evidence.

The report should feel like a careful investigation written for a smart reader,
not a dump of logs, tables, observations, or implementation internals.

## Audiences

### Project Creator

The project creator reads the report to understand and communicate their own
work. They may want to share the report with a hiring manager, client, teammate,
or reviewer.

They want to know:

- Does the report fairly represent what I made?
- Does it show the direction, judgment, and iteration behind the work?
- Does it separate my activity from AI/tool activity without exaggerating
  either?
- Does it avoid unsupported claims about authorship or contribution?
- Can I share this without needing to explain the raw evidence myself?

Evidence builds trust when it shows the creator initiating, refining, deciding,
reviewing, or integrating work across time. The creator also needs clear
unknowns so the report does not overclaim on their behalf.

### Hiring Manager

The hiring manager reads the report to evaluate how a candidate works. They may
not care about every artifact, but they care deeply about judgment, problem
framing, iteration, decision quality, and collaboration with AI tools.

They want to know:

- What was the project trying to accomplish?
- What did the candidate appear to contribute directly?
- How did the candidate use AI tools: as a substitute, collaborator, assistant,
  reviewer, or implementation accelerator?
- Which decisions show taste, judgment, technical skill, or product thinking?
- How reliable is this report as a signal?

Evidence builds trust when it is tied to specific decisions, changes,
questions, prompts, reviews, and artifacts. A hiring manager should be able to
skim the Executive Brief and Collaboration sections before deciding whether to
read the appendix.

### Client

The client reads the report to understand the work behind a deliverable. They
may be assessing progress, diligence, scope, or whether the produced artifact
matches the agreed goal.

They want to know:

- What was produced?
- How did the project evolve from initial request to final output?
- Which tradeoffs were made?
- Where did human judgment shape the work?
- What evidence supports the account of progress?
- What remains uncertain or outside the evidence?

Evidence builds trust when it shows traceable progression, decision points,
source materials, and outputs. Clients need a report that avoids technical
jargon unless it is essential to understanding the project.

### Auditor

The auditor reads the report to assess process, traceability, and reliability.
They may care less about the project's creative merit and more about whether
the reconstruction is bounded by evidence.

They want to know:

- What sources were reviewed?
- What evidence was excluded or unavailable?
- Which claims are directly supported?
- Which claims are interpretive but bounded?
- What confidence level applies to each major conclusion?
- Can every conclusion be traced to source references?

Evidence builds trust when conclusions are linked to observations, observations
are linked to evidence references, and limitations are stated plainly.

### Legal Reviewer

The legal reviewer reads the report to understand risk, attribution boundaries,
and evidentiary limits. They may be concerned about ownership, authorship,
confidentiality, or disputed claims.

They want to know:

- Does the report make unsupported authorship claims?
- Does it imply ownership, effort, value, or contribution percentages?
- Does it distinguish captured evidence from inferred activity?
- Does it preserve uncertainty where evidence is incomplete?
- Does it identify missing revision history, deleted evidence, or unsupported
  attribution?

Evidence builds trust when the report avoids speculation. The legal reviewer
should never have to wonder whether Workprint is quietly converting activity
counts into authorship claims.

### Future Teammate

The future teammate reads the report to get oriented. They want to understand
what happened, why decisions were made, and where they can safely continue.

They want to know:

- What is the project?
- What exists now?
- How did it get here?
- Which decisions should I preserve?
- Which open questions or gaps should I investigate next?
- Which source materials should I inspect if I need more detail?

Evidence builds trust when the report provides a coherent narrative and then
points to source references for deeper inspection.

## Product Principles

### Lead With Insight, Not Implementation Details

A reader should first encounter a plain-language explanation of what happened.
Tables, IDs, counts, and source references should support that explanation,
not replace it.

Instead of:

> Timeline Events: 14

Prefer:

> Workprint reconstructed fourteen significant project events, beginning with
> early project framing and ending with a guided report workflow that generated
> both Markdown and JSON outputs.

### Every Conclusion Must Be Traceable To Evidence

Every meaningful conclusion should connect to observations and evidence
references. The report may summarize, synthesize, and explain, but it must not
invent facts outside the available evidence.

Instead of:

> The creator owned the architecture.

Prefer:

> The available evidence shows the creator repeatedly asking architecture
> questions, approving implementation direction, and reviewing final behavior.
> Workprint cannot determine ownership from this evidence alone.

### State Uncertainty Explicitly

Unknowns are not failures. They are part of the report's trustworthiness.
Workprint should state what cannot be known and why.

Instead of:

> Unknowns: 3

Prefer:

> Three important questions could not be answered from the available evidence:
> whether any code was changed outside the captured conversations, whether
> deleted drafts existed, and whether final approval happened in another tool.

### Narratives Precede Supporting Tables

Readers need meaning before detail. A section should explain the point in
natural language, then use compact tables or lists to show supporting evidence.

### Never Infer Authorship, Ownership, Effort, Value, Or Contribution Percentages

Workprint may describe captured activity. It must not convert activity into
unsupported conclusions about ownership, authorship, value, effort, or
percentage contribution.

Allowed:

> The captured evidence shows the user directed three implementation changes
> and reviewed two outputs.

Prohibited:

> The user contributed 70 percent of the project.

### Evidence Boundaries Should Be Obvious

The report should make the boundary between evidence and interpretation
visible. Readers should understand that Workprint reports on captured evidence,
not the totality of work that may have occurred elsewhere.

### Reports Should Be Understandable By Non-Technical Readers

The report may include technical detail, but it should not require technical
knowledge to understand the project story. Use plain language first. Put
technical labels, source IDs, and evidence locators in supporting detail.

## Information Architecture

Future Workprint reports should use this order:

1. Executive Brief
2. Project Overview
3. Project Evolution
4. Human-AI Collaboration
5. Decision Analysis
6. Confidence Assessment
7. Evidence Gaps
8. Investigation Assurance
9. Evidence Appendix

This order is intentional. It answers human questions first, then provides
supporting evidence and diligence material.

## 1. Executive Brief

### Purpose

The Executive Brief gives a one-minute understanding of the project. It is the
most important section of the report.

### User Question Answered

What was this project, what was produced, how did it evolve, how did humans and
AI collaborate, how confident is the report, and what remains unknown?

### Required Inputs

- Project name.
- Evidence sources reviewed.
- Reconstructed project outputs.
- Major timeline stages.
- Collaboration signals.
- Key decisions.
- Confidence assessment.
- Most important unknowns.

### Required Outputs

- Short project goal.
- Short description of produced outputs.
- Natural-language evolution summary.
- Human-AI collaboration summary.
- Confidence band and explanation.
- Most important evidence gaps.
- Link or reference to evidence appendix.

### Prohibited Content

- Raw observation dumps.
- Wide tables.
- Unsupported authorship or ownership claims.
- Contribution percentages.
- Technical implementation detail that does not help a one-minute reader.

### Complete Example

> Workprint reconstructed the development of a guided investigation workflow
> for the Workprint project. The available evidence shows a project that began
> with source discovery, then expanded into a guided report-generation
> experience designed for less technical users.
>
> The project produced a command-line guided workflow, documentation for its
> use, and report outputs in both Markdown and JSON. Workprint identified
> fourteen significant project events, including project framing, adapter
> integration, report design, guided workflow implementation, dogfooding, and
> follow-up fixes.
>
> The collaboration pattern appears to be human-directed and AI-assisted. The
> captured evidence shows the user defining milestones, constraints, approval
> gates, and product requirements. AI/tool activity appears primarily in
> implementation, test execution, documentation drafting, and synthesis. This
> report does not infer authorship, ownership, effort, value, or contribution
> percentages.
>
> Confidence is High for the reconstructed sequence of captured events because
> the report is based on multiple structured evidence sources and tested
> outputs. Confidence is Limited for activity that may have happened outside
> the captured evidence, including unrecorded discussions, deleted drafts, or
> repository work not included in the source materials.
>
> The most important unknowns are whether additional conversations existed
> outside the provided exports, whether any decisions happened in private
> channels, and whether Git history would change the interpretation of project
> evolution.

## 2. Project Overview

### Purpose

Project Overview orients the reader before the narrative begins. It explains
what the project is and why the report exists.

### User Question Answered

What is this project and what evidence did Workprint review?

### Required Inputs

- Project name.
- Stated or inferred project goal from captured evidence.
- Evidence source list.
- Output artifacts or deliverables.
- Date range when available.

### Required Outputs

- Plain-language project description.
- Known outputs.
- Reviewed evidence sources.
- Evidence boundary statement.

### Prohibited Content

- Claims that the reviewed evidence is complete unless completeness is itself
  evidenced.
- Claims that a deliverable is final unless the evidence shows finality.
- Claims that a person or tool authored the project.

### Example

> Workprint reviewed exported conversations, static documents, and structured
> design evidence related to the Workprint reporting workflow. The reviewed
> sources show a project focused on turning evidence into explainable reports
> for non-technical readers.

## 3. Project Evolution

### Purpose

Project Evolution explains how the project moved from idea to output. This
section should make the project feel understandable as a sequence of human
choices, tool-assisted work, and evidence-backed changes.

### User Question Answered

How did the project develop over time?

### Required Inputs

- Timeline events.
- Observation statements.
- Evidence references.
- Stage or category labels.
- Dates or ordering signals.

### Required Outputs

- Narrative progression.
- Natural-language stage summary.
- Compact timeline only after the narrative.
- Evidence references for major events.

### Prohibited Content

- Leading with a raw timeline table.
- Treating event counts as the story.
- Inferring causality beyond evidence.
- Hiding uncertainty in event ordering.

### Narrative First

The section should begin with prose:

> The project appears to have evolved in four broad phases. First, the user
> defined the evidence sources and boundaries. Next, Workprint added source
> adapters and deterministic report generation. The project then shifted from
> correctness to readability, improving the report so non-technical readers
> could understand it. Finally, the team tested the guided workflow against the
> project itself and corrected the usability issues that appeared.

Only after this narrative should Workprint provide a compact timeline:

| Stage | What Changed | Evidence |
|---|---|---|
| Framing | User defined the project goal and guardrails. | `obs-001`, `obs-002` |
| Implementation | Guided workflow generated Markdown and JSON. | `obs-014` |
| Dogfooding | Usability issues appeared during real use. | `obs-021` |
| Refinement | Workflow added non-interactive options and stricter discovery. | `obs-025` |

### More Examples

Instead of:

> Event 7: adapter integration.

Prefer:

> The project expanded from conversation-only evidence to document and design
> evidence, which made the later guided workflow more useful across mixed
> project folders.

Instead of:

> Event 12 happened after Event 11.

Prefer:

> After the report became more readable, attention shifted to making it easier
> for a less technical user to generate that report without memorizing expert
> commands.

## 4. Human-AI Collaboration

### Purpose

Human-AI Collaboration is Workprint's signature capability. It should explain
how human direction and AI/tool activity interacted, while staying strictly
within evidence boundaries.

### User Question Answered

How did humans and AI appear to collaborate on this project?

### Required Inputs

- Observations with actor labels.
- User involvement classifications.
- AI/tool activity classifications.
- Decision observations.
- Evidence references.
- Attribution limits.

### Required Outputs

- Human Role Assessment.
- AI Role Assessment.
- Collaboration Profile.
- Decision Leadership.
- Captured Activities.
- Evidence Boundaries.

### Prohibited Content

- Authorship claims not directly supported by evidence.
- Ownership claims.
- Effort estimates.
- Value judgments based only on volume.
- Human-versus-AI percentages.
- Claims that AI "understood" intent unless evidence directly supports the
  user's stated intent.

### Human Role Assessment

Describe what the captured evidence shows humans doing.

Allowed examples:

> The captured evidence shows the user defining the milestone, approving the
> implementation scope, identifying dogfooding issues, and setting acceptance
> criteria.

> The user appears to have acted as project director in the captured evidence,
> because they supplied goals, constraints, and approval gates.

Required caveat:

> This is an assessment of captured activity, not a claim of total authorship,
> ownership, effort, or contribution.

### AI Role Assessment

Describe what AI/tools appear to have done in the captured evidence.

Allowed examples:

> AI/tool activity appears in implementation, test execution, summarization,
> and documentation drafting.

> The available evidence suggests AI served as an implementation and analysis
> assistant within human-defined constraints.

Prohibited:

> AI created the project.

> AI contributed 40 percent of the work.

### Collaboration Profile

The Collaboration Profile should name the observed pattern in plain language.
Examples:

- Human-directed, AI-assisted implementation.
- Human-led product design with AI-assisted documentation.
- AI-assisted exploration with human review and approval.
- Joint iteration with unclear final decision ownership.

Each profile must include why the pattern was chosen and what evidence limits
the conclusion.

Example:

> Collaboration Profile: Human-directed, AI-assisted implementation. The user
> supplied the milestone goals, constraints, and acceptance criteria. AI/tool
> activity appears in implementing the requested changes and summarizing test
> results. Workprint cannot determine total effort or authorship from the
> captured evidence.

### Decision Leadership

Decision Leadership describes who appears to have led specific decisions in
the captured evidence. It must be decision-specific, not global.

Allowed:

> The user appears to have led the decision to make Git discovery informational
> only, because the captured request explicitly set that constraint.

Prohibited:

> The user led all decisions.

### Captured Activities

Captured Activities should summarize measured activity without converting it
into ownership or value.

Instead of:

> User activity: 8

Prefer:

> Workprint found eight captured evidence events where the user initiated,
> directed, reviewed, or decided project work.

### Evidence Boundaries

This subsection should clearly state what cannot be concluded.

Example:

> The available evidence can show captured direction, review, implementation,
> and decision activity. It cannot show uncaptured work, private discussions,
> deleted drafts, total time spent, authorship, ownership, or percentage
> contribution.

## 5. Decision Analysis

### Purpose

Decision Analysis explains the major choices that shaped the project.

### User Question Answered

Which decisions mattered, who appeared to lead them, and how well supported are
those conclusions?

### Required Inputs

- Decision observations.
- Timeline events.
- Evidence references.
- Actor information.
- Confidence assessment.
- Attribution limits.

### Required Outputs

For each major decision:

- Summary.
- Supporting evidence.
- Confidence.
- Apparent decision leader.
- Alternative interpretations.
- Evidence references.

### Prohibited Content

- Decisions inferred only from final state.
- Global claims about who made all decisions.
- Unsupported intent.
- Unsupported tradeoff analysis.

### Decision Example

**Decision: Make Git discovery informational only**

Summary:

> The project chose to show Git repository presence during discovery while
> preventing Git from being selected for investigation until a Git evidence
> adapter exists.

Supporting evidence:

> The user's milestone instructions explicitly required Git detection to remain
> informational and prohibited Git investigation selection.

Confidence:

> Very High. The requirement is directly stated in captured evidence and later
> reflected in the guided workflow behavior.

Apparent decision leader:

> User-led in the captured evidence.

Alternative interpretations:

> None strongly supported by the available evidence. Workprint cannot determine
> whether the same decision was discussed elsewhere.

Evidence references:

> `obs-042`, `request-guided-clarification`

### Decision Template

Each decision should follow this shape:

> Workprint identified a decision about [topic]. The captured evidence shows
> [what happened]. This appears to have mattered because [effect on project].
> Confidence is [band] because [evidence reason]. Alternative interpretations
> include [bounded alternatives]. Evidence: [references].

## 6. Confidence Assessment

### Purpose

Confidence Assessment explains how much trust readers should place in the
report and why. It should be understandable to non-experts.

### User Question Answered

How reliable is this report?

### Required Inputs

- Source coverage.
- Evidence density.
- Corroboration across sources.
- Unknowns.
- Consistency between evidence and outputs.
- Limitations.

### Required Outputs

- Overall confidence band.
- Explanation of evidence strength.
- Coverage assessment.
- Corroboration assessment.
- Unknowns summary.
- Section-specific confidence where useful.

### Prohibited Content

- Arbitrary scoring formulas.
- False precision.
- Numeric confidence percentages.
- Confidence that hides missing evidence.

### Confidence Versus Related Concepts

Confidence:

> The report's trust level for a conclusion, expressed as an explainable band.

Evidence Strength:

> How direct, specific, and traceable the supporting evidence is.

Coverage:

> How much of the project lifecycle is represented by available sources.

Corroboration:

> Whether multiple independent or complementary sources support the same
> conclusion.

Unknowns:

> Important questions that cannot be answered from the available evidence.

### Confidence Bands

Very High:

> The conclusion is directly supported by explicit evidence, source references
> are available, and there are few plausible alternative interpretations.

High:

> The conclusion is well supported by captured evidence, though some adjacent
> context may be missing.

Moderate:

> The conclusion is reasonable from the available evidence, but coverage is
> incomplete or alternative interpretations remain plausible.

Limited:

> The conclusion is weakly supported or depends on partial evidence. It may be
> useful as a tentative reading, but it should not be treated as settled.

Low:

> The evidence is too sparse, indirect, or conflicting to support a meaningful
> conclusion.

### What Increases Confidence

- Explicit user statements.
- Clear decision language.
- Evidence references tied to source records.
- Repeated support across multiple observations.
- Consistency between requests, implementation, tests, and documentation.
- Multiple source types supporting the same sequence.

### What Decreases Confidence

- Missing conversations.
- Missing Git history.
- Missing revision history.
- Deleted evidence.
- Ambiguous actor labels.
- Gaps between request and output.
- Final artifacts without process evidence.
- Conflicting evidence.

### Worked Example: Very High

Conclusion:

> The user required the guided workflow to preserve expert CLI commands.

Assessment:

> Confidence is Very High because the requirement is directly stated in the
> captured milestone instructions and the resulting implementation preserved
> existing expert commands.

### Worked Example: High

Conclusion:

> The project evolved from evidence reconstruction toward reader-centered
> reporting.

Assessment:

> Confidence is High because multiple milestones show report readability,
> guided workflow, and executive report design becoming increasingly important.
> Confidence is not Very High because the report cannot determine whether the
> same shift was discussed outside the captured evidence.

### Worked Example: Moderate

Conclusion:

> The user appears to have acted as product director for the captured project
> work.

Assessment:

> Confidence is Moderate because the user supplied goals, constraints,
> approvals, and refinements in the captured evidence. The report should not
> state this as total project leadership because uncaptured work may exist.

### Worked Example: Limited

Conclusion:

> The project may have involved significant implementation activity outside the
> captured conversations.

Assessment:

> Confidence is Limited because implementation artifacts exist, but without
> complete Git history or development logs the report cannot reconstruct all
> implementation activity.

### Worked Example: Low

Conclusion:

> A specific person authored a specific paragraph.

Assessment:

> Confidence is Low unless the source evidence explicitly maps that person to
> that paragraph. Document-level owners, authors, or editors are not enough.

## 7. Evidence Gaps

### Purpose

Evidence Gaps build trust by showing what Workprint cannot know.

### User Question Answered

What important questions could not be answered from the available evidence?

### Required Inputs

- Missing source types.
- Adapter limitations.
- Unknowns from investigation.
- Attribution limits.
- Confidence limitations.

### Required Outputs

- Plain-language list of gaps.
- Why each gap matters.
- What evidence would reduce the gap.
- Whether the gap affects a specific conclusion.

### Prohibited Content

- Treating unknowns as errors.
- Hiding limitations in a footnote.
- Using gaps to speculate.
- Suggesting certainty where evidence is absent.

### Common Evidence Gaps

Missing Git history:

> The report cannot fully reconstruct code authorship, sequencing, or file-level
> implementation activity without repository history.

Missing conversations:

> The report may not include decisions made in private chats, meetings, email,
> or other tools.

Deleted evidence:

> Deleted drafts, removed comments, or overwritten files may change the
> project story but are not visible in the captured sources.

Unsupported attribution:

> The report can show captured activity but cannot assign authorship,
> ownership, effort, value, or contribution percentage without direct evidence.

Missing revision history:

> Static document or design exports may show content but not how it changed
> over time.

### Why Unknowns Increase Credibility

Unknowns show that Workprint is respecting the evidence boundary. A report that
states its limits is more trustworthy than one that fills gaps with confident
guesswork.

Instead of:

> No issues found.

Prefer:

> Workprint did not find evidence for external review in the provided sources.
> That does not mean external review did not happen; it means the available
> evidence does not show it.

## Executive Copy Quality Gate

### Purpose

The Executive Copy Quality Gate is a mandatory prose-quality review for the
reader-facing narrative sections of a future Executive Report. It runs after
evidence-backed draft copy has been written, but before the final report is
rendered.

This gate is a prose-quality audit, not an AI-authorship detector. Its purpose
is to keep Workprint's executive language direct, specific, evidence-preserving,
and appropriate for an investigative briefing.

The gate must use the `unslop-text` work from
<https://github.com/JCarterJohnson/vibecoded-design-tells>, specifically:

- `unslop-ai-text/skill/SKILL.md`
- `unslop-ai-text/skill/scripts/unslop_text_scan.py`
- `unslop-ai-text/skill/references/tells.md`
- `unslop-ai-text/skill/references/writing-with-intent.md`

### Sections Subject To Review

The gate applies to generated narrative copy in:

- Executive Brief.
- Project Evolution narrative.
- Collaboration Profile.
- Decision Analysis.
- Confidence Assessment.
- Evidence Gaps.
- Investigation Assurance.

It should not scan raw evidence excerpts, source IDs, evidence references,
structured JSON, table mechanics, or internal metadata unless those fields are
rendered as reader-facing prose.

### Required Audit Sequence

1. Generate evidence-backed draft copy.
2. Run the deterministic unslop-text scanner against only the generated
   narrative sections.
3. Review scanner findings by severity and concentration.
4. Correct genuine default-language tells without changing factual meaning,
   evidence references, attribution, confidence, or uncertainty.
5. Perform a structural review that checks:
   - generic assistant boilerplate;
   - sycophantic or congratulatory openings;
   - "not just X, but Y" constructions;
   - unnecessary recap conclusions;
   - empty fluent language;
   - listicle scaffolding where prose would be clearer;
   - uniform sentence rhythm;
   - over-formal default voice;
   - over-corrected anti-AI voice;
   - manufactured casualness;
   - unsupported persuasive language.
6. Re-run the scanner.
7. Confirm that all remaining findings are either corrected or intentionally
   waived with a documented reason.
8. Validate that copy edits did not alter evidence claims.
9. Only then render the final report.

### Failure Behavior

High-severity unresolved findings block final Executive Report generation.

Medium- or low-severity findings may remain only when the wording is
intentional and documented. A waiver must name the finding, the affected
section, the reason for keeping the wording, and confirmation that the wording
does not change evidence, confidence, attribution, or uncertainty.

A clean scanner result does not by itself mean the copy is ready. Structural
review is mandatory.

The quality gate may simplify or rewrite presentation, but it must never
strengthen a claim, raise confidence, invent a milestone, infer decision
leadership, remove an uncertainty, or make unsupported persuasive claims.

If the quality pass cannot preserve evidentiary meaning, retain the original
evidence-backed wording and report the copy-quality warning.

### Runtime And Dependency Direction

Future implementation should:

- avoid calling GitHub at report-generation time;
- avoid requiring network access;
- pin a reviewed version or commit of the scanner;
- prefer a clearly attributed optional development dependency or a small
  compatible integration that respects the upstream MIT license;
- record the upstream repository and pinned revision;
- keep the copy audit deterministic;
- avoid silently rewriting findings using an LLM;
- store audit results in report metadata or generation logs;
- allow the final report to state that narrative copy passed the Workprint
  copy-quality review;
- never claim that scanner results prove the prose is human-authored.

Open implementation questions:

- Which exact upstream commit should Workprint pin?
- Should the scanner run as an optional development dependency, a vendored
  compatibility layer, or a separately packaged tool?
- What report metadata shape should record scanner findings, waivers, and
  pinned scanner revision?
- How should projects without the optional scanner dependency fail: hard stop,
  warning, or feature flag?

## 8. Investigation Assurance

### Purpose

Investigation Assurance gives readers a standard diligence statement. It should
make the report's method and limits easy to trust.

### User Question Answered

Why should I trust this report, and what exactly is it claiming?

### Required Inputs

- Evidence sources reviewed.
- Method summary.
- Evidence boundary.
- Attribution safeguards.
- Limitation summary.

### Required Outputs

- Canonical diligence statement.
- Clear statement that the report reflects captured evidence only.
- Clear statement that unsupported attribution is not inferred.
- Clear statement that narrative copy was reviewed for generic generated-writing
  patterns.
- Clear statement that copy-quality review does not determine human or AI
  authorship.
- Clear statement that wording edits do not change evidence, confidence, or
  attribution.

### Prohibited Content

- Legal conclusions.
- Claims that Workprint verifies facts outside the supplied evidence.
- Claims that absence of evidence proves absence of activity.

### Canonical Diligence Statement

> This Workprint report is an evidence-backed reconstruction based only on the
> sources supplied for investigation. Workprint normalizes captured evidence,
> extracts traceable observations, and summarizes project evolution,
> collaboration, decisions, confidence, and unknowns. The report does not infer
> authorship, ownership, effort, value, or contribution percentages. Narrative
> language was reviewed for generic generated-writing patterns, but that
> copy-quality review does not determine whether a human or AI authored the
> text. Wording edits do not change the underlying evidence, confidence, or
> attribution; every substantive claim remains traceable to evidence. When
> evidence is incomplete, unavailable, ambiguous, or unsupported, Workprint
> states that limitation rather than filling the gap with speculation.

This paragraph should appear in every future Workprint report, with minor
wording changes allowed only when needed for context.

## 9. Evidence Appendix

### Purpose

The Evidence Appendix lets a reader verify the report's claims.

### User Question Answered

Where can I inspect the evidence behind the conclusions?

### Required Inputs

- Observation IDs.
- Evidence references.
- Source files.
- Actor labels.
- Activity labels.
- Timestamps when available.
- Confidence or limitation flags when available.

### Required Outputs

- Observation index.
- Source file list.
- Evidence reference list.
- Compact statements tied to IDs.
- Optional mapping from report sections to evidence references.

### Prohibited Content

- Replacing the main report with raw evidence.
- Long source excerpts.
- Unbounded tables that make the report unreadable.
- Evidence without enough context to locate it.

### Example

| Observation | Source | Activity | Evidence |
|---|---|---|---|
| `obs-014` | ChatGPT | decision | `sample-conversations.json#message/abc` |
| `obs-022` | Figma | implementation | `sample-file.json#page/p1/node/n4` |

The appendix is not the story. It is the verification layer under the story.

## Writing Style Guide

### Prefer Human Explanations Over Labels

Instead of:

> Timeline Events: 14

Prefer:

> Workprint reconstructed fourteen significant project events.

Instead of:

> Unknowns: 3

Prefer:

> Three important questions could not be answered from the available evidence.

Instead of:

> Sources analyzed: 4

Prefer:

> Workprint reviewed four evidence sources: ChatGPT, Claude, Figma, and Google
> Docs exports.

Instead of:

> Confidence: Moderate

Prefer:

> Confidence is Moderate because the captured evidence shows the main project
> sequence, but does not include complete Git history or revision logs.

Instead of:

> User involvement: directed, reviewed.

Prefer:

> The captured evidence shows the user directing implementation scope and
> reviewing the resulting behavior.

Instead of:

> AI activity: implementation.

Prefer:

> AI/tool activity appears in implementation and test execution within
> user-defined constraints.

Instead of:

> Evidence gaps: missing Git.

Prefer:

> Workprint could not inspect Git history, so it cannot fully reconstruct
> file-level implementation sequence or code authorship.

### Keep Claims Bounded

Use:

- "The captured evidence shows..."
- "The available sources support..."
- "Workprint reconstructed..."
- "This appears to..."
- "The report cannot determine..."

Avoid:

- "This proves..."
- "The user owned..."
- "AI created..."
- "The project was mostly..."
- "The exact contribution was..."

### Make Confidence Explainable

Every confidence label should answer "why?"

Weak:

> Confidence: High.

Strong:

> Confidence is High because the decision is explicitly stated in the user's
> request and confirmed by the resulting output behavior.

### Put Evidence References Where They Help

Evidence references should be visible but not intrusive. Use them after the
claim or in compact supporting lists.

Example:

> The user appears to have led the decision to keep Git informational only.
> Evidence: `obs-032`, `obs-035`.

## Design Tenets

These tenets are canonical. Future report work should use them as product
principles, acceptance criteria, and review language.

1. Understanding over information

   Every section should increase the reader's understanding of the project.
   Supporting detail remains available, but it must not obscure the primary
   narrative.

2. Evidence before inference

   Every factual conclusion and attribution must be traceable to supplied
   evidence. Unsupported claims remain unknown.

3. Narrative before detail

   Explain what happened and why it matters before presenting counts, tables,
   IDs, or evidence indexes.

4. Transparency over false certainty

   Explain confidence, evidence strength, coverage, corroboration, conflicts,
   and gaps. Never use numerical precision to disguise weak evidence.

5. Human questions first

   Every report section must answer a question a reader naturally asks about
   the project.

6. Decision leadership, not contribution scoring

   Describe who appears to have initiated, directed, reviewed, approved, or
   decided work. Never translate activity into authorship, ownership, effort,
   value, or contribution percentages.

7. Separate human and AI activity

   Keep human-led, AI-led, joint, collaborator, and unattributed activity
   distinct. Do not collapse interaction into a single contribution score.

8. Trust is a product feature

   Explain how conclusions were reached, what evidence supports them, and why
   unsupported conclusions were withheld.

9. Plain language over system language

   Prefer reader-facing explanations over internal terms such as object counts,
   working trees, normalized messages, or pipeline state.

10. Deliberate voice over generated default

    Executive copy must sound like a specific investigator communicating
    findings to an intelligent nontechnical reader. It must not fall back to
    generic AI prose or an exaggerated "trying not to sound like AI" voice.

## Acceptance Criteria

A Workprint report succeeds when a reader who only reads the Executive Brief,
section headings, and conclusion can answer:

- What was this project?
- What was produced?
- How did it evolve?
- How did humans and AI collaborate?
- Which decisions mattered?
- How trustworthy is this report?
- What cannot be known?

From the reader's perspective, success means:

- The report is understandable without reading raw evidence first.
- The main story is clear within one minute.
- The evidence boundary is obvious.
- Major conclusions are traceable.
- Unknowns are visible and useful.
- Confidence is explained, not merely labeled.
- Human and AI activity are separated without unsupported attribution.
- The appendix makes verification possible.
- Executive narrative passes both lexical and structural copy review.
- The report contains no unresolved high-severity unslop-text findings.
- Copy review never changes substantive evidentiary meaning.
- Copy review results are reproducible and recorded.
- A clean scanner result is never presented as proof of human authorship.
- The report voice is direct, specific, and appropriate for an investigative
  briefing.
- The report avoids both generic AI prose and performative anti-AI prose.
- A Workprint web interface must look and behave like a deliberate expression
  of its investigative purpose, not like an untouched framework
  template or a generic AI-generated SaaS dashboard.

## Future Considerations

These ideas are intentionally out of scope for this specification, but may
become future product directions:

- Interactive reports.
- Visual timelines.
- Confidence visualizations.
- Git adapter and repository-history reconstruction.
- Live evidence connections.
- Source comparison views.
- Reader-specific report modes.
- Export to PDF or presentation formats.
- Evidence redaction workflows.
- Reviewer comments and approval flows.
- Side-by-side artifact evolution.
- Decision maps.

## Web Interface Design Guardrail

Future Workprint web interfaces must use the `unslop-ui` guidance and scanner
from
<https://github.com/JCarterJohnson/vibecoded-design-tells/tree/main/skill>.

The purpose is to prevent Workprint from falling back to generic AI-generated
interface patterns.

This requirement applies to web application screens, dashboards, report
viewers, onboarding, upload and investigation flows, timelines, confidence
displays, collaboration visualizations, and marketing or landing pages.

### Before Implementation

- Select a concrete visual reference or named design direction.
- Define Workprint's color choices and why they fit the product.
- Define typography choices and why they fit the product.
- Define the purpose, primary user task, and primary action of each screen.
- Base layout on the task rather than a generic SaaS template.
- Document major design decisions.

Avoid vague briefs such as:

- modern and clean;
- sleek;
- polished SaaS;
- professional dashboard.

The brief must be concrete enough that a contributor can explain why the
interface looks the way it does.

### During Implementation

- Review the upstream `SKILL.md`.
- Review `skill/references/tells.md`.
- Review `skill/references/choosing-a-look.md`.
- Treat Tailwind, shadcn, and similar libraries as implementation tools, not
  as Workprint's visual identity.
- Avoid untouched framework defaults.
- Avoid generic AI-generated patterns unless intentionally chosen and
  documented, including:
  - default purple or blue gradients;
  - gradient heading text;
  - decorative neon glow;
  - emoji used as interface icons;
  - centered hero plus three feature cards;
  - interchangeable dashboard card grids;
  - the cream, serif, and sage "tasteful default".
- Never replace one generic visual default with another.
- Preserve accessibility, evidence clarity, and usability over aesthetic
  novelty.

### UI Audit Gate

Before a web UI milestone is complete:

1. Run the pinned `devibe_scan.py` scanner against the frontend.
2. Review findings by severity.
3. Correct genuine default-design tells.
4. Record intentional exceptions and their rationale.
5. Re-run the scanner.
6. Perform a manual review for:
   - layout coherence;
   - visual hierarchy;
   - spacing consistency;
   - typography hierarchy;
   - responsive behavior;
   - overflow and truncation;
   - keyboard navigation;
   - contrast and accessibility;
   - clarity of evidence and confidence displays;
   - alignment with Workprint's investigative purpose.

### Failure Behavior

- Unresolved high-severity scanner findings block release.
- A clean scan does not mean the design is complete.
- Manual visual review is mandatory.
- Intentional exceptions require documented rationale.
- The audit must not claim the UI was human-designed.
- Fixes must use Workprint's chosen design language rather than substituting
  another fashionable default.

### Integration Direction

- Do not fetch the skill from GitHub during production builds.
- Pin a reviewed upstream commit.
- Preserve MIT attribution.
- Use a reproducible local or CI integration.
- Retain scanner results and waivers as build artifacts or audit logs.

Future work should preserve the principles in this document: lead with insight,
trace every conclusion to evidence, state uncertainty clearly, and never infer
unsupported authorship, ownership, effort, value, or contribution percentages.

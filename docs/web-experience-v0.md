# Web Experience v0 UX Specification

Status: Approved product contract
Scope: First web experience product contract
Milestone: First Five Minutes

This specification uses the approved "First Five Minutes" screen map as the
product contract, but collapses it into a simpler novice-facing experience.
It does not choose a frontend framework, visual design system, colors,
typography, or component library.

The design standard for this revision is: optimize for the simplicity of
Google's homepage rather than a traditional enterprise workflow. Complexity is
allowed in Workprint's engine. It is not allowed in the first experience.

## Product Frame

User problem: Workprint can investigate evidence, but a novice user should
not need to understand how Workprint works internally, how confidence is
assembled, or how command-line workflows behave to get a trustworthy first
report.

User story: A novice user can tell Workprint what the project is, add where
the work happened, wait while it investigates, understand what it discovered,
inspect why a claim is supported, and export a report.

UX story: The experience should feel like one calm page that grows only when
needed. The user should never feel like they are configuring a system. They
should feel like they are answering one simple question at a time.

Marketing story: See what you did, what AI did, and how the work came
together.

Smallest useful version: Define the simplified first web journey, major
screens, low-fidelity wireframes, states, disclosures, first-insight behavior,
evidence drill-down, export flow, usability risks, assumptions, and open
questions. Implementation, framework choice, visual styling, authentication,
live integrations, and new evidence sources wait.

Trust and usability risks:

- Users may expect Workprint to prove authorship, ownership, or effort.
- Users may interpret source counts, commit counts, or message counts as
  contribution percentages.
- Users may upload incomplete static exports and miss source limits.
- Users may trust a polished report before inspecting its evidence boundary.
- Users may not understand that "unknown" is a valid result.
- Users may abandon the flow if Workprint makes them stop on explanatory
  screens that could have been absorbed into the task.

Required product question: Does this help the user understand or demonstrate
what they did, what AI did, or how they worked together?

Answer: Yes. The redesigned flow keeps the user focused on project, work
history, investigation, and discoveries while preserving evidence boundaries,
unknowns, and traceable drill-down.

## Design Boundaries

This milestone should not:

- choose a frontend framework;
- choose colors, typography, icons, or a component library;
- write frontend code;
- add authentication or account management;
- add live third-party integrations;
- change evidence, attribution, confidence, or investigation rules;
- calculate human-versus-AI contribution percentages;
- imply that Workprint can prove authorship, ownership, effort, value, or
  complete project history.

## Simplicity Principles

- One guiding question per screen.
- One obvious primary action per screen.
- Disclosures appear beside the action they affect.
- Explanations appear only when they help the user make the next decision.
- Source guidance is contextual, not a separate lesson.
- Evidence review is a lightweight preview, not an inspection workflow.
- Advanced detail lives in expandable rows, drawers, or report sections.
- "Would Google, Apple, or Notion make the user stop here?" is the recurring
  simplification test.

Interface promise:

"See what you did, what AI did, and how the work came together."

Supporting trust copy:

"Workprint uses your project history to support every conclusion and clearly
marks what it cannot determine."

The user's mental model should always be:

```text
Tell Workprint about my project.
Add where the work happened.
Wait while it investigates.
Understand what it discovered.
```

## Collapsed Screen Model

The approved web v0 UX architecture has four primary screens:

| Major screen | Guiding question | Approved sequence absorbed |
| --- | --- | --- |
| 1. Start | What project should Workprint understand? | Landing, report purpose, project basics |
| 2. Add Where The Work Happened | Where did the work happen? | Add project evidence, upload and source guidance, evidence review, trust boundary |
| 3. Investigating | What is Workprint doing now? | Investigation progress |
| 4. Discoveries | What did Workprint find, and why should I believe it? | First insight, executive report, evidence drill-down, export |

No separate screen should exist only to explain implementation details. If a
screen does not help the user complete one of the four mental-model steps, it
should be removed, merged, or converted into progressive detail.

## Low-Fidelity Wireframe Legend

Wireframes are intentionally low fidelity. They show information priority and
interaction regions only.

```text
[Primary]      Primary action
[Secondary]    Secondary action
[Info]         Plain-language helper text
[Trust]        Disclosure beside the relevant action
[Panel]        Grouped content
[Detail]       Progressive disclosure
[Drawer]       Evidence drill-down
```

## Screen 1: Start

Guiding question: What project should Workprint understand?

```text
+--------------------------------------------------+
| Workprint                                        |
|--------------------------------------------------|
| See what you did, what AI did, and how the work  |
| came together.                                   |
|                                                  |
| What are you working on?                         |
| [____________________________________________]   |
|                                                  |
| [Primary: Add where the work happened]           |
| [Secondary: View a sample report]                |
|                                                  |
| [Detail: Add a project name or description]      |
|                                                  |
| [Detail: What Workprint can show]                |
+--------------------------------------------------+
```

- User goal: Start without learning Workprint internals.
- Primary action: Add where the work happened.
- Secondary action: View a sample report.
- Required information: One plain-language project prompt.
- Content hierarchy: Interface promise, one project prompt, primary action,
  optional details.
- Progressive disclosure: "What Workprint can show" expands to the four-part
  promise: what you contributed, what AI contributed, how you worked together,
  and what the evidence cannot determine. "Add a project name or description"
  lets the user refine report labeling later.
- Trust considerations: User-entered context is a label and framing aid, not
  evidence-backed fact; this note belongs inside optional detail, not as an
  early stop.
- Likely confusion points: User may think they need to prepare a formal report
  setup before seeing value.
- Success state: User gives Workprint enough context to continue.
- Failure state: Empty prompt; show a brief inline prompt and keep the user on
  the same screen.
- What should not appear: Internal architecture, source-reader names, report
  section inventory, confidence algorithms, pricing, dashboard navigation,
  contribution scores.

## Screen 2: Add Where The Work Happened

Guiding question: Where did the work happen?

```text
+--------------------------------------------------+
| Add where the work happened                      |
|--------------------------------------------------|
| [Drop files or choose a folder]                  |
|                                                  |
| Workprint can start with conversations, docs,    |
| designs, and repository history.                 |
|                                                  |
| [Panel: Added places]                            |
| Conversation export                Ready         |
| Google Docs export                 Limited       |
| Repository history                 Ready         |
| Unsupported file                   Needs action  |
|                                                  |
| [Trust beside scan results: Ready means readable |
|  evidence, not a complete project history.]      |
|                                                  |
| [Primary: Investigate]                           |
| [Secondary: Add another place]                   |
| [Detail: What these sources may miss]            |
+--------------------------------------------------+
```

- User goal: Give Workprint the places where the work happened and understand
  whether they can be used.
- Primary action: Investigate.
- Secondary action: Add another place.
- Required information: Upload affordance, supported examples,
  added material status, needs-action items, local trust note.
- Content hierarchy: Upload first, evidence preview second, trust note beside
  preview and investigation action.
- Progressive disclosure: "What these sources may miss" expands into source
  limits only for sources the user added. Static docs may omit revision
  history. Static designs may omit comments and contributor activity. Git
  records repository metadata, not proof of who wrote every line.
- Trust considerations: The action to investigate must sit beside the
  disclosure that Workprint reports only what the provided evidence supports.
- Likely confusion points: "Ready" may sound like "complete"; "limited" may
  sound like failure.
- Success state: At least one supported evidence source is ready; unsupported
  files are clearly removable or replaceable.
- Failure state: No supported evidence; keep the upload area visible and show
  one plain sentence about supported examples.
- What should not appear: A separate trust-boundary page, raw parser logs,
  first insight, executive report copy, implementation terms, unsupported
  live-service promises.

### Inline Trust Behavior

Trust disclosures should be attached to moments of action:

- Beside project description: "This labels the report; it is not proof."
- Beside upload: "Add places you are comfortable including in a
  report."
- Beside source status: "Ready means readable, not complete."
- Beside Investigate: "Workprint will report supported claims, source limits,
  and unknowns. It does not create contribution percentages."
- Beside Export: "Exports may include excerpts, file names, names, emails,
  metadata, and evidence references."

There should be no standalone trust page in v0. If the user would not expect
Google, Apple, or Notion to stop them on a separate explanation screen, the
disclosure belongs inline.

## Screen 3: Investigating

Guiding question: What is Workprint doing now?

```text
+--------------------------------------------------+
| Investigating                                    |
|--------------------------------------------------|
| Workprint is reading your project history.       |
|                                                  |
| Reading your project         [done]              |
| Finding important moments    [in progress]       |
| Preparing your discoveries   [pending]           |
|                                                  |
| [Trust: Workprint is organizing evidence, not    |
|  filling gaps with guesses.]                     |
|                                                  |
| [Secondary: Cancel]                              |
| [Detail: Show source progress]                   |
+--------------------------------------------------+
```

- User goal: Wait with confidence and understand that progress is happening.
- Primary action: None while running; move forward automatically when ready.
- Secondary action: Cancel.
- Required information: Current status, short reassurance, cancel option.
- Content hierarchy: Plain status sentence, three progress stages, trust note.
- Progressive disclosure: "Show source progress" reveals which evidence
  sources have been read without exposing logs.
- Trust considerations: Progress copy must reinforce that Workprint is not
  inventing missing evidence.
- Likely confusion points: User may think the system is writing a free-form AI
  story rather than deriving a report from evidence.
- Success state: Investigation completes and reveals discoveries.
- Failure state: Investigation fails inline with retry, remove problem source,
  or export evidence review options.
- What should not appear: Raw logs, model prompts, internal source-reader
  names, speculative early conclusions, long stage lists.

## Screen 4: Discoveries

Guiding question: What did Workprint find, and why should I believe it?

```text
+--------------------------------------------------+
| Discoveries                                      |
|--------------------------------------------------|
| [First supported insight dominates viewport]     |
|                                                  |
| [Plain-language claim]                           |
|                                                  |
| Why Workprint believes this                      |
| Supported by [sources]. Confidence: [band].      |
| What Workprint cannot determine: [limit].        |
|                                                  |
| [Secondary: See evidence]                        |
|                                                  |
| ---------------- continue to report ------------ |
|                                                  |
| [Primary: View full report]                      |
|                                                  |
| [Below the break: Report preview]                |
| What happened                                    |
| Human, AI, and joint activity                    |
| Decisions and timeline                           |
| Confidence and gaps                              |
|                                                  |
| [Secondary: Export report]                       |
| [Trust: Export includes evidence references and  |
|  source limitations by default.]                 |
+--------------------------------------------------+
```

- User goal: Understand the main discovery, read the report, inspect support,
  and export.
- Primary action: View full report.
- Secondary action: See evidence.
- Required information: First insight, support summary, confidence reason,
  unknown, report sections, evidence access, export action.
- Content hierarchy: First insight first, proof and limit immediately beside
  it, deliberate break, report preview, export.
- Progressive disclosure: The full report appears after a clear continuation.
  Evidence opens in a drawer. Export options open as a lightweight panel.
- Trust considerations: The first insight must show support and an unknown
  before the user reads the full report.
- Likely confusion points: User may overgeneralize the first insight or treat
  the report as complete project history.
- Success state: User can explain what Workprint found and trace a claim to
  evidence.
- Failure state: No sufficiently supported insight; show a "What Workprint
  could not determine yet" summary and let the user inspect limitations or add
  more places where the work happened.
- What should not appear: Dashboard grid layout, unsupported superlatives,
  global authorship claims, contribution percentages, hidden evidence
  references, editable rewriting of claims.

### First-Insight Reveal Behavior

The first insight should dominate the initial discoveries viewport. It should
not compete with a dashboard, report grid, export control, or secondary
metrics. Reveal it as one compact unit:

1. Claim: one plain-language sentence.
2. Why Workprint believes this: source types and evidence references
   summarized in human language.
3. Confidence: qualitative band with the shortest useful reason.
4. Unknown: the most important limit on the claim.

If no insight meets the support threshold, the discoveries screen should say:
"Workprint found evidence, but not enough to make a reliable first insight
yet." It should then show the strongest evidence gaps and offer Add where the
work happened or Export limitations.

The first insight must never be a global contribution ranking, authorship
claim, or unsupported project-quality judgment.

### Evidence Drill-Down Behavior

Evidence drill-down opens from claims in the discoveries screen and report
sections. It should appear as a drawer or inline panel, not a new workflow.

```text
+--------------------------------------------------+
| Discoveries                         [Drawer]     |
|------------------------------------|-------------|
| Claim in report                    | Why this?   |
|                                    |-------------|
|                                    | Source      |
|                                    | Evidence    |
|                                    | What it     |
|                                    | does not    |
|                                    | prove       |
|                                    | [Close]     |
+--------------------------------------------------+
```

The drill-down should show:

- the selected claim;
- the evidence references supporting or limiting the claim;
- source type and source label;
- timestamp or ordering information when supported;
- original excerpt or stable locator when available;
- what the evidence does not prove;
- whether the claim is measured, estimated, or unknown.

The drill-down should not transform metadata into attribution. For example,
Git author fields may be shown as Git-recorded metadata, but not as proof of
line authorship.

### Export Flow

Export should open from the discoveries screen as a small focused panel:

```text
+--------------------------------------------------+
| Export report                                    |
|--------------------------------------------------|
| [ ] Markdown report                              |
| [ ] JSON data for tools                          |
|                                                  |
| Included by default: evidence references, source |
| limitations, confidence, and unknowns.           |
|                                                  |
| [Trust: Exports may include excerpts, file names,|
|  names, emails, metadata, and evidence refs.]    |
|                                                  |
| [Primary: Export] [Secondary: Cancel]            |
+--------------------------------------------------+
```

Export must preserve evidence references and limitations. v0 should not allow
the user to export a report with trust disclosures removed.

## Shared Interaction States

### Loading States

- Upload: show file name and simple status: checking, ready, limited, or needs
  action.
- Project check: say "Checking what Workprint can read."
- Investigation: use three stages only: reading your project, finding
  important moments, preparing your discoveries.
- Export: say "Preparing your report with evidence references."

### Empty States

- Start without a project answer: "Tell Workprint what you are working on."
- No places added: "Add conversations, documents, designs, or repository
  history to begin."
- No supported places found: "Workprint did not recognize these files yet."
- No first insight: "There is evidence here, but not enough for a reliable
  first insight yet."
- No evidence for a claim: the claim should not appear as supported.

### Error States

- Unsupported file: "Workprint cannot read this file type yet."
- Unreadable file: "This file could not be read. Remove it or try another
  export."
- Duplicate source: "This appears to repeat evidence already added. Workprint
  will avoid counting exact duplicates twice."
- Investigation failed: keep uploaded evidence and offer retry, remove problem
  source, or export evidence review.
- Export failed: keep the report visible and offer retry.

## Privacy And Trust Disclosures

Disclosures should be short, local, and repeated only when relevant:

- Workprint uses the evidence the user provides for this investigation.
- Workprint reports only what the evidence supports.
- Static exports may omit revision history, comments, authorship, or deleted
  work.
- Git metadata records names and emails as stored in Git, but those values do
  not prove who wrote every line.
- Workprint does not calculate contribution percentages or productivity
  scores.
- Unknown is an honest result when evidence does not support an answer.
- Exported reports may contain source names, excerpts, metadata, file names,
  and evidence references.

## Novice-User Usability Risks

- "Evidence" may sound legalistic; use "where the work happened" in setup and
  keep "evidence" for trust explanations and report language where precision
  matters.
- "Contribution" may sound like a score; tie it to evidenced activity,
  decisions, direction, execution, review, and collaboration.
- "Unknown" may feel like failure; present it as honesty.
- "Repository history" is clearer than "Git" for many users.
- "JSON" needs a plain label such as "data for tools."
- Static export limitations may be missed unless shown beside the uploaded
  source.
- Evidence drill-down may overwhelm users if raw metadata appears first.
- The report can become intimidating if all sections expand at once.
- Too many acknowledgements will make trust feel like friction instead of
  clarity.
- The first insight can lose power if it appears beside too many report
  panels, controls, or metrics.

## Assumptions

- The first web experience uses existing Workprint investigation behavior as
  the evidence contract.
- The approved web v0 UX architecture has four progressive screens: Start,
  Add where the work happened, Investigating, and Discoveries.
- Uploaded evidence can be reviewed before investigation starts.
- The first insight can be chosen from already-supported investigation output
  without adding new inference.
- Markdown and JSON remain the initial export formats.
- v0 is local or bounded to user-provided evidence; live service connections
  are not assumed.

## Open Product Questions

- What deterministic threshold qualifies a first supported insight?
- Which source statuses should be shown to novices: ready, limited, needs
  action, and unsupported, or an even smaller set?
- Should folder upload be required for repository history, or deferred until
  implementation design?
- Should the sample report use synthetic evidence or Workprint dogfood
  evidence?
- How should the product label user-provided project context in exported
  reports?
- Should export allow users to exclude excerpts while keeping evidence
  references?
- What privacy model applies to uploaded files in the eventual web runtime:
  local-only, session-only upload, or stored projects?
- What recovery path should exist when an investigation succeeds but produces
  mostly unknowns?
- How should Workprint respond when users ask for a contribution percentage?

## Simplicity Acceptance Test

Before freezing the UX, each primary screen must pass these checks:

| Screen | Purpose in one sentence | One obvious next action | No technical term required | Details optional | Nothing removable without harm |
| --- | --- | --- | --- | --- | --- |
| Start | Tell Workprint what the user is working on. | Add where the work happened. | Yes. | Yes. | Yes. |
| Add Where The Work Happened | Give Workprint the places where the work happened. | Investigate. | Yes. | Yes. | Yes. |
| Investigating | Show that Workprint is reviewing the provided project history. | Wait for discoveries. | Yes. | Yes. | Yes. |
| Discoveries | Show the first supported insight and why Workprint believes it. | View full report. | Yes. | Yes. | Yes. |

If any screen fails one of these checks, simplify the screen before choosing a
framework, visual system, or component library.

## UX Review Through Three Lenses

### VP Of User Experience

This revision is much closer to a novice mental model. The user answers a
project question, adds where the work happened, waits, and reads discoveries.
The main risk is that the discoveries screen may carry too much weight; the
future design pass should make the first insight immediately understandable
and keep the full report calmly expandable.

### Product And Technical Partner

The simplified flow preserves Workprint's evidence boundaries because it
changes presentation, not investigation behavior. The dedicated trust screen
has been removed, but its safeguards remain next to the actions they govern.
The main unresolved implementation design question is the first-insight
selection rule.

### World-Class Marketer

The clearest story is now simpler: "See what you did, what AI did, and how
the work came together." That is more memorable than a setup wizard and still
careful enough not to promise authorship certification or contribution
scoring.

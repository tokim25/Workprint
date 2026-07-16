# Web Wireframes v0

Status: Approved wireframe direction
Purpose: Low-fidelity visual wireframes for the approved web v0 experience
Scope: Page structure, information hierarchy, interaction states, and
conceptual accessibility behavior

This document builds on the approved product contract in
`docs/web-experience-v0.md` and the approved visual direction in
`docs/visual-direction-v0.md`. It is a design-documentation milestone. It
does not choose a frontend framework, component library, fonts, color values,
icons, or implementation details.

## Product Contract

User problem: A novice user needs a simple way to understand what they
contributed, what AI contributed, and how the work came together without using
a terminal or understanding Workprint's internal architecture.

User story: As someone who built a project with AI, I want to add where the
work happened and quickly understand what I did, what AI did, and what we
shaped together.

UX story: The experience should feel calm, warm, personal, and obvious. Each
screen should ask one question and present one clear next action.

Marketing story: "See what you did, what AI did, and how the work came
together."

Smallest useful version: Create low-fidelity visual wireframes for the
approved four-screen experience:

1. Start.
2. Add where the work happened.
3. Investigating.
4. Discoveries.

## Design Constraints

Follow the approved Warm Investigator direction:

- recognition before analysis;
- warmth must never weaken precision;
- the user's work is the visual focus;
- first insights need generous space;
- evidence should feel close to claims;
- unknowns should feel honest;
- avoid dashboard grids;
- avoid wrapping every section in cards;
- use progressive disclosure instead of density;
- personal does not mean anthropomorphic.

The wireframes must not:

- write or imply frontend code;
- choose a framework;
- choose fonts, color values, icons, or a component library;
- expand beyond the approved four-screen flow;
- add authentication, live integrations, or new evidence/confidence rules;
- calculate contribution percentages;
- turn evidence support into authorship, ownership, effort, or value claims.

## Wireframe Legend

```text
[Primary]       Main action
[Secondary]     Supporting action
[Input]         User-entered text
[Upload]        File or folder selection area
[Status]        Plain-language state
[Trust]         Local evidence or privacy boundary
[Detail]        Optional progressive disclosure
[Drawer]        Evidence detail panel
[Panel]         Lightweight grouped region, not a heavy card grid
```

Layout notes:

- These are structure diagrams, not visual designs.
- Containers represent regions and reading order, not component choices.
- Copy is intentionally plain and may be refined before implementation.
- Desktop-first structure should collapse into a single-column mobile reading
  order without changing the four-screen flow.

## Screen 1: Start

Guiding question: What project should Workprint understand?

```text
+------------------------------------------------------------------+
| Workprint                                                        |
|                                                                  |
| See what you did, what AI did, and how the work came together.   |
|                                                                  |
| What are you working on?                                         |
| [Input: short project answer_______________________________]     |
|                                                                  |
| [Primary: Add where the work happened]                           |
| [Secondary: View a sample report]                                |
|                                                                  |
| [Detail: Add a project name or description]                      |
| [Detail: What Workprint can show]                                |
+------------------------------------------------------------------+
```

- User goal: Start without configuring a report or learning Workprint
  internals.
- Primary action: Add where the work happened.
- Secondary action: View a sample report.
- Layout regions: product name, promise, one project prompt, action row,
  optional details.
- Information hierarchy: promise first, prompt second, primary action third,
  optional details last.
- Progressive disclosure: Project name/description and "What Workprint can
  show" stay collapsed unless the user asks for them.
- Trust copy placement: Inside optional project detail: "This labels the
  report. Workprint will not treat it as proof."
- Empty state: If the input is empty, keep the user here and say, "Tell
  Workprint what you are working on."
- Error state: No technical error state should appear here; validation should
  be limited to missing prompt text.
- Success state: The user has given enough context to continue.
- Keyboard flow: Focus starts on the project input, then primary action,
  secondary action, optional detail controls. Enter from the input should
  activate the primary action when text is present.
- Likely novice-user confusion: The user may think they need a formal project
  title or report description before seeing value.
- What must not appear: Multi-field setup, internal architecture, source
  terminology, confidence mechanics, contribution scores, dashboard previews,
  visual branding exploration.

Simplicity test:

- One guiding question: yes.
- One obvious primary action: yes.
- No technical term required to proceed: yes.
- Supporting detail is optional: yes.
- Removing another element would make the next action less clear: yes.

## Screen 2: Add Where The Work Happened

Guiding question: Where did the work happen?

```text
+------------------------------------------------------------------+
| Add where the work happened                                      |
|                                                                  |
| [Upload: Drop files or choose a folder]                          |
|                                                                  |
| Workprint can start with conversations, docs, designs, and       |
| repository history.                                              |
|                                                                  |
| Added places                                                     |
|   Conversation export                            Ready           |
|   Google Docs export                             Limited         |
|   Repository history                             Ready           |
|   Notes.pdf                                      Needs action    |
|                                                                  |
| [Trust: Ready means readable evidence, not complete history.]    |
|                                                                  |
| [Primary: Investigate]                                           |
| [Secondary: Add another place]                                   |
| [Detail: What these sources may miss]                            |
+------------------------------------------------------------------+
```

- User goal: Add the places where work happened and understand whether
  Workprint can use them.
- Primary action: Investigate.
- Secondary action: Add another place.
- Layout regions: title, upload region, supported examples, added places
  list, local trust note, actions, source-limit detail.
- Information hierarchy: upload first, status list second, trust note beside
  the list, investigate action next.
- Progressive disclosure: "What these sources may miss" reveals only limits
  for added sources. Static docs may omit revision history; static designs may
  omit comments and contributor activity; repository history records metadata,
  not proof of who wrote every line.
- Trust copy placement: Directly below source statuses and above Investigate.
- Empty state: If nothing is added, show the upload region and "Add
  conversations, documents, designs, or repository history to begin."
- Error state: Unsupported or unreadable items appear inline in the added
  places list with remove or replace choices.
- Success state: At least one readable place is available and the Investigate
  action is enabled.
- Keyboard flow: Upload control, added-place rows, row actions, source-limit
  disclosure, primary action, secondary action. Rows with status details must
  be expandable by keyboard.
- Likely novice-user confusion: "Ready" may sound complete; "Limited" may
  sound like failure.
- What must not appear: A separate trust-boundary page, raw logs, parser
  language, first insight, report sections, unsupported live-service promises,
  dashboard grids.

Simplicity test:

- One guiding question: yes.
- One obvious primary action: yes.
- No technical term required to proceed: yes.
- Supporting detail is optional: yes.
- Removing another element would make the next action less clear: yes.

## Screen 3: Investigating

Guiding question: What is Workprint doing now?

```text
+------------------------------------------------------------------+
| Investigating                                                    |
|                                                                  |
| Workprint is reading your project history.                       |
|                                                                  |
| Reading your project                         Done                |
| Finding important moments                    In progress         |
| Preparing your discoveries                   Waiting             |
|                                                                  |
| [Trust: Workprint is organizing evidence, not filling gaps       |
|  with guesses.]                                                  |
|                                                                  |
| [Secondary: Cancel]                                              |
| [Detail: Show source progress]                                   |
+------------------------------------------------------------------+
```

- User goal: Wait with confidence and understand that Workprint is doing
  bounded work.
- Primary action: None while running; the screen advances automatically when
  discoveries are ready.
- Secondary action: Cancel.
- Layout regions: title, plain progress sentence, three progress stages, trust
  note, cancel action, optional source progress.
- Information hierarchy: current activity first, progress second, evidence
  boundary third.
- Progressive disclosure: "Show source progress" reveals per-source reading
  status only; no raw logs or internal process terms.
- Trust copy placement: Immediately under progress stages.
- Empty state: Not applicable once investigation begins; if no readable
  places exist, the user should remain on Screen 2.
- Error state: Investigation failure appears in place with a short reason and
  retry path.
- Success state: All stages complete and the user moves to Discoveries.
- Keyboard flow: During progress, focus should not jump unexpectedly. Cancel
  and optional source progress remain reachable. When discoveries load, focus
  should move to the first insight heading.
- Likely novice-user confusion: The user may think AI is creating a story
  beyond the evidence.
- What must not appear: Model prompts, logs, adapter names, technical
  pipeline stages, speculative interim findings, celebratory animation.

Simplicity test:

- One guiding question: yes.
- One obvious primary action: yes; wait for discoveries is the primary path.
- No technical term required to proceed: yes.
- Supporting detail is optional: yes.
- Removing another element would make the next action less clear: yes.

## Screen 4: Discoveries

Guiding question: What did Workprint find, and why should I believe it?

```text
+------------------------------------------------------------------+
| Discoveries                                                      |
|                                                                  |
| [First insight area: generous space]                             |
|                                                                  |
| You repeatedly set the direction.                                |
|                                                                  |
| Why Workprint believes this                                      |
| Workprint found multiple moments where your messages set         |
| constraints, requested revisions, or chose the next step.        |
| Confidence: Moderate                                             |
| Cannot determine: total authorship or contribution share.        |
|                                                                  |
| [Secondary: See evidence]                                        |
|                                                                  |
| ---------------- Continue to report ----------------             |
|                                                                  |
| [Primary: View full report]                                      |
|                                                                  |
| Report preview                                                   |
|   What happened                                                  |
|   Human, AI, and joint activity                                  |
|   Decisions and timeline                                         |
|   Confidence and gaps                                            |
|                                                                  |
| [Secondary: Export report]                                       |
| [Trust: Export includes evidence references and source limits.]  |
+------------------------------------------------------------------+
```

- User goal: Understand the first supported insight, inspect its evidence, and
  continue to the full report.
- Primary action: View full report.
- Secondary action: See evidence.
- Layout regions: discovery title, first insight area, support note, unknown,
  evidence action, continuation break, report preview, export action.
- Information hierarchy: claim first, evidence support second, unknown third,
  evidence drill-down fourth, report continuation fifth.
- Progressive disclosure: Evidence opens in a drawer. Full report appears
  after deliberate continuation. Export opens as a focused panel.
- Trust copy placement: "Why Workprint believes this" sits directly under the
  claim. Export trust copy sits beside export.
- Empty state: If no reliable first insight exists, show the no-insight
  state instead of a weak claim.
- Error state: If report continuation or export fails, keep the first insight
  visible and offer retry.
- Success state: User can explain the main finding and why Workprint believes
  it.
- Keyboard flow: Focus lands on the first insight heading, then support text,
  See evidence, View full report, report preview controls, Export report.
  Evidence drawer should trap focus while open and return focus to See
  evidence when closed.
- Likely novice-user confusion: The user may read "You repeatedly set the
  direction" as total authorship or contribution proof.
- What must not appear: Dashboard grid, contribution percentages, authorship
  certification, unsupported superlatives, report table above the first
  insight, hidden evidence references.

Simplicity test:

- One guiding question: yes.
- One obvious primary action: yes.
- No technical term required to proceed: yes.
- Supporting detail is optional: yes.
- Removing another element would make the next action less clear: yes.

## Focused State Wireframes

### File Or Folder Upload In Progress

```text
+------------------------------------------------------------------+
| Add where the work happened                                      |
|                                                                  |
| [Upload: Checking Workprint Project.zip]                         |
|                                                                  |
| Checking what Workprint can read...                              |
|                                                                  |
| Added places                                                     |
|   Workprint Project.zip                       Checking           |
|                                                                  |
| [Trust: Use places you are comfortable including in a report.]   |
|                                                                  |
| [Primary: Investigate disabled]                                  |
| [Secondary: Add another place]                                   |
+------------------------------------------------------------------+
```

Decision: The upload state should feel calm and bounded. It should not expose
file parsing logs or imply investigation has already begun.

### Recognized, Limited, And Unsupported Material States

```text
+------------------------------------------------------------------+
| Added places                                                     |
|                                                                  |
| Conversation export                         Ready                |
|   [Detail: Can show captured conversation activity.]              |
|                                                                  |
| Google Docs export                          Limited              |
|   [Detail: Static exports may not include revision history.]      |
|                                                                  |
| design-notes.pdf                            Needs action         |
|   Workprint cannot read this file type yet.                      |
|   [Secondary: Remove] [Secondary: Replace]                       |
|                                                                  |
| [Trust: Status describes readability, not completeness.]         |
+------------------------------------------------------------------+
```

Decision: "Limited" is not an error. Unsupported items need a direct recovery
choice without blocking readable sources.

### Investigation Failure And Retry

```text
+------------------------------------------------------------------+
| Investigating                                                    |
|                                                                  |
| Workprint could not finish this investigation.                   |
|                                                                  |
| One place could not be read. Everything else is still here.      |
|                                                                  |
| [Primary: Try again]                                             |
| [Secondary: Review added places]                                 |
| [Secondary: Export evidence review]                              |
|                                                                  |
| [Trust: Workprint has not changed your project files.]           |
+------------------------------------------------------------------+
```

Decision: Failure should preserve momentum and confidence. It should say what
happened, keep the user's work intact, and offer one clear recovery path.

### No Reliable First Insight

```text
+------------------------------------------------------------------+
| Discoveries                                                      |
|                                                                  |
| Workprint found evidence, but not enough for a reliable first    |
| insight yet.                                                     |
|                                                                  |
| What Workprint can say                                           |
| - These places were readable.                                    |
| - Some source limits reduce confidence.                          |
| - More project history may help.                                 |
|                                                                  |
| [Primary: Add where the work happened]                           |
| [Secondary: Export limitations]                                  |
| [Secondary: View evidence review]                                |
+------------------------------------------------------------------+
```

Decision: No-insight is a valid outcome, not a failure. The screen should
protect trust by refusing a weak first claim.

### First-Insight Evidence Drawer

```text
+------------------------------------------------------------------+
| Discoveries                                      | Why this?      |
|--------------------------------------------------|---------------|
| You repeatedly set the direction.                | Claim         |
|                                                  | You repeatedly|
| [First insight remains visible behind drawer]    | set the       |
|                                                  | direction.    |
|                                                  |               |
|                                                  | Evidence      |
|                                                  | Conversation  |
|                                                  | export        |
|                                                  | "Please keep  |
|                                                  | this focused  |
|                                                  | on..."        |
|                                                  |               |
|                                                  | What this     |
|                                                  | does not prove|
|                                                  | Total         |
|                                                  | authorship or |
|                                                  | contribution  |
|                                                  | share.        |
|                                                  |               |
|                                                  | [Close]       |
+------------------------------------------------------------------+
```

Decision: Evidence should feel close to the claim, like an annotation or
supporting note. The drawer should explain what the evidence does and does
not prove.

### Full-Report Continuation

```text
+------------------------------------------------------------------+
| Continue to report                                               |
|                                                                  |
| [Primary: View full report]                                      |
|                                                                  |
| The report keeps the same evidence boundaries and expands the    |
| first discovery into:                                            |
|                                                                  |
| What happened                                                    |
| Human, AI, and joint activity                                    |
| Decisions and timeline                                           |
| Confidence and gaps                                              |
| Evidence references                                              |
+------------------------------------------------------------------+
```

Decision: The report should feel like a continuation of the first insight,
not a dashboard replacing it.

### Export Panel

```text
+------------------------------------------------------------------+
| Export report                                                    |
|                                                                  |
| Choose format                                                    |
| [ ] Markdown report                                              |
| [ ] JSON data for tools                                          |
|                                                                  |
| Included by default                                              |
| Evidence references, source limitations, confidence, and         |
| unknowns.                                                        |
|                                                                  |
| [Trust: Exports may include excerpts, file names, names, emails, |
|  metadata, and evidence references.]                             |
|                                                                  |
| [Primary: Export]                                                |
| [Secondary: Cancel]                                              |
+------------------------------------------------------------------+
```

Decision: Export should preserve trust disclosures and evidence references.
The user should not be able to export a polished report with limitations
removed in v0.

## Desktop-First Responsive Considerations

- Desktop should use a centered content column with generous surrounding
  space, not a dashboard shell.
- The first insight should remain above the report preview at all viewport
  widths.
- Evidence drawer may appear beside the claim on wider screens and as a
  focused overlay or inline expansion on narrow screens, but it must preserve
  reading order and return focus correctly.
- Upload and source status rows should remain scannable without requiring
  horizontal scrolling.
- Report preview sections should stack vertically on smaller screens.
- Export panel should remain focused and short; it should not become a full
  settings page.

## Conceptual Accessibility Behavior

- Each screen should have one top-level heading matching the screen name.
- The guiding question should be reachable immediately after the heading.
- Primary and secondary actions should have explicit accessible names.
- Source status rows should expose both source name and status.
- "Limited" and "Needs action" must not rely on color alone.
- Progressive disclosure controls should expose expanded/collapsed state.
- Investigation progress should be announced politely, not repeatedly.
- Error messages should be associated with the relevant file, field, or screen
  state.
- Evidence drawer should trap focus while open, support Escape or Close, and
  return focus to the control that opened it.
- Motion should be reducible without losing state meaning.

## Major Interaction Decisions

- The first screen remains one prompt plus one primary action.
- "Add where the work happened" is the setup language; "evidence" is reserved
  for trust explanations and report support.
- The source review stays lightweight and local to upload.
- Investigation uses three novice-facing stages only: Reading your project,
  Finding important moments, Preparing your discoveries.
- The first insight gets generous space before the report appears.
- Evidence drill-down is adjacent to the claim and explains limits as well as
  support.
- The full report is a deliberate continuation, not the initial discoveries
  layout.
- Export keeps evidence references and source limitations included by default.

## UX/Product/Marketing Self-Review

### VP Of User Experience

The wireframes keep the novice path understandable: one question, one primary
action, and optional detail at each stage. The most important usability risk
is the Add Where The Work Happened screen: source statuses must be clear
without becoming a mini dashboard. The first insight is protected with space
and evidence support before report continuation.

### Product And Technical Partner

The wireframes preserve the approved four-screen architecture and do not add
new evidence sources, confidence rules, attribution rules, or implementation
choices. They keep Workprint's evidence boundary visible by placing support,
unknowns, and export disclosures near the relevant actions.

### World-Class Marketer

The benefit is immediately legible: "See what you did, what AI did, and how
the work came together." The first insight is the proof moment. Language is
plain and careful; it avoids claiming authorship, ownership, contribution
share, or project completeness.

## Unresolved Questions

- Should the first insight use a sample phrase in the interface, or should the
  production UI keep the claim area abstract until evidence is processed?
- Should evidence drill-down be a side drawer on desktop or an inline
  annotation by default?
- How much of the report preview should be visible before the user chooses
  View full report?
- Should "Export limitations" be available from the no-insight state as
  Markdown only, or as both Markdown and JSON?
- What exact source status labels should v0 use if testing shows "Limited" is
  misunderstood?
- How should the upload state communicate folder scanning without naming
  internal file recognition rules?

## Deviations From Approved Product Contract

None. This document preserves the approved four-screen architecture:

1. Start.
2. Add where the work happened.
3. Investigating.
4. Discoveries.

It does not choose implementation technology, visual branding, fonts, color
values, icons, component libraries, animation production, authentication,
live integrations, or new evidence/confidence rules.

# Decision Log

Status: Living document
Purpose: Records accepted enduring product and architectural decisions
Expected Update Frequency: Update when major product decisions change

This log records accepted architectural and product decisions that future
contributors should preserve unless the project deliberately revisits them.
Each entry uses the same structure: Context, Alternatives, Decision,
Consequences, and Status.

## Timeline Is Deterministic

Context: Workprint needs to reconstruct project evolution from normalized
observations while keeping the result explainable and testable.

Alternatives: Timeline generation could use an LLM or probabilistic clustering
to group observations into richer narrative events. It could also avoid
timeline generation entirely and leave readers with raw observations.

Decision: Timeline generation is deterministic. Observations are ordered by
timestamp, source, and ID. Related observations are grouped only when they
share conversation context, stage, and a close timestamp window. User
involvement is marked measured only when captured evidence directly supports
it.

Consequences: Timeline output is predictable, testable, and explainable. The
timeline may be less semantically rich than an AI-generated reconstruction,
but it does not hide grouping logic or attribution inference.

Status: Accepted.

## AI Reasoning Providers Require Explicit Upload Disclosure

Context: Workprint's local evidence handling and provider-assisted reasoning
have different privacy boundaries. Local file, Git, and local session evidence
can be read on the user's machine, while OpenAI, Claude, Gemini, Microsoft
Copilot, GitHub Copilot, or another reasoning provider needs selected evidence
to leave the device for processing. Dogfooding showed that local-only
heuristics do not produce the level of synthesis Workprint's product promise
requires.

Decision: Workprint treats provider-assisted reasoning as core functionality
and as a separate, explicit user action. The UI must disclose which provider
will process the evidence, that selected evidence will be sent to that
provider, what kinds of evidence are included, and that local collection is
only the input step. Reasoning providers may suggest candidate insights, but
Workprint must verify evidence IDs, preserve unknowns, and block unsupported
attribution, ownership, effort, contribution, intent, or human-versus-AI
claims before display.

Consequences: Workprint must avoid blanket privacy copy such as "nothing is
uploaded" once provider reasoning is available. Local collection copy may say
local preview/review does not upload evidence, but it must also explain that
real reasoning requires a chosen AI provider and a separate upload/process
boundary. OpenAI, Claude, and Gemini are the initial provider choices, offered
as an equal list rather than a single default the user must opt out of; all
three use the same bounded evidence-packet contract rather than custom,
provider-specific trust rules (see "Provider Choice Is Explicit, Not Defaulted
To One Vendor" below for why this replaced an earlier "OpenAI first" plan).

Status: Accepted.

## Provider Choice Is Explicit, Not Defaulted To One Vendor

Context: An earlier draft of the provider-reasoning direction (see
`docs/ai-reasoning-providers.md`'s original "Provider Order" section) named
OpenAI as the first reasoning provider, with Claude, Gemini, and the Copilots
following later on the same contract. The project owner corrected this: nudging
users toward a single default vendor is not the intended experience, even
temporarily.

Decision: From the first shipped version, the user picks which AI reasoning
provider processes their evidence packet -- there is no default vendor. The
initial provider list is OpenAI, Claude, and Gemini, presented as an equal
choice. The provider is selected per report, not as a one-time account-level
setting, since different reports may reasonably warrant different providers.
Workprint is bring-your-own-key (BYOK): the user supplies their own provider
account and API key. Workprint does not bill for, resell, or intermediate
provider access, which keeps the existing single-user, no-database,
no-accounts architecture intact rather than requiring new billing
infrastructure.

Microsoft Copilot and GitHub Copilot are explicitly deferred, not merely
lower-priority. Unlike OpenAI/Claude/Gemini, they are not simple API-key
integrations: GitHub Copilot is tied to a user's GitHub account and often an
employer's org settings, and Microsoft Copilot is tied to a Microsoft/Office
365 account and that organization's admin controls. Adding either is a
different kind of integration with a different privacy and access model, not
an additional entry in the same picker.

Consequences: Provider-selection UI must present OpenAI, Claude, and Gemini as
co-equal options, never a preselected or visually-favored default. Any future
Copilot/GitHub Copilot integration should be scoped and disclosed as its own
feature with its own access-model explanation, not folded into the existing
provider list as if it followed the same contract.

Status: Accepted.

## The Report's Primary Reader Is The Person Being Judged

Context: Workprint's reports could reasonably be written for two different
audiences: the person whose work is being reconstructed, or a third party
evaluating them (a manager, a client). Writing for one well can mean writing
for the other poorly -- a report performing confidence for an evaluator is not
the same document as an honest self-account.

Decision: The primary reader is the person who will be judged by the report,
not the outside evaluator. The report is an honest account of that person's
task delegation, how they described and guided the work, their discernment of
the AI's output and process, and the diligence they exercised using AI. A
single document serves both audiences because it is not written differently
for either -- honesty toward the primary reader is what makes the report
credible to a skeptical evaluator reading it secondhand.

Consequences: Report copy should be written in the second person, addressed to
the person who did the work, not in a third-person case-file register aimed at
an evaluator. No separate "manager view" or "client view" should be built;
one report, one voice.

Status: Accepted.

## The Report's Spine Is AI-Assisted Insight, With AI Fluency As A Lens

Context: Workprint has two candidate organizing structures for its report: the
general "turn project evidence into AI-assisted insights you can inspect"
product promise (`docs/foundation/PRODUCT_PRINCIPLES.md`), and the AI Fluency
Framework (Delegation/Description/Discernment/Diligence,
`src/workprint/ai_fluency.py`) built earlier this project.

Decision: The primary spine is the AI-assisted insight report. AI Fluency is a
lens the engine applies to evidence, not a competing report format or a
second, parallel report structure.

Consequences: AI Fluency evidence and the Playbook Worksheet remain real
features, but they are organized as a section/view within the one insight
report, not maintained as an alternative top-level report a user chooses
between.

Status: Accepted.

## Local-Only Mechanical Claim Generation Is Retired

Context: Before provider-assisted reasoning existed, `lib/active-discovery.ts`'s
`pickActiveDiscovery()` produced a mechanical fallback headline (e.g. "Git
records N commits between X and Y") when no richer claim was available.
Dogfooding confirmed this does not produce a viable insight -- it describes
Workprint's own process, not the work -- and provider-assisted reasoning is now
core, not an enhancement layered on top of a working local mode.

Decision: The mechanical fallback tier is retired outright rather than kept as
a lesser fallback. With no AI reasoning provider connected, the Discoveries
screen shows a distinct "connect an AI agent to see your first insight" state
-- it does not fall back to a weaker, locally-generated claim.

Consequences: `pickActiveDiscovery()`'s mechanical branches in
`lib/active-discovery.ts` should be removed rather than preserved as a
degraded path; only `pickExecutiveDiscovery()`'s real, provider-derived claim
(or the explicit no-provider-connected state) should reach the Discoveries
headline. Local evidence collection remains a real, useful step -- it prepares
the evidence packet a provider will reason over -- but it is not positioned as
delivering the product's core value on its own.

Status: Accepted.

## First Insight Must Analyze The Work, Never List Evidence

Context: An early example of a "good" first insight
(`docs/ai-reasoning-providers.md`'s original "Claim And Finding Examples"
section) read: "The project evidence describes an aggregated project made from
related prototypes, notes, and implementation records." On review, this is
itself a list of evidence artifacts (prototypes, notes, records) rather than
an insight about the work.

Decision: The first insight must never enumerate evidence sources, file types,
or categories. It must give a high-level understanding of one or more of: the
project, the process, the relationship between the AI agent and the user, or
the user themselves -- derived from analyzing the evidence, not describing the
evidence's shape. It reads like a headline: one plain sentence, 90-160
characters, sized so it can be taken in immediately. Every deeper finding in
the report body goes one level further into one or more of those same four
dimensions, backed by cited evidence.

Consequences: The stale "aggregated project... prototypes, notes, and
implementation records" example in `docs/ai-reasoning-providers.md` is
replaced with an example that analyzes one of the four dimensions instead of
listing artifacts. Any future claim-generation prompt or validation rule should
reject a candidate first insight that only enumerates what evidence exists.

Status: Accepted.

## The First Insight Is The Report's Headline, Not A Separate Screen

Context: The Discoveries screen (the first-payoff moment after connecting
evidence) and the fuller downloadable report could be built as two unrelated
experiences with two different claims, or as one experience where the first
insight leads into the same report.

Decision: The Discoveries screen's headline and the report's first insight are
the same claim, functioning as an "amuse-bouche" -- one high-level, evidenced
claim that invites the reader into the fuller report. The detailed report
carries an ordered list of deeper findings (the existing `findings` field in
`src/workprint/engine.py` and the multi-section executive report structure)
that each go deeper into one of the four dimensions from the first-insight
rule above.

Consequences: There is one first-insight claim, reused as both the
Discoveries headline and the report's opening line, not two independently
generated claims that could drift apart or contradict each other.

Status: Accepted.

## Unsupported Insight Is Collected In Evidence Gaps, Never Blocking

Context: A project may have connected evidence but no claim clears the bar for
a real, supported first insight (as observed directly: a real project's
evidence produced no explicit statement matching goal-detection patterns).

Decision: When there is no supported insight from any source, this does not
block or bury the rest of the report, and it is not scattered as caveats
throughout. Unresolved or unsupported items are collected at the end of the
report, in the existing Evidence Gaps section
(`docs/executive-report.md`), rather than a new section built for this case.

Consequences: A weak-evidence project still produces a complete, readable
report; the absence of a first insight is one clearly-labeled item in Evidence
Gaps, not nine consecutive "no/could not/did not" sentences standing in for a
headline.

Status: Accepted.

## AI Claim Validation Is A Four-Step Pipeline With A Reject/Rewrite/Hold Contract

Context: Provider-generated claims are untrusted output and need a defined
validation contract -- both what happens to an invalid claim, and how
validation is actually performed, given that a model auditing its own output
is a known blind spot.

Decision: Invalid provider claims are handled by exactly one of three
outcomes, chosen by failure type, not interchangeably:
- Missing or nonexistent evidence ID: reject outright.
- A claim citing real evidence but stronger than the evidence supports: rewrite
  down to what the evidence actually supports.
- A boundary violation (infers authorship, effort, ownership, contribution,
  intent, or human-vs-AI percentage): reject outright, never rewrite into an
  "unknown" -- softening a boundary violation into an unknown still frames the
  forbidden question as legitimate.
"Held for user review" is reserved for genuinely ambiguous cases (e.g.
disagreement between validation passes), not a catch-all for the other two
failure types.

Validation itself is a four-step pipeline: (1) deterministic checks on the
evidence packet going in (evidence-ID existence, a banned-pattern scan for
authorship/ownership/percentage language); (2) an AI pass that analyzes the
validated evidence and originates a candidate claim; (3) a second AI pass that
corroborates or revises that claim; (4) deterministic checks again on the
final claim text coming out of step 3, not only on the evidence that went in
-- since the two AI passes may share the same blind spot, AI-on-AI review is
never the only line of defense.

Consequences: Any provider-reasoning implementation must include both
deterministic passes (steps 1 and 4), not rely on the two AI passes alone to
police each other. The reject/rewrite/hold mapping must be implemented as
determined branches keyed to failure type, not a single generic
"invalid, discard" path.

Status: Accepted.

## Provider Failures Are Visible, Never A Silent Fallback

Context: With local-only mechanical claim generation retired, a provider
timeout, error, or quota failure has no lesser fallback tier to quietly drop
into.

Decision: Provider failure must surface as a visible, named error -- the
failure type is shown to the user, with retry or an explicit, labeled fallback
offered. It must never silently substitute a local mechanical claim or any
other unlabeled substitute.

Consequences: Provider-calling code must distinguish and surface failure types
(timeout, auth/quota error, malformed response) rather than collapsing them
into one generic error message, and the UI must not have a code path that
quietly falls back to `pickActiveDiscovery()`-style local claims now that that
tier is retired.

Status: Accepted.

## Provider Payloads Are Never Persisted

Context: Sending evidence to a third-party AI provider raises a real retention
question distinct from the disclosure-before-sending requirement already
established.

Decision: Workprint does not persist provider payloads (the evidence packet
sent, or the raw provider response) beyond the active session, and this is
stated to the user in plain, specific language alongside the packet-preview
and disclosure UI -- not just implied by omission. Example copy: "Workprint
doesn't keep what it sends. Close the app, and everything it shared with
[provider] is gone."

Consequences: No provider request/response logging or caching may persist
across app restarts without a future milestone explicitly approving it and
updating this decision.

Status: Accepted.

## Evidence Packet Ceiling Is 30,000 Tokens

Context: An unbounded evidence packet risks both cost (provider API pricing is
typically token-based) and the "smallest useful packet" principle already
established in `docs/ai-reasoning-providers.md`'s evidence-packet contract.

Decision: The evidence packet sent to a reasoning provider is capped at 30,000
tokens. Content cut to fit the ceiling should be surfaced as a named item in
the Evidence Gaps section rather than dropped silently.

Consequences: Packet-assembly code needs a token-counting and truncation step
before a provider call, not just a size-agnostic dump of all discovered
evidence. The exact truncation priority (source diversity vs. recency) is not
yet finalized -- source-diversity-first is the current recommendation -- and
should be confirmed before or during implementation, not assumed settled by
this entry alone.

Status: Accepted.

## Executive Report Is Derived From Investigation

Context: Workprint needs a reader-facing executive report that answers human
questions before detailed evidence tables, while preserving the existing
investigation model.

Alternatives: The Executive Report could be a separate investigation path, a
hand-authored narrative, or an LLM-generated summary over raw evidence.

Decision: The Executive Report is derived from the completed Investigation. It
is additive and does not change evidence extraction, observations, timeline
generation, or the core investigation model.

Consequences: Readers get a clearer report without weakening the evidence
pipeline. Executive copy is bounded by existing investigation data. The report
may be more conservative than a free-form narrative, but it remains traceable.

Status: Accepted.

## Confidence Uses Qualitative Bands

Context: Workprint needs to communicate how reliable a reconstruction is
without implying false numerical precision.

Alternatives: Confidence could be omitted, calculated as a numeric score, or
left to unsupported prose.

Decision: Confidence uses qualitative bands such as Very High, High, Moderate,
Limited, and Low. Each assessment should explain evidence strength, coverage,
corroboration, conflicts, and gaps.

Consequences: Confidence remains understandable and auditable. The system
avoids hidden scoring formulas and false precision, but contributors must keep
the rationale clear.

Status: Accepted.

## Contribution Percentages Are Intentionally Out Of Scope

Context: Human-AI collaboration reports create pressure to quantify how much
work was done by humans, AI tools, collaborators, or other actors.

Alternatives: Workprint could estimate contribution percentages from message
counts, tokens, commits, edit volume, or activity counts. It could also avoid
collaboration analysis entirely.

Decision: Workprint does not calculate human-versus-AI contribution
percentages. It does not convert counts into ownership, effort, value, or
authorship claims. It may report captured evidence events and involvement
classifications with clear caveats.

Consequences: Reports avoid false precision and unsupported attribution. Some
readers may want a simple score, but Workprint deliberately favors trust over
convenience.

Status: Accepted.

## Guided Workflow Orchestrates Existing Capabilities

Context: Workprint needs to become usable by people who do not know expert CLI
commands, while preserving established evidence behavior.

Alternatives: The guided workflow could implement its own discovery, import,
investigation, report, or attribution logic. It could also remain purely an
expert CLI product.

Decision: Guided Investigation orchestrates existing capabilities. It reuses
Project Discovery, translates selections into evidence inputs, and calls the
same multi-source investigation and report generation pipeline used by expert
commands.

Consequences: The workflow improves usability without forking evidence logic.
Bug fixes and evidence rules remain centralized. The current guided experience
is still terminal-based, so it is a step toward low-code/no-code rather than
the final form.

Status: Accepted.

## Static Exports Preserve Evidence Boundaries

Context: Google Docs and Figma static exports can be useful evidence, but they
do not contain full revision or authorship history.

Alternatives: Workprint could infer paragraph authorship, node authorship,
edit history, or contributor activity from file-level metadata. It could also
refuse static exports entirely.

Decision: Static exports are accepted as bounded evidence. Workprint preserves
document-level or file-level metadata, stable locators, and explicit content,
but it does not infer revision history, edit-by-edit authorship, contributor
activity, or node/paragraph authorship unless the evidence explicitly maps
those facts.

Consequences: Static exports become useful without being overstated. Reports
must clearly disclose their limits. Future richer adapters can add revision or
comment evidence when actual source data supports it.

Status: Accepted.

## Executive Copy-Quality Audit Uses A Pinned Upstream Scanner

Context: Executive Report v1 included copy-quality audit metadata with the
`unslop-text` upstream revision pinned, but the scanner was not yet integrated.
Completing the audit gate required using the upstream work without describing
the scanner, research, rules, or methodology as Workprint's original work.

Alternatives: Workprint could keep the audit unavailable, reimplement similar
rules without attribution, fetch upstream files at report-generation time, or
vendor a reviewed subset of the upstream project.

Decision: Workprint vendors the reviewed `unslop-text` scanner and references
from JCarterJohnson's `vibecoded-design-tells` project at pinned revision
`f7c4aefc2c797a66e55b49354a93917ab60d33ac`, preserves attribution and
licensing information through the MIT license and third-party notice, and wraps
the scanner in Workprint-owned integration code. Workprint adds deterministic
structural checks because lexical findings alone cannot assess overall writing
quality, plus evidence-preservation validation, Markdown disclosure, and
additive JSON metadata. The audit is documented as a writing-pattern review,
not an authorship detector.

Consequences: Report generation can run the lexical scanner offline and record
clear upstream attribution. Workprint owns the integration boundary and status
rules while preserving the upstream license and credit. Future audit changes
must continue to distinguish JCarterJohnson's upstream work from Workprint's
additions and must not imply endorsement.

Status: Accepted.

## Git Evidence Uses Local Read-Only Metadata

Context: Workprint needs repository activity evidence to support chronology,
implementation milestones, and evidence gaps without overstating what Git can
prove. Git records contain useful metadata, but they also include names,
email addresses, commit messages, file paths, and line-change counts that can
be misread as identity, authorship, effort, ownership, value, or productivity
signals.

Alternatives: Workprint could omit Git evidence, call the GitHub API, parse
`.git` internals directly, inspect file contents, or infer people and effort
from author fields and line counts.

Decision: Workprint uses a local-only Git adapter that invokes the installed
`git` command through a small read-only command boundary. The adapter records
repository and commit metadata, preserves Git-recorded author and committer
values exactly, and maps data into conservative observations. It does not use
network access, inspect file contents, mutate repositories, resolve identities,
or convert commit counts, file counts, additions, or deletions into
authorship, ownership, effort, value, productivity, or contribution measures.

Consequences: Git evidence can support implementation chronology, merge
milestones, completed-output evidence, and reduced Git-history gaps while
remaining traceable and deterministic. Bare repositories, remote-only history,
unrelated nested repositories, and file-content analysis are out of scope for
v1. Reports must disclose shallow history and preserve the distinction between
Git metadata and unsupported attribution.

Status: Accepted.

## Claude Desktop Chat's Optional Dependency Is Pinned, Not Name-Matched

Context: The Claude Desktop Chat adapter's deep-parse mode needed a library
that parses Chromium's undocumented IndexedDB-over-LevelDB format. A PyPI
package name ("chromium-reader") was assumed to be the pip-installable form
of a GitHub project actually researched (`cclgroupltd/ccl_chromium_reader`),
and declared as the optional dependency in `pyproject.toml` without
installing and running it. When a working Python 3.10+ environment later
became available, the assumption proved wrong: "chromium-reader" is an
unrelated package by a different author, with a confirmed bug in its own
global-metadata string decoding that silently drops every real IndexedDB
database record on real data. The correct library is not published on PyPI
under any name; it is only installable from its GitHub source.

Alternatives: Workprint could keep depending on the wrong PyPI package and
patch around its bug, pick a different, differently shaped library, or
declare the dependency directly against a pinned commit of the
verified-correct source.

Decision: The `claude-desktop-chat` optional dependency points at a pinned
commit of `cclgroupltd/ccl_chromium_reader` via a direct `git+https://`
reference, matching the precedent already set for the `unslop-text` upstream
integration (see "Executive Copy-Quality Audit Uses A Pinned Upstream
Scanner" above). Before any dependency is declared for a milestone going
forward, it must be installed and imported at least once, and its PyPI
project metadata, when applicable, cross-checked against the source actually
researched (see "External Dependencies Are Verified, Not Assumed" in
`ENGINEERING_PRINCIPLES.md`).

Consequences: The dependency now resolves to code that actually implements
the documented API. Pinning to a commit trades automatic upstream fixes for
reproducibility, matching how Workprint already treats other vendored or
pinned external code. This decision does not resolve whether deep parsing
can reliably recover real conversation content on a given machine; see the
Claude Desktop Chat adapter's own documentation for that separate, still-open
finding.

Status: Accepted.

## AI Fluency Reporting Uses Anthropic's Named Framework, With Attribution

Context: Workprint added a report section organizing existing evidence under
Anthropic's AI Fluency Framework (Delegation, Description, Discernment,
Diligence, developed with Prof. Rick Dakan and Prof. Joseph Feller). The
framework and its terminology are released under CC BY-NC-SA 4.0:
non-commercial use only, with required attribution to the authors, and any
derivative use of the framework's own materials must share alike.

Alternatives: Workprint could build its own, differently named categories
inspired by the same four-competency idea and avoid citing the framework at
all, or pause the feature until the framework's authors were contacted for
explicit permission.

Decision: Workprint uses the framework's official terminology directly, with
a visible attribution line (naming Dakan and Feller, and the CC BY-NC-SA
license) everywhere the section appears in a report. Workprint does not
reproduce the framework's own infographics or long-form materials, only its
short competency definitions restated in Workprint's own words, and it never
scores or rates fluency -- consistent with "Decision Leadership Over
Contribution Scoring" in `PRODUCT_PRINCIPLES.md`, this section only
reorganizes evidence Workprint already gathered for the user's own
reflection.

Consequences: Reports can use recognizable, well-documented terminology
instead of inventing parallel language, at the cost of a standing obligation
to keep attribution visible.

Update (2026-07-19): Workprint's own code is now open source under the
Apache License, Version 2.0 (see "Workprint Is Open Source Under the Apache
License, Version 2.0" below), which permits commercial use of Workprint's
code by anyone. This does not conflict with the condition originally noted
above: because Workprint restates the framework's competency definitions in
its own words rather than reproducing the framework's own materials
verbatim, CC BY-NC-SA's non-commercial and share-alike terms bind use of the
*framework's own materials* independently of whatever license Workprint's
code carries -- not Workprint's own commercial status. Anyone who forks
Workprint and reproduces the framework's own materials more substantially
than this attribution-only usage would need to independently comply with
CC BY-NC-SA's terms for that specific content, regardless of Workprint's
Apache license. See `NOTICE` for the attribution text.

Status: Accepted.

## Workprint Is Open Source Under the Apache License, Version 2.0

Context: Workprint was previously licensed "All Rights Reserved" (see the
prior `LICENSE` and `RIGHTS.md`), reflecting its earlier state as a private,
unreleased project. The project owner decided to make Workprint open source,
with two explicit requirements: standard liability protection if the
software doesn't produce the results a user expects, and a license that
would not conflict with the AI Fluency Framework's own CC BY-NC-SA 4.0
terms (see the decision above).

Alternatives: MIT License (simplest, most permissive; no patent grant or
retaliation clause, and no formal NOTICE-file convention) and GNU AGPL-3.0
(copyleft; requires anyone who modifies Workprint and runs it as a network
service to release their modified source, preventing a competitor from
building a closed-source product on top without reciprocity, at the cost of
being more restrictive and less commonly adopted).

Decision: Workprint is licensed under the Apache License, Version 2.0. All
three candidate licenses provide materially identical "AS IS, NO WARRANTY"
liability protection -- that requirement does not differentiate them. Apache
2.0 was chosen for three project-specific reasons: (1) its NOTICE-file
mechanism (Section 4(d)) is the established, expected place to carry the AI
Fluency Framework attribution, and matches the convention this project
already uses for its other vendored third-party code (see
`third_party/vibecoded-design-tells/NOTICE.md`); (2) its explicit patent
grant and patent-retaliation clause offer real protection that MIT lacks,
relevant for a project building AI tooling; (3) it is the more commonly
required default for company-scale adoption or contribution. The top-level
`NOTICE` file carries the AI Fluency Framework attribution and points to
`third_party/vibecoded-design-tells/NOTICE.md` for the vendored MIT-licensed
scanner.

Consequences: Workprint's source is now genuinely open (anyone may use,
modify, or commercialize it, consistent with the Open Source Definition),
with the standard Apache warranty disclaimer and liability limitation
protecting the project owner. `LICENSE`, `NOTICE`, `RIGHTS.md`,
`README.md`, `package.json`, and `pyproject.toml` were all updated together
so no file contradicts another about Workprint's licensing status.

Status: Accepted.

## The Packaged App's Production Server Binds To Loopback Only

Context: A structured architecture review of the packaged Electron app
(failure domains, scalability, data, security, operations, cost,
complexity) found that `electron/main.js`'s `startProductionServer()`
never set `HOSTNAME`, so Next's standalone `server.js` fell back to its
own default of `0.0.0.0` -- binding `/api/investigate`,
`/api/git-summary`, and `/api/claude-local-summary` to every network
interface on the machine, not just loopback.

Decision: Set `HOSTNAME: "127.0.0.1"` explicitly alongside `PORT` in the
production server's spawn environment. Verified with `lsof -iTCP:3820
-sTCP:LISTEN` against a real packaged build, confirming the bind changed
from a wildcard to `127.0.0.1:3820`.

Consequences: Any other device on the same network could previously have
issued a direct HTTP request naming an arbitrary local path and had
Workprint read that path's git history, Claude session data, or project
files and return the result -- no CORS bypass needed, since these are
plain server endpoints, not browser-mediated requests. That surface is
now closed by default. The same review pass also fixed adjacent gaps
found alongside it: temp investigation files are now written 0600
instead of inheriting the default (often world-readable) umask; a
missing `app.requestSingleInstanceLock()` meant a second launch silently
hung for 30 seconds before quitting with no explanation; there was no
handler for the production server child exiting mid-session; `server.log`
had no size cap; and the `BrowserWindow` had no `will-navigate` guard
against evidence content ever containing a link. See
`docs/desktop-app.md`'s "Hardening Pass" section for verification detail
on each.

Status: Accepted.

# AI Reasoning Providers

Status: Product and engineering direction
Purpose: Defines the provider-assisted reasoning model for Workprint
Expected Update Frequency: Update when reasoning providers or provider terms change

Workprint's core experience depends on AI-assisted reasoning over bounded,
traceable project evidence. Local collection prepares evidence; a chosen AI
provider helps synthesize that evidence into candidate insights; Workprint
then verifies boundaries before anything becomes a user-facing finding.

## Product Position

Workprint is not a local-only heuristic dashboard. Local-only evidence review
can preview what Workprint found, but it does not produce the level of
synthesis the product promise requires.

The intended experience is:

1. The user tells Workprint what they are working on.
2. The user adds where the work happened.
3. Workprint prepares a bounded evidence packet.
4. The user chooses an AI reasoning provider.
5. Workprint sends selected evidence to that provider for reasoning.
6. Workprint validates provider output against evidence IDs and product
   boundaries.
7. The user sees supported insights, unknowns, and evidence drill-downs.

## Provider Order

There is no default provider. The user chooses which AI reasoning provider
processes their evidence packet, every time -- Workprint must never nudge
toward, preselect, or visually favor one provider over another.

The initial provider list, presented as an equal choice: OpenAI, Claude, and
Gemini. All three use the same evidence-packet and output contract described
below; none is a special case.

The provider is chosen per report, not as a one-time account-level setting --
different reports may reasonably call for different providers.

Microsoft Copilot and GitHub Copilot are explicitly deferred, not merely
lower-priority in the same list. They are not simple API-key integrations the
way OpenAI, Claude, and Gemini are: GitHub Copilot is tied to a user's GitHub
account and often an employer's org settings; Microsoft Copilot is tied to a
Microsoft/Office 365 account and that organization's admin controls. Adding
either is a distinct integration with its own access model and its own
disclosure language -- not an additional entry that follows the same BYOK
contract as the first three providers. Scope and disclose them as a separate
future feature when they're built, rather than implying today that they
already fit the same picker.

## Evidence Packet Contract

The evidence packet should be the smallest useful packet for reasoning, and is
capped at 30,000 tokens. Content cut to fit the ceiling must be surfaced as a
named item in the Evidence Gaps section, not dropped silently. (Truncation
priority -- source diversity vs. recency -- is not yet finalized;
source-diversity-first is the current recommendation.)

It may include:

- evidence IDs;
- selected excerpts;
- source labels;
- file names and relative paths;
- timestamps;
- commit hashes and commit metadata;
- line counts and byte sizes;
- Workprint-generated unknowns and limitations.

It must not include:

- the whole project folder;
- unrestricted filesystem access;
- hidden files unless explicitly allowed by a future milestone;
- credentials, secrets, tokens, certificates, private keys, or environment
  files;
- blocked sensitive files;
- files the user did not select;
- file contents outside Workprint's allowlist and limits.

## Provider Output Contract

Providers should return structured candidate findings, not final authority.

Each candidate finding should include:

- a claim, written as one plain sentence between 90 and 160 characters when it
  is the first supported insight;
- supporting evidence IDs;
- a short explanation of why the evidence supports the claim;
- an evidence-linked finding that analyzes the work pattern and helps the user
  understand the role they and the AI agent appear to have played;
- confidence language;
- unknowns and limitations;
- any provider-side uncertainty.

Invalid provider output is handled by exactly one of three outcomes, chosen by
failure type -- these are not interchangeable:

- **Reject outright** when a claim lacks evidence IDs, cites evidence IDs that
  do not exist in the sent packet, or infers authorship, effort, ownership,
  value, contribution, importance, intent, or human-versus-AI percentages. A
  boundary violation is rejected, never rewritten into an "unknown" --
  softening it that way still frames the forbidden question as legitimate.
- **Rewrite down** when a claim cites real, valid evidence but is stronger than
  that evidence supports (e.g. states AI involvement is proven when the
  evidence only shows AI participation). Rewrite to what the evidence actually
  supports rather than discarding a partially-valid claim.
- **Hold for user review** only for genuinely ambiguous cases -- for example,
  disagreement between the two validation passes below -- not as a catch-all
  for the other two failure types.

Validation is a four-step pipeline, not a single pass: (1) deterministic
checks on the evidence packet going in (evidence-ID existence, a banned-pattern
scan for authorship/ownership/percentage language); (2) an AI pass that
analyzes the validated evidence and originates a candidate claim; (3) a second
AI pass that corroborates or revises that claim; (4) deterministic checks
again on the final claim text coming out of step 3, not only on the evidence
that went in. Step 4 exists because the two AI passes may share the same blind
spot -- AI-on-AI review must never be the only line of defense.

## Claim And Finding Examples

The first supported insight should be specific, plain-language, and compact:
one sentence, 90-160 characters. It must analyze the work -- the project, the
process, the relationship between the user and the AI agent, or the user
themselves -- not describe what evidence exists or what shape it takes. A
claim that only names evidence sources or file types (however precisely) is
not an insight, even if it is accurate and well-supported; it is a table of
contents. Every deeper finding in the report body goes further into one of
those same four dimensions, backed by cited evidence.

Good first insight:

"The user set direction repeatedly, narrowing the AI agent's early proposals
into the final four-screen flow."

Too vague:

"Workprint found evidence."

Too long:

"The user appears to have set the overall direction for the project across
many different moments captured in the evidence, including narrowing scope,
rejecting several early proposals from the AI agent, and approving specific
implementation choices, though this pattern is not confirmed in every evidence
source and some observations remain ambiguous or incomplete."

An artifact list, not an insight (do not use, even though it may be accurate):

"The project evidence describes an aggregated project made from related
prototypes, notes, and implementation records."

Evidence-linked findings should analyze the work rather than list artifacts.
They should help the user understand how the work came together and what role
the user and AI agent appear to have played, while staying inside evidence.

Allowed claim patterns:

- "The supplied files describe an aggregated project assembled from related
  prototypes, project notes, and repository activity."
- "The evidence shows a sequence from direction-setting to implementation,
  with notes preceding repository changes."
- "The captured user turns define constraints and acceptance criteria."
- "The captured assistant turns propose implementation structure and wording."
- "The AI agent appears in the evidence as a synthesis partner because captured
  assistant turns propose structure and next steps."
- "The user appears to have directed the work when they approved the four-screen
  flow and rejected additional setup complexity."
- "Git records commits after the planning notes, but Git does not prove who
  personally wrote the changed lines."
- "The evidence shows AI participation in the conversation, but not whether AI
  generated the final files."
- "The supplied evidence supports a collaboration pattern, not a contribution
  percentage."
- "The evidence shows review or correction when the user rejects, revises, or
  narrows an assistant proposal."

Avoid:

- "You did most of the work."
- "AI created these files."
- "This proves authorship."
- "More changed lines means more effort."
- "The project is complete."
- "The AI agent was responsible for implementation" unless the evidence
  directly supports that exact narrow role.

## User Disclosure

The UI must say, near the action that starts reasoning:

- which provider will process the evidence;
- selected evidence will be sent to that provider;
- provider processing is governed by the selected provider's terms, policies,
  and account settings;
- Workprint sends a bounded evidence packet, not the whole project folder;
- the user should confirm they have permission to process the selected
  evidence with that provider.

This cannot live only in documentation. It must be visible in the product
before reasoning begins.

## Licensing And Permission Boundary

Workprint is licensed under Apache-2.0. That license covers the Workprint
software. It does not grant rights to upload project evidence to an AI
provider.

Users may have separate obligations based on:

- employer policy;
- client agreements;
- contractor agreements;
- NDAs;
- copyright licenses;
- open-source licenses;
- data-processing agreements;
- provider account terms;
- industry or regional privacy rules.

Workprint should not provide legal advice. It should make the upload and
licensing boundary explicit enough that users know when they need permission
before using provider-assisted reasoning.

## Marketing Language

Preferred:

"Turn project evidence into AI-assisted insights you can inspect."

Supporting:

"Workprint gathers the evidence, sends selected evidence to the AI reasoning
provider you choose, and keeps every insight tied to what the evidence can
support."

Avoid:

- "Nothing is uploaded."
- "Fully local insights."
- "Private by default" without explaining provider processing.
- "The AI verified your work."
- "AI detected what you contributed."
- "Workprint proves authorship."

## Implementation Notes

The initial milestone should add OpenAI, Claude, and Gemini behind the same
stable reasoning interface together, presented as an equal choice -- not one
provider shipped first with the others deferred as follow-on work. No
provider's behavior should be hard-coded into the UI or investigation engine
in a way that makes any of the three a special case, or that makes adding
Microsoft Copilot or GitHub Copilot later harder than it needs to be.

The first provider implementation should include:

- explicit user confirmation;
- a visible evidence-packet preview;
- server-side packet limits;
- structured provider output;
- evidence-ID validation;
- unsupported-claim rejection;
- safe provider error handling;
- no persistence of provider payloads beyond the active session unless a
  future milestone explicitly approves it.

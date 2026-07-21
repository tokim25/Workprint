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

OpenAI is the first reasoning provider.

Future providers should use the same contract:

- Claude
- Gemini
- Microsoft Copilot
- GitHub Copilot

Microsoft Copilot and GitHub Copilot should be treated as separate provider
families. Microsoft Copilot may involve Microsoft 365 account data and tenant
controls. GitHub Copilot may involve repository, IDE, pull request, or GitHub
account context. Workprint should not imply they share the same access model,
privacy model, licensing terms, or evidence availability.

## Evidence Packet Contract

The evidence packet should be the smallest useful packet for reasoning.

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

Workprint should reject or downgrade provider output when:

- a claim lacks evidence IDs;
- evidence IDs do not exist in the sent packet;
- the claim infers authorship, effort, ownership, value, contribution,
  importance, intent, or human-versus-AI percentages;
- the claim says AI involvement is proven when the evidence does not prove it;
- the provider omits important unknowns;
- the claim is stronger than the cited evidence.

## Claim And Finding Examples

The first supported insight should be specific, plain-language, and compact:
one sentence, 90-160 characters. It should describe the most useful
evidence-supported pattern, not the whole report.

Good first insight:

"The project evidence describes an aggregated project made from related
prototypes, notes, and implementation records."

Too vague:

"Workprint found evidence."

Too long:

"The project evidence describes a multi-phase body of work made from several
related prototypes, multiple implementation notes, source records, and planning
artifacts that may have involved AI collaboration but also includes many
unknowns."

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

The first OpenAI milestone should add the provider adapter behind a stable
reasoning interface. It should not hard-code OpenAI behavior into the UI or
investigation engine in a way that makes Claude, Gemini, Microsoft Copilot, or
GitHub Copilot special cases later.

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

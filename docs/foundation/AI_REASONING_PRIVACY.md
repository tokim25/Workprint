# AI Reasoning Privacy

Status: Foundation guide
Purpose: Defines privacy, trust, and licensing boundaries for AI reasoning providers
Expected Update Frequency: Update when Workprint adds or changes reasoning providers

Workprint uses AI reasoning providers to synthesize evidence into clearer
insights. Local evidence collection is the input layer; provider-assisted
reasoning is the core analysis layer. The product must not blur the privacy,
licensing, or trust boundary between those layers.

## Core Boundary

Local evidence collection and AI reasoning are separate user actions with
different privacy consequences.

Workprint can read selected local evidence on the user's machine. That local
reading does not by itself authorize Workprint to send evidence to OpenAI,
Claude, Gemini, Microsoft Copilot, GitHub Copilot, or any other reasoning
provider.

If the user chooses an AI reasoning provider, Workprint sends a bounded
evidence packet to that provider for processing. The product must say this
plainly before the provider is used.

## Required User Disclosure

Before provider-assisted reasoning begins, the interface must disclose:

- which provider will process the evidence;
- that selected project evidence will leave the user's device;
- what kinds of evidence are included;
- that Workprint sends bounded excerpts and metadata, not unrestricted project
  folder access;
- that the provider's processing is governed by that provider's terms,
  policies, and account settings;
- that local collection by itself is not the full reasoning experience.

This disclosure should appear beside the action that starts provider
reasoning. It should not be hidden in a general privacy page or a one-time
onboarding step.

## Evidence Packet Limits

AI reasoning providers should receive the smallest useful evidence packet.

The packet may include selected evidence excerpts, evidence IDs, source labels,
file names, relative paths, timestamps, commit metadata, line counts, and
Workprint-generated unknowns or limitations.

The packet must not include unrestricted filesystem access, full project
folders, hidden files, blocked sensitive files, credentials, private keys,
tokens, certificates, environment files, or file contents outside the user's
explicit selection and Workprint's allowlist.

## Provider Role

AI providers may suggest candidate insights. Workprint remains responsible for
deciding what can be displayed.

Provider output must be treated as untrusted until Workprint verifies that:

- every displayed claim cites supplied evidence IDs;
- the claim does not violate attribution, authorship, ownership, effort,
  contribution, or AI-involvement boundaries;
- the claim preserves important unknowns;
- the user can inspect the supporting evidence.

An unsupported provider claim is rejected outright (missing/invalid evidence
IDs, or any attribution/ownership/effort/contribution/intent/human-vs-AI
boundary violation -- never softened into an "unknown," which would still
treat the forbidden question as legitimate), rewritten down to what the cited
evidence actually supports (a claim stronger than its evidence), or held for
user review (genuinely ambiguous cases only). See
`docs/ai-reasoning-providers.md`'s "Provider Output Contract" for the full
mapping. Claims should not silently become Workprint findings.

## Licensing And Terms Boundary

Workprint's Apache-2.0 license covers the Workprint software. It does not
grant the user rights to upload third-party, employer-owned, client-owned,
confidential, proprietary, copyrighted, or regulated project evidence to an AI
provider.

Before provider-assisted reasoning, the product and documentation must make
clear that:

- the user is responsible for confirming they are allowed to process selected
  evidence with the chosen provider;
- provider processing is governed by that provider's terms, data-use policies,
  account settings, retention controls, and enterprise agreements;
- Workprint cannot guarantee that a provider's license terms match the user's
  obligations to clients, employers, collaborators, or source owners;
- generated reasoning output may be subject to provider-specific terms;
- third-party frameworks, examples, or licensed source material included in
  evidence may carry separate attribution or reuse obligations.

Workprint should not give legal advice. It should make the boundary visible
and avoid language that implies provider upload is automatically permitted.

## Product Language

Acceptable language:

- "Analyze with OpenAI."
- "Selected evidence will be sent to OpenAI for reasoning."
- "Workprint sends a bounded evidence packet, not your whole project folder."
- "Local collection prepares evidence; provider reasoning processes selected
  evidence with the AI provider you choose."
- "OpenAI helped synthesize this from the evidence shown below."
- "Make sure you have permission to process this evidence with the selected
  provider."

Avoid:

- "Nothing is uploaded" when provider reasoning is available or enabled.
- "Private by default" without explaining the provider boundary.
- "AI discovered" without naming the provider and showing evidence.
- "The AI verified" when Workprint only received a model response.
- Any claim that a provider determined authorship, ownership, effort,
  contribution, intent, or human-versus-AI percentages.

## Local Collection Mode

Local collection mode is a privacy-aware input step, not a lesser version of
the core product. It previews what evidence Workprint can see and prepares the
bounded evidence packet a provider will reason over.

Local-only mechanical claim generation is retired, not merely de-emphasized.
Without a connected AI reasoning provider, Workprint does not generate a
first insight or finding of any quality -- there is no downgraded local
fallback claim to fall back to. The Discoveries screen instead shows a plain
"connect an AI agent to see your first insight" state. Do not use language
implying a local-only path still produces limited-but-real insights ("insight
quality will be limited"); the accurate statement is that no insight is
produced until a provider is connected.

## Reasoning Provider Expansion

There is no default provider, including at first launch. The user chooses
which AI reasoning provider processes their evidence, per report, from an
equal-choice list -- Workprint must never preselect or visually favor one.

The initial list is OpenAI, Claude, and Gemini, all using the same
bounded-evidence-packet contract. Workprint is bring-your-own-key: the user
supplies their own provider account and API key, and Workprint does not bill
for or intermediate provider access.

Microsoft Copilot and GitHub Copilot are explicitly deferred as a separate,
later feature, not merely lower-priority entries in the same list. They are
not simple API-key integrations: Microsoft Copilot is tied to a Microsoft/
Office 365 account and that organization's admin controls, and GitHub
Copilot is tied to a user's GitHub account and often an employer's org
settings. Workprint should expose those differences plainly instead of
pretending all providers have the same evidence access, privacy model, or
account controls -- and should not imply, before that work is built, that
Copilot/GitHub Copilot fit the same picker as the first three providers.

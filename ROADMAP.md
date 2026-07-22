# Roadmap

## Completed Foundation

### v0.3.0 — ChatGPT vertical slice

- [x] ChatGPT export reader
- [x] Normalized messages
- [x] Canonical observations
- [x] Investigation engine
- [x] Markdown and JSON reports
- [x] CLI
- [x] Tests

### v0.4.0 — Claude and multi-source support

- [x] Claude export reader
- [x] Shared `EvidenceAdapter` contract
- [x] Adapter registry
- [x] Shared multi-source investigation command
- [x] Exact, source-aware duplicate suppression for repeated evidence inputs

## Active Capability — Timeline Report

Status: Complete

Goal: Generate a chronological, evidence-linked account of how a project
developed, including the investigated user's involvement at every stage.

This capability is additive. Existing import, investigation, report, and
multi-source commands remain compatible, and existing findings remain
available.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for requirements and acceptance criteria.

## Active Capability — Google Docs Adapter

Status: Complete

Goal: Import Google Docs revision and document evidence into Workprint's
normalized evidence pipeline.

See [docs/google-docs-import.md](docs/google-docs-import.md) for supported
formats and static-export limitations.

## Active Capability — Figma Adapter

Status: Complete

Goal: Import Figma design activity evidence without adding source-specific
logic to the investigation engine.

See [docs/figma-import.md](docs/figma-import.md) for supported schema,
metadata handling, and static-export limitations.

## Active Capability — Report Visual Design and Shareability

Status: Complete

Goal: Improve report presentation so outputs are polished, readable, and easy
to share with nontechnical audiences.

## Active Capability — Project Discovery

Status: Complete

Goal: Preview supported evidence in a project directory before import or
investigation.

See [docs/project-discovery.md](docs/project-discovery.md) for command usage,
supported evidence, and limitations.

## Active Capability — Guided Investigation Wizard

Status: Complete

Goal: Guide users from discovered evidence through source selection,
readiness review, and investigation setup without requiring command-line
knowledge.

See [docs/guided-investigation.md](docs/guided-investigation.md) for the
guided workflow, selection syntax, output behavior, and limitations.

## Active Capability — Claude Session Evidence Discoveries UI

Status: Complete

Goal: Surface local Claude Code, Cowork, and Desktop Chat evidence (Tiers
1a-1c) in the Next.js Discoveries UI, following the existing `git-summary`
bridge pattern and `project-file-evidence.tsx`'s review-before-read
philosophy. Verified end-to-end against this repository's own real local
evidence in a running dev server. See [PROJECT_PLAN.md](PROJECT_PLAN.md)
for implemented scope and limitations.

## Active Capability — Local MCP Server

Status: Complete

Goal: Make Workprint's discovery and investigation capabilities callable
directly from inside Claude Desktop or Claude Code over the Model Context
Protocol, rather than only via the CLI or web app. Three read-only tools
(`list_supported_sources`, `discover_project`, `investigate_project`)
wrap the existing discovery/investigation pipeline unchanged. Verified
end-to-end with a real spawned server and MCP client session against this
repository's own evidence. See [docs/mcp-server.md](docs/mcp-server.md)
and [PROJECT_PLAN.md](PROJECT_PLAN.md) for configuration, tool details,
and limitations.

## Active Capability — Low-Code/No-Code User Experience

Status: Complete

Goal: Make Workprint usable end to end by someone with no coding
experience. A native OS folder picker (inside an Electron desktop shell)
replaces the free-text path field, and the discoveries screen generates
and downloads real Markdown/JSON reports. A real, unsigned `.dmg`/`.zip`
installer now builds with a bundled Python backend (no Node.js or Python
required on the end user's machine), verified end-to-end against an
actual freshly built, mounted DMG -- not just the unpacked build. Still
open: no code signing/notarization (requires the project owner's own
Apple Developer credentials), Windows/Linux packaging is unconfigured,
and there is no auto-update. See
[docs/desktop-app.md](docs/desktop-app.md) and
[PROJECT_PLAN.md](PROJECT_PLAN.md) for the itemized scope and gaps.

## Active Capability — Brand Identity

Status: Complete

Goal: Replace the plain-text wordmark with Workprint's real visual
identity. The provided SVG mark and app icon are now wired into the web
header, browser favicon/Apple touch icon, and the Electron dock/window
icon. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full scope.

## Active Capability — AI Fluency Evidence & Playbook Worksheet

Status: Complete

Goal: Help users reflect on their own AI use with evidence Workprint
already gathers, organized under Anthropic's AI Fluency Framework
(Delegation, Description, Discernment, Diligence) -- without scoring or
rating anyone. Every report now includes an "AI Fluency Evidence"
section, and a downloadable Playbook Worksheet lays the same evidence
out as a fill-in table for the user (or a Claude chat/Cowork session) to
complete. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full scope,
the licensing decision, and current limitations.

## Active Capability — Claude Session Evidence (Tier 1a)

Status: Complete

Goal: Automatically discover and normalize evidence from local Claude Code
sessions and imported claude.ai Export Data archives, so AI collaboration
evidence does not depend on a user remembering a manual export step for
every source.

See [docs/claude-code-adapter.md](docs/claude-code-adapter.md) and
[PROJECT_PLAN.md](PROJECT_PLAN.md) for implemented scope and limitations.

## Active Capability — Claude Session Evidence (Tier 1b)

Status: Complete

Goal: Extend Claude session evidence to local Claude Cowork sessions. Each
Cowork session turned out to write a transcript in the same JSONL shape
Claude Code uses, inside its own sandboxed session directory, so this needed
no new dependency — only a different project-matching rule, since a Cowork
transcript's own working directory is an internal sandbox path rather than
the user's real project folder.

See [docs/claude-cowork-adapter.md](docs/claude-cowork-adapter.md) and
[PROJECT_PLAN.md](PROJECT_PLAN.md) for implemented scope and limitations.

## Active Capability — Claude Session Evidence (Tier 1c)

Status: Complete (experimental deep-parse mode, verified against real data)

Goal: Report on the Claude desktop app's local claude.ai chat cache.
Presence-only detection (does the cache exist, when was it last touched) is
verified and on by default. An opt-in, explicitly experimental deep-parse
mode scans a specific, verified database using a pinned optional
dependency; a verification pass against real data caught and fixed two
real bugs (a mismatched dependency and a database-enumeration assumption),
and a second pass confirmed the turn-classification heuristic itself
against a real Chrome-written fixture, since the one live record found in
the actual local cache during the first pass had no recoverable value.
Whether claude.ai's real cache reliably produces a *readable* value in
ordinary use is still open. Its evidence is account-wide, not specific to
the project under investigation, since claude.ai chat has no folder
concept to match against.

See [docs/claude-desktop-chat-adapter.md](docs/claude-desktop-chat-adapter.md)
and [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full trade-off, privacy, and
verification status.

## Upcoming Capabilities

Workprint's next phase is the path from working product to trustworthy
version 1.0. The priority is not to add more sources for their own sake. The
priority is to make Workprint's core loop unmistakably useful:

1. choose a project;
2. approve the evidence and context Workprint may use;
3. receive a meaningful evidence-backed explanation of the user's role, AI's
   role, and what cannot be known;
4. inspect why Workprint believes each claim;
5. share the result with confidence.

### 1. First Insight Quality v2

Goal: Make the first supported insight feel like a real insight, not an
inventory of detected evidence.

The first insight must explain what the user did or where human judgment,
review, direction, correction, or sequencing appears. It may also explain what
AI/tooling appears to have done, how the work moved from idea to
implementation, or what the evidence cannot separate.

Quality bar:

- rejects evidence-source summaries as first insights;
- uses plain, specific language;
- ties every insight to inspectable evidence;
- preserves uncertainty instead of overclaiming;
- reflects Workprint's AI Fluency lens without scoring the user.

### 2. User-Approved Context Builder

Goal: Help users add fuller long-chat and project context without pretending
the full history was sent or verified.

This capability should improve bounded evidence packets through source
diversity, recency balance, user-approved long-chat summaries, and clear
packet previews. Users should understand what is included, what is summarized,
what is metadata-only, and what is missing.

Quality bar:

- summary evidence remains distinct from direct transcript evidence;
- users get copyable prompts for Claude, ChatGPT, Gemini, and other agents;
- Workprint labels full evidence, excerpts, summaries, and metadata clearly;
- broader context improves insight quality without weakening attribution
  boundaries.

### 3. Trust Layer UX

Goal: Make Workprint's trust model visible and understandable inside the app,
not hidden in documentation.

This includes plain-language explanations for bounded evidence, confidence
levels, evidence strength, summary evidence, unknowns, attribution limits, and
provider processing.

Quality bar:

- confidence labels explain what Workprint means by high, moderate, limited,
  low, and unknown;
- every major claim answers "why should I believe this?";
- users can inspect the evidence behind important findings;
- privacy and provider-processing language is close to the action;
- trust copy reduces confusion without overwhelming first-time users.

### 4. Mac App Release Quality

Goal: Make the macOS app feel dependable enough for regular use by a
nontechnical user.

The app should install and run without a terminal, handle provider and local
backend errors gracefully, and follow a dogfood-before-upload release process.

Quality bar:

- signed and notarized macOS builds when project credentials are available;
- stable local backend startup and shutdown;
- no silent uploads or hidden provider defaults;
- clear empty, loading, error, and success states;
- consistent versioning, release notes, and asset naming;
- every release is dogfooded before public asset upload.

### 5. Shareable Report Experience

Goal: Make Workprint reports useful to someone who did not generate them.

The report should explain human-AI collaboration, evidence, confidence, and
unknowns in a way that is legible to clients, teammates, hiring reviewers, or
other external readers.

Quality bar:

- reader-friendly report view or export bundle;
- clear executive summary and AI Fluency evidence section;
- evidence inspection remains available without making the report feel like a
  raw data dump;
- share language avoids unsupported authorship, ownership, effort, value, and
  contribution claims;
- reports remain useful even when some evidence is summary-only or incomplete.

## Version 1.0 Definition

Version 1.0 should mean:

> A nontechnical user can install Workprint, choose a project, approve the
> evidence used, receive a meaningful evidence-backed explanation of their role
> and AI's role, inspect why Workprint believes it, and share the result with
> confidence.

Minimum 1.0 requirements:

- installer-ready macOS app with no terminal setup for normal use;
- stable investigation flow from project selection through report export;
- reliable provider handling for supported reasoning providers;
- evidence packet preview before provider processing;
- meaningful first insight that explains user agency or human judgment;
- AI Fluency lens integrated as evidence-backed language, not scoring;
- confidence, unknowns, and attribution limits understandable to nontechnical
  users;
- direct evidence, excerpts, summaries, and metadata clearly distinguished;
- release checklist that includes dogfooding before asset upload;
- documentation for API keys, bounded evidence, supported sources, summaries,
  privacy, and limitations.

Windows and Linux support should follow once the Mac product loop is
trustworthy. Mobile should be treated as a future report-viewing experience,
not the primary evidence-gathering product.

## Quality Responsibilities

High-quality milestones require both product judgment and implementation
discipline.

Tony should provide:

- real dogfood projects and screenshots from actual use;
- examples of first insights that feel useful, weak, confusing, or too
  technical;
- decisions about product language when two truthful phrasings imply different
  positioning;
- approval for trust, privacy, licensing, and third-party attribution choices;
- provider keys and real-provider dogfood feedback when needed;
- release judgment on whether a build is ready to upload.

Codex should provide:

- small milestone plans centered on user capability, UX story, and marketing
  clarity;
- implementation that preserves evidence, attribution, confidence, and privacy
  boundaries;
- tests for both successful paths and confusing edge cases;
- dogfood passes against real Workprint evidence before claiming completion;
- copy review through UX, product, and marketing lenses;
- clear reports of what changed, what passed, what failed, and what remains
  incomplete.

Shared quality rituals:

- begin each milestone with the user problem, user story, UX story, marketing
  story, smallest useful version, and risks;
- dogfood the actual user journey, not only the underlying function;
- treat confusing screenshots as product evidence;
- prefer one excellent completed loop over several partially trustworthy
  features;
- stop before shipping when passing tests contradict the user experience.

## Later Capabilities

1. Semantic correlation only after deterministic behavior is trustworthy —
   this is also the prerequisite for ever attributing Claude Desktop Chat
   evidence (Tier 1c) to a specific project, since that source has no folder
   concept of its own to match against.

Detailed requirements for upcoming capabilities are tracked in
[PROJECT_PLAN.md](PROJECT_PLAN.md).

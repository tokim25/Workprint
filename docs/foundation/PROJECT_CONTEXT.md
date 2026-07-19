# Project Context

Status: Living document
Purpose: Records the current repository state, milestones, capabilities, and limitations
Expected Update Frequency: Living document

This document is the living memory of the repository. It should evolve as
Workprint changes. When a milestone completes, when architecture changes, or
when limitations are resolved or discovered, update this file alongside the
more specific implementation and product documents.

## Current Architecture

Workprint is organized as a small evidence pipeline:

```text
Evidence Sources
  ↓
Discovery
  ↓
Adapters
  ↓
Normalized Evidence
  ↓
Observations
  ↓
Timeline
  ↓
Investigation
  ↓
Executive Report
  ↓
Markdown / JSON
```

Evidence adapters own source parsing and return normalized records. The
investigation engine works from normalized observations rather than
source-specific artifacts. Timeline generation groups and orders observations
deterministically. Reports present investigation data in Markdown or JSON
without changing the evidence model.

## Completed Milestones

Workprint currently includes these completed capabilities:

- ChatGPT import.
- Claude import.
- EvidenceAdapter contract.
- Adapter registry.
- Canonical observations.
- Deterministic investigation engine.
- Timeline Report.
- Google Docs static export adapter.
- Figma static export adapter.
- Local Git evidence adapter.
- Report visual design and shareability.
- Executive Report v1.
- Executive Report copy-quality audit integration.
- Project Discovery.
- Guided Investigation Wizard.
- Markdown and JSON reporting.
- Multi-source investigations.
- Exact, source-aware duplicate suppression.
- A web-based, four-screen Next.js product experience (start, sources,
  investigating, discoveries), superseding the terminal-based Guided
  Investigation workflow as the primary way most people use Workprint.
- Claude Code, Claude Cowork, and Claude Desktop Chat evidence adapters
  (local session evidence beyond manually exported files), the last of
  which is explicitly experimental and account-wide rather than
  project-scoped; see `docs/claude-desktop-chat-adapter.md`.
- All three of the above surfaced in the Next.js Discoveries UI, alongside
  Git and project-file evidence.
- A local MCP server (`workprint-mcp`) exposing read-only discovery and
  investigation tools, callable directly from inside Claude Desktop or
  Claude Code; see `docs/mcp-server.md`.
- Real report generation and download (Markdown and JSON) from the web
  app's discoveries screen, replacing inert placeholder buttons.
- A native OS folder picker inside an Electron desktop shell
  (`npm run electron:dev`), removing the need to type a filesystem path
  when choosing a project -- see `docs/desktop-app.md` for what this does
  and does not yet cover.

## Current Milestone

The active milestone is Low-Code/No-Code User Experience. Its goal is to make
Workprint usable by people with no coding experience, end to end: choosing a
project, seeing evidence, and getting a report out, without ever touching a
terminal or typing a filesystem path.

The web-based experience described in earlier versions of this document as a
near-term goal is now built (see Completed Milestones above) and is the
primary product surface. The CLI remains useful infrastructure for
validation, automation, and expert workflows, but it is not the primary
product experience.

What remains for genuine no-code use is distribution: today, even the web
app requires `npm install` and `npm run dev` (or `npm run electron:dev`) to
start, which assumes terminal comfort neither the browser flow nor the
Electron flow removes. `docs/desktop-app.md` documents the concrete gap
between "the Electron shell and native folder picker work" and "a
non-coder can double-click a single installer with zero setup" --
including a verified-but-not-yet-wired finding that PyInstaller can bundle
the Python backend into a fully standalone binary.

## Near-Term Roadmap

Near-term work should continue reducing the amount of project-specific command
knowledge required from users while preserving evidence boundaries. Likely
areas include:

- clearer guided workflow language;
- safer source selection;
- better readiness explanations from discovery;
- report output flows that are easier to share;
- more direct connection between discovery results and user-facing confidence;
- continued dogfooding against Workprint's own project history.

## Long-Term Roadmap

Long-term development should expand both evidence coverage and user
accessibility. Directionally, Workprint should move toward:

- additional source adapters;
- richer project timelines;
- better coverage and corroboration analysis;
- no-code or low-code report generation;
- stronger evidence appendix navigation;
- more useful executive reports for hiring, client, audit, and teammate
  contexts;
- clear integration points for future interfaces without weakening the core
  investigation model.

## Known Limitations

Static Google Docs exports do not recover revision history, edit-by-edit
authorship, deleted text, or paragraph authorship unless supplied evidence maps
those facts directly.

Static Figma exports do not recover version history, comments, comment
resolution history, contributor activity, or authorship. File-level metadata
does not become node-level attribution.

Discovery recognizes supported evidence, but it does not validate every future
investigation outcome. Local Git repositories are selectable evidence sources
when the installed `git` command can resolve a non-bare repository or worktree.

Guided Investigation is currently terminal-based; it remains available as
expert-workflow infrastructure but is no longer the primary way most people
use Workprint. The web app is the primary no-code surface now, but reaching
it still requires terminal commands (`npm install`, `npm run dev`); see
`docs/desktop-app.md` for the specific remaining gap.

Executive Report v1 is deterministic and derived from existing investigation
data. It includes an offline copy-quality audit integration using the pinned
`unslop-text` scanner from JCarterJohnson's `vibecoded-design-tells` project,
plus Workprint-owned structural checks and evidence-preservation validation.
It does not use LLM-generated narrative copy, semantic clustering,
probabilistic confidence scoring, hidden contribution estimates, or authorship
detection.

## Technical Debt

Semantic duplicate detection across different platforms is not implemented.
Current duplicate suppression handles exact, source-aware duplicates.

Git evidence import is local-only. It does not call GitHub, fetch remotes,
inspect file contents, support bare repositories, traverse unrelated nested
repositories, or resolve author and committer identities.

Low-code and no-code UX is now actively built (the web app, the Electron
native folder picker, real report generation) rather than at the definition
stage, but distribution is not solved: starting the app at all still
requires terminal commands, and there is no packaged installer yet. See
`docs/desktop-app.md`.

## Future Dogfooding

An aspirational milestone is for Workprint to investigate the Workprint
repository itself using its own evidence sources: Git history, AI
conversations, documentation, design artifacts, and other supported project
records.

That future self-investigation should produce an Executive Report that
accurately explains Workprint's evolution, major decisions, collaboration
patterns, confidence, and evidence gaps. This is not a current capability.

## Major Capabilities

Workprint can import supported ChatGPT and Claude conversation exports, static
Google Docs exports, static Figma JSON exports, and local Git repository
metadata. It can discover supported evidence in a project folder, combine
multiple sources into one investigation, generate deterministic observations
and timeline events, build an Executive Report, run the Executive Report
copy-quality audit offline, and render Markdown or JSON outputs.

The system preserves source boundaries. It separates user activity,
collaborator activity, AI/tool activity, joint activity, and unattributed
activity when evidence supports those distinctions. It keeps unsupported
activity unknown.

## Current Investigation Pipeline

The current investigation pipeline begins with explicit or discovered evidence
inputs. Registered adapters validate and read source artifacts. Normalized
records are converted into observations with evidence references. Multi-source
orchestration suppresses exact duplicates and sorts observations before
passing them to the investigation engine.

The engine orders observations, summarizes captured activity, creates bounded
findings, builds timeline events, and records unknowns and limitations. The
Executive Report is derived from the completed investigation. Markdown and JSON
renderers then present the same investigation data for readers and tools.

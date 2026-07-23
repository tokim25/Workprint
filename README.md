# Workprint

**Turn your project evidence into AI-assisted insights you can inspect.**

Workprint reads evidence about a project — a local Git repository, local
project notes, local Claude Code/Cowork/Desktop Chat session history, or
exported conversations and documents — and prepares bounded evidence packets
for AI reasoning providers. Its job is to turn provider-assisted reasoning
into a report you can trust: what the evidence directly supports, and what it
honestly cannot determine.
Workprint never calculates authorship, effort, ownership, or
human-vs-AI contribution percentages. It shows evidence, not verdicts.

No coding experience is required to use it.

## Get Started (No Terminal Required)

**[Download Workprint for macOS (Apple Silicon)](https://github.com/tokim25/Workprint/releases/latest)**
— no Node.js, no Python, nothing else to install. Apple Silicon Macs
(M1/M2/M3/M4) only for now; no Intel Mac, Windows, or Linux build yet.

1. **Open it.** The first time, macOS will say it can't verify the
   developer — this is normal for a small, independently built app that
   isn't (yet) signed by Apple, not a sign anything is wrong.
   Right-click the app and choose **Open** once, then confirm. You won't
   see this warning again.
2. **Tell Workprint what you're working on.** One sentence is enough.
3. **Add where the work happened.** Either connect a real project folder
   (unlocks Git history and local Claude session evidence) or add
   individual files for evidence — or just click **Use sample project**
   to try Workprint without picking anything.
4. **Connect a reasoning provider.** OpenAI, Claude, and Gemini appear as
   equal bring-your-own-key choices — there is no default. Microsoft Copilot
   and GitHub Copilot are planned as a separate, later integration since they
   don't fit the same simple API-key model.
5. **Click Investigate.** Workprint sends selected, bounded evidence to the
   provider you choose for reasoning, then shows supported findings with a
   plain-language explanation of *why* it believes them and what it still
   cannot determine.
6. **Build the full report,** then download it as Markdown or JSON — or
   download the **AI Fluency Playbook Worksheet** (see below).

Local collection happens on your computer. Provider-assisted reasoning requires
selected evidence to be sent to the AI provider you choose. Workprint should
send bounded excerpts and metadata, not your whole project folder, and should
make that upload boundary clear before reasoning starts.

Important: Workprint's license gives you rights to use the Workprint software.
It does **not** give you permission to upload employer, client, collaborator,
third-party, confidential, copyrighted, regulated, or proprietary project
evidence to an AI provider. Before using provider-assisted reasoning, make sure
you have permission to process the selected evidence with that provider and
that the provider's terms, data-use policies, retention settings, and your
account or enterprise agreements fit your obligations.

See [docs/ai-reasoning-providers.md](docs/ai-reasoning-providers.md) and
[docs/foundation/AI_REASONING_PRIVACY.md](docs/foundation/AI_REASONING_PRIVACY.md)
for the reasoning, privacy, and licensing boundaries.

### No Install? Use Workprint Inside Claude Or ChatGPT

Prefer not to download anything yet, or don't have an Apple Silicon Mac? The
same investigation approach is also available as a **Claude Skill** and a
**ChatGPT Custom GPT**:
**[github.com/tokim25/workprint-skills](https://github.com/tokim25/workprint-skills)**.

This is a lighter-weight version of Workprint. It applies the same
evidence-boundary and claim rules through instructions (plus a script run for
the ChatGPT zip-upload path), not through this app's full deterministic
validation pipeline — good for trying the idea; the desktop app above remains
the fuller, more rigorously checked experience.

### The AI Fluency Playbook Worksheet

Every report includes an **AI Fluency Evidence** section, organized
under Anthropic's AI Fluency Framework — Delegation, Description,
Discernment, and Diligence — using real evidence from your project (which
AI tools you used, whether commits followed AI sessions, whether test
files changed, and more). Workprint does not score or rate you; it only
surfaces the evidence. The **Playbook Worksheet** lays that same evidence
out as a fill-in table, ready to bring into a conversation with Claude
and reflect on together.

### Want the latest, unreleased build?

Released versions lag behind `main`. To build the current development
version yourself, see "Run It Yourself" below. Building the app requires
a terminal — only *using* the downloaded release doesn't.

## What Workprint Can Read

- **Local Git history** — commits, authors, timestamps, changed files.
- **Project notes and documentation** — Markdown, MDX, plain text, RST, and
  AsciiDoc files that are not generic repository boilerplate.
- **Local Claude Code, Claude Cowork, and Claude Desktop Chat** session
  history, read directly from your machine.
- **Exported conversations** from ChatGPT and Claude.
- **User-approved long-chat summaries** for context that cannot fit in a
  bounded packet, labeled as summary evidence rather than full transcripts.
- **Static exports** from Google Docs and Figma.

Each source is read with clear, documented boundaries — see
[docs/project-notes-import.md](docs/project-notes-import.md),
[docs/claude-code-adapter.md](docs/claude-code-adapter.md),
[docs/claude-cowork-adapter.md](docs/claude-cowork-adapter.md), and
[docs/claude-desktop-chat-adapter.md](docs/claude-desktop-chat-adapter.md)
for exactly what each source does and does not tell Workprint.
See [docs/chat-summary-evidence.md](docs/chat-summary-evidence.md) for the
user-approved summary format and its limits.

## Run It Yourself

This section is for whoever is setting Workprint up, packaging the app,
or extending it — it assumes comfort with a terminal.

### Run the app in development mode

```bash
npm install
npm run dev            # plain browser, at http://localhost:3000
# or
npm run electron:dev   # the same app in a native desktop window
```

### Build a real, installable desktop app

Requires Node.js/npm (for the app) and a Python 3.10+ environment with
PyInstaller (only to compile the bundled backend binary — end users of
the built app need neither Node.js nor Python installed).

```bash
python3.12 -m venv .build-venv && source .build-venv/bin/activate
pip install -e . && pip install pyinstaller
deactivate
WORKPRINT_BUILD_PYTHON=.build-venv/bin/python3 npm run build:backend

npm run electron:dist   # release/Workprint-*.dmg and .zip
```

See [docs/desktop-app.md](docs/desktop-app.md) for exactly what this
build does, what was verified against a real built app, and what
remains (code signing/notarization requires the project owner's own
Apple Developer credentials, and isn't set up yet).

### Connect Workprint to Claude directly (MCP)

Workprint also runs as a local MCP server, so Claude Desktop or Claude
Code can call it directly to discover and investigate a project. This is a
different integration from the Claude Skill above — MCP requires setting up
this repository's Python backend as a local server; the Skill only needs a
folder of instructions dropped into Claude, no server required. See
[docs/mcp-server.md](docs/mcp-server.md) for setup.

## Expert CLI Reference

Workprint also has a full command-line interface for anyone who prefers
it or wants to script investigations.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

**Preview evidence in a project folder:**

```bash
workprint discover path/to/project
```

**Run a guided investigation** (choose a folder, review evidence, select
sources, and generate reports interactively):

```bash
workprint guide
```

Non-interactively:

```bash
workprint guide \
  --path path/to/project \
  --include chatgpt,figma \
  --project "Workprint" \
  --output-dir workprint-output \
  --yes
```

**Create a user-approved long-chat summary template:**

```bash
workprint chat-summary-template \
  --title "Project long-chat summary" \
  --output project-chat-summary.json
```

Review the file before changing `approved_by_user` to `true`. Workprint treats
this as summary evidence, not proof that the complete chat history was sent.

**Investigate a single exported source:**

```bash
workprint investigate chatgpt fixtures/chatgpt/sample-conversations.json \
  --project "Workprint" \
  --output report.md

workprint investigate claude fixtures/claude/sample-conversations.json \
  --project "Workprint" \
  --output claude-report.md

workprint investigate google-docs fixtures/google-docs/sample-document.json \
  --project "Workprint" \
  --output google-docs-report.md

workprint investigate figma fixtures/figma/sample-file.json \
  --project "Workprint" \
  --output figma-report.md
```

**Combine multiple sources:**

```bash
workprint investigate-multi \
  --evidence chatgpt=exports/chatgpt.json \
  --evidence claude=exports/claude.json \
  --project "Workprint" \
  --output combined-report.md
```

**Import observations only** (no report):

```bash
workprint import chatgpt fixtures/chatgpt/sample-conversations.json --output observations.json
```

All of the above also work without installing, using
`PYTHONPATH=src python3 -m workprint.cli <command>`.

## Run Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
npm run typecheck
npm run lint
```

## Project Governance

- [docs/foundation/00-START-HERE.md](docs/foundation/00-START-HERE.md) —
  the foundation: vision, product and engineering principles, and the
  required reading order for anyone making product or architecture
  decisions.
- [docs/foundation/DECISION_LOG.md](docs/foundation/DECISION_LOG.md) —
  the current, actively maintained record of accepted product and
  architectural decisions.
- [PROJECT_PLAN.md](PROJECT_PLAN.md) / [ROADMAP.md](ROADMAP.md) — what's
  shipped, what's active, and what's next.
- [AGENTS.md](AGENTS.md) — permanent instructions for coding agents
  working in this repository.
- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, testing, branch, commit,
  and pull request expectations.

## Limits

Workprint reports what its evidence sources directly support. It does
not infer authorship, ownership, effort, or human-vs-AI contribution —
counts of commits, messages, or turns are never converted into those
claims. It can miss implicit decisions, subtle revisions, or activity
that happened outside the evidence it was given (a conversation that
wasn't exported, a tool it doesn't yet read). Where the evidence runs
out, Workprint says so explicitly rather than guessing.

## Rights

Copyright © 2026 Tony Kim. Licensed under the Apache License, Version 2.0
— see [LICENSE](LICENSE) and [NOTICE](NOTICE). Workprint's AI Fluency
Evidence section credits Anthropic's AI Fluency Framework (developed by
Prof. Rick Dakan and Prof. Joseph Feller); the framework's own materials
remain separately licensed under CC BY-NC-SA 4.0 regardless of Workprint's
own license — see [NOTICE](NOTICE) for the full attribution.

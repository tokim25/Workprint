# Workprint — Context Snapshot

*Written 2026-07-20. This is a point-in-time snapshot for resuming work after a chat compaction or in a fresh session — not a replacement for the repo's own `docs/foundation/` docs, which are the timeless onboarding reference. If this file and the repo disagree, trust the repo (`git log`, the code, `docs/foundation/DECISION_LOG.md`) over this snapshot.*

## What Workprint is

A local-first desktop app that reconstructs the story of a project — decisions, reasoning, dead ends — from scattered evidence (Git history, Claude Code/Cowork/Desktop Chat sessions, Figma files, ChatGPT exports, Google Docs exports). Built for a **non-coder audience** who wants low-code/no-code accessibility.

**Core philosophy, non-negotiable:** Workprint never infers authorship, effort, or ownership. Every claim ships with explicit `supports` / `does not prove` boundary language. It reads evidence and states what it can and cannot establish — it does not score or judge. This applies even to newer features like AI Fluency reporting ("Workprint does not score or rate AI fluency").

**License:** Apache License 2.0 (open source), chosen specifically because its NOTICE-file mechanism accommodates the Anthropic AI Fluency Framework's CC BY-NC-SA 4.0 attribution requirement, plus its patent grant/retaliation clause. See `docs/foundation/DECISION_LOG.md` → "Workprint Is Open Source Under the Apache License, Version 2.0."

## Architecture

- **Electron** shell wrapping a **Next.js** frontend (App Router, React 19).
- A **Python package** (`src/workprint/`) does all real evidence reading/synthesis: adapters (`git.py`, `claude_code.py`, `claude_cowork.py`, `claude_desktop_chat.py`, `figma.py`, `chatgpt.py`, `google_docs.py`), a discovery layer (`discovery.py`), a synthesis engine (`engine.py` → `Investigation`/findings), an executive-report layer (`executive.py` → `ExecutiveReport`/`ExecutiveBrief`/`ConfidenceAssessment`, real multi-source claim + confidence scoring), and an AI Fluency layer (`ai_fluency.py`, organizes evidence under Anthropic's Delegation/Description/Discernment/Diligence framework).
- **Bridge pattern**: Next.js API routes (`app/api/{git-summary,claude-local-summary,investigate}/route.ts`) spawn the Python code as a subprocess via `node:child_process`. In dev mode this is `python3 -m workprint.<module>`; in the packaged app it's a single PyInstaller-built binary (`workprint-backend`, dispatches via `src/workprint/bundled_cli.py`), so packaged end users need zero Python installed. `lib/workprint-python-command.ts` resolves which mode to use.
- **Packaging**: `next.config.ts` `output: "standalone"` + electron-builder. `scripts/build-backend.sh` builds the PyInstaller binary; `scripts/copy-standalone-assets.js` + `scripts/after-pack.js` (an electron-builder `afterPack` hook) handle two real gotchas: electron-builder's `extraResources` silently drops nested `node_modules`, and adding files after Electron's own ad-hoc signature requires re-signing (`codesign --deep --force --sign -`) or Gatekeeper rejects the app as "damaged" rather than the milder "unidentified developer."
- **No database, no queue, no multi-service backend** — deliberately, for a single-user local tool. An architecture review this session confirmed this is the right amount of complexity for the stated scale.

## Current release state

- **v0.4.0 is live** on GitHub Releases (`github.com/tokim25/Workprint/releases/tag/v0.4.0`), with a real, checksummed, unsigned/ad-hoc-signed arm64 DMG. `package.json` and `pyproject.toml` versions are now in sync (both were drifted — 0.1.0 vs 0.3.0 — until fixed this session).
- README's download link points at `/releases/latest`, so it auto-updates on future releases — no manual link maintenance needed.
- The portfolio site (`tokim25.github.io`, separate repo) also links `/releases/latest` for the same reason (was previously hardcoded to a stale `v0.1.0` direct download link).

## What shipped this session (chronological, most recent first)

1. **Discoveries screen fix** (3 phases, PR: "Fix the Discoveries screen: stop showing a fake insight"): the first-payoff screen after connecting evidence was showing a hardcoded sample claim ("You repeatedly set the direction") and a hardcoded "Moderate" confidence badge *regardless of what evidence was connected* — confirmed via reading `components/workprint-app.tsx`, not guessed. Fixed by:
   - `lib/active-discovery.ts`'s `pickActiveDiscovery()`: priority-ordered picker (Git → Claude Code → Claude Cowork → Claude Desktop Chat → project files → sample), reusing already-existing claim generators. Mechanical/count-based claims now report `"Limited"` confidence instead of a lying `"Moderate"`.
   - `pickExecutiveDiscovery()`: the real multi-source synthesis engine (`executive_report.executive_brief.project_goal` + `confidence_assessment.band`) was *already computed* by `/api/investigate` but never read by this screen. `startInvestigation()` now fires a real `/api/investigate` call in parallel with the existing stage-animation, upgrading the headline in place once it resolves — but only when `project_goal.status === "explicitly_supported"` (verified this literal value in `src/workprint/executive.py`), never downgrading a decent claim to "no explicit goal statement."
   - Dropzone copy now explains what it actually recognizes (ChatGPT `conversations.json`, Google Docs exports needing a `workprint-source: google-docs` marker line, Figma's raw REST API JSON requirement) — previously undersold real capability. A real "Connect Figma" OAuth flow is explicitly flagged as **not built**, future work only.
   - No backend changes needed for any of this — it was 100% a wiring problem, not a missing-capability problem.
2. **v0.4.0 release**: version bump + rebuilt DMG including the above.
3. **Architecture-review-driven hardening pass** (used the `architecture-reviewer` skill against the real packaged app): found and fixed
   - 🔴 Production server bound to `0.0.0.0` (reachable by any device on the same network) instead of loopback — fixed by setting `HOSTNAME: "127.0.0.1"` in `electron/main.js`.
   - 🟠 Investigation temp files written with default (often world-readable) permissions — fixed with `os.open(..., 0o600)`.
   - 🟡 No `app.requestSingleInstanceLock()` — a second launch silently hung for 30s then quit with no explanation.
   - 🟡 No crash handling for the production server child — now shows a clear dialog on unexpected exit.
   - 🟢 `server.log` had no rotation — capped at 5MB.
   - 🟢 No `will-navigate` guard on the `BrowserWindow` — added as defense-in-depth.
   - **A second real bug found while dogfooding the rebuild** (not from review): `git-summary`/`claude-local-summary` intermittently hung under a normal double-click (`open`) launch — same root cause as a previously-fixed `investigate` bug (GUI-launched-context pipe unreliability), turns out not limited to large payloads. Fixed with the same `--output-file` temp-file pattern already used for `investigate`.
   - v0.3.0 released with these fixes (later superseded by v0.4.0 above).
4. Earlier in the session (see `docs/foundation/DECISION_LOG.md` and `PROJECT_PLAN.md`/`ROADMAP.md` for full detail): Apache 2.0 licensing, brand identity integration (SVG logo assets, app icons), AI Fluency Framework reporting + downloadable Playbook Worksheet, MCP server, Electron packaging with bundled Python backend, native folder picker, and the original v0.1.0 GitHub Release.

## Established working conventions (apply these without being asked)

- **Verify against real data, not mocks or assumptions**, before claiming something works. This repo's history is full of real bugs that only surfaced via dogfooding against real data (a genuinely-built DMG, this repo's own Git/Claude history, real API responses) that unit tests and code review missed. Examples: the `AI_SOURCE_LABELS` dict keyed on the wrong string format (unit tests had the identical wrong assumption baked in); the Electron dock icon crash; the GUI-launch stdio/pipe bugs; the `0.0.0.0` binding.
- **Read `docs/foundation/` before architecture-level work** (00-START-HERE.md, AGENT_WORKING_CONTEXT.md, DECISION_LOG.md, etc.) — comprehensive, mature, already exists, don't duplicate it.
- **Branch → PR → merge per verified milestone**, without re-asking each time, once the general direction is agreed. This repo does NOT do direct-to-main commits (unlike the separate portfolio site repo, which does).
- **PR descriptions include a real test plan** with checked-off items describing what was actually verified, not just "should work."
- Full Python suite (`pytest`, 245 passed / 12 skipped as of this snapshot) + `npm run typecheck` + `npm run lint` gate every merge.
- Node/npm/git/gh binaries on this machine live at `/opt/homebrew/bin`, not on the default shell PATH — prefix commands with `export PATH="/opt/homebrew/bin:$PATH"` or call by full path.
- Building the PyInstaller backend needs a `.build-venv` (Python 3.10+, `pip install -e . && pip install pyinstaller`) — disposable, gitignored, fine to delete and recreate each time (~10s).

## Known limitations / explicitly out of scope for now

- No real Figma OAuth connector — the Figma adapter requires a user to manually obtain the raw REST API file JSON via a personal access token. Flagged in the UI, not silently implied to be easier than it is.
- No upload-file-bytes-to-backend route — dropped files are matched by filename/extension only (never content) except in `components/project-file-evidence.tsx`, the one place that reads bounded text client-side after user confirmation.
- Claude session evidence is aggregate-only at the API boundary — individual message content is read internally by the Python adapters but discarded into counts before serialization; there's no per-message excerpt available to the frontend today.
- No code signing/notarization (needs the project owner's own paid Apple Developer account) — the DMG is ad-hoc signed only, so macOS shows the "unidentified developer" warning on first launch (expected, documented, not a bug).
- No frontend test runner exists yet (no jest/vitest in `package.json`) — Python has real pytest coverage; new frontend logic gets extracted into small pure functions (e.g. `lib/active-discovery.ts`) so it's unit-testable later without blocking today's ship on installing a harness.

# Desktop App (Electron)

Workprint can run as a real desktop app: a native OS folder picker, a
bundled Python backend, and a self-contained installer that needs no
Node.js or Python installed on the end user's machine. This is the
Low-Code/No-Code milestone -- see `PROJECT_PLAN.md` for the full picture.

## Running It Today (Development Mode)

```bash
npm install
npm run electron:dev
```

This spawns `next dev` as a child process, waits for it to respond, and
opens an Electron `BrowserWindow` pointed at it -- the same Next.js app
that runs in a browser, just wrapped in a native window. `npm run dev`
(no Electron) still works exactly as before for anyone who prefers a
browser tab. Requires Node.js and npm already installed, the same as
running the web app directly.

## Building A Real Installer

This has two build-time dependencies that are separate from what an end
user needs: Node.js/npm (for the app itself) and a Python 3.10+
environment with PyInstaller (only to compile the bundled backend
binary; end users never need Python).

```bash
# One-time (or whenever src/workprint/*.py changes): build the
# standalone Python backend binary. Requires a Python 3.10+ environment
# with the project installed and PyInstaller available:
python3.12 -m venv .build-venv && source .build-venv/bin/activate
pip install -e . && pip install pyinstaller
deactivate
WORKPRINT_BUILD_PYTHON=.build-venv/bin/python3 npm run build:backend

# Build the app itself:
npm run electron:pack   # fast: unpacked release/mac-arm64/Workprint.app
npm run electron:dist   # full: release/Workprint-*.dmg and .zip
```

`npm run build:backend` wraps `scripts/build-backend.sh`, which runs
PyInstaller against `src/workprint/bundled_cli.py` -- a small dispatcher
(`git-summary` / `claude-local-summary` / `web-investigate`) that forwards
to the same bridge modules' unchanged `main(argv)` functions dev mode
calls via `python3 -m workprint.<module>`. `lib/workprint-python-command.ts`
picks between the two invocation styles based on whether
`WORKPRINT_BACKEND_BIN` is set (only true in a packaged app; see
`electron/main.js`'s `startProductionServer`).

`npm run electron:pack`/`electron:dist` first run `next build` with
`output: "standalone"` (`next.config.ts`), copy in `public/` and
`.next/static` (Next's standalone mode deliberately excludes both;
`scripts/copy-standalone-assets.js` handles it), then run
`electron-builder` per the `"build"` field in `package.json`. An
`afterPack` hook (`scripts/after-pack.js`) copies the standalone build's
own `node_modules` into the packaged app directly with `fs.cpSync` --
electron-builder's `extraResources` file-matcher silently drops any
nested `node_modules` directory it copies, a real limitation the `filter`
option does not override -- and then re-signs the app bundle ad hoc, since
copying files in after packaging invalidates Electron's own pre-existing
signature (see "What Was Actually Verified" below).

## What The Electron Shell Adds

`electron/main.js` registers a `dialog:choose-project-folder` IPC handler
that opens the OS's native "Choose Folder" dialog and returns a real
absolute path. `electron/preload.js` exposes this to the page as
`window.workprintElectron.chooseProjectFolder()` via `contextBridge`
(`contextIsolation: true`, `nodeIntegration: false`).

`components/workprint-app.tsx` detects this bridge with
`useSyncExternalStore` (hydration-safe, since `window` does not exist
during server rendering) and, when running inside Electron, moves the
native "Connect Project Folder" section above the browser file picker and
gives both distinct labels -- no path-typing at all inside the desktop
app. In a plain browser (or `npm run dev` without Electron), the manual
text field remains exactly as it was, since the browser's File System
Access API cannot hand back a real OS path from any in-browser picker.

## What Was Actually Verified

Everything below was tested against a real, unsigned `.dmg` built on this
machine -- not just code review. Four real bugs were found and fixed only
because of this:

- **The app failed to start at all.** `electron/icon.png` was
  accidentally excluded from the packaged app by an over-eager `files`
  pattern, and `app.dock.setIcon()` threw on the missing file.
- **The production server crashed with `Cannot find module 'next'`.**
  electron-builder's `extraResources` copying silently drops any nested
  `node_modules` directory regardless of the `filter` option -- a real,
  documented electron-builder limitation, not a config mistake. Fixed
  with the `afterPack` hook described above.
- **Real API requests hung indefinitely inside the packaged app,
  specifically when launched via `open`/double-click (no terminal
  attached) -- but worked in ~12 seconds launched from a terminal.**
  `electron/main.js` was using `stdio: "inherit"` for the child Node
  process running the production server, which passes along Electron's
  own stdio; that is not a real, working pipe when there is no attached
  terminal. Fixed by giving that child real pipes and logging to
  `app.getPath("userData")/server.log` instead of forwarding to
  `process.stdout` (which could carry the same problem in the main
  process).
- **Even with real pipes, a full investigation's multi-megabyte JSON
  payload still hung specifically under the GUI-launched context.**
  Piping that much data through a grandchild subprocess (Node server to
  bundled Python binary) depends on the parent draining the pipe
  promptly; something about the GUI-launched process context made that
  unreliable under load. Fixed by having `web_investigate.py` write
  large payloads to a temp file (`--output-file`) instead of stdout,
  which `app/api/investigate/route.ts` now reads back directly --
  sidestepping pipe backpressure entirely rather than diagnosing its
  exact cause further. `git-summary` and `claude-local-summary` keep
  their small, pipe-based output unchanged.
- **The DMG-distributed app was rejected by Gatekeeper as "damaged," not
  the milder "unidentified developer" warning.** `codesign -dv` showed a
  broken signature: Electron's own binaries ship pre-signed ad hoc, and
  the `afterPack` hook's file copy afterward invalidated that signature
  without anything re-signing it. Fixed by re-signing ad hoc
  (`codesign --deep --force --sign -`) inside `after-pack.js`, after the
  copy. Verified with `spctl -a -vvv` and `codesign --verify --deep
  --strict` before and after.

After these fixes, a full report generation (git evidence, this
repository's own history) was confirmed working end to end through:
the unpacked `.app` launched via `open`; the same `.app` copied out of a
mounted, freshly built `.dmg`; and a direct `curl` against the running
packaged app's API routes -- each producing real evidence, a working AI
Fluency Evidence section, and a downloadable Playbook Worksheet.

Timeouts in `app/api/*/route.ts` were raised from dev-mode's 8s/30s to
15s/60s to accommodate the bundled PyInstaller binary's real
self-extraction overhead on every invocation (a warm `python3 -m`
process in dev mode does not pay this cost) plus a possible one-time
macOS Gatekeeper scan on an unsigned binary's very first execution on a
machine.

## Hardening Pass (2026-07-20)

An architecture review of the packaged app surfaced several real gaps,
fixed and verified against a freshly built, freshly packaged `.app`
(`npm run electron:pack`):

- **The production server bound to every network interface, not just
  this machine.** Next's standalone `server.js` falls back to
  `HOSTNAME || "0.0.0.0"` when unset, and `startProductionServer()`
  never set it -- so `/api/investigate`, `/api/git-summary`, and
  `/api/claude-local-summary` were reachable by any other device on the
  same network by default. Fixed by setting `HOSTNAME: "127.0.0.1"`
  alongside `PORT` in `electron/main.js`. Verified with `lsof
  -iTCP:3820 -sTCP:LISTEN`, which now shows `127.0.0.1:3820` instead of
  a wildcard bind.
- **Investigation output was written to a shared temp directory with
  default, world-readable permissions.** `web_investigate.py`'s
  `--output-file` used a plain `open(path, "w")`. Fixed with `os.open(...,
  0o600)` so the file (which can contain real project evidence, commit
  content, and Claude session excerpts) is owner-only. Verified with
  `stat -f "%Sp"` showing `-rw-------` on a real investigation run.
- **A second launch (e.g. an extra Dock click before the first fully
  quits) silently hung for 30 seconds then quit with no explanation** --
  it was racing the first instance for port 3820 and losing. Fixed with
  `app.requestSingleInstanceLock()`; the second launch now exits
  immediately and focuses the existing window instead.
- **No supervision if the production server child died mid-session** --
  every subsequent request would just fail with no explanation. Fixed
  with an `exit` handler that shows a clear dialog telling the user to
  relaunch, instead of a silently broken UI.
- **`server.log` had no rotation**, appending every request's Python
  subprocess output for the app's entire install lifetime. Fixed with a
  5MB size cap, truncated on launch when exceeded.
- Added a `will-navigate` guard on the `BrowserWindow` as
  defense-in-depth: nothing currently renders attacker-influenced links,
  but evidence content (commit messages, chat excerpts) is arbitrary
  text Workprint didn't author, so the window can no longer be navigated
  outside its own local server.

The existing "Build full report" / git-summary / Claude-summary buttons
already disabled themselves while a request was in flight, so no
concurrency guard was needed there.

**A second real bug turned up while verifying the rebuilt DMG for this
pass**, not from code review: `/api/git-summary` intermittently hung for
the full 15s timeout under a normal `open`/double-click launch, despite
succeeding in ~5s every time when the same binary was launched from a
terminal. This is the same GUI-launched-context pipe unreliability
`/api/investigate` was already fixed for -- it turns out that bug isn't
limited to large payloads; it can hit small ones too, just less
predictably. Fixed by applying the identical `--output-file` pattern to
`git_summary.py` and `claude_local_summary.py` (owner-only permissions
included) and their routes. Verified by launching the rebuilt app via
`open` and firing 8 consecutive `git-summary` calls and 4 consecutive
`claude-local-summary` calls with no hangs, after reproducing the hang
on the pre-fix build first.

## What Remains

This is the honest gap between "a real installer exists and works" and
"anyone can be handed a link and it just works with zero friction":

- **No code signing or notarization.** The current build is genuinely
  unsigned (ad hoc only, `identity: null` in `package.json`'s `build`
  config). It runs correctly once opened, but macOS Gatekeeper will still
  show its standard "Apple could not verify this app" warning on first
  launch from Finder, requiring the user to right-click and choose
  "Open" once (or approve it in System Settings). This is expected,
  unavoidable behavior for any unsigned Mac app, not a bug -- and it is
  not something that can be resolved on the project owner's behalf. Real
  code signing requires a paid Apple Developer Program membership and the
  owner's own signing identity; notarization additionally requires
  submitting builds to Apple's own service with those same credentials.
- **Only macOS (arm64) has been built and verified.** `electron-builder`'s
  config only specifies a `mac` target. Windows and Linux packaging is
  unconfigured and completely untested; `BACKEND_BINARY_NAME` in
  `electron/main.js` already accounts for the `.exe` suffix Windows would
  need, but nothing else has been adapted or verified for those
  platforms.
- **No auto-update.** `electron-builder` supports this, but it is not
  configured; every new version currently means building and
  redistributing a new `.dmg` by hand.
- **No automated tests for the Electron/packaging layer itself**
  (`electron/main.js`, the build scripts, `electron-builder` config).
  This codebase has no JS/TS test framework at all yet (matching the
  pre-existing state of its frontend test coverage), so this layer is
  verified by actually building and running the real packaged app, as
  documented above, rather than by unit tests. The two new pieces of
  Python behavior this milestone added (`bundled_cli.py`'s dispatcher,
  `web_investigate.py`'s `--output-file` flag) do have real automated
  tests, in `tests/test_bundled_cli.py` and `tests/test_web_investigate.py`.

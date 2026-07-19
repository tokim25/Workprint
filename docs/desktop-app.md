# Desktop App (Electron)

Workprint can run inside an Electron shell instead of a plain browser tab,
which unlocks one thing a browser genuinely cannot do: a native OS folder
picker with a real filesystem path. This is part of the Low-Code/No-Code
milestone -- see `PROJECT_PLAN.md` for the full picture, including what
this does not cover yet.

## Running It Today (Development Mode)

```bash
npm install
npm run electron:dev
```

This spawns `next dev` as a child process, waits for it to respond, and
opens an Electron `BrowserWindow` pointed at it -- the same Next.js app
that runs in a browser, just wrapped in a native window. `npm run dev`
(no Electron) still works exactly as before for anyone who prefers a
browser tab.

Requires Node.js and npm already installed, the same as running the web
app directly. This mode is for development and testing, not end-user
distribution -- see "What Remains" below.

## What The Electron Shell Adds

`electron/main.js` registers a `dialog:choose-project-folder` IPC handler
that opens the OS's native "Choose Folder" dialog and returns a real
absolute path. `electron/preload.js` exposes this to the page as
`window.workprintElectron.chooseProjectFolder()` via `contextBridge`
(`contextIsolation: true`, `nodeIntegration: false`).

`components/workprint-app.tsx` detects this bridge with
`useSyncExternalStore` (hydration-safe, since `window` does not exist
during server rendering) and swaps the "Local project path" text field for
a "Choose Project Folder" button when it is available -- no path-typing at
all inside the desktop app. In a plain browser (or `npm run dev` without
Electron), the manual text field remains exactly as it was, since the
browser's File System Access API cannot hand back a real OS path from any
in-browser picker.

## What Remains

This is the honest gap between "the Electron shell works" and "a
non-coder can double-click an installer with no terminal at all":

- **The Python backend still assumes a system `python3`.** Verified
  separately (not yet wired in) that `pyinstaller --onefile` can bundle
  the `workprint` console script into a fully standalone ~9MB binary that
  runs `workprint discover` correctly with no Python installed and no
  `PYTHONPATH` set. Wiring this in means: bundling equivalent standalone
  entry points for `git_summary`, `claude_local_summary`, and
  `web_investigate` (the modules the Next.js API routes actually spawn),
  updating those routes to invoke the bundled binary instead of
  `python3 -m ...`, and including the binary as an `electron-builder`
  `extraResource`.
- **No production build path yet.** `npm run electron:dev` always spawns
  `next dev`. A real installer needs a pre-built `next build` (standalone
  output mode) started directly by Electron's main process, not a
  developer-mode dev server.
- **No `electron-builder` packaging config, and no code signing or
  notarization.** Both are real, separate pieces of work; code signing in
  particular requires a paid Apple Developer Program membership and
  Windows code-signing certificate that only the project owner can obtain
  -- this is not something that can be set up on someone else's behalf.

None of this blocks using Workprint today. It blocks handing a stranger a
single file and having it just work with zero setup, which is the actual
bar "no-code" implies.

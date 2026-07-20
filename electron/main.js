const { app, BrowserWindow, dialog, ipcMain } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");

const DEV_SERVER_URL = "http://localhost:3000";
const PROD_SERVER_PORT = 3820;
const PROD_SERVER_URL = `http://localhost:${PROD_SERVER_PORT}`;
const READY_CHECK_INTERVAL_MS = 300;
const READY_CHECK_TIMEOUT_MS = 30_000;
const BACKEND_BINARY_NAME =
  process.platform === "win32" ? "workprint-backend.exe" : "workprint-backend";

let nextServerProcess = null;
let mainWindow = null;
let productionServerReady = false;
let isQuittingApp = false;
const MAX_SERVER_LOG_BYTES = 5 * 1024 * 1024;

app.setName("Workprint");

// Without this, launching a second instance (e.g. a stray extra Dock
// click before the first has finished quitting) starts a second
// production server that races the first for PROD_SERVER_PORT, loses,
// and hangs silently until READY_CHECK_TIMEOUT_MS before quitting with
// no message to the user. Bail out of the second instance immediately
// instead, and focus the first instance's window.
const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
}

function waitForServerReady(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;

  return new Promise((resolve, reject) => {
    function attempt() {
      const request = http.get(url, (response) => {
        response.destroy();
        resolve();
      });
      request.on("error", () => {
        if (Date.now() > deadline) {
          reject(new Error(`Timed out waiting for ${url} to become ready`));
          return;
        }
        setTimeout(attempt, READY_CHECK_INTERVAL_MS);
      });
    }
    attempt();
  });
}

function startDevServer() {
  // Spawns `next dev` via npm, which must already be on PATH -- true for
  // a developer running `npm run electron:dev`, not for a packaged end
  // user (see startProductionServer for that path).
  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
  const child = spawn(npmCommand, ["run", "dev"], {
    cwd: path.join(__dirname, ".."),
    env: process.env,
    stdio: "inherit",
  });
  nextServerProcess = child;
  return child;
}

function startProductionServer() {
  // electron-builder's extraResources config (see package.json's "build"
  // field) copies the Next.js standalone build and the PyInstaller-built
  // Python backend into process.resourcesPath at these two paths.
  const serverEntry = path.join(process.resourcesPath, "standalone", "server.js");
  const backendBinary = path.join(
    process.resourcesPath,
    "backend",
    BACKEND_BINARY_NAME,
  );
  // stdio: "inherit" would pass along Electron's own stdout/stderr, which
  // is not a real, working pipe when the app is launched from Finder/
  // `open` (no attached terminal) rather than a shell. That mismatch was
  // measured to stall this child's own ability to service its grandchild
  // Python subprocess's output under load: a real API call worked in ~12s
  // launched from a terminal, but hung past a 60s timeout launched via
  // `open`. Real pipes avoid depending on Electron's stdio validity;
  // logging to a file rather than forwarding to process.stdout avoids the
  // same risk in the main process's own (possibly equally invalid) stdio.
  const child = spawn(process.execPath, [serverEntry], {
    cwd: path.dirname(serverEntry),
    env: {
      ...process.env,
      ELECTRON_RUN_AS_NODE: "1",
      // Next's standalone server.js falls back to HOSTNAME || "0.0.0.0"
      // when unset, which binds the investigate/git-summary/claude-local-
      // summary endpoints to every network interface -- reachable by any
      // other device on the same LAN, not just this machine. Force
      // loopback-only.
      HOSTNAME: "127.0.0.1",
      PORT: String(PROD_SERVER_PORT),
      WORKPRINT_BACKEND_BIN: backendBinary,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const logPath = path.join(app.getPath("userData"), "server.log");
  // Each request's Python subprocess stdout/stderr appends here for the
  // app's entire install lifetime with no rotation otherwise -- cap it
  // instead of letting it grow unbounded across months of use.
  try {
    if (fs.statSync(logPath).size > MAX_SERVER_LOG_BYTES) {
      fs.truncateSync(logPath, 0);
    }
  } catch {
    // No existing log file yet -- nothing to truncate.
  }
  const logStream = fs.createWriteStream(logPath, { flags: "a" });
  child.stdout.pipe(logStream);
  child.stderr.pipe(logStream);

  child.on("exit", () => {
    // Suppress the dialog for our own intentional kill on quit, and for
    // exits during startup -- createWindow()'s waitForServerReady/.catch
    // already surfaces a startup failure without this handler's help.
    if (productionServerReady && !isQuittingApp) {
      dialog.showErrorBox(
        "Workprint's local server stopped",
        "Workprint's local server process exited unexpectedly. Please relaunch the app to continue.",
      );
    }
  });

  nextServerProcess = child;
  return child;
}

async function createWindow() {
  const serverUrl = app.isPackaged ? PROD_SERVER_URL : DEV_SERVER_URL;
  await waitForServerReady(serverUrl, READY_CHECK_TIMEOUT_MS);
  if (app.isPackaged) {
    productionServerReady = true;
  }

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    icon: path.join(__dirname, "icon.png"),
    title: "Workprint",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const allowedOrigin = new URL(serverUrl).origin;
  mainWindow.webContents.on("will-navigate", (event, targetUrl) => {
    // Nothing in the app currently renders attacker-influenced links, but
    // evidence content (commit messages, chat excerpts) is arbitrary text
    // Workprint didn't author -- block navigating this window anywhere
    // outside its own local server as defense-in-depth.
    if (new URL(targetUrl).origin !== allowedOrigin) {
      event.preventDefault();
    }
  });

  mainWindow.loadURL(serverUrl);
}

ipcMain.handle("workprint:choose-project-folder", async () => {
  if (!mainWindow) {
    return { canceled: true, path: null };
  }
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openDirectory"],
    title: "Choose your project folder",
  });
  if (result.canceled || result.filePaths.length === 0) {
    return { canceled: true, path: null };
  }
  return { canceled: false, path: result.filePaths[0] };
});

app.on("second-instance", () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    mainWindow.focus();
  }
});

app.whenReady().then(() => {
  // BrowserWindow's `icon` option only sets the title-bar icon on
  // Windows/Linux -- on macOS the Dock icon is a separate API and, when
  // running unpackaged (`electron .`), defaults to the generic Electron
  // icon unless set explicitly here.
  if (process.platform === "darwin" && app.dock) {
    app.dock.setIcon(path.join(__dirname, "icon.png"));
  }
  if (app.isPackaged) {
    startProductionServer();
  } else {
    startDevServer();
  }
  createWindow().catch((error) => {
    console.error("Failed to start Workprint desktop app:", error);
    app.quit();
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow().catch((error) => console.error(error));
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  isQuittingApp = true;
  if (nextServerProcess) {
    nextServerProcess.kill();
  }
});

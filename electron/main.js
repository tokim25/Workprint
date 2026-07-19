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

app.setName("Workprint");

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
      PORT: String(PROD_SERVER_PORT),
      WORKPRINT_BACKEND_BIN: backendBinary,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const logPath = path.join(app.getPath("userData"), "server.log");
  const logStream = fs.createWriteStream(logPath, { flags: "a" });
  child.stdout.pipe(logStream);
  child.stderr.pipe(logStream);
  nextServerProcess = child;
  return child;
}

async function createWindow() {
  const serverUrl = app.isPackaged ? PROD_SERVER_URL : DEV_SERVER_URL;
  await waitForServerReady(serverUrl, READY_CHECK_TIMEOUT_MS);

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
  if (nextServerProcess) {
    nextServerProcess.kill();
  }
});

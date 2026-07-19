const { app, BrowserWindow, dialog, ipcMain } = require("electron");
const { spawn } = require("node:child_process");
const path = require("node:path");
const http = require("node:http");

const DEV_SERVER_URL = "http://localhost:3000";
const READY_CHECK_INTERVAL_MS = 300;
const READY_CHECK_TIMEOUT_MS = 30_000;

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

function startNextServer() {
  // Development mode only: spawns `next dev` via npm, which must already
  // be on PATH (true for a developer running `npm run electron:dev`, not
  // for an end user). Production packaging bundles a pre-built `next
  // start` / standalone server directly with the app instead, so end
  // users never need Node.js or npm installed themselves -- see the
  // "Build Electron wrapper with bundled Python backend" milestone item.
  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
  const child = spawn(npmCommand, ["run", "dev"], {
    cwd: path.join(__dirname, ".."),
    env: process.env,
    stdio: "inherit",
  });
  nextServerProcess = child;
  return child;
}

async function createWindow() {
  await waitForServerReady(DEV_SERVER_URL, READY_CHECK_TIMEOUT_MS);

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

  mainWindow.loadURL(DEV_SERVER_URL);
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
  startNextServer();
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

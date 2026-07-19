const { contextBridge, ipcRenderer } = require("electron");

// Exposed as window.workprintElectron. The renderer (the same Next.js app
// that also runs in a plain browser) checks for this object's presence to
// decide whether the native OS folder dialog is available; when it is
// not (a plain browser, or `npm run dev` outside Electron), the app falls
// back to the existing manual path text field.
contextBridge.exposeInMainWorld("workprintElectron", {
  chooseProjectFolder: () => ipcRenderer.invoke("workprint:choose-project-folder"),
});

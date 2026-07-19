export type ChooseProjectFolderResult = {
  canceled: boolean;
  path: string | null;
};

type WorkprintElectronBridge = {
  chooseProjectFolder: () => Promise<ChooseProjectFolderResult>;
};

declare global {
  interface Window {
    workprintElectron?: WorkprintElectronBridge;
  }
}

export function isElectronBridgeAvailable(): boolean {
  return typeof window !== "undefined" && Boolean(window.workprintElectron);
}

export async function chooseProjectFolderNative(): Promise<string | null> {
  if (typeof window === "undefined" || !window.workprintElectron) {
    return null;
  }
  const result = await window.workprintElectron.chooseProjectFolder();
  return result.canceled ? null : result.path;
}

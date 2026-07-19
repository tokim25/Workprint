/**
 * Resolves how to invoke a Workprint Python bridge module.
 *
 * In a packaged Electron app, Electron's main process sets
 * WORKPRINT_BACKEND_BIN to the path of a bundled PyInstaller binary that
 * dispatches to the same bridge modules' main() functions, so packaged
 * end users need no system Python install. In dev mode (npm run dev or
 * npm run electron:dev), that variable is unset, so this falls back to
 * the existing `python3 -m workprint.<module>` invocation.
 */
export function workprintPythonCommand(
  subcommand: string,
  args: string[],
): { command: string; args: string[] } {
  const bundledBin = process.env.WORKPRINT_BACKEND_BIN;
  if (bundledBin) {
    return { command: bundledBin, args: [subcommand, ...args] };
  }
  const moduleName = `workprint.${subcommand.replace(/-/g, "_")}`;
  return {
    command: process.env.WORKPRINT_PYTHON ?? "python3",
    args: ["-m", moduleName, ...args],
  };
}

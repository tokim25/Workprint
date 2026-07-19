// electron-builder's extraResources file-matcher silently drops any
// nested `node_modules` directory it copies (a known limitation, not
// something the "filter" option overrides), which broke
// .next/standalone's own traced node_modules -- required at runtime by
// the packaged app's production Next.js server. This afterPack hook
// copies it in directly with plain fs, bypassing that matcher entirely.
// dist-backend has no nested node_modules and copies fine via the
// normal "extraResources" config in package.json, so it is not
// duplicated here.
const { cpSync, existsSync } = require("node:fs");
const { execFileSync } = require("node:child_process");
const path = require("node:path");

exports.default = async function afterPack(context) {
  const root = path.join(__dirname, "..");
  const standaloneSource = path.join(root, ".next", "standalone");
  const isMac = context.electronPlatformName === "darwin";
  const appPath = isMac
    ? path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`)
    : null;
  const resourcesDir = isMac
    ? path.join(appPath, "Contents", "Resources")
    : path.join(context.appOutDir, "resources");
  const standaloneDest = path.join(resourcesDir, "standalone");

  if (!existsSync(standaloneSource)) {
    throw new Error(`${standaloneSource} does not exist -- run "npm run build:standalone" first.`);
  }

  cpSync(standaloneSource, standaloneDest, { recursive: true, force: true });
  console.log(`[after-pack] copied ${standaloneSource} -> ${standaloneDest}`);

  if (isMac) {
    // Electron's own binaries ship with a valid ad-hoc signature, but
    // copying extra files into the bundle afterward (here, and via
    // extraResources) invalidates it -- the CodeResources seal no longer
    // matches the actual contents. Gatekeeper treats that mismatch as
    // "damaged" (a hard block), not the milder "unidentified developer"
    // warning a cleanly unsigned or freshly ad-hoc re-signed app gets.
    // Verified with `spctl -a -vvv` before/after this fix.
    execFileSync("codesign", ["--deep", "--force", "--sign", "-", appPath]);
    console.log(`[after-pack] re-signed ${appPath} ad-hoc after adding extra resources`);
  }
};

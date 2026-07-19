// Next.js's standalone output (next.config.ts's `output: "standalone"`)
// deliberately excludes public/ and .next/static -- its own docs say to
// copy them in manually before running server.js. Node's fs.cpSync (not
// a shell `cp -r`) keeps this working the same way on every platform
// electron-builder might target.
const { cpSync, existsSync } = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const standaloneDir = path.join(root, ".next", "standalone");

if (!existsSync(standaloneDir)) {
  console.error(
    `${standaloneDir} does not exist -- run "next build" first (npm run build).`,
  );
  process.exit(1);
}

cpSync(path.join(root, "public"), path.join(standaloneDir, "public"), {
  recursive: true,
});
cpSync(
  path.join(root, ".next", "static"),
  path.join(standaloneDir, ".next", "static"),
  { recursive: true },
);

console.log(`Copied public/ and .next/static into ${standaloneDir}`);

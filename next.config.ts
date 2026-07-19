import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces .next/standalone: a minimal self-contained server with only
  // its actually-used node_modules traced in, instead of requiring the
  // full node_modules tree at runtime. This is what the packaged
  // Electron build serves in production; dev mode is unaffected and
  // still uses `next dev`.
  output: "standalone",
};

export default nextConfig;

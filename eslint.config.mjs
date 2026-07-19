import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextVitals,
  ...nextTypescript,
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "out/**",
      "release/**",
      "dist-backend/**",
      "build-backend/**",
    ],
  },
  {
    // Electron main/preload processes and Node build scripts conventionally
    // use CommonJS require() rather than ESM import, independent of the
    // rest of this app.
    files: ["electron/**/*.js", "scripts/**/*.js"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
];

export default eslintConfig;

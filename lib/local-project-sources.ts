import type { ProjectSource } from "@/lib/sample-data";

export type LocalProjectFile = {
  name: string;
  path: string;
};

export type LocalProjectSummary = {
  fileCount: number;
  folderName: string;
  sources: ProjectSource[];
};

const documentationExtensions = new Set([
  ".adoc",
  ".doc",
  ".docx",
  ".md",
  ".mdx",
  ".pdf",
  ".rst",
  ".txt",
]);

const configurationNames = new Set([
  ".env.example",
  ".eslintrc",
  ".gitignore",
  ".prettierrc",
  "components.json",
  "next.config.js",
  "next.config.mjs",
  "next.config.ts",
  "package.json",
  "postcss.config.js",
  "postcss.config.mjs",
  "pyproject.toml",
  "tailwind.config.js",
  "tailwind.config.ts",
  "tsconfig.json",
  "vite.config.ts",
]);

const configurationExtensions = new Set([
  ".config.js",
  ".config.mjs",
  ".config.ts",
  ".ini",
  ".json",
  ".toml",
  ".yaml",
  ".yml",
]);

const designExtensions = new Set([
  ".ai",
  ".fig",
  ".figma",
  ".psd",
  ".sketch",
  ".svg",
  ".xd",
]);

const conversationHints = [
  "ai-history",
  "chatgpt",
  "claude",
  "conversation",
  "copilot",
  "prompt",
  "prompts",
  "transcript",
];

const sourceExtensions = new Set([
  ".css",
  ".go",
  ".html",
  ".java",
  ".js",
  ".jsx",
  ".kt",
  ".php",
  ".py",
  ".rb",
  ".rs",
  ".scss",
  ".swift",
  ".ts",
  ".tsx",
  ".vue",
]);

export function summarizeLocalProject(
  files: LocalProjectFile[],
  fallbackFolderName: string,
): LocalProjectSummary {
  const folderName = getFolderName(files, fallbackFolderName);
  const normalizedFiles = files.map((file) => ({
    name: file.name,
    path: normalizePath(file.path || file.name),
  }));

  const gitFound = normalizedFiles.some((file) => pathIncludesGit(file.path));
  const projectFiles = normalizedFiles.filter((file) => {
    const extension = getExtension(file.name);
    return sourceExtensions.has(extension);
  });
  const documentationFiles = normalizedFiles.filter((file) => {
    const extension = getExtension(file.name);
    const path = file.path.toLowerCase();
    return documentationExtensions.has(extension) || path.includes("/docs/");
  });
  const configurationFiles = normalizedFiles.filter((file) => {
    const lowerName = file.name.toLowerCase();
    const lowerPath = file.path.toLowerCase();
    const extension = getExtension(lowerName);
    return (
      configurationNames.has(lowerName) ||
      configurationExtensions.has(extension) ||
      lowerPath.includes("/config/")
    );
  });
  const designFiles = normalizedFiles.filter((file) =>
    designExtensions.has(getExtension(file.name)),
  );
  const conversationFiles = normalizedFiles.filter((file) => {
    const searchableName = file.path.toLowerCase();
    return conversationHints.some((hint) => searchableName.includes(hint));
  });

  return {
    fileCount: files.length,
    folderName,
    sources: [
      {
        id: "local-git-repository",
        name: "Git repository metadata",
        description: gitFound
          ? "Found a .git entry in the selected folder."
          : "No .git entry was visible in the selected folder.",
        status: gitFound ? "ready" : "unsupported",
        note: gitFound
          ? "This only means the folder appears to be a Git repository. Workprint has not read commit history."
          : "Not available from the selected folder listing.",
        count: gitFound ? 1 : 0,
        countLabel: gitFound ? "entry found" : "entries found",
      },
      makeSource(
        "local-project-files",
        "Project files",
        "Recognized source files by filename extension.",
        projectFiles.length,
      ),
      makeSource(
        "local-documentation",
        "Documentation",
        "Recognized documentation files and docs folders.",
        documentationFiles.length,
      ),
      makeSource(
        "local-configuration",
        "Configuration files",
        "Recognized configuration files by name or extension.",
        configurationFiles.length,
      ),
      makeSource(
        "local-design",
        "Design files",
        "Recognized design files by extension.",
        designFiles.length,
      ),
      makeSource(
        "local-ai-history",
        "Conversation or AI-history files",
        "Recognized explicit conversation, prompt, transcript, or AI-history filenames.",
        conversationFiles.length,
      ),
    ],
  };
}

function makeSource(
  id: string,
  name: string,
  foundDescription: string,
  count: number,
): ProjectSource {
  return {
    id,
    name,
    description:
      count > 0 ? foundDescription : "No matching local files were recognized.",
    status: count > 0 ? "ready" : "unsupported",
    note:
      count > 0
        ? "Found by filename, folder path, or extension only. File contents were not read."
        : "Not available in the selected folder listing.",
    count,
    countLabel: count === 1 ? "file found" : "files found",
  };
}

function getFolderName(files: LocalProjectFile[], fallbackFolderName: string) {
  const firstPath = normalizePath(files[0]?.path ?? "");
  const firstPathSegments = firstPath.split("/").filter(Boolean);
  const firstSegment = firstPathSegments.length > 1 ? firstPathSegments[0] : "";
  return firstSegment || fallbackFolderName || "Selected project";
}

function getExtension(filename: string) {
  const lowerName = filename.toLowerCase();
  const lastDot = lowerName.lastIndexOf(".");

  if (lastDot <= 0) {
    return "";
  }

  return lowerName.slice(lastDot);
}

function normalizePath(path: string) {
  return path.replaceAll("\\", "/");
}

function pathIncludesGit(path: string) {
  const segments = normalizePath(path).split("/");
  return segments.includes(".git");
}

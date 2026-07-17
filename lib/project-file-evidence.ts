import type { LocalProjectFile } from "@/lib/local-project-sources";

export const PROJECT_FILE_EVIDENCE_LIMITS = {
  maxEligibleFiles: 25,
  maxBytesPerFile: 100_000,
  maxTotalBytesRead: 500_000,
  maxExcerptCharacters: 600,
  maxExcerptLines: 12,
} as const;

export type ProjectFileEvidenceStatus =
  | "eligible"
  | "read"
  | "excluded"
  | "unsupported"
  | "blocked_sensitive"
  | "blocked_oversized";

export type ProjectFileEvidenceCandidate = {
  extension: string;
  file: LocalProjectFile;
  manifestType: string | null;
  path: string;
  reason: string;
  size: number | null;
  status: ProjectFileEvidenceStatus;
};

export type ProjectFileEvidenceFact = {
  excerpt: string;
  extension: string;
  lineCount: number;
  manifestType: string | null;
  name: string;
  path: string;
  size: number;
};

const allowedExtensions = new Set([
  ".adoc",
  ".json",
  ".md",
  ".mdx",
  ".rst",
  ".toml",
  ".txt",
  ".yaml",
  ".yml",
]);

const manifestNames = new Set([
  "package.json",
  "pyproject.toml",
  "tsconfig.json",
]);

const blockedDirectories = new Set([
  ".cache",
  ".git",
  ".next",
  ".nuxt",
  ".parcel-cache",
  ".svelte-kit",
  ".turbo",
  "bower_components",
  "build",
  "coverage",
  "dist",
  "node_modules",
  "out",
  "target",
  "tmp",
  "vendor",
]);

const sensitivePatterns = [
  ".env",
  "credential",
  "credentials",
  "keychain",
  "passwd",
  "password",
  "private-key",
  "private_key",
  "secret",
  "secrets",
  "token",
];

const sensitiveExtensions = new Set([
  ".cer",
  ".cert",
  ".crt",
  ".der",
  ".key",
  ".p12",
  ".pem",
  ".pfx",
]);

export function getProjectFileCandidates(files: LocalProjectFile[]) {
  let eligibleCount = 0;

  return files.map((file): ProjectFileEvidenceCandidate => {
    const path = normalizePath(file.path || file.name);
    const name = file.name || lastPathSegment(path);
    const extension = getExtension(name);
    const size = typeof file.size === "number" ? file.size : file.file?.size ?? null;
    const manifestType = getManifestType(name);

    if (isInBlockedDirectory(path)) {
      return candidate(file, path, extension, manifestType, size, "unsupported", "Inside a generated, dependency, cache, vendor, build, or Git folder.");
    }

    if (isSensitivePath(path, extension)) {
      return candidate(file, path, extension, manifestType, size, "blocked_sensitive", "Blocked because the name or path looks sensitive.");
    }

    if (!isAllowedContent(name, extension)) {
      return candidate(file, path, extension, manifestType, size, "unsupported", "This file type is counted by metadata only in this milestone.");
    }

    if (!file.file) {
      return candidate(file, path, extension, manifestType, size, "unsupported", "The browser did not provide a readable file handle.");
    }

    if (size !== null && size > PROJECT_FILE_EVIDENCE_LIMITS.maxBytesPerFile) {
      return candidate(file, path, extension, manifestType, size, "blocked_oversized", "Blocked because it is larger than the per-file reading limit.");
    }

    if (eligibleCount >= PROJECT_FILE_EVIDENCE_LIMITS.maxEligibleFiles) {
      return candidate(file, path, extension, manifestType, size, "unsupported", "Outside the v0 eligible-file limit for this project.");
    }

    eligibleCount += 1;
    return candidate(file, path, extension, manifestType, size, "eligible", "Eligible for browser-local reading after confirmation.");
  });
}

export async function readProjectFileEvidence(
  candidates: ProjectFileEvidenceCandidate[],
  excludedPaths: Set<string>,
) {
  const facts: ProjectFileEvidenceFact[] = [];
  let totalBytesRead = 0;

  for (const item of candidates) {
    if (item.status !== "eligible" || excludedPaths.has(item.path) || !item.file.file) {
      continue;
    }

    const size = item.size ?? item.file.file.size;
    if (totalBytesRead + size > PROJECT_FILE_EVIDENCE_LIMITS.maxTotalBytesRead) {
      continue;
    }

    const text = await item.file.file.text();
    totalBytesRead += size;

    facts.push({
      excerpt: boundedExcerpt(text),
      extension: item.extension,
      lineCount: lineCount(text),
      manifestType: item.manifestType,
      name: item.file.name,
      path: item.path,
      size,
    });
  }

  return facts;
}

export function describeFileKind(item: Pick<ProjectFileEvidenceCandidate, "extension" | "manifestType">) {
  return item.manifestType ?? (item.extension || "no extension");
}

function candidate(
  file: LocalProjectFile,
  path: string,
  extension: string,
  manifestType: string | null,
  size: number | null,
  status: ProjectFileEvidenceStatus,
  reason: string,
): ProjectFileEvidenceCandidate {
  return { extension, file, manifestType, path, reason, size, status };
}

function boundedExcerpt(text: string) {
  const lines = text.replaceAll("\r\n", "\n").replaceAll("\r", "\n").split("\n");
  const visibleLines = lines.slice(0, PROJECT_FILE_EVIDENCE_LIMITS.maxExcerptLines);
  let excerpt = visibleLines.join("\n").slice(0, PROJECT_FILE_EVIDENCE_LIMITS.maxExcerptCharacters);

  if (text.length > excerpt.length) {
    excerpt = `${excerpt.trimEnd()}\n...`;
  }

  return excerpt;
}

function getExtension(filename: string) {
  const lowerName = filename.toLowerCase();
  const lastDot = lowerName.lastIndexOf(".");

  if (lastDot <= 0) {
    return "";
  }

  return lowerName.slice(lastDot);
}

function getManifestType(filename: string) {
  const lowerName = filename.toLowerCase();

  if (!manifestNames.has(lowerName)) {
    return null;
  }

  if (lowerName === "package.json") {
    return "package manifest";
  }

  if (lowerName === "pyproject.toml") {
    return "Python project manifest";
  }

  return "TypeScript configuration";
}

function isAllowedContent(filename: string, extension: string) {
  const lowerName = filename.toLowerCase();
  return lowerName.startsWith("readme") || manifestNames.has(lowerName) || allowedExtensions.has(extension);
}

function isInBlockedDirectory(path: string) {
  return path
    .split("/")
    .filter(Boolean)
    .slice(0, -1)
    .some((segment) => blockedDirectories.has(segment.toLowerCase()));
}

function isSensitivePath(path: string, extension: string) {
  const lowerPath = path.toLowerCase();

  if (sensitiveExtensions.has(extension)) {
    return true;
  }

  return sensitivePatterns.some((pattern) => {
    if (pattern === ".env") {
      return lowerPath
        .split("/")
        .some((segment) => segment === ".env" || segment.startsWith(".env."));
    }

    return lowerPath.includes(pattern);
  });
}

function lastPathSegment(path: string) {
  return path.split("/").filter(Boolean).at(-1) ?? path;
}

function lineCount(text: string) {
  if (text.length === 0) {
    return 0;
  }

  return text.replaceAll("\r\n", "\n").replaceAll("\r", "\n").split("\n").length;
}

function normalizePath(path: string) {
  return path.replaceAll("\\", "/");
}

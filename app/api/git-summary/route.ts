import { realpath, stat } from "node:fs/promises";
import { spawn } from "node:child_process";
import { NextResponse } from "next/server";

const MAX_PATH_LENGTH = 4096;
const DEFAULT_COMMIT_LIMIT = 5;
const MAX_COMMIT_LIMIT = 20;
const PROCESS_TIMEOUT_MS = 8000;

type GitSummaryRequest = {
  repositoryPath?: unknown;
  commitLimit?: unknown;
};

type SafeErrorCode =
  | "adapter_failed"
  | "adapter_timeout"
  | "adapter_unavailable"
  | "git_read_failed"
  | "git_unavailable"
  | "invalid_request"
  | "missing_path"
  | "not_directory"
  | "not_git_repository"
  | "path_not_found"
  | "path_too_long"
  | "unsupported_repository";

export async function POST(request: Request) {
  let body: GitSummaryRequest;

  try {
    body = await request.json();
  } catch {
    return errorResponse(
      "invalid_request",
      "Send a repository path as JSON.",
      400,
    );
  }

  if (!body || typeof body !== "object") {
    return errorResponse(
      "invalid_request",
      "Send a repository path as JSON.",
      400,
    );
  }

  const pathResult = await canonicalRepositoryPath(body.repositoryPath);
  if (!pathResult.ok) {
    return errorResponse(pathResult.code, pathResult.message, pathResult.status);
  }

  const limitResult = boundedCommitLimit(body.commitLimit);
  if (!limitResult.ok) {
    return errorResponse("invalid_request", "Commit limit must be a number.", 400);
  }

  const pythonResult = await runGitSummary(pathResult.path, limitResult.limit);

  if (!pythonResult.ok) {
    return errorResponse(pythonResult.code, pythonResult.message, pythonResult.status);
  }

  return NextResponse.json(pythonResult.payload);
}

export function GET() {
  return errorResponse(
    "invalid_request",
    "Git summaries must be requested with POST.",
    405,
  );
}

async function canonicalRepositoryPath(
  repositoryPath: unknown,
): Promise<
  | { ok: true; path: string }
  | { ok: false; code: SafeErrorCode; message: string; status: number }
> {
  if (typeof repositoryPath !== "string" || !repositoryPath.trim()) {
    return {
      ok: false,
      code: "missing_path",
      message: "Enter a local repository path.",
      status: 400,
    };
  }

  if (repositoryPath.length > MAX_PATH_LENGTH) {
    return {
      ok: false,
      code: "path_too_long",
      message: "Repository path is too long.",
      status: 400,
    };
  }

  try {
    const canonicalPath = await realpath(repositoryPath);
    const pathStat = await stat(canonicalPath);

    if (!pathStat.isDirectory()) {
      return {
        ok: false,
        code: "not_directory",
        message: "Repository path must be a folder.",
        status: 400,
      };
    }

    return { ok: true, path: canonicalPath };
  } catch {
    return {
      ok: false,
      code: "path_not_found",
      message: "Repository path was not found.",
      status: 404,
    };
  }
}

function boundedCommitLimit(
  commitLimit: unknown,
):
  | { ok: true; limit: number }
  | { ok: false } {
  if (commitLimit === undefined || commitLimit === null) {
    return { ok: true, limit: DEFAULT_COMMIT_LIMIT };
  }

  const limit = Number(commitLimit);
  if (!Number.isInteger(limit) || limit < 1) {
    return { ok: false };
  }

  return { ok: true, limit: Math.min(limit, MAX_COMMIT_LIMIT) };
}

function runGitSummary(repositoryPath: string, commitLimit: number) {
  return new Promise<
    | { ok: true; payload: unknown }
    | { ok: false; code: SafeErrorCode; message: string; status: number }
  >((resolve) => {
    const child = spawn(
      process.env.WORKPRINT_PYTHON ?? "python3",
      [
        "-m",
        "workprint.git_summary",
        "--repository",
        repositoryPath,
        "--limit",
        String(commitLimit),
      ],
      {
        env: {
          ...process.env,
          PYTHONPATH: "src",
        },
        shell: false,
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    let stdout = "";
    let settled = false;
    const timeout = setTimeout(() => {
      settled = true;
      child.kill("SIGTERM");
      resolve({
        ok: false,
        code: "adapter_timeout",
        message: "Git summary took too long. Try a smaller repository or lower commit limit.",
        status: 504,
      });
    }, PROCESS_TIMEOUT_MS);

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
    });

    child.on("error", () => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      resolve({
        ok: false,
        code: "adapter_unavailable",
        message: "The local Git summary process could not start.",
        status: 500,
      });
    });

    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);

      const parsed = parsePythonPayload(stdout);
      if (!parsed.ok) {
        resolve({
          ok: false,
          code: "adapter_failed",
          message: "Workprint could not read Git metadata for this repository.",
          status: 500,
        });
        return;
      }

      if (code !== 0) {
        const error = safePythonError(parsed.payload);
        resolve({
          ok: false,
          code: error.code,
          message: error.message,
          status: 400,
        });
        return;
      }

      resolve({ ok: true, payload: parsed.payload });
    });
  });
}

function parsePythonPayload(stdout: string):
  | { ok: true; payload: unknown }
  | { ok: false } {
  try {
    return { ok: true, payload: JSON.parse(stdout) };
  } catch {
    return { ok: false };
  }
}

function safePythonError(payload: unknown): { code: SafeErrorCode; message: string } {
  if (
    payload &&
    typeof payload === "object" &&
    "error" in payload &&
    payload.error &&
    typeof payload.error === "object"
  ) {
    const error = payload.error as { code?: unknown; message?: unknown };
    if (typeof error.code === "string" && typeof error.message === "string") {
      return { code: safeErrorCode(error.code), message: error.message };
    }
  }

  return {
    code: "adapter_failed",
    message: "Workprint could not read Git metadata for this repository.",
  };
}

function safeErrorCode(code: string): SafeErrorCode {
  const allowedCodes = new Set<SafeErrorCode>([
    "git_read_failed",
    "git_unavailable",
    "invalid_request",
    "missing_path",
    "not_directory",
    "not_git_repository",
    "path_not_found",
    "path_too_long",
    "unsupported_repository",
  ]);
  return allowedCodes.has(code as SafeErrorCode)
    ? (code as SafeErrorCode)
    : "adapter_failed";
}

function errorResponse(code: SafeErrorCode, message: string, status: number) {
  return NextResponse.json(
    {
      ok: false,
      error: { code, message },
    },
    { status },
  );
}

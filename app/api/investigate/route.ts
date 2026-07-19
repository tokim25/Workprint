import { realpath, stat } from "node:fs/promises";
import { spawn } from "node:child_process";
import { NextResponse } from "next/server";

const MAX_PATH_LENGTH = 4096;
// Longer than git-summary/claude-local-summary's 8s: a full investigation
// does more work (loads every selected source's evidence, not just a
// bounded summary) and the result is a one-time download, not a value
// read on every keystroke.
const PROCESS_TIMEOUT_MS = 30000;

type InvestigateRequest = {
  projectPath?: unknown;
  include?: unknown;
  projectName?: unknown;
  includeDesktopChatDeepParse?: unknown;
};

type SafeErrorCode =
  | "adapter_failed"
  | "adapter_timeout"
  | "adapter_unavailable"
  | "discovery_failed"
  | "invalid_request"
  | "investigation_failed"
  | "missing_path"
  | "no_evidence_selected"
  | "not_directory"
  | "path_not_found"
  | "path_too_long";

export async function POST(request: Request) {
  let body: InvestigateRequest;

  try {
    body = await request.json();
  } catch {
    return errorResponse("invalid_request", "Send a project path as JSON.", 400);
  }

  if (!body || typeof body !== "object") {
    return errorResponse("invalid_request", "Send a project path as JSON.", 400);
  }

  const pathResult = await canonicalProjectPath(body.projectPath);
  if (!pathResult.ok) {
    return errorResponse(pathResult.code, pathResult.message, pathResult.status);
  }

  const include =
    typeof body.include === "string" && body.include.trim() ? body.include : null;
  const projectName =
    typeof body.projectName === "string" && body.projectName.trim()
      ? body.projectName
      : null;
  const includeDesktopChatDeepParse = body.includeDesktopChatDeepParse === true;

  const pythonResult = await runWebInvestigate(
    pathResult.path,
    include,
    projectName,
    includeDesktopChatDeepParse,
  );

  if (!pythonResult.ok) {
    return errorResponse(pythonResult.code, pythonResult.message, pythonResult.status);
  }

  return NextResponse.json(pythonResult.payload);
}

export function GET() {
  return errorResponse(
    "invalid_request",
    "Investigations must be requested with POST.",
    405,
  );
}

async function canonicalProjectPath(
  projectPath: unknown,
): Promise<
  | { ok: true; path: string }
  | { ok: false; code: SafeErrorCode; message: string; status: number }
> {
  if (typeof projectPath !== "string" || !projectPath.trim()) {
    return {
      ok: false,
      code: "missing_path",
      message: "Enter a local project path.",
      status: 400,
    };
  }

  if (projectPath.length > MAX_PATH_LENGTH) {
    return {
      ok: false,
      code: "path_too_long",
      message: "Project path is too long.",
      status: 400,
    };
  }

  try {
    const canonicalPath = await realpath(projectPath);
    const pathStat = await stat(canonicalPath);

    if (!pathStat.isDirectory()) {
      return {
        ok: false,
        code: "not_directory",
        message: "Project path must be a folder.",
        status: 400,
      };
    }

    return { ok: true, path: canonicalPath };
  } catch {
    return {
      ok: false,
      code: "path_not_found",
      message: "Project path was not found.",
      status: 404,
    };
  }
}

function runWebInvestigate(
  projectPath: string,
  include: string | null,
  projectName: string | null,
  includeDesktopChatDeepParse: boolean,
) {
  return new Promise<
    | { ok: true; payload: unknown }
    | { ok: false; code: SafeErrorCode; message: string; status: number }
  >((resolve) => {
    const args = ["-m", "workprint.web_investigate", "--project", projectPath];
    if (include) {
      args.push("--include", include);
    }
    if (projectName) {
      args.push("--project-name", projectName);
    }
    if (includeDesktopChatDeepParse) {
      args.push("--include-desktop-chat-deep-parse");
    }

    const child = spawn(process.env.WORKPRINT_PYTHON ?? "python3", args, {
      env: {
        ...process.env,
        PYTHONPATH: "src",
      },
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let settled = false;
    const timeout = setTimeout(() => {
      settled = true;
      child.kill("SIGTERM");
      resolve({
        ok: false,
        code: "adapter_timeout",
        message: "The investigation took too long for this project.",
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
        message: "The local investigation process could not start.",
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
          message: "Workprint could not generate a report for this project.",
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
    message: "Workprint could not generate a report for this project.",
  };
}

function safeErrorCode(code: string): SafeErrorCode {
  const allowedCodes = new Set<SafeErrorCode>([
    "discovery_failed",
    "invalid_request",
    "investigation_failed",
    "missing_path",
    "no_evidence_selected",
    "not_directory",
    "path_not_found",
    "path_too_long",
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

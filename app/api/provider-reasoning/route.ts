import { NextResponse } from "next/server";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  buildEvidencePacket,
  buildProviderPrompt,
  buildProviderRepairPrompt,
  callReasoningProvider,
  defaultProviderModel,
  GEMINI_FALLBACK_MODELS,
  isProviderCapacityError,
  isReasoningProviderId,
  parseCandidateInsight,
  providerLabel,
  validateCandidateInsight,
  type CandidateInsight,
  type EvidencePacket,
  type EvidencePacketItem,
  type ReasoningFailureCode,
  type ReasoningProviderId,
} from "@/lib/provider-reasoning";

const PROVIDER_TIMEOUT_MS = 45_000;
const MAX_DEBUG_RESPONSE_CHARS = 24_000;

type ReasoningPassResult = {
  insight: CandidateInsight;
  model: string;
  notes: string[];
};

type ProviderCallResult = {
  model: string;
  notes: string[];
  response: string;
};

type ProviderReasoningRequest = {
  apiKey?: unknown;
  evidence?: unknown;
  model?: unknown;
  project?: unknown;
  provider?: unknown;
};

export async function POST(request: Request) {
  let body: ProviderReasoningRequest;

  try {
    body = await request.json();
  } catch {
    return errorResponse("invalid_request", "Send provider, key, and evidence as JSON.", 400);
  }

  const validation = validateRequest(body);
  if (!validation.ok) {
    return errorResponse(validation.code, validation.message, validation.status);
  }

  const packet = buildEvidencePacket({
    project: validation.project,
    provider: validation.provider,
    evidence: validation.evidence.map((item) => ({
      id: item.id,
      source: item.source,
      title: item.title,
      excerpt: item.excerpt,
      supports: item.supports,
      doesNotProve: item.does_not_prove,
    })),
  });

  if (packet.evidence.length === 0) {
    return errorResponse(
      "invalid_request",
      "Select at least one evidence item before asking a provider to reason.",
      400,
    );
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), PROVIDER_TIMEOUT_MS);

  try {
    const firstPass = await runReasoningPass({
      apiKey: validation.apiKey,
      candidate: null,
      mode: "originate",
      model: validation.model,
      packet,
      provider: validation.provider,
      signal: controller.signal,
    });
    const firstValidation = validateCandidateInsight(firstPass.insight, packet);
    if (!firstValidation.ok) {
      return errorResponse(firstValidation.code, firstValidation.message, 400);
    }

    const secondPass = await runReasoningPass({
      apiKey: validation.apiKey,
      candidate: firstPass.insight,
      mode: "corroborate",
      model: firstPass.model,
      packet,
      provider: validation.provider,
      signal: controller.signal,
    });
    const finalValidation = validateCandidateInsight(secondPass.insight, packet);
    if (!finalValidation.ok) {
      return errorResponse(finalValidation.code, finalValidation.message, 400);
    }

    return NextResponse.json({
      ok: true,
      provider: validation.provider,
      providerLabel: providerLabel(validation.provider),
      model: secondPass.model,
      insight: secondPass.insight,
      packet: {
        evidenceCount: packet.evidence.length,
        approximateTokens: packet.approximate_tokens,
        truncated: packet.truncated,
        unknowns: packet.unknowns,
      },
      validation: {
        status: "accepted",
        notes: [
          ...dedupeNotes([...firstPass.notes, ...secondPass.notes]),
          ...firstValidation.notes,
          "A second provider pass corroborated or revised the candidate before display.",
          ...finalValidation.notes,
        ],
      },
    });
  } catch (error) {
    if (controller.signal.aborted) {
      return errorResponse(
        "provider_timeout",
        "The reasoning provider took too long to respond. Try again or choose another provider.",
        504,
      );
    }

    const code = providerErrorCode(error);
    const message =
      error instanceof Error && error.message
        ? error.message
        : "The reasoning provider could not process the evidence packet.";
    return errorResponse(code, message, code === "auth_or_quota_error" ? 401 : 502);
  } finally {
    clearTimeout(timeout);
  }
}

export function GET() {
  return errorResponse(
    "invalid_request",
    "Provider reasoning must be requested with POST.",
    405,
  );
}

async function runReasoningPass(input: {
  apiKey: string;
  candidate: CandidateInsight | null;
  mode: "originate" | "corroborate";
  model: string;
  packet: EvidencePacket;
  provider: ReasoningProviderId;
  signal: AbortSignal;
}): Promise<ReasoningPassResult> {
  const prompt = buildProviderPrompt(
    input.packet,
    input.mode,
    input.candidate ?? undefined,
  );
  const providerResponse = await callProviderWithFallback({
    provider: input.provider,
    apiKey: input.apiKey,
    model: input.model,
    prompt,
    signal: input.signal,
  });
  const parsed = parseCandidateInsight(providerResponse.response);

  if (!parsed) {
    const repairResponse = await callProviderWithFallback({
      provider: input.provider,
      apiKey: input.apiKey,
      model: providerResponse.model,
      prompt: buildProviderRepairPrompt(providerResponse.response),
      signal: input.signal,
    });
    const repaired = parseCandidateInsight(repairResponse.response);
    if (repaired) {
      return {
        insight: repaired,
        model: repairResponse.model,
        notes: dedupeNotes([...providerResponse.notes, ...repairResponse.notes]),
      };
    }

    const debugPath = await writeProviderDebugFile({
      model: repairResponse.model,
      mode: input.mode,
      provider: input.provider,
      repairResponse: repairResponse.response,
      response: providerResponse.response,
      stage: "parse_failed_after_repair",
    });

    throw Object.assign(
      new Error(
        [
          "The provider returned text instead of the structured JSON Workprint requested.",
          debugPath
            ? `Workprint saved a local debug file at ${debugPath}.`
            : "Workprint could not save a local debug file for this response.",
          "Try again, or choose a different provider if it keeps happening.",
        ].join(" "),
      ),
      { code: "malformed_provider_response" satisfies ReasoningFailureCode },
    );
  }

  return {
    insight: parsed,
    model: providerResponse.model,
    notes: providerResponse.notes,
  };
}

async function callProviderWithFallback(input: {
  apiKey: string;
  model: string;
  prompt: string;
  provider: ReasoningProviderId;
  signal: AbortSignal;
}): Promise<ProviderCallResult> {
  try {
    return {
      model: input.model,
      notes: [],
      response: await callReasoningProvider(input),
    };
  } catch (error) {
    if (input.provider !== "gemini" || !isProviderCapacityError(error)) {
      throw error;
    }

    for (const fallbackModel of GEMINI_FALLBACK_MODELS) {
      if (sameModel(input.model, fallbackModel)) {
        continue;
      }

      try {
        return {
          model: fallbackModel,
          notes: [
            `Gemini reported ${input.model} was temporarily busy, so Workprint retried with ${fallbackModel}.`,
          ],
          response: await callReasoningProvider({
            ...input,
            model: fallbackModel,
          }),
        };
      } catch (fallbackError) {
        if (!isProviderCapacityError(fallbackError)) {
          throw fallbackError;
        }
      }
    }

    throw Object.assign(
      new Error(
        "Gemini is currently experiencing high demand. Workprint tried the fallback model too; please try again later or choose another provider.",
      ),
      { code: "provider_failed" satisfies ReasoningFailureCode },
    );
  }
}

function sameModel(left: string, right: string) {
  return left.replace(/^models\//, "") === right.replace(/^models\//, "");
}

function dedupeNotes(notes: string[]) {
  return [...new Set(notes.filter(Boolean))];
}

async function writeProviderDebugFile(input: {
  model: string;
  mode: "originate" | "corroborate";
  provider: ReasoningProviderId;
  repairResponse: string;
  response: string;
  stage: string;
}) {
  try {
    const directory = providerDebugDirectory();
    await mkdir(directory, { recursive: true });
    const timestamp = new Date().toISOString();
    const filename = `${timestamp.replace(/[:.]/g, "-")}-${input.provider}-${input.mode}-${input.stage}.json`;
    const filePath = path.join(directory, filename);
    await writeFile(
      filePath,
      JSON.stringify(
        {
          schema_version: "1.0",
          timestamp,
          provider: input.provider,
          model: input.model,
          mode: input.mode,
          stage: input.stage,
          note: "Local-only debug capture for a provider response Workprint could not parse. API keys and evidence packets are not included.",
          original_response: input.response.slice(0, MAX_DEBUG_RESPONSE_CHARS),
          repair_response: input.repairResponse.slice(0, MAX_DEBUG_RESPONSE_CHARS),
          truncated:
            input.response.length > MAX_DEBUG_RESPONSE_CHARS ||
            input.repairResponse.length > MAX_DEBUG_RESPONSE_CHARS,
        },
        null,
        2,
      ),
      { encoding: "utf-8", mode: 0o600 },
    );
    return filePath;
  } catch {
    return "";
  }
}

function providerDebugDirectory() {
  if (process.env.WORKPRINT_PROVIDER_DEBUG_DIR) {
    return process.env.WORKPRINT_PROVIDER_DEBUG_DIR;
  }

  return path.join(process.cwd(), "workprint-debug");
}

function validateRequest(body: ProviderReasoningRequest):
  | {
      ok: true;
      apiKey: string;
      evidence: EvidencePacketItem[];
      model: string;
      project: string;
      provider: ReasoningProviderId;
    }
  | {
      ok: false;
      code: ReasoningFailureCode;
      message: string;
      status: number;
    } {
  if (!isReasoningProviderId(body.provider)) {
    return {
      ok: false,
      code: "invalid_request",
      message: "Choose OpenAI, Claude, or Gemini before reasoning.",
      status: 400,
    };
  }

  if (typeof body.apiKey !== "string" || !body.apiKey.trim()) {
    return {
      ok: false,
      code: "invalid_request",
      message: "Enter an API key for the selected provider.",
      status: 400,
    };
  }

  if (!Array.isArray(body.evidence)) {
    return {
      ok: false,
      code: "invalid_request",
      message: "Select evidence before reasoning.",
      status: 400,
    };
  }

  const evidence = body.evidence
    .map(normalizeEvidence)
    .filter((item): item is EvidencePacketItem => item !== null);

  return {
    ok: true,
    apiKey: body.apiKey.trim(),
    evidence,
    model:
      typeof body.model === "string" && body.model.trim()
        ? body.model.trim()
        : defaultProviderModel(body.provider),
    project:
      typeof body.project === "string" && body.project.trim()
        ? body.project.trim()
        : "Workprint Project",
    provider: body.provider,
  };
}

function normalizeEvidence(value: unknown): EvidencePacketItem | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const record = value as Record<string, unknown>;
  const id = readString(record.id);
  const source = readString(record.source);
  const title = readString(record.title);
  const excerpt = readString(record.excerpt);
  const supports = readString(record.supports);
  const doesNotProve = readString(record.does_not_prove) || readString(record.doesNotProve);

  if (!id || !source || !title || !excerpt) {
    return null;
  }

  return {
    id,
    source,
    title,
    excerpt,
    supports,
    does_not_prove: doesNotProve,
  };
}

function readString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function providerErrorCode(error: unknown): ReasoningFailureCode {
  if (
    error &&
    typeof error === "object" &&
    "code" in error &&
    typeof (error as { code?: unknown }).code === "string"
  ) {
    const code = (error as { code: string }).code;
    if (
      code === "auth_or_quota_error" ||
      code === "boundary_violation" ||
      code === "invalid_evidence" ||
      code === "invalid_request" ||
      code === "malformed_provider_response" ||
      code === "provider_failed" ||
      code === "provider_timeout"
    ) {
      return code;
    }
  }

  return "provider_failed";
}

function errorResponse(code: ReasoningFailureCode, message: string, status: number) {
  return NextResponse.json({ ok: false, error: { code, message } }, { status });
}

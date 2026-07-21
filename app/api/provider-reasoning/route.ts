import { NextResponse } from "next/server";
import {
  buildEvidencePacket,
  buildProviderPrompt,
  buildProviderRepairPrompt,
  callReasoningProvider,
  defaultProviderModel,
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
    const firstValidation = validateCandidateInsight(firstPass, packet);
    if (!firstValidation.ok) {
      return errorResponse(firstValidation.code, firstValidation.message, 400);
    }

    const secondPass = await runReasoningPass({
      apiKey: validation.apiKey,
      candidate: firstPass,
      mode: "corroborate",
      model: validation.model,
      packet,
      provider: validation.provider,
      signal: controller.signal,
    });
    const finalValidation = validateCandidateInsight(secondPass, packet);
    if (!finalValidation.ok) {
      return errorResponse(finalValidation.code, finalValidation.message, 400);
    }

    return NextResponse.json({
      ok: true,
      provider: validation.provider,
      providerLabel: providerLabel(validation.provider),
      model: validation.model,
      insight: secondPass,
      packet: {
        evidenceCount: packet.evidence.length,
        approximateTokens: packet.approximate_tokens,
        truncated: packet.truncated,
        unknowns: packet.unknowns,
      },
      validation: {
        status: "accepted",
        notes: [
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
}) {
  const prompt = buildProviderPrompt(
    input.packet,
    input.mode,
    input.candidate ?? undefined,
  );
  const response = await callReasoningProvider({
    provider: input.provider,
    apiKey: input.apiKey,
    model: input.model,
    prompt,
    signal: input.signal,
  });
  const parsed = parseCandidateInsight(response);

  if (!parsed) {
    const repairResponse = await callReasoningProvider({
      provider: input.provider,
      apiKey: input.apiKey,
      model: input.model,
      prompt: buildProviderRepairPrompt(response),
      signal: input.signal,
    });
    const repaired = parseCandidateInsight(repairResponse);
    if (repaired) {
      return repaired;
    }

    throw Object.assign(
      new Error(
        "The provider returned text instead of the structured JSON Workprint requested. Try again, or choose a different provider if it keeps happening.",
      ),
      { code: "malformed_provider_response" satisfies ReasoningFailureCode },
    );
  }

  return parsed;
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

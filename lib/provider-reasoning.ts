import type { EvidenceItem } from "@/lib/sample-data";

export const REASONING_PROVIDERS = [
  {
    id: "openai",
    label: "OpenAI",
    defaultModel: "gpt-5",
  },
  {
    id: "claude",
    label: "Claude",
    defaultModel: "claude-sonnet-4-5",
  },
  {
    id: "gemini",
    label: "Gemini",
    defaultModel: "gemini-3.5-flash",
  },
] as const;

export type ReasoningProviderId = (typeof REASONING_PROVIDERS)[number]["id"];

export type EvidencePacketItem = {
  id: string;
  source: string;
  title: string;
  excerpt: string;
  supports: string;
  does_not_prove: string;
};

export type EvidencePacket = {
  schema_version: "1.0";
  project: string;
  provider: ReasoningProviderId;
  token_budget: number;
  approximate_tokens: number;
  truncated: boolean;
  evidence: EvidencePacketItem[];
  unknowns: string[];
  instructions: string[];
};

export type CandidateInsight = {
  claim: string;
  evidence_ids: string[];
  explanation: string;
  confidence: string;
  unknowns: string;
  provider_uncertainty: string;
};

export const PROVIDER_INSIGHT_RESPONSE_SCHEMA = {
  type: "object",
  properties: {
    claim: {
      type: "string",
      description:
        "One plain sentence, 90-160 characters, analyzing the work rather than listing evidence.",
    },
    evidence_ids: {
      type: "array",
      items: { type: "string" },
      description: "Existing evidence IDs from the bounded Workprint packet.",
    },
    explanation: {
      type: "string",
      description: "Why the cited evidence supports the claim.",
    },
    confidence: {
      type: "string",
      description: "High, Moderate, Limited, or Low; qualitative language only.",
    },
    unknowns: {
      type: "string",
      description: "What the evidence cannot determine.",
    },
    provider_uncertainty: {
      type: "string",
      description: "Any uncertainty from this reasoning pass.",
    },
  },
  required: [
    "claim",
    "evidence_ids",
    "explanation",
    "confidence",
    "unknowns",
    "provider_uncertainty",
  ],
} as const;

const PROVIDER_CONFIDENCE_BANDS = new Set(["High", "Moderate", "Limited", "Low"]);

export type ReasoningSuccess = {
  ok: true;
  provider: ReasoningProviderId;
  providerLabel: string;
  model: string;
  insight: CandidateInsight;
  packet: {
    evidenceCount: number;
    approximateTokens: number;
    truncated: boolean;
    unknowns: string[];
  };
  validation: {
    status: "accepted" | "rewritten_down" | "held_for_review";
    notes: string[];
  };
};

export type ReasoningFailureCode =
  | "auth_or_quota_error"
  | "boundary_violation"
  | "invalid_evidence"
  | "invalid_request"
  | "malformed_provider_response"
  | "provider_failed"
  | "provider_timeout";

export type ReasoningFailure = {
  ok: false;
  error: {
    code: ReasoningFailureCode;
    message: string;
  };
};

export const MAX_EVIDENCE_PACKET_TOKENS = 30_000;
export const GEMINI_FALLBACK_MODELS = ["gemini-2.5-flash"] as const;
const APPROX_CHARS_PER_TOKEN = 4;
const MAX_PROVIDER_OUTPUT_TOKENS = 2_000;

const forbiddenClaimPatterns = [
  /\b\d+(?:\.\d+)?\s*%/,
  /\bcontribution percentage\b/i,
  /\bownership\b/i,
  /\bauthorship\b/i,
  /\bauthored\b/i,
  /\bowner\b/i,
  /\beffort\b/i,
  /\bdid most of the work\b/i,
  /\bhuman[-\s]?versus[-\s]?AI\b/i,
];

export function providerLabel(provider: ReasoningProviderId) {
  return (
    REASONING_PROVIDERS.find((candidate) => candidate.id === provider)?.label ??
    provider
  );
}

export function defaultProviderModel(provider: ReasoningProviderId) {
  const record = REASONING_PROVIDERS.find((candidate) => candidate.id === provider);
  return record?.defaultModel ?? "";
}

export function isReasoningProviderId(value: unknown): value is ReasoningProviderId {
  return (
    typeof value === "string" &&
    REASONING_PROVIDERS.some((provider) => provider.id === value)
  );
}

export function isProviderCapacityError(error: unknown) {
  if (!error || typeof error !== "object") {
    return false;
  }

  const message =
    error instanceof Error
      ? error.message
      : "message" in error && typeof (error as { message?: unknown }).message === "string"
        ? (error as { message: string }).message
        : "";

  return (
    /\b(high demand|overload|overloaded|temporarily unavailable|try again later|resource exhausted|rate limit|quota)\b/i.test(
      message,
    )
  );
}

export function buildEvidencePacket(input: {
  project: string;
  provider: ReasoningProviderId;
  evidence: EvidenceItem[];
}): EvidencePacket {
  const packet: EvidencePacket = {
    schema_version: "1.0",
    project: input.project,
    provider: input.provider,
    token_budget: MAX_EVIDENCE_PACKET_TOKENS,
    approximate_tokens: 0,
    truncated: false,
    evidence: [],
    unknowns: [
      "Workprint does not infer authorship, ownership, effort, value, intent, or contribution percentages.",
    ],
    instructions: [
      "Return only JSON matching the requested schema.",
      "Every claim must cite evidence IDs from this packet.",
      "Analyze the work, process, collaboration pattern, or user direction; do not merely list evidence sources.",
      "Prefer unknown over unsupported certainty.",
      "The packet must not include credentials, secrets, tokens, certificates, private keys, environment files, or unrestricted project-folder access.",
    ],
  };

  for (const item of input.evidence) {
    const candidate = normalizeEvidenceItem(item);
    const candidatePacket = {
      ...packet,
      evidence: [...packet.evidence, candidate],
    };
    const approximateTokens = approximateTokenCount(candidatePacket);

    if (approximateTokens > MAX_EVIDENCE_PACKET_TOKENS) {
      packet.truncated = true;
      packet.unknowns.push(
        "Some selected evidence was not sent because it exceeded Workprint's 30,000-token packet ceiling.",
      );
      break;
    }

    packet.evidence.push(candidate);
    packet.approximate_tokens = approximateTokens;
  }

  return packet;
}

export function validateCandidateInsight(
  insight: CandidateInsight,
  packet: EvidencePacket,
): { ok: true; notes: string[] } | { ok: false; code: ReasoningFailureCode; message: string } {
  if (!insight.claim || !Array.isArray(insight.evidence_ids)) {
    return {
      ok: false,
      code: "malformed_provider_response",
      message: "The provider did not return the required insight structure.",
    };
  }

  const emptyFields = [
    ["claim", insight.claim],
    ["explanation", insight.explanation],
    ["confidence", insight.confidence],
    ["unknowns", insight.unknowns],
    ["provider_uncertainty", insight.provider_uncertainty],
  ].filter(([, value]) => typeof value !== "string" || !value.trim());
  if (emptyFields.length > 0) {
    return {
      ok: false,
      code: "malformed_provider_response",
      message: `The provider returned an incomplete insight: ${emptyFields
        .map(([field]) => field)
        .join(", ")}.`,
    };
  }

  if (!PROVIDER_CONFIDENCE_BANDS.has(insight.confidence)) {
    return {
      ok: false,
      code: "malformed_provider_response",
      message:
        "The provider returned a confidence value Workprint could not display.",
    };
  }

  if (insight.evidence_ids.length === 0) {
    return {
      ok: false,
      code: "invalid_evidence",
      message: "The provider response did not cite any evidence IDs.",
    };
  }

  const packetIds = new Set(packet.evidence.map((item) => item.id));
  const invalidIds = insight.evidence_ids.filter((id) => !packetIds.has(id));
  if (invalidIds.length > 0) {
    return {
      ok: false,
      code: "invalid_evidence",
      message: `The provider cited evidence Workprint did not send: ${invalidIds.join(", ")}.`,
    };
  }

  const boundaryViolation = forbiddenClaimPatterns.find((pattern) =>
    pattern.test(insight.claim),
  );
  if (boundaryViolation) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider response crossed Workprint's attribution boundary and was rejected.",
    };
  }

  return {
    ok: true,
    notes: [
      "The final claim cites evidence IDs from the bounded packet.",
      "The final claim passed Workprint's deterministic attribution-boundary checks.",
    ],
  };
}

export function buildProviderPrompt(packet: EvidencePacket, mode: "originate" | "corroborate", candidate?: CandidateInsight) {
  return [
    "You are helping Workprint generate a candidate first insight from bounded project evidence.",
    "You are not final authority. Workprint will verify your output before display.",
    "Do not infer authorship, ownership, effort, value, intent, contribution percentages, or human-versus-AI percentages.",
    "Do not claim the project is complete unless evidence explicitly says so.",
    mode === "corroborate"
      ? "This is the second validation pass. Revise the candidate down if it is stronger than the evidence supports."
      : "This is the first reasoning pass. Produce the strongest supported candidate insight.",
    `Return only JSON with this schema: ${JSON.stringify(PROVIDER_INSIGHT_RESPONSE_SCHEMA)}.`,
    candidate ? `Candidate from first pass: ${JSON.stringify(candidate)}` : "",
    `Evidence packet: ${JSON.stringify(packet)}`,
  ]
    .filter(Boolean)
    .join("\n\n");
}

export function buildProviderRepairPrompt(response: string) {
  return [
    "Convert this provider response into exactly the Workprint JSON schema.",
    "Do not add new claims, evidence IDs, attribution, ownership, effort, value, intent, or contribution percentages.",
    "If the response does not support a required field, use an empty string. If it cites no evidence IDs, use an empty array.",
    "Return only JSON. Do not include Markdown, prose, or commentary.",
    `Schema: ${JSON.stringify(PROVIDER_INSIGHT_RESPONSE_SCHEMA)}`,
    `Provider response to convert: ${response.slice(0, 8_000)}`,
  ].join("\n\n");
}

export async function callReasoningProvider(input: {
  provider: ReasoningProviderId;
  apiKey: string;
  model: string;
  prompt: string;
  signal: AbortSignal;
}) {
  if (input.provider === "openai") {
    return callOpenAI(input);
  }

  if (input.provider === "claude") {
    return callClaude(input);
  }

  return callGemini(input);
}

export function parseCandidateInsight(text: string): CandidateInsight | null {
  const jsonText = extractJsonObject(stripMarkdownFence(text));
  if (!jsonText) {
    return null;
  }

  try {
    const parsed = normalizeCandidateShape(JSON.parse(jsonText));
    if (
      typeof parsed.claim !== "string" ||
      !Array.isArray(parsed.evidence_ids) ||
      typeof parsed.explanation !== "string" ||
      typeof parsed.confidence !== "string" ||
      typeof parsed.unknowns !== "string" ||
      typeof parsed.provider_uncertainty !== "string"
    ) {
      return null;
    }

    return {
      claim: parsed.claim.trim(),
      evidence_ids: parsed.evidence_ids.filter(
        (id): id is string => typeof id === "string" && Boolean(id.trim()),
      ),
      explanation: parsed.explanation.trim(),
      confidence: parsed.confidence.trim(),
      unknowns: parsed.unknowns.trim(),
      provider_uncertainty: parsed.provider_uncertainty.trim(),
    };
  } catch {
    return null;
  }
}

function normalizeEvidenceItem(item: EvidenceItem): EvidencePacketItem {
  return {
    id: item.id,
    source: item.source,
    title: item.title,
    excerpt: item.excerpt,
    supports: item.supports,
    does_not_prove: item.doesNotProve,
  };
}

function approximateTokenCount(value: unknown) {
  return Math.ceil(JSON.stringify(value).length / APPROX_CHARS_PER_TOKEN);
}

async function callOpenAI(input: {
  apiKey: string;
  model: string;
  prompt: string;
  signal: AbortSignal;
}) {
  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${input.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: input.model,
      input: input.prompt,
      max_output_tokens: MAX_PROVIDER_OUTPUT_TOKENS,
      store: false,
    }),
    signal: input.signal,
  });

  return parseProviderTextResponse(response, async (payload) => {
    if (typeof payload.output_text === "string") {
      return payload.output_text;
    }

    return extractText(payload);
  });
}

async function callClaude(input: {
  apiKey: string;
  model: string;
  prompt: string;
  signal: AbortSignal;
}) {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": input.apiKey,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: input.model,
      max_tokens: MAX_PROVIDER_OUTPUT_TOKENS,
      messages: [{ role: "user", content: input.prompt }],
    }),
    signal: input.signal,
  });

  return parseProviderTextResponse(response, async (payload) => extractText(payload));
}

async function callGemini(input: {
  apiKey: string;
  model: string;
  prompt: string;
  signal: AbortSignal;
}) {
  const model = input.model.startsWith("models/")
    ? input.model
    : `models/${input.model}`;
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/${model}:generateContent`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": input.apiKey,
      },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: input.prompt }] }],
        generationConfig: {
          maxOutputTokens: MAX_PROVIDER_OUTPUT_TOKENS,
          responseMimeType: "application/json",
          responseSchema: PROVIDER_INSIGHT_RESPONSE_SCHEMA,
        },
      }),
      signal: input.signal,
    },
  );

  return parseProviderTextResponse(response, async (payload) => extractText(payload));
}

async function parseProviderTextResponse(
  response: Response,
  extract: (payload: Record<string, unknown>) => Promise<string>,
) {
  const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;

  if (!response.ok) {
    const status = response.status;
    const message =
      typeof payload.error === "object" && payload.error !== null
        ? extractText(payload.error as Record<string, unknown>)
        : "The reasoning provider returned an error.";

    if (status === 401 || status === 403 || status === 429) {
      throw providerError("auth_or_quota_error", message);
    }

    throw providerError("provider_failed", message);
  }

  return extract(payload);
}

function providerError(code: ReasoningFailureCode, message: string) {
  return Object.assign(new Error(message), { code });
}

function extractText(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map(extractText).filter(Boolean).join("\n");
  }

  if (!value || typeof value !== "object") {
    return "";
  }

  const record = value as Record<string, unknown>;
  if (typeof record.text === "string") {
    return record.text;
  }
  if (typeof record.output_text === "string") {
    return record.output_text;
  }
  if (record.content) {
    return extractText(record.content);
  }
  if (record.output) {
    return extractText(record.output);
  }
  if (record.candidates) {
    return extractText(record.candidates);
  }
  if (record.parts) {
    return extractText(record.parts);
  }
  if (record.message) {
    return extractText(record.message);
  }

  return "";
}

function extractJsonObject(text: string) {
  const trimmed = text.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    return trimmed;
  }

  const start = trimmed.indexOf("{");
  const end = trimmed.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) {
    return null;
  }

  return trimmed.slice(start, end + 1);
}

function stripMarkdownFence(text: string) {
  return text
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
}

function normalizeCandidateShape(value: unknown): Partial<CandidateInsight> {
  const record = unwrapCandidateRecord(value);

  return {
    claim: readCandidateString(record, ["claim", "first_insight", "firstInsight", "summary"]),
    evidence_ids: readEvidenceIds(record),
    explanation: readCandidateString(record, [
      "explanation",
      "support",
      "rationale",
      "why_supported",
      "whySupported",
    ]),
    confidence: readCandidateString(record, [
      "confidence",
      "confidence_level",
      "confidenceLevel",
      "confidence_language",
      "confidenceLanguage",
    ]),
    unknowns: readCandidateString(record, ["unknowns", "limitations", "what_evidence_cannot_determine"]),
    provider_uncertainty: readCandidateString(record, [
      "provider_uncertainty",
      "providerUncertainty",
      "uncertainty",
    ]),
  };
}

function unwrapCandidateRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object") {
    return {};
  }

  if (Array.isArray(value)) {
    return unwrapCandidateRecord(value[0]);
  }

  const record = value as Record<string, unknown>;
  for (const key of ["insight", "candidate", "candidate_insight", "candidateInsight", "finding", "first_insight"]) {
    const nested = record[key];
    if (nested && typeof nested === "object") {
      return unwrapCandidateRecord(nested);
    }
  }

  return record;
}

function readCandidateString(record: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = record[key];
    const text = stringifyCandidateValue(value);
    if (text) {
      return text;
    }
  }

  return "";
}

function readEvidenceIds(record: Record<string, unknown>) {
  const value =
    record.evidence_ids ??
    record.evidenceIds ??
    record.supporting_evidence_ids ??
    record.supportingEvidenceIds;

  return extractEvidenceIds(value);
}

function stringifyCandidateValue(value: unknown): string {
  if (typeof value === "string") {
    return value.trim();
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map(stringifyCandidateValue).filter(Boolean).join("; ");
  }

  if (!value || typeof value !== "object") {
    return "";
  }

  const record = value as Record<string, unknown>;
  const preferred =
    record.level ??
    record.label ??
    record.value ??
    record.summary ??
    record.text ??
    record.description ??
    record.reasoning ??
    record.rationale;
  const preferredText = stringifyCandidateValue(preferred);
  if (preferredText) {
    return preferredText;
  }

  return Object.entries(record)
    .map(([key, entry]) => {
      const text = stringifyCandidateValue(entry);
      return text ? `${key}: ${text}` : "";
    })
    .filter(Boolean)
    .join("; ");
}

function extractEvidenceIds(value: unknown): string[] {
  if (typeof value === "string" && value.trim()) {
    return value
      .split(/[,;\s]+/)
      .map((id) => id.trim())
      .filter(Boolean);
  }

  if (Array.isArray(value)) {
    return value.flatMap(extractEvidenceIds);
  }

  if (!value || typeof value !== "object") {
    return [];
  }

  const record = value as Record<string, unknown>;
  return extractEvidenceIds(
    record.id ??
      record.evidence_id ??
      record.evidenceId ??
      record.ref ??
      record.reference,
  );
}

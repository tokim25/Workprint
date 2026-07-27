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
    defaultModel: "claude-sonnet-5",
  },
  {
    id: "gemini",
    label: "Gemini",
    defaultModel: "gemini-3.6-flash",
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
  included_for: string[];
};

export type EvidencePacketAssembly = {
  strategy: string;
  priority_order: string[];
  source_counts: Record<string, number>;
  included_counts: Record<string, number>;
  omitted_count: number;
  omitted_by_source: Record<string, number>;
  disclosure: string[];
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
  assembly: EvidencePacketAssembly;
};

export type CandidateInsight = {
  claim: string;
  evidence_ids: string[];
  explanation: string;
  confidence: string;
  unknowns: string;
  provider_uncertainty: string;
  visible_role_patterns: VisibleRolePattern[];
  role_section_label: string;
  why_workprint_uses_this_phrase: string;
  what_this_does_not_prove: string;
  summary_evidence_used: boolean;
  summary_evidence_boundary: string;
  fallback_reason: string | null;
};

export type VisibleRolePattern = {
  label: string;
  basis: string;
  behaviors: string[];
  confidence: string;
  evidence_refs: string[];
  boundary: string;
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
    visible_role_patterns: {
      type: "array",
      description:
        "Up to two evidence-backed working-pattern labels for the proof card, not official job titles.",
      items: {
        type: "object",
        properties: {
          label: { type: "string" },
          basis: { type: "string" },
          behaviors: { type: "array", items: { type: "string" } },
          confidence: { type: "string" },
          evidence_refs: { type: "array", items: { type: "string" } },
          boundary: { type: "string" },
        },
        required: [
          "label",
          "basis",
          "behaviors",
          "confidence",
          "evidence_refs",
          "boundary",
        ],
      },
    },
    role_section_label: {
      type: "string",
      description: 'Must be exactly "How you shaped the work".',
    },
    why_workprint_uses_this_phrase: {
      type: "string",
      description:
        "A concise explanation of why the working-pattern phrase fits the cited evidence.",
    },
    what_this_does_not_prove: {
      type: "string",
      description:
        "A concise boundary. It must not prove authorship, ownership, effort, or contribution share.",
    },
    summary_evidence_used: {
      type: "boolean",
      description: "Whether the claim relies on user-approved summary evidence.",
    },
    summary_evidence_boundary: {
      type: "string",
      description:
        "Boundary for summary evidence, or empty string if no summary evidence was used.",
    },
    fallback_reason: {
      type: "string",
      description:
        "Empty string for a supported role insight; a plain reason when Workprint must fallback.",
    },
  },
  required: [
    "claim",
    "evidence_ids",
    "explanation",
    "confidence",
    "unknowns",
    "provider_uncertainty",
    "visible_role_patterns",
    "role_section_label",
    "why_workprint_uses_this_phrase",
    "what_this_does_not_prove",
    "summary_evidence_used",
    "summary_evidence_boundary",
    "fallback_reason",
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
    status: "accepted" | "rewritten_down" | "held_for_review" | "fallback";
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

export const MAX_EVIDENCE_PACKET_TOKENS = 45_000;
export const GEMINI_FALLBACK_MODELS = ["gemini-3.5-flash-lite"] as const;
export const OPENAI_FALLBACK_MODELS = ["gpt-5-mini"] as const;
export const CLAUDE_FALLBACK_MODELS = ["claude-haiku-4-5-20251001"] as const;
const APPROX_CHARS_PER_TOKEN = 4;
const MAX_PROVIDER_OUTPUT_TOKENS = 3_000;
const PACKET_PRIORITY_ORDER = [
  "source diversity",
  "human direction and judgment",
  "AI Fluency 4D signals",
  "recency",
] as const;

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
  /\byou were the\b/i,
  /\byour official role\b/i,
  /\byou deserve credit\b/i,
  /\byou owned\b/i,
  /\byou contributed\b/i,
  /\bresponsible for\b/i,
];

const overpraisePatterns = [
  /\bbrilliant(?:ly)?\b/i,
  /\bexceptional(?:ly)?\b/i,
  /\bexcellent\b/i,
  /\belevated the product\b/i,
  /\bmaster(?:y|ful)\b/i,
  /\btalent\b/i,
];

const sourceDetectionOnlyPatterns = [
  /\bpresence of (?:an? )?(?:active )?(?:claude|chatgpt|gemini|ai|llm|chat|desktop).*cache\b/i,
  /\b(?:claude|chatgpt|gemini|ai|llm|chat|desktop).*cache (?:indicates|shows|suggests|was found|was detected)\b/i,
  /\b(?:ai|llm|conversational ai) tools were (?:available|present|detected|utilized)\b/i,
  /\bavailable and utilized on the development system\b/i,
  /\bused on the local machine\b/i,
  /\bdevelopment system\b/i,
  /\bsource(?:s)? (?:were|was) detected\b/i,
];

const firstInsightRequiredPatterns = [
  /\byou\b/i,
  /\buser\b/i,
  /\bhuman\b/i,
  /\bdirected?\b/i,
  /\bchose\b/i,
  /\bdecided\b/i,
  /\bapproved\b/i,
  /\breview(?:ed|s|ing)?\b/i,
  /\bjudg(?:e)?ment\b/i,
  /\bsequenc(?:e|ed|ing)\b/i,
  /\biteration\b/i,
  /\brepair loop\b/i,
  /\bvalidation\b/i,
  /\bdelegat(?:e|ed|ion|ing)\b/i,
  /\bdescrib(?:e|ed|ing|es)\b/i,
  /\bdiscern(?:ed|ment|ing)?\b/i,
  /\bdiligen(?:ce|t)\b/i,
  /\bverif(?:y|ied|ication|ying)\b/i,
  /\bcriteria\b/i,
  /\bcheckpoint\b/i,
  /\bprompt(?:ed|ing)?\b/i,
  /\bhandoff\b/i,
  /\btool choice\b/i,
  /\bplatform choice\b/i,
  /\baccountab(?:ility|le)\b/i,
  /\bresponsib(?:ility|le)\b/i,
];

const aiToolActivityPatterns = [
  /\bai\b/i,
  /\bllm\b/i,
  /\bclaude\b/i,
  /\bchatgpt\b/i,
  /\bgemini\b/i,
  /\btool(?:ing)?\b/i,
  /\bimplementation repairs?\b/i,
];

const aiFluencyLensPatterns = [
  /\bdelegat(?:e|ed|ion|ing)\b/i,
  /\bdescrib(?:e|ed|ing|es|ption)\b/i,
  /\bdiscern(?:ed|ment|ing)?\b/i,
  /\bdiligen(?:ce|t)\b/i,
  /\bgoal(?:s)?\b/i,
  /\bdirection\b/i,
  /\bdirected?\b/i,
  /\bconstraint(?:s)?\b/i,
  /\bacceptance criteria\b/i,
  /\bcriteria\b/i,
  /\bjudg(?:e)?ment\b/i,
  /\bsequenc(?:e|ed|ing)\b/i,
  /\breview(?:ed|s|ing)?\b/i,
  /\brevis(?:e|ed|ion|ing)\b/i,
  /\breject(?:ed|s|ing)?\b/i,
  /\bcorrect(?:ed|ion|ing)?\b/i,
  /\bverif(?:y|ied|ication|ying)\b/i,
  /\btest(?:ed|s|ing)?\b/i,
  /\bdisclos(?:e|ed|ure|ing)\b/i,
  /\baccountab(?:ility|le)\b/i,
  /\bresponsib(?:ility|le)\b/i,
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

function errorMessageText(error: unknown): string {
  if (!error || typeof error !== "object") {
    return "";
  }

  return error instanceof Error
    ? error.message
    : "message" in error && typeof (error as { message?: unknown }).message === "string"
      ? (error as { message: string }).message
      : "";
}

export function isProviderCapacityError(error: unknown) {
  return /\b(high demand|overload|overloaded|temporarily unavailable|try again later|resource exhausted|rate limit|quota)\b/i.test(
    errorMessageText(error),
  );
}

const MODEL_UNAVAILABLE_PATTERN =
  /\b(model[\s_-]?not[\s_-]?found|does not exist|is not found|no longer available|has been (?:deprecated|retired|decommissioned|removed)|unknown model|invalid model|unsupported model|not supported for generatecontent)\b/i;

export function isModelUnavailableError(error: unknown) {
  return MODEL_UNAVAILABLE_PATTERN.test(errorMessageText(error));
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
      "This packet was assembled to balance source diversity, human direction signals, AI Fluency 4D signals, and recency.",
      "The first insight must feel like a mirror and proof point: it must explain what the user did OR where human judgment, review, direction, correction, sequencing, or collaboration appears.",
      'Use "How you shaped the work" as the role_section_label.',
      "The first insight sentence should be plain human language. Put working-pattern labels underneath in visible_role_patterns.",
      "Use at most two visible_role_patterns. They are working patterns, not official job titles.",
      "Use an empty string for fallback_reason when the first insight is supported.",
      "Use direct language only for direct role evidence. Use appeared, looked like, or the evidence suggests for partial or summary-based role evidence.",
      "If evidence is Git-only, metadata-only, source-presence-only, AI-strong/user-weak, or missing user actions, return the strict helpful fallback instead of inventing a role label.",
      "Fallback claim: Workprint found project activity, but not enough direct role evidence yet to describe how you shaped the work.",
      "If evidence clearly shows AI/tool activity but weakly shows user activity, fallback claim: Workprint found AI-assisted project activity, but not enough direct role evidence yet to describe how you shaped the work.",
      "When supported, connect user behavior to the effect on the work. Do not imply unsupported causality or broad project arcs without corroboration.",
      "The first insight may also explain what AI/tooling appears to have done, how the work moved from idea to implementation, or what the evidence cannot separate.",
      "Use the AI Fluency 4D lens when supported by evidence: Delegation, Description, Discernment, and Diligence.",
      "AI Fluency terms may appear in the first insight only when immediately grounded in plain-language behavior. Do not use them as scores, grades, or abstract competencies.",
      "Delegation means what the user gave to AI, kept for themselves, or shaped together; Description means how goals, constraints, process, or AI behavior were specified; Discernment means review, correction, evaluation, or selection; Diligence means verification, disclosure, appropriate use, or accountability.",
      "Credit the AI Fluency Framework to Prof. Rick Dakan, Prof. Joseph Feller, and Anthropic Academy resources if you mention the framework directly.",
      "Analyze the work, process, collaboration pattern, or user direction; do not merely list evidence sources, tool availability, or cache presence.",
      "Do not use presence-only Claude Desktop chat cache evidence as the first insight headline.",
      "Do not say you were the, your official role, you deserve credit, you owned, you contributed X%, or you were responsible for unless a narrow responsibility is directly evidenced.",
      "Do not praise or grade the user. Avoid excellent, exceptional, brilliant, mastery, and similar language.",
      "Prefer unknown over unsupported certainty.",
      "The packet must not include credentials, secrets, tokens, certificates, private keys, environment files, or unrestricted project-folder access.",
    ],
    assembly: {
      strategy:
        "balanced-context-v1: source diversity first, then human direction and AI Fluency signals, then recency within the bounded token budget.",
      priority_order: [...PACKET_PRIORITY_ORDER],
      source_counts: {},
      included_counts: {},
      omitted_count: 0,
      omitted_by_source: {},
      disclosure: [
        "Workprint sends a bounded evidence packet, not the whole project folder or complete chat history.",
        "The packet reserves room for source diversity and human-direction signals before filling remaining space with recent evidence.",
      ],
    },
  };

  for (const item of input.evidence) {
    packet.assembly.source_counts[item.source] =
      (packet.assembly.source_counts[item.source] ?? 0) + 1;
  }

  const selected = assembleEvidenceCandidates(input.evidence);
  const includedIds = new Set<string>();

  for (const item of selected) {
    const candidate = normalizeEvidenceItem(item.evidence, item.reasons);
    const candidatePacket = {
      ...packet,
      evidence: [...packet.evidence, candidate],
    };
    const approximateTokens = approximateTokenCount(candidatePacket);

    if (approximateTokens > MAX_EVIDENCE_PACKET_TOKENS) {
      packet.truncated = true;
      packet.unknowns.push(
        "Some selected evidence was not sent because it exceeded Workprint's 45,000-token packet ceiling.",
      );
      break;
    }

    packet.evidence.push(candidate);
    includedIds.add(candidate.id);
    packet.assembly.included_counts[candidate.source] =
      (packet.assembly.included_counts[candidate.source] ?? 0) + 1;
    packet.approximate_tokens = approximateTokens;
  }

  const omitted = input.evidence.filter((item) => !includedIds.has(item.id));
  packet.assembly.omitted_count = omitted.length;
  for (const item of omitted) {
    packet.assembly.omitted_by_source[item.source] =
      (packet.assembly.omitted_by_source[item.source] ?? 0) + 1;
  }

  if (omitted.length > 0 && !packet.truncated) {
    packet.truncated = true;
  }

  if (omitted.length > 0) {
    packet.unknowns.push(
      `${omitted.length} selected evidence item(s) were omitted from the provider packet after Workprint balanced source diversity, human-direction signals, AI Fluency signals, and recency.`,
    );
    packet.assembly.disclosure.push(
      `${omitted.length} selected evidence item(s) were omitted from the provider packet to stay within the bounded token budget.`,
    );
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
    ["role_section_label", insight.role_section_label],
    ["why_workprint_uses_this_phrase", insight.why_workprint_uses_this_phrase],
    ["what_this_does_not_prove", insight.what_this_does_not_prove],
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

  const claimAndExplanationText = [
    insight.claim,
    insight.explanation,
    insight.why_workprint_uses_this_phrase,
    insight.what_this_does_not_prove,
  ].join(" ");

  const sourceDetectionOnly = sourceDetectionOnlyPatterns.find((pattern) =>
    pattern.test(claimAndExplanationText),
  );
  if (sourceDetectionOnly) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider returned a source-detection statement rather than a Workprint first insight.",
    };
  }

  const humanCenteredInsight = firstInsightRequiredPatterns.some((pattern) =>
    pattern.test(claimAndExplanationText),
  );
  const isFallback = Boolean(insight.fallback_reason);
  if (!humanCenteredInsight && !isFallback) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider insight did not explain what the user did or where human judgment, review, or sequencing appears.",
    };
  }

  const aiFluencyAligned = aiFluencyLensPatterns.some((pattern) =>
    pattern.test(claimAndExplanationText),
  );
  if (!aiFluencyAligned && !isFallback) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider insight did not align with an evidence-supported AI Fluency lens: Delegation, Description, Discernment, or Diligence.",
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
    pattern.test(claimAndExplanationText),
  );
  if (boundaryViolation) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider response crossed Workprint's attribution boundary and was rejected.",
    };
  }

  const overpraise = overpraisePatterns.find((pattern) =>
    pattern.test(claimAndExplanationText),
  );
  if (overpraise) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider insight praised or graded the user instead of describing evidence-backed behavior.",
    };
  }

  if (insight.role_section_label !== "How you shaped the work") {
    return {
      ok: false,
      code: "malformed_provider_response",
      message:
        'The provider did not use Workprint\'s required role label: "How you shaped the work".',
    };
  }

  if (insight.visible_role_patterns.length > 2) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider returned too many role patterns for the first insight proof card.",
    };
  }

  if (!isFallback && insight.visible_role_patterns.length === 0) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider insight did not include an evidence-backed working pattern.",
    };
  }

  const roleEvidenceIds = new Set(insight.evidence_ids);
  for (const pattern of insight.visible_role_patterns) {
    if (
      !pattern.label.trim() ||
      !pattern.basis.trim() ||
      !pattern.boundary.trim() ||
      pattern.behaviors.length === 0 ||
      pattern.evidence_refs.length === 0
    ) {
      return {
        ok: false,
        code: "malformed_provider_response",
        message:
          "The provider returned an incomplete role-pattern proof card.",
      };
    }

    for (const ref of pattern.evidence_refs) {
      if (!packetIds.has(ref) && !roleEvidenceIds.has(ref)) {
        return {
          ok: false,
          code: "invalid_evidence",
          message: `The provider cited role-pattern evidence Workprint did not send: ${ref}.`,
        };
      }
    }
  }

  const aiToolCentered =
    aiToolActivityPatterns.some((pattern) => pattern.test(insight.claim)) &&
    !humanCenteredInsight;
  if (aiToolCentered) {
    return {
      ok: false,
      code: "boundary_violation",
      message:
        "The provider led with AI/tool activity without enough user-role evidence.",
    };
  }

  return {
    ok: true,
    notes: [
      "The final claim cites evidence IDs from the bounded packet.",
      "The final claim passed Workprint's deterministic attribution-boundary checks.",
      "The final claim passed Workprint's AI Fluency lens check.",
    ],
  };
}

export function buildFallbackInsight(
  packet: EvidencePacket,
  reason: string,
): CandidateInsight {
  const hasAiToolEvidence = packet.evidence.some((item) =>
    aiToolActivityPatterns.some((pattern) => pattern.test(evidencePacketItemText(item))),
  );
  const claim = hasAiToolEvidence
    ? "Workprint found AI-assisted project activity, but not enough direct role evidence yet to describe how you shaped the work."
    : "Workprint found project activity, but not enough direct role evidence yet to describe how you shaped the work.";
  const evidenceIds = packet.evidence.slice(0, 3).map((item) => item.id);
  const summaryEvidenceUsed = packet.evidence.some((item) =>
    /\bchat-summary|summary evidence|approved summary\b/i.test(
      evidencePacketItemText(item),
    ),
  );

  return {
    claim,
    evidence_ids: evidenceIds,
    explanation: hasAiToolEvidence
      ? "Workprint can see AI/tool activity and project changes, but it cannot yet connect that activity to direct user direction, review, decisions, or sequencing."
      : "Workprint can see project activity, but the selected evidence does not yet show enough direct user direction, review, decisions, or sequencing.",
    confidence: "Limited",
    unknowns:
      "Workprint cannot determine how the user shaped the work without stronger role evidence, such as direct conversation turns or a user-approved chat summary.",
    provider_uncertainty: reason,
    visible_role_patterns: [],
    role_section_label: "How you shaped the work",
    why_workprint_uses_this_phrase:
      "Workprint did not assign a working-pattern label because the evidence does not directly support one yet.",
    what_this_does_not_prove:
      "This does not prove authorship, ownership, effort, value, intent, or contribution share.",
    summary_evidence_used: summaryEvidenceUsed,
    summary_evidence_boundary: summaryEvidenceUsed
      ? "Summary evidence may provide context, but Workprint did not process the full underlying transcript unless it was explicitly selected."
      : "",
    fallback_reason: reason,
  };
}

function evidencePacketItemText(item: EvidencePacketItem) {
  return [
    item.id,
    item.source,
    item.title,
    item.excerpt,
    item.supports,
    item.does_not_prove,
    item.included_for.join(" "),
  ].join(" ");
}

export function buildProviderPrompt(packet: EvidencePacket, mode: "originate" | "corroborate", candidate?: CandidateInsight) {
  return [
    "You are helping Workprint generate a candidate first insight from bounded project evidence.",
    "You are not final authority. Workprint will verify your output before display.",
    "Do not infer authorship, ownership, effort, value, intent, contribution percentages, or human-versus-AI percentages.",
    "Do not claim the project is complete unless evidence explicitly says so.",
    "The first insight must feel like a mirror and proof point: it must tell the user what they did OR where human judgment, review, direction, correction, sequencing, or collaboration appears.",
    'Use role_section_label exactly as "How you shaped the work".',
    "The first insight sentence should be plain human language. Put working-pattern labels underneath in visible_role_patterns.",
    "Use at most two visible_role_patterns. They are working patterns, not official job titles.",
    "Use an empty string for fallback_reason when the first insight is supported.",
    "Use direct language only for direct role evidence. Use appeared, looked like, or the evidence suggests for partial or summary-based role evidence.",
    "If evidence is Git-only, metadata-only, source-presence-only, AI-strong/user-weak, or missing user actions, return the strict helpful fallback instead of inventing a role label.",
    "Fallback claim: Workprint found project activity, but not enough direct role evidence yet to describe how you shaped the work.",
    "If evidence clearly shows AI/tool activity but weakly shows user activity, fallback claim: Workprint found AI-assisted project activity, but not enough direct role evidence yet to describe how you shaped the work.",
    "When supported, connect user behavior to the effect on the work. Do not imply unsupported causality or broad project arcs without corroboration.",
    "The first insight may also include what AI/tooling appears to have done, how the work moved from idea to implementation, or what the evidence cannot separate.",
    "Use the AI Fluency 4D lens when supported by evidence: Delegation, Description, Discernment, and Diligence.",
    "AI Fluency terms may appear in the first insight only when immediately grounded in plain-language behavior. Do not use them as scores, grades, or abstract competencies.",
    "Delegation means what the user gave to AI, kept for themselves, or shaped together; Description means how goals, constraints, process, or AI behavior were specified; Discernment means review, correction, evaluation, or selection; Diligence means verification, disclosure, appropriate use, or accountability.",
    "Credit the AI Fluency Framework to Prof. Rick Dakan, Prof. Joseph Feller, and Anthropic Academy resources if you mention the framework directly.",
    "Do not make the first insight merely about source detection, tool availability, cache presence, or a system where AI tools were available.",
    "Presence-only Claude Desktop chat cache evidence may support a limitation, but it must not be the first insight headline.",
    "Do not say you were the, your official role, you deserve credit, you owned, you contributed X%, or you were responsible for unless a narrow responsibility is directly evidenced.",
    "Do not praise or grade the user. Avoid excellent, exceptional, brilliant, mastery, and similar language.",
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
    'Use role_section_label exactly as "How you shaped the work" if the response contains enough role evidence.',
    "Use visible_role_patterns only for evidence-backed working patterns, not official job titles.",
    "If the response is evidence inventory, source detection, AI-strong/user-weak, or lacks user-role evidence, use the strict helpful fallback claim and set fallback_reason.",
    "Use an empty string for fallback_reason when the first insight is supported.",
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
      visible_role_patterns: normalizeVisibleRolePatterns(parsed.visible_role_patterns),
      role_section_label: normalizeRoleSectionLabel(parsed.role_section_label),
      why_workprint_uses_this_phrase: stringifyCandidateValue(
        parsed.why_workprint_uses_this_phrase,
      ),
      what_this_does_not_prove: stringifyCandidateValue(
        parsed.what_this_does_not_prove,
      ),
      summary_evidence_used: normalizeCandidateBoolean(parsed.summary_evidence_used),
      summary_evidence_boundary: stringifyCandidateValue(
        parsed.summary_evidence_boundary,
      ),
      fallback_reason: normalizeFallbackReason(parsed.fallback_reason),
    };
  } catch {
    return null;
  }
}

function normalizeEvidenceItem(item: EvidenceItem, includedFor: string[]): EvidencePacketItem {
  return {
    id: item.id,
    source: item.source,
    title: item.title,
    excerpt: item.excerpt,
    supports: item.supports,
    does_not_prove: item.doesNotProve,
    included_for: includedFor,
  };
}

function approximateTokenCount(value: unknown) {
  return Math.ceil(JSON.stringify(value).length / APPROX_CHARS_PER_TOKEN);
}

function assembleEvidenceCandidates(evidence: EvidenceItem[]) {
  const selected = new Map<string, { evidence: EvidenceItem; reasons: string[] }>();

  const add = (item: EvidenceItem, reason: string) => {
    const current = selected.get(item.id);
    if (current) {
      if (!current.reasons.includes(reason)) {
        current.reasons.push(reason);
      }
      return;
    }
    selected.set(item.id, { evidence: item, reasons: [reason] });
  };

  const bySource = new Map<string, EvidenceItem[]>();
  for (const item of evidence) {
    const sourceItems = bySource.get(item.source) ?? [];
    sourceItems.push(item);
    bySource.set(item.source, sourceItems);
  }

  for (const source of [...bySource.keys()].sort()) {
    const first = bySource.get(source)?.[0];
    if (first) {
      add(first, "source diversity");
    }
  }

  for (const item of evidence) {
    const text = evidenceSearchText(item);
    if (firstInsightRequiredPatterns.some((pattern) => pattern.test(text))) {
      add(item, "human direction and judgment");
    }
  }

  for (const item of evidence) {
    const text = evidenceSearchText(item);
    if (aiFluencyLensPatterns.some((pattern) => pattern.test(text))) {
      add(item, "AI Fluency 4D signals");
    }
  }

  for (const item of evidence) {
    add(item, "recency");
  }

  return [...selected.values()];
}

function evidenceSearchText(item: EvidenceItem) {
  return [
    item.source,
    item.title,
    item.excerpt,
    item.supports,
    item.doesNotProve,
  ].join(" ");
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

  return parseProviderTextResponse(response, "openai", async (payload) => {
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

  return parseProviderTextResponse(response, "claude", async (payload) => extractText(payload));
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

  return parseProviderTextResponse(response, "gemini", async (payload) => extractText(payload));
}

async function parseProviderTextResponse(
  response: Response,
  provider: ReasoningProviderId,
  extract: (payload: Record<string, unknown>) => Promise<string>,
) {
  const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;

  if (!response.ok) {
    const status = response.status;
    const rawMessage =
      typeof payload.error === "object" && payload.error !== null
        ? extractText(payload.error as Record<string, unknown>)
        : "The reasoning provider returned an error.";
    const message = normalizeProviderErrorMessage(rawMessage, provider);

    if (status === 401 || status === 403 || status === 429) {
      throw providerError("auth_or_quota_error", message);
    }

    throw providerError("provider_failed", message);
  }

  return extract(payload);
}

function normalizeProviderErrorMessage(message: string, provider: ReasoningProviderId) {
  if (MODEL_UNAVAILABLE_PATTERN.test(message)) {
    const label = providerLabel(provider);
    return `${label}'s selected model is no longer available for this account. Workprint will try a newer ${label} model.`;
  }

  if (
    /generation_config\.response_schema|response_schema|responseSchema|proto field|unknown name "type"/i.test(
      message,
    )
  ) {
    return "Workprint could not start provider reasoning because the provider rejected the structured response format. Try again after updating Workprint, or choose a different provider.";
  }

  return message;
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

function normalizeCandidateShape(value: unknown): Record<string, unknown> {
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
    visible_role_patterns:
      record.visible_role_patterns ??
      record.visibleRolePatterns ??
      record.role_patterns ??
      record.rolePatterns ??
      record.how_you_shaped_the_work,
    role_section_label: readCandidateString(record, [
      "role_section_label",
      "roleSectionLabel",
      "role_label",
      "roleLabel",
    ]),
    why_workprint_uses_this_phrase: readCandidateString(record, [
      "why_workprint_uses_this_phrase",
      "whyWorkprintUsesThisPhrase",
      "role_pattern_basis",
      "rolePatternBasis",
      "basis",
    ]),
    what_this_does_not_prove: readCandidateString(record, [
      "what_this_does_not_prove",
      "whatThisDoesNotProve",
      "does_not_prove",
      "doesNotProve",
      "boundary",
    ]),
    summary_evidence_used: record.summary_evidence_used ?? record.summaryEvidenceUsed,
    summary_evidence_boundary: readCandidateString(record, [
      "summary_evidence_boundary",
      "summaryEvidenceBoundary",
    ]),
    fallback_reason: readNullableCandidateString(record, [
      "fallback_reason",
      "fallbackReason",
    ]),
  };
}

function normalizeVisibleRolePatterns(value: unknown): VisibleRolePattern[] {
  if (!value) {
    return [];
  }

  const records = Array.isArray(value) ? value : [value];
  return records
    .map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }

      const record = entry as Record<string, unknown>;
      const label = readCandidateString(record, ["label", "role", "name"]);
      const basis = readCandidateString(record, [
        "basis",
        "rationale",
        "reason",
        "why",
        "description",
      ]);
      const confidence = readCandidateString(record, [
        "confidence",
        "confidence_level",
        "confidenceLevel",
      ]);
      const boundary = readCandidateString(record, [
        "boundary",
        "what_this_does_not_prove",
        "whatThisDoesNotProve",
        "does_not_prove",
        "doesNotProve",
      ]);
      const behaviors = extractStringList(
        record.behaviors ?? record.activities ?? record.actions,
      );
      const evidenceRefs = extractEvidenceIds(
        record.evidence_refs ??
          record.evidenceRefs ??
          record.evidence_ids ??
          record.evidenceIds,
      );

      return {
        label,
        basis,
        behaviors,
        confidence,
        evidence_refs: evidenceRefs,
        boundary,
      };
    })
    .filter((pattern): pattern is VisibleRolePattern => Boolean(pattern));
}

function normalizeRoleSectionLabel(value: unknown): string {
  const text = stringifyCandidateValue(value);
  return text || "How you shaped the work";
}

function normalizeFallbackReason(value: unknown) {
  const text = stringifyCandidateValue(value);
  return text ? text : null;
}

function normalizeCandidateBoolean(value: unknown) {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    return value.trim().toLowerCase() === "true";
  }

  return false;
}

function readNullableCandidateString(record: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    if (!(key in record)) {
      continue;
    }

    const value = record[key];
    if (value === null) {
      return null;
    }

    const text = stringifyCandidateValue(value);
    if (text) {
      return text;
    }
  }

  return null;
}

function extractStringList(value: unknown): string[] {
  if (typeof value === "string") {
    return value
      .split(/[,;]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  if (Array.isArray(value)) {
    return value
      .map(stringifyCandidateValue)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
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

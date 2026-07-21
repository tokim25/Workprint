import type { ClaudeLocalSummary } from "./claude-local-summary";
import type { GitSummary } from "./git-summary";
import type { ProjectFileEvidenceFact } from "./project-file-evidence";

export type ActiveDiscovery = {
  claim: string;
  evidenceIds?: string[];
  support: string;
  unknown: string;
  confidence: string;
  kind: "insight" | "status" | "provider_needed";
};

export type SampleDiscovery = {
  claim: string;
  evidenceIds?: string[];
  support: string;
  unknown: string;
  confidence: string;
  kind: "insight" | "status";
};

type PickActiveDiscoveryInput = {
  gitSummary: GitSummary | null;
  claudeSummary: ClaudeLocalSummary | null;
  projectFileFacts: ProjectFileEvidenceFact[];
  sample: SampleDiscovery;
};

export const PROVIDER_NEEDED_DISCOVERY: ActiveDiscovery = {
  claim: "Connect an AI reasoning provider to see your first insight.",
  support:
    "Workprint can collect local evidence, but it does not turn that evidence into an insight until OpenAI, Claude, or Gemini processes a bounded evidence packet you explicitly approve.",
  unknown:
    "No AI reasoning provider has processed the selected evidence yet, so Workprint has not produced findings, confidence, attribution, or a first insight for this project.",
  confidence: "Not assessed",
  kind: "provider_needed",
};

export function pickActiveDiscovery({
  gitSummary,
  claudeSummary,
  projectFileFacts,
  sample,
}: PickActiveDiscoveryInput): ActiveDiscovery {
  if (gitSummary || claudeSummary || projectFileFacts.length > 0) {
    return PROVIDER_NEEDED_DISCOVERY;
  }

  return sample;
}

// Reads the real, already-synthesized claim + confidence the full
// investigation computes from ALL evidence sources (not just Git) --
// see src/workprint/executive.py's build_executive_report and
// src/workprint/models/executive.py's ExecutiveBrief/ConfidenceAssessment.
// Returns null when the payload doesn't have the expected shape, or when
// the engine found no explicit goal statement (status "unknown" rather
// than "explicitly_supported"). In that case, the UI must show the
// provider-needed state rather than inventing a local fallback insight.
export function pickExecutiveDiscovery(json: unknown): ActiveDiscovery | null {
  if (!json || typeof json !== "object") {
    return null;
  }

  const executiveReport = (json as Record<string, unknown>).executive_report;
  if (!executiveReport || typeof executiveReport !== "object") {
    return null;
  }

  const brief = (executiveReport as Record<string, unknown>).executive_brief;
  const confidenceAssessment = (executiveReport as Record<string, unknown>)
    .confidence_assessment;
  if (
    !brief ||
    typeof brief !== "object" ||
    !confidenceAssessment ||
    typeof confidenceAssessment !== "object"
  ) {
    return null;
  }

  const briefRecord = brief as Record<string, unknown>;
  const goal = briefRecord.project_goal;
  const unknownsSummary = briefRecord.unknowns_summary;
  if (!goal || typeof goal !== "object" || typeof unknownsSummary !== "string") {
    return null;
  }

  const goalRecord = goal as Record<string, unknown>;
  if (
    goalRecord.status !== "explicitly_supported" ||
    typeof goalRecord.summary !== "string"
  ) {
    return null;
  }

  const confidenceRecord = confidenceAssessment as Record<string, unknown>;
  if (typeof confidenceRecord.band !== "string") {
    return null;
  }

  return {
    claim: goalRecord.summary,
    support:
      typeof goalRecord.rationale === "string" && goalRecord.rationale
        ? goalRecord.rationale
        : "Workprint synthesized this from all connected evidence sources.",
    unknown: unknownsSummary,
    confidence: confidenceRecord.band,
    kind: "insight",
  };
}

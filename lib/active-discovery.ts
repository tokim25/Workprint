import {
  claudeCodeDiscoveryClaim,
  claudeCoworkDiscoveryClaim,
  claudeDesktopChatDiscoveryClaim,
  sessionDiscoverySupport,
  type ClaudeLocalSummary,
} from "./claude-local-summary";
import { gitDiscoveryClaim, gitDiscoverySupport, type GitSummary } from "./git-summary";
import type { ProjectFileEvidenceFact } from "./project-file-evidence";

export type ActiveDiscovery = {
  claim: string;
  support: string;
  unknown: string;
  confidence: string;
  kind: "insight" | "status";
};

export type SampleDiscovery = {
  claim: string;
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

// Every mechanical/count-based branch below reports a fixed "Limited"
// confidence rather than the real, evidence-scored bands ("Very High"
// through "Low") the executive report computes -- a commit count or a
// session count is a metadata tally, not a synthesized finding, and
// labeling it "Moderate" (as the old hardcoded sample confidence did,
// unconditionally, regardless of source) overstated what these branches
// actually establish. Reserve non-"Limited" confidence for the real
// executive-report band once that becomes available.
const MECHANICAL_CONFIDENCE = "Limited";

export function pickActiveDiscovery({
  gitSummary,
  claudeSummary,
  projectFileFacts,
  sample,
}: PickActiveDiscoveryInput): ActiveDiscovery {
  if (gitSummary) {
    return {
      claim: gitDiscoveryClaim(gitSummary),
      support: gitDiscoverySupport(gitSummary),
      unknown: gitSummary.limitations.join(" "),
      confidence: MECHANICAL_CONFIDENCE,
      kind: "status",
    };
  }

  if (claudeSummary) {
    if (claudeSummary.claude_code.session_count > 0) {
      return {
        claim: claudeCodeDiscoveryClaim(claudeSummary.claude_code),
        support: sessionDiscoverySupport(claudeSummary.claude_code),
        unknown: claudeSummary.limitations.join(" "),
        confidence: MECHANICAL_CONFIDENCE,
        kind: "status",
      };
    }

    if (claudeSummary.claude_cowork.session_count > 0) {
      return {
        claim: claudeCoworkDiscoveryClaim(claudeSummary.claude_cowork),
        support: sessionDiscoverySupport(claudeSummary.claude_cowork),
        unknown: claudeSummary.limitations.join(" "),
        confidence: MECHANICAL_CONFIDENCE,
        kind: "status",
      };
    }

    if (claudeSummary.claude_desktop_chat.cache_detected) {
      const chat = claudeSummary.claude_desktop_chat;
      return {
        claim: claudeDesktopChatDiscoveryClaim(chat),
        support:
          chat.deep_parse_found_turns && chat.turns
            ? sessionDiscoverySupport(chat.turns)
            : "Presence-only: no conversation content was read.",
        unknown: claudeSummary.limitations.join(" "),
        confidence: MECHANICAL_CONFIDENCE,
        kind: "status",
      };
    }
  }

  if (projectFileFacts.length > 0) {
    const noun = projectFileFacts.length === 1 ? "file" : "files";
    return {
      claim: `Workprint read ${projectFileFacts.length} project ${noun} in this browser.`,
      support: `Files read: ${projectFileFacts.map((fact) => fact.path).join(", ")}.`,
      unknown:
        "Workprint did not read file contents beyond what was confirmed in the browser, and file names and extensions do not prove authorship, effort, ownership, or intent.",
      confidence: MECHANICAL_CONFIDENCE,
      kind: "status",
    };
  }

  return sample;
}

// Reads the real, already-synthesized claim + confidence the full
// investigation computes from ALL evidence sources (not just Git) --
// see src/workprint/executive.py's build_executive_report and
// src/workprint/models/executive.py's ExecutiveBrief/ConfidenceAssessment.
// Returns null when the payload doesn't have the expected shape, or when
// the engine found no explicit goal statement (status "unknown" rather
// than "explicitly_supported") -- in that case the mechanical claim from
// pickActiveDiscovery above is a better thing to show than "no explicit
// goal statement appears in the evidence."
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

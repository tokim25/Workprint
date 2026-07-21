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
  evidenceIds?: string[];
  support: string;
  unknown: string;
  confidence: string;
  kind: "insight" | "status";
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
  const projectFileInsight = pickProjectFileInsight(projectFileFacts);
  if (projectFileInsight) {
    return projectFileInsight;
  }

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

  if (claudeSummary?.claude_desktop_chat.cache_detected) {
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

  return sample;
}

function pickProjectFileInsight(
  projectFileFacts: ProjectFileEvidenceFact[],
): ActiveDiscovery | null {
  const factsWithText = projectFileFacts.filter((fact) =>
    firstMeaningfulLine(fact.excerpt),
  );

  if (factsWithText.length === 0) {
    return null;
  }

  const corpus = factsWithText
    .map((fact) => fact.excerpt)
    .join("\n")
    .toLowerCase();

  if (
    corpus.includes("feedback") &&
    includesAny(corpus, [
      "bot",
      "chatbot",
      "coach",
      "coaching",
      "practice",
      "scenario",
      "sbin",
    ])
  ) {
    const evidence = rankedProjectFileEvidence(factsWithText, [
      "feedback",
      "coach",
      "coaching",
      "scenario",
      "practice",
      "sbin",
      "bot",
      "chatbot",
    ]);

    return {
      claim: "Your project materials describe a feedback coaching experience.",
      evidenceIds: evidence.map((fact) => `project-file-${fact.path}`),
      support:
        `Workprint found local project files that describe feedback guidance, coaching flows, and practice scenarios: ${formatEvidenceList(evidence)}.`,
      unknown:
        "These files do not determine who wrote the material, how much effort it took, whether AI was involved, or whether the described experience is complete or correct.",
      confidence: "Moderate",
      kind: "insight",
    };
  }

  if (includesAny(corpus, ["chatbot", " bot "])) {
    const evidence = rankedProjectFileEvidence(factsWithText, ["chatbot", "bot"]);

    return {
      claim: "Your project materials describe a chatbot experience.",
      evidenceIds: evidence.map((fact) => `project-file-${fact.path}`),
      support:
        `Workprint found local project files that directly discuss the chatbot or bot experience: ${formatEvidenceList(evidence)}.`,
      unknown:
        "These files do not determine authorship, effort, ownership, intent, AI involvement, or whether the implementation matches the described experience.",
      confidence: "Limited",
      kind: "insight",
    };
  }

  if (corpus.includes("scenario") && corpus.includes("practice")) {
    const evidence = rankedProjectFileEvidence(factsWithText, [
      "scenario",
      "practice",
    ]);

    return {
      claim: "Your project materials include practice scenarios and user flows.",
      evidenceIds: evidence.map((fact) => `project-file-${fact.path}`),
      support:
        `Workprint found local files that describe scenario and practice-flow material: ${formatEvidenceList(evidence)}.`,
      unknown:
        "These files do not prove importance, completeness, authorship, effort, ownership, intent, or AI involvement.",
      confidence: "Limited",
      kind: "insight",
    };
  }

  const prototypeInsight = pickPrototypeInsight(factsWithText);
  if (prototypeInsight) {
    return prototypeInsight;
  }

  const titledEvidence = factsWithText
    .map((fact) => ({ fact, title: firstTitleLine(fact.excerpt) }))
    .filter((item): item is { fact: ProjectFileEvidenceFact; title: string } =>
      Boolean(item.title),
    )
    .slice(0, 3);

  if (titledEvidence.length > 0) {
    const titles = titledEvidence.map((item) => item.title);
    const noun = titledEvidence.length === 1 ? "file" : "files";

    return {
      claim: projectMaterialsClaim(titles),
      evidenceIds: titledEvidence.map((item) => `project-file-${item.fact.path}`),
      support:
        `Workprint found README or project-note titles in ${titledEvidence.length} local ${noun}: ${formatTitledEvidence(titledEvidence)}.`,
      unknown:
        "These titles and excerpts do not prove authorship, effort, ownership, intent, completeness, correctness, or AI involvement.",
      confidence: MECHANICAL_CONFIDENCE,
      kind: "insight",
    };
  }

  return null;
}

function pickPrototypeInsight(
  factsWithText: ProjectFileEvidenceFact[],
): ActiveDiscovery | null {
  const prototypeFacts = factsWithText
    .map((fact) => {
      const title = firstTitleLine(fact.excerpt);
      const match = fact.excerpt.match(
        /(?:static,\s*)?responsive prototype for ([^.\n]+)/i,
      );

      return {
        fact,
        title,
        subject: match?.[1]?.trim(),
      };
    })
    .filter(
      (item): item is {
        fact: ProjectFileEvidenceFact;
        title: string;
        subject: string;
      } => Boolean(item.title && item.subject),
    );

  if (prototypeFacts.length === 0) {
    return null;
  }

  const subjectCounts = new Map<string, number>();
  for (const item of prototypeFacts) {
    subjectCounts.set(item.subject, (subjectCounts.get(item.subject) ?? 0) + 1);
  }

  const subject = [...subjectCounts.entries()].sort(
    (left, right) => right[1] - left[1],
  )[0]?.[0];

  if (!subject) {
    return null;
  }

  const evidence = prototypeFacts
    .filter((item) => item.subject === subject)
    .slice(0, 3);
  const noun = evidence.length === 1 ? "file" : "files";

  return {
    claim: `Your project materials describe responsive prototypes for ${subject}.`,
    evidenceIds: evidence.map((item) => `project-file-${item.fact.path}`),
    support:
      `Workprint found README titles in ${evidence.length} local ${noun} that describe responsive prototypes: ${formatTitledEvidence(evidence)}.`,
    unknown:
      "These README files do not prove who made the prototypes, how much effort they took, whether AI was involved, or whether the prototypes are complete or correct.",
    confidence: MECHANICAL_CONFIDENCE,
    kind: "insight",
  };
}

function rankedProjectFileEvidence(
  facts: ProjectFileEvidenceFact[],
  terms: string[],
) {
  return [...facts]
    .map((fact) => ({
      fact,
      score: terms.reduce(
        (total, term) =>
          total + occurrenceCount(fact.excerpt.toLowerCase(), term),
        0,
      ),
    }))
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 3)
    .map((item) => item.fact);
}

function occurrenceCount(text: string, term: string) {
  return text.split(term).length - 1;
}

function includesAny(text: string, terms: string[]) {
  return terms.some((term) => text.includes(term));
}

function formatEvidenceList(facts: ProjectFileEvidenceFact[]) {
  return facts
    .map((fact) => {
      const line = firstMeaningfulLine(fact.excerpt);
      return line ? `${fact.path} says "${line}"` : fact.path;
    })
    .join("; ");
}

function formatTitledEvidence(
  items: { fact: ProjectFileEvidenceFact; title: string }[],
) {
  return items
    .map((item) => `${item.fact.path} says "${item.title}"`)
    .join("; ");
}

function projectMaterialsClaim(titles: string[]) {
  const sharedPrefix = commonTitlePrefix(titles);

  if (sharedPrefix) {
    return `Your project materials describe ${withArticle(sharedPrefix)}.`;
  }

  if (titles.length === 1) {
    return `Your project materials describe ${withArticle(titles[0])}.`;
  }

  return `Your project materials describe ${titles.length} related project pieces.`;
}

function commonTitlePrefix(titles: string[]) {
  if (titles.length < 2) {
    return null;
  }

  const splitTitles = titles.map((title) =>
    title
      .split(/\s+[—-]\s+/)
      .map((part) => part.trim())
      .filter(Boolean),
  );
  const firstPrefix = splitTitles[0]?.[0];

  if (
    firstPrefix &&
    firstPrefix.length >= 6 &&
    splitTitles.every((parts) => parts[0] === firstPrefix)
  ) {
    return firstPrefix;
  }

  return null;
}

function withArticle(phrase: string) {
  const trimmed = phrase.trim();

  if (!trimmed) {
    return "a project";
  }

  if (/^(?:a|an|the|your|this|these)\b/i.test(trimmed)) {
    return trimmed;
  }

  return `${startsWithVowelSound(trimmed) ? "an" : "a"} ${trimmed}`;
}

function startsWithVowelSound(phrase: string) {
  return /^[aeiou]/i.test(phrase);
}

function firstTitleLine(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .map((line) => line.replace(/^#+\s*/, "").trim())
    .find((line) => isUsefulTitle(line));
}

function isUsefulTitle(line: string | undefined) {
  if (!line || line === "...") {
    return false;
  }

  if (line.length < 8 || line.length > 140) {
    return false;
  }

  if (/^run locally\b/i.test(line)) {
    return false;
  }

  if (/^(?:install|usage|setup|configuration|development)\b/i.test(line)) {
    return false;
  }

  return /[a-z]/i.test(line);
}

function firstMeaningfulLine(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line && line !== "...");
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

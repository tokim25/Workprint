export type SourceStatus = "ready" | "limited" | "unsupported";

export type ProjectSource = {
  id: string;
  name: string;
  description: string;
  status: SourceStatus;
  note: string;
  count?: number;
  countLabel?: string;
};

export type EvidenceItem = {
  id: string;
  source: string;
  title: string;
  excerpt: string;
  supports: string;
  doesNotProve: string;
};

export const projectSources: ProjectSource[] = [
  {
    id: "conversation-export",
    name: "Conversation export",
    description: "Prompts, responses, revisions, and decision discussion.",
    status: "ready",
    note: "Can show captured conversation activity.",
  },
  {
    id: "project-docs",
    name: "Project files",
    description: "Briefs, plans, notes, and working documents.",
    status: "limited",
    note: "Static files may not include revision history or deleted work.",
  },
  {
    id: "repository-history",
    name: "Repository history",
    description: "Recorded commits and project changes over time.",
    status: "ready",
    note: "Repository metadata does not prove who wrote every line.",
  },
  {
    id: "unsupported-pdf",
    name: "Loose reference PDF",
    description: "A sample unsupported item included to show recovery.",
    status: "unsupported",
    note: "Workprint cannot read this sample file type yet.",
  },
];

export const evidenceItems: EvidenceItem[] = [
  {
    id: "ev-001",
    source: "Conversation export",
    title: "You narrowed the first experience",
    excerpt:
      "Use the approved four-screen model and make the first insight dominate the Discoveries viewport.",
    supports:
      "This supports direction-setting because it gives a clear product constraint and prioritizes the first value moment.",
    doesNotProve:
      "It does not prove total authorship, ownership, effort, intent, or contribution share.",
  },
  {
    id: "ev-002",
    source: "Visual direction",
    title: "Warm Investigator was chosen as the direction",
    excerpt:
      "Recognition before analysis. Warmth must never weaken precision. Evidence should feel close to claims.",
    supports:
      "This supports the interaction tone: personal recognition first, followed by precise evidence explanation.",
    doesNotProve:
      "It does not prove that every later implementation choice will satisfy the visual direction.",
  },
  {
    id: "ev-003",
    source: "Wireframes",
    title: "Evidence sits beside the claim",
    excerpt:
      "The evidence drawer should explain what the evidence does and does not prove.",
    supports:
      "This supports the trust boundary by keeping evidence close to the claim it qualifies.",
    doesNotProve:
      "It does not determine authorship, ownership, effort, or value.",
  },
];

export const insight = {
  claim: "You repeatedly set the direction.",
  support:
    "Workprint found multiple sample moments where your messages set constraints, requested revisions, or chose the next step.",
  confidence: "Moderate",
  kind: "insight" as const,
  unknown:
    "The sample evidence cannot determine total authorship, ownership, effort, intent, or contribution share.",
};

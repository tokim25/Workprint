import { formatDate } from "./git-summary";

export type ClaudeSessionAggregate = {
  session_count: number;
  turn_count: number;
  human_turn_count: number;
  assistant_turn_count: number;
  sidechain_turn_count: number;
  tool_use_counts: Record<string, number>;
  earliest_turn_date: string | null;
  latest_turn_date: string | null;
};

export type ClaudeDesktopChatSummary = {
  cache_detected: boolean;
  last_modified: string | null;
  deep_parse_available: boolean;
  deep_parse_requested: boolean;
  deep_parse_found_turns: boolean;
  turns?: ClaudeSessionAggregate;
};

export type ClaudeLocalSummary = {
  ok: true;
  claude_code: ClaudeSessionAggregate;
  claude_cowork: ClaudeSessionAggregate;
  claude_desktop_chat: ClaudeDesktopChatSummary;
  limitations: string[];
};

export type ClaudeLocalSummaryError = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type ClaudeLocalSummaryResponse = ClaudeLocalSummary | ClaudeLocalSummaryError;

export function claudeCodeDiscoveryClaim(summary: ClaudeSessionAggregate) {
  return sessionDiscoveryClaim("Claude Code", summary);
}

export function claudeCoworkDiscoveryClaim(summary: ClaudeSessionAggregate) {
  return sessionDiscoveryClaim("Claude Cowork", summary);
}

function sessionDiscoveryClaim(label: string, summary: ClaudeSessionAggregate) {
  if (summary.session_count === 0) {
    return `${label} recorded no local sessions for this project.`;
  }

  const sessionNoun = summary.session_count === 1 ? "session" : "sessions";
  const start = formatDate(summary.earliest_turn_date);
  const end = formatDate(summary.latest_turn_date);

  if (start && end) {
    return `${label} recorded ${summary.session_count} local ${sessionNoun} between ${start} and ${end}.`;
  }

  return `${label} recorded ${summary.session_count} local ${sessionNoun}.`;
}

export function sessionDiscoverySupport(summary: ClaudeSessionAggregate) {
  const toolEntries = Object.entries(summary.tool_use_counts).sort(
    (a, b) => b[1] - a[1],
  );
  const toolSummary = toolEntries
    .slice(0, 3)
    .map(([name, count]) => `${name} (${count})`)
    .join(", ");
  const turnNoun = summary.turn_count === 1 ? "turn" : "turns";

  if (toolSummary) {
    return `${summary.turn_count} recorded ${turnNoun}, including tool use: ${toolSummary}.`;
  }

  return `${summary.turn_count} recorded ${turnNoun}.`;
}

export function claudeDesktopChatDiscoveryClaim(chat: ClaudeDesktopChatSummary) {
  if (!chat.cache_detected) {
    return "No local Claude Desktop chat cache was detected.";
  }

  const modified = formatDate(chat.last_modified);
  const when = modified ? `, last changed ${modified}` : "";

  if (!chat.deep_parse_requested) {
    return `A local Claude Desktop chat cache was detected${when}.`;
  }

  if (chat.deep_parse_found_turns && chat.turns) {
    const turnNoun = chat.turns.turn_count === 1 ? "turn" : "turns";
    return `Detailed reading found ${chat.turns.turn_count} candidate conversation ${turnNoun} (experimental, account-wide).`;
  }

  return `A local Claude Desktop chat cache was detected${when}, but detailed reading found nothing readable this time.`;
}

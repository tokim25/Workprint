import {
  claudeCodeDiscoveryClaim,
  claudeCoworkDiscoveryClaim,
  claudeDesktopChatDiscoveryClaim,
  sessionDiscoverySupport,
  type ClaudeLocalSummary,
  type ClaudeSessionAggregate,
} from "@/lib/claude-local-summary";

type ClaudeSessionEvidenceProps = {
  summary: ClaudeLocalSummary | null;
};

export function ClaudeSessionEvidence({ summary }: ClaudeSessionEvidenceProps) {
  if (!summary) {
    return (
      <section
        aria-labelledby="claude-session-heading"
        className="mt-10 max-w-4xl border-t border-[var(--line)] pt-6"
      >
        <h2
          className="text-2xl font-semibold tracking-[-0.03em]"
          id="claude-session-heading"
        >
          Local Claude session evidence
        </h2>
        <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
          Claude session data is not available until a local project path is
          connected.
        </p>
      </section>
    );
  }

  return (
    <section
      aria-labelledby="claude-session-heading"
      className="mt-12 max-w-5xl border-t border-[var(--line)] pt-8"
    >
      <h2
        className="text-2xl font-semibold tracking-[-0.03em]"
        id="claude-session-heading"
      >
        Local Claude session evidence
      </h2>
      <div className="mt-6 space-y-6">
        <SessionSourceCard
          claim={claudeCodeDiscoveryClaim(summary.claude_code)}
          data={summary.claude_code}
          label="Claude Code"
        />
        <SessionSourceCard
          claim={claudeCoworkDiscoveryClaim(summary.claude_cowork)}
          data={summary.claude_cowork}
          label="Claude Cowork"
        />
        <article className="border-l-2 border-[var(--line)] pl-5">
          <p className="text-sm font-semibold text-[var(--accent)]">
            Claude Desktop Chat
          </p>
          <p className="mt-2 text-lg font-semibold tracking-[-0.02em]">
            {claudeDesktopChatDiscoveryClaim(summary.claude_desktop_chat)}
          </p>
          {summary.claude_desktop_chat.deep_parse_requested &&
          summary.claude_desktop_chat.deep_parse_found_turns &&
          summary.claude_desktop_chat.turns ? (
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              {sessionDiscoverySupport(summary.claude_desktop_chat.turns)}
            </p>
          ) : null}
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
            This evidence is account-wide. It cannot be confirmed to relate to
            this specific project, because claude.ai chat has no concept of a
            project folder.
          </p>
        </article>
      </div>
      <p className="mt-6 rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6 text-[var(--muted)]">
        {summary.limitations.join(" ")}
      </p>
    </section>
  );
}

function SessionSourceCard({
  label,
  claim,
  data,
}: {
  label: string;
  claim: string;
  data: ClaudeSessionAggregate;
}) {
  return (
    <article className="border-l-2 border-[var(--line)] pl-5">
      <p className="text-sm font-semibold text-[var(--accent)]">{label}</p>
      <p className="mt-2 text-lg font-semibold tracking-[-0.02em]">{claim}</p>
      {data.turn_count > 0 ? (
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          {sessionDiscoverySupport(data)}
        </p>
      ) : null}
    </article>
  );
}

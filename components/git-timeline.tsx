import {
  formatDate,
  formatTimestamp,
  recordedLineChanges,
  type GitRecentCommit,
  type GitSummary,
} from "@/lib/git-summary";

type GitTimelineProps = {
  summary: GitSummary | null;
};

export function GitTimeline({ summary }: GitTimelineProps) {
  if (!summary) {
    return (
      <section
        aria-labelledby="git-timeline-heading"
        className="mt-10 max-w-4xl border-t border-[var(--line)] pt-6"
      >
        <h2
          className="text-2xl font-semibold tracking-[-0.03em]"
          id="git-timeline-heading"
        >
          Recent commits recorded by Git
        </h2>
        <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
          Git timeline data is not available until a local repository path is
          connected.
        </p>
      </section>
    );
  }

  const start = formatDate(summary.summary.earliest_commit_date);
  const end = formatDate(summary.summary.latest_commit_date);
  const commits = summary.recent_commits;
  const capApplies =
    summary.summary.total_commit_count > summary.summary.recent_commit_count;

  return (
    <section
      aria-labelledby="git-timeline-heading"
      className="mt-12 max-w-5xl border-t border-[var(--line)] pt-8"
    >
      <div className="max-w-3xl">
        <h2
          className="text-2xl font-semibold tracking-[-0.03em]"
          id="git-timeline-heading"
        >
          Recent commits recorded by Git
        </h2>
        <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
          Git records {summary.summary.total_commit_count}{" "}
          {summary.summary.total_commit_count === 1 ? "commit" : "commits"}
          {start && end ? ` between ${start} and ${end}` : ""} in{" "}
          {summary.repository.name}.
          {summary.repository.current_branch
            ? ` The observable current branch is ${summary.repository.current_branch}.`
            : " The current branch was not available."}
        </p>
        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
          This view shows {summary.summary.recent_commit_count} most recent{" "}
          {summary.summary.recent_commit_count === 1 ? "commit" : "commits"}
          {capApplies
            ? ` from a bounded limit of ${summary.summary.recent_commit_limit}, not the complete history.`
            : "."}
        </p>
      </div>

      {commits.length === 0 ? (
        <p className="mt-6 rounded-2xl border border-[var(--line)] p-4 text-sm leading-6 text-[var(--muted)]">
          This repository is available to Git, but Git records no commits in
          the returned summary.
        </p>
      ) : (
        <div className="mt-8 space-y-5">
          {commits.map((commit) => (
            <CommitTimelineItem commit={commit} key={commit.commit_sha} />
          ))}
        </div>
      )}
    </section>
  );
}

function CommitTimelineItem({ commit }: { commit: GitRecentCommit }) {
  const lineChanges = recordedLineChanges(commit);

  return (
    <article className="border-l-2 border-[var(--line)] pl-5">
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--accent)]">
          {commit.abbreviated_sha}
        </p>
        <h3 className="max-w-3xl break-words text-xl font-semibold tracking-[-0.02em]">
          {commit.message || "Commit message not available"}
        </h3>
        <p className="text-sm leading-6 text-[var(--muted)]">
          Recorded {formatTimestamp(commit.committed_at)}. The recorded author
          field is &quot;{commit.author}&quot;.
        </p>
        <p className="text-sm leading-6 text-[var(--muted)]">
          Git records {commit.file_change_count} changed{" "}
          {commit.file_change_count === 1 ? "file" : "files"}
          {lineChanges
            ? ` and ${lineChanges.additions} additions / ${lineChanges.deletions} deletions as recorded line changes.`
            : ". Line change counts are not available for this commit."}
        </p>
      </div>

      <details className="mt-4 rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6">
        <summary className="cursor-pointer font-semibold text-[var(--foreground)]">
          View file changes for commit {commit.abbreviated_sha}
        </summary>
        {commit.file_changes.length === 0 ? (
          <p className="mt-3 text-[var(--muted)]">
            No bounded file-change records were returned for this commit.
          </p>
        ) : (
          <ul className="mt-4 space-y-3">
            {commit.file_changes.map((change) => (
              <li
                className="border-t border-[var(--line)] pt-3 first:border-t-0 first:pt-0"
                key={`${commit.commit_sha}-${change.path}`}
              >
                <p className="break-words font-semibold text-[var(--foreground)]">
                  {change.path}
                </p>
                <p className="text-[var(--muted)]">
                  Change type: {change.change_type}.{" "}
                  {change.additions === null || change.deletions === null
                    ? "Recorded line changes are not available."
                    : `${change.additions} additions / ${change.deletions} deletions recorded by Git.`}
                </p>
              </li>
            ))}
          </ul>
        )}
        {commit.file_change_count > commit.file_changes.length ? (
          <p className="mt-4 text-[var(--muted)]">
            Git records {commit.file_change_count} changed files for this
            commit. This view shows the first {commit.file_changes.length} file
            changes to keep the report a reasonable size.
          </p>
        ) : null}
        <p className="mt-4 border-t border-[var(--line)] pt-3 text-[var(--muted)]">
          Evidence: Git commit {commit.commit_sha}. These are recorded Git
          facts, not proof of authorship, effort, importance, ownership,
          contribution, intent, collaboration quality, or AI involvement.
        </p>
      </details>
    </article>
  );
}

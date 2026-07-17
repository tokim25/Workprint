export type GitFileChange = {
  path: string;
  change_type: string;
  additions: number | null;
  deletions: number | null;
};

export type GitRecentCommit = {
  commit_sha: string;
  abbreviated_sha: string;
  committed_at: string;
  author: string;
  message: string;
  body: string;
  is_merge: boolean;
  file_change_count: number;
  file_changes: GitFileChange[];
  file_change_limit: number;
};

export type GitSummary = {
  ok: true;
  repository: {
    name: string;
    current_branch: string | null;
    is_shallow: boolean;
  };
  summary: {
    total_commit_count: number;
    earliest_commit_date: string | null;
    latest_commit_date: string | null;
    recent_commit_count: number;
    recent_commit_limit: number;
  };
  recent_commits: GitRecentCommit[];
  limitations: string[];
};

export type GitSummaryError = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type GitSummaryResponse = GitSummary | GitSummaryError;

export function gitDiscoveryClaim(summary: GitSummary) {
  const count = summary.summary.total_commit_count;
  const noun = count === 1 ? "commit" : "commits";
  const start = formatDate(summary.summary.earliest_commit_date);
  const end = formatDate(summary.summary.latest_commit_date);

  if (count === 0) {
    return `Git records 0 commits in ${summary.repository.name}.`;
  }

  if (start && end) {
    return `Git records ${count} ${noun} between ${start} and ${end}.`;
  }

  return `Git records ${count} ${noun} in ${summary.repository.name}.`;
}

export function gitDiscoverySupport(summary: GitSummary) {
  const branch = summary.repository.current_branch
    ? ` The observable current branch is ${summary.repository.current_branch}.`
    : " The current branch was not available.";
  const recent = summary.summary.recent_commit_count;
  const noun = recent === 1 ? "recent commit" : "recent commits";

  return `Workprint read local Git metadata and returned ${recent} bounded ${noun}.${branch}`;
}

export function formatDate(value: string | null) {
  if (!value) {
    return null;
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

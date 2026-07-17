from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from workprint.adapters import GitAdapter
from workprint.models import NormalizedGitCommit, NormalizedGitRepository


DEFAULT_COMMIT_LIMIT = 5
MAX_COMMIT_LIMIT = 20
MAX_FILE_CHANGES_PER_COMMIT = 25
MAX_PATH_LENGTH = 4096


@dataclass(frozen=True)
class GitSummaryError(Exception):
    code: str
    message: str


def build_git_summary(
    repository_path: str,
    commit_limit: int = DEFAULT_COMMIT_LIMIT,
    adapter: GitAdapter | None = None,
) -> dict[str, Any]:
    root = _validated_path(repository_path)
    bounded_limit = _bounded_limit(commit_limit)
    git_adapter = adapter or GitAdapter()

    try:
        records = git_adapter.read(root)
    except ValueError as exc:
        raise _safe_adapter_error(exc) from exc

    repository = next(
        (record for record in records if isinstance(record, NormalizedGitRepository)),
        None,
    )
    commits = [record for record in records if isinstance(record, NormalizedGitCommit)]
    recent_commits = commits[-bounded_limit:]

    return {
        "ok": True,
        "repository": {
            "name": root.name or str(root),
            "current_branch": repository.current_branch if repository else None,
            "is_shallow": repository.is_shallow if repository else False,
        },
        "summary": {
            "total_commit_count": len(commits),
            "earliest_commit_date": commits[0].committed_at.isoformat() if commits else None,
            "latest_commit_date": commits[-1].committed_at.isoformat() if commits else None,
            "recent_commit_count": len(recent_commits),
            "recent_commit_limit": bounded_limit,
        },
        "recent_commits": [_commit_to_dict(commit) for commit in recent_commits],
        "limitations": [
            "Git author metadata is not verified identity or proof of authorship.",
            "Commit and line counts do not measure effort, importance, ownership, or contribution.",
            "Git cannot determine human versus AI involvement.",
            "Work outside Git may not be represented.",
        ],
    }


def _validated_path(repository_path: str) -> Path:
    if not isinstance(repository_path, str):
        raise GitSummaryError("invalid_path", "Repository path must be text.")
    if not repository_path.strip():
        raise GitSummaryError("missing_path", "Enter a local repository path.")
    if len(repository_path) > MAX_PATH_LENGTH:
        raise GitSummaryError("path_too_long", "Repository path is too long.")

    root = Path(repository_path).expanduser().resolve()
    if not root.exists():
        raise GitSummaryError("path_not_found", "Repository path was not found.")
    if not root.is_dir():
        raise GitSummaryError("not_directory", "Repository path must be a folder.")
    return root


def _bounded_limit(commit_limit: int) -> int:
    try:
        parsed = int(commit_limit)
    except (TypeError, ValueError) as exc:
        raise GitSummaryError("invalid_limit", "Commit limit must be a number.") from exc
    if parsed < 1:
        raise GitSummaryError("invalid_limit", "Commit limit must be at least 1.")
    return min(parsed, MAX_COMMIT_LIMIT)


def _safe_adapter_error(exc: ValueError) -> GitSummaryError:
    message = str(exc).lower()
    if "not a git repository" in message:
        return GitSummaryError(
            "not_git_repository",
            "This folder is not available as a Git repository.",
        )
    if "bare git repositories" in message:
        return GitSummaryError(
            "unsupported_repository",
            "Bare Git repositories are not supported in this prototype.",
        )
    if "git executable not found" in message:
        return GitSummaryError(
            "git_unavailable",
            "Git is not available to the local Workprint process.",
        )
    return GitSummaryError(
        "git_read_failed",
        "Workprint could not read Git metadata for this repository.",
    )


def _commit_to_dict(commit: NormalizedGitCommit) -> dict[str, Any]:
    return {
        "commit_sha": commit.commit_sha,
        "abbreviated_sha": commit.abbreviated_sha,
        "committed_at": commit.committed_at.isoformat(),
        "author": f"{commit.author_name} <{commit.author_email}>",
        "message": commit.subject,
        "body": commit.body,
        "is_merge": commit.is_merge,
        "file_change_count": len(commit.file_changes),
        "file_changes": [
            {
                "path": change.path,
                "change_type": change.change_type,
                "additions": change.additions,
                "deletions": change.deletions,
            }
            for change in commit.file_changes[:MAX_FILE_CHANGES_PER_COMMIT]
        ],
        "file_change_limit": MAX_FILE_CHANGES_PER_COMMIT,
    }


def _json_error(error: GitSummaryError) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Return a bounded Git summary as JSON.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_COMMIT_LIMIT)
    args = parser.parse_args(argv)

    try:
        payload = build_git_summary(args.repository, args.limit)
    except GitSummaryError as exc:
        print(json.dumps(_json_error(exc), ensure_ascii=False))
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

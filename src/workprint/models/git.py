from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class GitFileChange:
    path: str
    change_type: str
    additions: int | None
    deletions: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "additions": self.additions,
            "deletions": self.deletions,
        }


@dataclass(frozen=True)
class NormalizedGitRepository:
    id: str
    source: str
    source_locator: str
    repository_root: str
    current_branch: str | None
    is_bare: bool
    is_shallow: bool
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("repository id is required")
        if not self.repository_root:
            raise ValueError("repository root is required")


@dataclass(frozen=True)
class NormalizedGitCommit:
    id: str
    source: str
    source_locator: str
    repository_root: str
    current_branch: str | None
    commit_sha: str
    abbreviated_sha: str
    committed_at: datetime
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    subject: str
    body: str
    parent_shas: tuple[str, ...]
    is_merge: bool
    file_changes: tuple[GitFileChange, ...]
    tags: tuple[str, ...]
    is_shallow: bool
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("commit id is required")
        if not self.commit_sha:
            raise ValueError("commit SHA is required")
        if not self.abbreviated_sha:
            raise ValueError("abbreviated SHA is required")
        if not isinstance(self.subject, str):
            raise TypeError("subject must be a string")
        if not isinstance(self.body, str):
            raise TypeError("body must be a string")

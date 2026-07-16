from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from workprint.adapters.base import EvidenceAdapter
from workprint.models import GitFileChange, NormalizedGitCommit, NormalizedGitRepository


FIELD_SEPARATOR = "\x1f"


@dataclass(frozen=True)
class _GitCommand:
    executable: str = "git"

    def run(self, repository: Path | None, args: list[str]) -> str:
        command = [self.executable, "-c", "core.quotePath=false"]
        if repository is not None:
            command.extend(["-C", str(repository)])
        command.extend(args)
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError as exc:
            raise ValueError("git executable not found") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            if detail:
                raise ValueError(detail) from exc
            raise ValueError("git command failed") from exc
        return result.stdout


class GitAdapter(EvidenceAdapter[Any]):
    """Read local Git metadata without mutating the repository."""

    source_name = "git"
    source_type = "repository"

    def __init__(self, git_executable: str = "git") -> None:
        self._git = _GitCommand(git_executable)

    @property
    def display_name(self) -> str:
        return "Git"

    def validate_input(self, path: str | Path) -> Path:
        source_path = Path(path).expanduser()
        if not source_path.exists():
            raise ValueError(f"path not found: {source_path}")
        if not source_path.is_dir():
            raise ValueError(f"input is not a directory: {source_path}")
        return self._repository_root(source_path)

    def discover(self, path: str | Path) -> dict[str, Any] | None:
        try:
            root = self.validate_input(path)
            is_shallow = self._bool(root, "rev-parse", "--is-shallow-repository")
            branch = self._branch(root)
        except ValueError:
            return None
        return {
            "source": self.adapter_id,
            "label": self.display_name,
            "record_count": 1,
            "repository_root": str(root),
            "current_branch": branch,
            "is_shallow": is_shallow,
        }

    def read(self, path: str | Path) -> list[NormalizedGitRepository | NormalizedGitCommit]:
        root = self.validate_input(path)
        if self._bool(root, "rev-parse", "--is-bare-repository"):
            raise ValueError("bare Git repositories are not supported by the Git adapter")

        branch = self._branch(root)
        is_shallow = self._bool(root, "rev-parse", "--is-shallow-repository")
        records: list[NormalizedGitRepository | NormalizedGitCommit] = [
            NormalizedGitRepository(
                id=f"git-repository:{root}",
                source=self.adapter_id,
                source_locator=f"{root}#git/repository",
                repository_root=str(root),
                current_branch=branch,
                is_bare=False,
                is_shallow=is_shallow,
                metadata={"source_type": self.source_type},
            )
        ]

        for sha in self._commit_shas(root):
            records.append(self._commit_record(root, branch, is_shallow, sha))
        return records

    def _repository_root(self, path: Path) -> Path:
        try:
            root = self._git.run(path, ["rev-parse", "--show-toplevel"]).strip()
        except ValueError as exc:
            if "git executable not found" in str(exc):
                raise
            raise ValueError(f"not a Git repository: {path}") from exc
        if not root:
            raise ValueError(f"not a Git repository: {path}")
        repository_root = Path(root).resolve()
        if self._bool(repository_root, "rev-parse", "--is-bare-repository"):
            raise ValueError("bare Git repositories are not supported by the Git adapter")
        return repository_root

    def _bool(self, root: Path, *args: str) -> bool:
        return self._git.run(root, list(args)).strip().lower() == "true"

    def _branch(self, root: Path) -> str | None:
        branch = self._git.run(root, ["branch", "--show-current"]).strip()
        return branch or None

    def _commit_shas(self, root: Path) -> tuple[str, ...]:
        try:
            output = self._git.run(root, ["log", "--reverse", "--format=%H"])
        except ValueError as exc:
            message = str(exc).lower()
            if "does not have any commits yet" in message or "bad default revision" in message:
                return ()
            raise
        return tuple(line.strip() for line in output.splitlines() if line.strip())

    def _commit_record(
        self,
        root: Path,
        branch: str | None,
        is_shallow: bool,
        sha: str,
    ) -> NormalizedGitCommit:
        fields = self._git.run(
            root,
            [
                "show",
                "-s",
                f"--format=%H{FIELD_SEPARATOR}%h{FIELD_SEPARATOR}%aI{FIELD_SEPARATOR}%an{FIELD_SEPARATOR}%ae{FIELD_SEPARATOR}%cn{FIELD_SEPARATOR}%ce{FIELD_SEPARATOR}%P{FIELD_SEPARATOR}%s{FIELD_SEPARATOR}%B",
                sha,
            ],
        ).split(FIELD_SEPARATOR, 9)
        if len(fields) != 10:
            raise ValueError(f"could not parse Git commit metadata for {sha}")

        (
            commit_sha,
            abbreviated_sha,
            timestamp,
            author_name,
            author_email,
            committer_name,
            committer_email,
            parents,
            subject,
            raw_body,
        ) = fields
        body = raw_body.strip()
        if body.startswith(subject):
            body = body[len(subject):].strip()
        parent_shas = tuple(item for item in parents.split() if item)
        file_changes = self._file_changes(root, sha)
        tags = tuple(sorted(self._git.run(root, ["tag", "--points-at", sha]).splitlines()))

        return NormalizedGitCommit(
            id=f"git-commit:{commit_sha}",
            source=self.adapter_id,
            source_locator=f"{root}#commit/{commit_sha}",
            repository_root=str(root),
            current_branch=branch,
            commit_sha=commit_sha,
            abbreviated_sha=abbreviated_sha,
            committed_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
            author_name=author_name,
            author_email=author_email,
            committer_name=committer_name,
            committer_email=committer_email,
            subject=subject,
            body=body,
            parent_shas=parent_shas,
            is_merge=len(parent_shas) > 1,
            file_changes=file_changes,
            tags=tags,
            is_shallow=is_shallow,
            metadata={"source_type": self.source_type},
        )

    def _file_changes(self, root: Path, sha: str) -> tuple[GitFileChange, ...]:
        status_by_path = self._status_by_path(root, sha)
        stats_by_path = self._stats_by_path(root, sha)
        paths = sorted(set(status_by_path) | set(stats_by_path))
        return tuple(
            GitFileChange(
                path=path,
                change_type=status_by_path.get(path, "unknown"),
                additions=stats_by_path.get(path, (None, None))[0],
                deletions=stats_by_path.get(path, (None, None))[1],
            )
            for path in paths
        )

    def _status_by_path(self, root: Path, sha: str) -> dict[str, str]:
        output = self._git.run(
            root,
            ["diff-tree", "--no-commit-id", "--name-status", "-r", "-M", "--root", sha],
        )
        values: dict[str, str] = {}
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            status = parts[0]
            path = parts[-1]
            values[path] = status[0]
        return values

    def _stats_by_path(self, root: Path, sha: str) -> dict[str, tuple[int | None, int | None]]:
        output = self._git.run(
            root,
            ["diff-tree", "--no-commit-id", "--numstat", "-r", "-M", "--root", sha],
        )
        values: dict[str, tuple[int | None, int | None]] = {}
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            additions = _parse_count(parts[0])
            deletions = _parse_count(parts[1])
            path = parts[-1]
            values[path] = (additions, deletions)
        return values


def _parse_count(value: str) -> int | None:
    if value == "-":
        return None
    return int(value)

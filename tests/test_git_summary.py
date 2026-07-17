from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import GitAdapter
from workprint.git_summary import (
    MAX_COMMIT_LIMIT,
    MAX_FILE_CHANGES_PER_COMMIT,
    GitSummaryError,
    build_git_summary,
    main,
)


GIT = shutil.which("git")


class FailingGitAdapter(GitAdapter):
    def __init__(self, message: str) -> None:
        self.message = message

    def read(self, path):  # noqa: ANN001
        raise ValueError(self.message)


@unittest.skipUnless(GIT, "git executable is required for Git summary tests")
class GitSummaryTests(unittest.TestCase):
    def test_returns_bounded_factual_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")
            self._commit_file(repo, "b.txt", "second\n", "Add second")

            summary = build_git_summary(str(repo), commit_limit=1)

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["repository"]["name"], repo.name)
        self.assertEqual(summary["summary"]["total_commit_count"], 2)
        self.assertIsNotNone(summary["summary"]["earliest_commit_date"])
        self.assertIsNotNone(summary["summary"]["latest_commit_date"])
        self.assertEqual(summary["summary"]["recent_commit_count"], 1)
        self.assertEqual(summary["recent_commits"][0]["message"], "Add second")
        self.assertIn("Workprint Tester <tester@example.com>", summary["recent_commits"][0]["author"])
        self.assertIn("Commit and line counts do not measure effort", summary["limitations"][1])

    def test_empty_repository_returns_zero_commit_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))

            summary = build_git_summary(str(repo))

        self.assertEqual(summary["summary"]["total_commit_count"], 0)
        self.assertIsNone(summary["summary"]["earliest_commit_date"])
        self.assertEqual(summary["recent_commits"], [])

    def test_rejects_missing_path(self):
        with self.assertRaises(GitSummaryError) as context:
            build_git_summary("")

        self.assertEqual(context.exception.code, "missing_path")

    def test_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "not-a-directory.txt"
            file_path.write_text("x", encoding="utf-8")

            with self.assertRaises(GitSummaryError) as context:
                build_git_summary(str(file_path))

        self.assertEqual(context.exception.code, "not_directory")

    def test_rejects_non_git_folder_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(GitSummaryError) as context:
                build_git_summary(directory)

        self.assertEqual(context.exception.code, "not_git_repository")
        self.assertNotIn(directory, context.exception.message)

    def test_caps_commit_limit_and_file_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            for index in range(MAX_COMMIT_LIMIT + 5):
                self._commit_file(repo, f"file-{index}.txt", "x\n", f"Add file {index}")
            for index in range(MAX_FILE_CHANGES_PER_COMMIT + 5):
                (repo / f"many-{index}.txt").write_text("x\n", encoding="utf-8")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-m", "Add many files", env=self._dates(99))

            summary = build_git_summary(str(repo), commit_limit=999)

        self.assertEqual(summary["summary"]["recent_commit_limit"], MAX_COMMIT_LIMIT)
        self.assertEqual(summary["summary"]["recent_commit_count"], MAX_COMMIT_LIMIT)
        last_commit = summary["recent_commits"][-1]
        self.assertEqual(last_commit["file_change_limit"], MAX_FILE_CHANGES_PER_COMMIT)
        self.assertEqual(len(last_commit["file_changes"]), MAX_FILE_CHANGES_PER_COMMIT)

    def test_invalid_limit_is_structured_error(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            with self.assertRaises(GitSummaryError) as context:
                build_git_summary(str(repo), commit_limit=0)

        self.assertEqual(context.exception.code, "invalid_limit")

    def test_git_failure_does_not_leak_raw_error(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            adapter = FailingGitAdapter("fatal: secret/path failed badly")

            with self.assertRaises(GitSummaryError) as context:
                build_git_summary(str(repo), adapter=adapter)

        self.assertEqual(context.exception.code, "git_read_failed")
        self.assertNotIn("secret", context.exception.message)

    def test_cli_returns_json_error_for_non_git_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            exit_code = main(["--repository", directory])

        self.assertEqual(exit_code, 1)

    @staticmethod
    def _init_repo(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        GitSummaryTests._git(path, "init")
        GitSummaryTests._git(path, "config", "user.name", "Workprint Tester")
        GitSummaryTests._git(path, "config", "user.email", "tester@example.com")
        return path.resolve()

    @staticmethod
    def _commit_file(repo: Path, relative_path: str, content: str, message: str) -> None:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        GitSummaryTests._git(repo, "add", relative_path)
        try:
            count = int(GitSummaryTests._git(repo, "rev-list", "--count", "HEAD").strip())
        except subprocess.CalledProcessError:
            count = 0
        GitSummaryTests._git(repo, "commit", "-m", message, env=GitSummaryTests._dates(count + 1))

    @staticmethod
    def _dates(index: int) -> dict[str, str]:
        day = (index % 28) + 1
        minute = index % 60
        timestamp = f"2026-02-{day:02d}T12:{minute:02d}:00+00:00"
        return {
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }

    @staticmethod
    def _git(repo: Path | None, *args: str, env: dict[str, str] | None = None) -> str:
        command = [GIT]
        if repo is not None:
            command.extend(["-C", str(repo)])
        command.extend(args)
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=merged_env,
        )
        return result.stdout


if __name__ == "__main__":
    unittest.main()

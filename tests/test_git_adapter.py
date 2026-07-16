from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import GitAdapter, get_adapter
from workprint.extractor import extract_observations
from workprint.models import NormalizedGitCommit, NormalizedGitRepository


GIT = shutil.which("git")


@unittest.skipUnless(GIT, "git executable is required for Git adapter tests")
class GitAdapterTests(unittest.TestCase):
    def test_adapter_is_registered(self):
        adapter = get_adapter("git")

        self.assertIsInstance(adapter, GitAdapter)
        self.assertEqual(adapter.adapter_id, "git")
        self.assertEqual(adapter.display_name, "Git")

    def test_reads_repository_commits_in_deterministic_order(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first file")
            self._commit_file(repo, "b.txt", "second\n", "Add second file")

            records = GitAdapter().read(repo)

        commits = self._commits(records)
        self.assertEqual([item.subject for item in commits], ["Add first file", "Add second file"])
        self.assertEqual(commits[0].file_changes[0].path, "a.txt")
        self.assertEqual(commits[0].file_changes[0].change_type, "A")
        self.assertEqual(commits[0].file_changes[0].additions, 1)

    def test_preserves_commit_body_tag_and_author_committer(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            path = repo / "body.txt"
            path.write_text("body\n", encoding="utf-8")
            self._git(repo, "add", "body.txt")
            self._git(
                repo,
                "-c",
                "user.name=Committer Name",
                "-c",
                "user.email=committer@example.com",
                "commit",
                "--author",
                "Author Name <author@example.com>",
                "-m",
                "Choose parser",
                "-m",
                "I decided to keep local Git evidence deterministic.",
                env=self._dates(1),
            )
            sha = self._git(repo, "rev-parse", "HEAD").strip()
            self._git(repo, "tag", "v1.0", sha)

            commit = self._commits(GitAdapter().read(repo))[0]

        self.assertEqual(commit.author_name, "Author Name")
        self.assertEqual(commit.author_email, "author@example.com")
        self.assertEqual(commit.committer_name, "Committer Name")
        self.assertEqual(commit.committer_email, "committer@example.com")
        self.assertEqual(commit.subject, "Choose parser")
        self.assertIn("I decided to keep", commit.body)
        self.assertEqual(commit.tags, ("v1.0",))

    def test_handles_multi_file_unicode_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "ascii.txt", "hello\n", "Initial commit")
            (repo / "café.txt").write_text("bonjour\n", encoding="utf-8")
            (repo / "notes.txt").write_text("note\n", encoding="utf-8")
            self._git(repo, "add", "café.txt", "notes.txt")
            self._git(repo, "commit", "-m", "Add café notes", env=self._dates(2))

            commit = self._commits(GitAdapter().read(repo))[-1]

        self.assertEqual(commit.subject, "Add café notes")
        self.assertEqual({item.path for item in commit.file_changes}, {"café.txt", "notes.txt"})

    def test_detects_merge_commits(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "base.txt", "base\n", "Base commit")
            trunk = self._git(repo, "branch", "--show-current").strip()
            self._git(repo, "switch", "-c", "feature")
            self._commit_file(repo, "feature.txt", "feature\n", "Add feature")
            self._git(repo, "switch", trunk)
            self._commit_file(repo, "main.txt", "main\n", "Add main")
            self._git(repo, "merge", "--no-ff", "feature", "-m", "Merge feature branch", env=self._dates(4))

            merge = self._commits(GitAdapter().read(repo))[-1]

        self.assertTrue(merge.is_merge)
        self.assertEqual(len(merge.parent_shas), 2)
        self.assertEqual(merge.subject, "Merge feature branch")

    def test_empty_repository_returns_repository_record(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))

            records = GitAdapter().read(repo)

        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], NormalizedGitRepository)
        self.assertEqual(records[0].repository_root, str(repo))

    def test_non_repository_failure_is_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "not a Git repository"):
                GitAdapter().read(directory)

    def test_git_unavailable_failure_is_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "git executable not found"):
                GitAdapter(git_executable="workprint-missing-git").read(directory)

    def test_adapter_does_not_mutate_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first file")
            head_before = self._git(repo, "rev-parse", "HEAD")
            status_before = self._git(repo, "status", "--short")

            GitAdapter().read(repo)

            self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before)
            self.assertEqual(self._git(repo, "status", "--short"), status_before)

    def test_extracted_git_observations_preserve_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "report.md", "# Report\n", "I chose the report format")

            observations = extract_observations(GitAdapter().read(repo))

        self.assertTrue(any(item.source == "git" for item in observations))
        self.assertTrue(any(item.activity == "decision" for item in observations))
        artifact = next(item for item in observations if item.artifact == "report.md")
        self.assertIn("not effort or value", artifact.statement)
        self.assertIn("/file/report.md", artifact.evidence_refs[0])
        self.assertEqual(artifact.metadata["file_path"], "report.md")

    def test_shallow_repository_is_detected_when_practical(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self._init_repo(Path(directory) / "source")
            self._commit_file(source, "a.txt", "first\n", "Add first file")
            self._commit_file(source, "b.txt", "second\n", "Add second file")
            shallow = Path(directory) / "shallow"
            self._git(
                None,
                "clone",
                "--depth",
                "1",
                source.as_uri(),
                str(shallow),
            )

            records = GitAdapter().read(shallow)

        self.assertTrue(records[0].is_shallow)
        observations = extract_observations(records)
        self.assertTrue(any(item.activity == "unknown" and "shallow" in item.statement for item in observations))

    @staticmethod
    def _init_repo(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        GitAdapterTests._git(path, "init")
        GitAdapterTests._git(path, "config", "user.name", "Workprint Tester")
        GitAdapterTests._git(path, "config", "user.email", "tester@example.com")
        return path.resolve()

    @staticmethod
    def _commit_file(repo: Path, relative_path: str, content: str, message: str) -> None:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        GitAdapterTests._git(repo, "add", relative_path)
        try:
            count = int(GitAdapterTests._git(repo, "rev-list", "--count", "HEAD").strip())
        except subprocess.CalledProcessError:
            count = 0
        index = count + 1
        GitAdapterTests._git(repo, "commit", "-m", message, env=GitAdapterTests._dates(index))

    @staticmethod
    def _dates(index: int) -> dict[str, str]:
        timestamp = f"2026-01-{index:02d}T12:00:00+00:00"
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

    @staticmethod
    def _commits(records):
        return [item for item in records if isinstance(item, NormalizedGitCommit)]


if __name__ == "__main__":
    unittest.main()

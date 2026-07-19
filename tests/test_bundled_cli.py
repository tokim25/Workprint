from __future__ import annotations

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from workprint.bundled_cli import COMMANDS, main


GIT = shutil.which("git")


class BundledCliTests(unittest.TestCase):
    def test_all_route_subcommands_are_registered(self):
        # Regression guard: lib/workprint-python-command.ts derives the
        # dev-mode module name from the subcommand string
        # ("git-summary" -> "workprint.git_summary"). If a subcommand here
        # doesn't follow that convention, dev mode and packaged mode
        # would silently invoke different code.
        self.assertEqual(
            set(COMMANDS),
            {"git-summary", "claude-local-summary", "web-investigate"},
        )

    def test_unknown_subcommand_prints_usage_and_fails(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(["not-a-real-command"])
        self.assertEqual(exit_code, 2)
        self.assertIn("Usage:", stderr.getvalue())

    def test_no_subcommand_prints_usage_and_fails(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main([])
        self.assertEqual(exit_code, 2)
        self.assertIn("Usage:", stderr.getvalue())

    @unittest.skipUnless(GIT, "git executable is required")
    def test_git_summary_subcommand_dispatches_to_real_module(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve()
            self._git(repo, "init")
            self._git(repo, "config", "user.name", "Workprint Tester")
            self._git(repo, "config", "user.email", "tester@example.com")
            (repo / "a.txt").write_text("first\n", encoding="utf-8")
            self._git(repo, "add", "a.txt")
            self._git(repo, "commit", "-m", "Add first")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["git-summary", "--repository", str(repo)])

        self.assertEqual(exit_code, 0)
        self.assertIn('"ok": true', stdout.getvalue())

    @staticmethod
    def _git(repo: Path, *args: str) -> None:
        import subprocess

        subprocess.run(
            [GIT, "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()

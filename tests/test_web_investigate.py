from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from workprint.web_investigate import (
    DESKTOP_CHAT_DEEP_PARSE_ENV,
    WebInvestigateError,
    _desktop_chat_deep_parse_enabled,
    build_web_investigation,
    main,
)


GIT = shutil.which("git")


class WebInvestigateTests(unittest.TestCase):
    def setUp(self):
        # Same isolation as test_discovery.py/test_guided.py/test_mcp_server.py:
        # Claude Desktop Chat evidence is account-wide and would otherwise be
        # picked up from whatever real cache exists on the machine running
        # these tests.
        patcher = patch.dict(
            os.environ,
            {
                "WORKPRINT_CLAUDE_HOME": "/nonexistent/workprint-test-path",
                "WORKPRINT_COWORK_HOME": "/nonexistent/workprint-test-path",
                "WORKPRINT_CLAUDE_DESKTOP_HOME": "/nonexistent/workprint-test-path",
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_rejects_missing_path(self):
        with self.assertRaises(WebInvestigateError) as context:
            build_web_investigation("")
        self.assertEqual(context.exception.code, "missing_path")

    def test_rejects_path_not_found(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "does-not-exist"
            with self.assertRaises(WebInvestigateError) as context:
                build_web_investigation(str(missing))
        self.assertEqual(context.exception.code, "path_not_found")

    def test_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "not-a-directory.txt"
            file_path.write_text("x", encoding="utf-8")
            with self.assertRaises(WebInvestigateError) as context:
                build_web_investigation(str(file_path))
        self.assertEqual(context.exception.code, "not_directory")

    def test_no_evidence_selected_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(WebInvestigateError) as context:
                build_web_investigation(directory)
        self.assertEqual(context.exception.code, "no_evidence_selected")

    @unittest.skipUnless(GIT, "git executable is required")
    def test_returns_full_markdown_and_json_for_real_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")
            self._commit_file(repo, "b.txt", "second\n", "Add second")

            result = build_web_investigation(
                str(repo), include="git", project_name="Test Project"
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["project"], "Test Project")
        self.assertEqual(result["sources"], ["git"])
        self.assertIn("# Executive Report: Test Project", result["markdown"])
        self.assertIn("findings", result["json"])
        self.assertIn("executive_report", result["json"])
        # Unlike mcp_server.py's bounded response (built for a
        # conversational tool result), this is a full report meant for
        # download, so nothing here should be truncated or capped.
        self.assertGreater(len(result["json"]["observations"]), 0)
        for finding in result["json"]["findings"]:
            self.assertNotIn("evidence_id_count", finding)
        self.assertIn("ai_fluency", result["json"])
        self.assertIn("AI Collaboration Playbook Worksheet", result["playbookMarkdown"])
        self.assertIn("_(fill in)_", result["playbookMarkdown"])

    @unittest.skipUnless(GIT, "git executable is required")
    def test_cli_writes_json_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")
            exit_code = main(["--project", str(repo), "--include", "git"])
        self.assertEqual(exit_code, 0)

    @unittest.skipUnless(GIT, "git executable is required")
    def test_cli_output_file_writes_payload_and_prints_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")
            output_file = Path(directory) / "report.json"

            captured = io.StringIO()
            with redirect_stdout(captured):
                exit_code = main(
                    [
                        "--project",
                        str(repo),
                        "--include",
                        "git",
                        "--output-file",
                        str(output_file),
                    ]
                )

            self.assertEqual(exit_code, 0)
            confirmation = json.loads(captured.getvalue())
            self.assertTrue(confirmation["ok"])
            self.assertEqual(confirmation["output_file"], str(output_file))
            self.assertTrue(output_file.exists())
            written_payload = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertIn("ai_fluency", written_payload["json"])

    def test_cli_returns_error_exit_code_for_bad_path(self):
        exit_code = main(["--project", "/definitely/not/a/real/path"])
        self.assertEqual(exit_code, 1)

    def test_desktop_chat_deep_parse_env_toggle_restores_previous_value(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(DESKTOP_CHAT_DEEP_PARSE_ENV, None)
            with _desktop_chat_deep_parse_enabled(True):
                self.assertEqual(os.environ.get(DESKTOP_CHAT_DEEP_PARSE_ENV), "1")
            self.assertNotIn(DESKTOP_CHAT_DEEP_PARSE_ENV, os.environ)

    @staticmethod
    def _init_repo(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        WebInvestigateTests._git(path, "init")
        WebInvestigateTests._git(path, "config", "user.name", "Workprint Tester")
        WebInvestigateTests._git(path, "config", "user.email", "tester@example.com")
        return path.resolve()

    @staticmethod
    def _commit_file(repo: Path, relative_path: str, content: str, message: str) -> None:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        WebInvestigateTests._git(repo, "add", relative_path)
        WebInvestigateTests._git(
            repo,
            "commit",
            "-m",
            message,
            env={
                "GIT_AUTHOR_DATE": "2026-02-01T12:00:00+00:00",
                "GIT_COMMITTER_DATE": "2026-02-01T12:00:00+00:00",
            },
        )

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

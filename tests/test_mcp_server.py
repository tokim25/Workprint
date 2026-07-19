from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import mcp  # noqa: F401

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

GIT = shutil.which("git")

if HAS_MCP:
    from workprint.mcp_server import (
        DEFAULT_EVIDENCE_ID_PREVIEW,
        DESKTOP_CHAT_DEEP_PARSE_ENV,
        _desktop_chat_deep_parse_enabled,
        create_server,
        discover_project,
        investigate_project,
        list_supported_sources,
    )


@unittest.skipUnless(
    HAS_MCP, "requires the optional mcp extra (pip install 'workprint[mcp]')"
)
class McpServerTests(unittest.TestCase):
    def setUp(self):
        # Claude Code/Cowork/Desktop Chat are not injectable here the way
        # claude_local_summary.py's build function allows; isolate from
        # real machine state the same way test_discovery.py and
        # test_guided.py do.
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

    def test_create_server_exposes_read_only_tools(self):
        server = create_server()
        tools = {tool.name: tool for tool in server._tool_manager.list_tools()}

        self.assertEqual(
            set(tools.keys()),
            {"list_supported_sources", "discover_project", "investigate_project"},
        )
        for tool in tools.values():
            self.assertTrue(tool.annotations.readOnlyHint)
            self.assertFalse(tool.annotations.destructiveHint)
            self.assertFalse(tool.annotations.openWorldHint)

    def test_list_supported_sources(self):
        result = list_supported_sources()
        self.assertTrue(result["ok"])
        self.assertIn("claude-code", result["sources"])
        self.assertIn("git", result["sources"])

    def test_discover_project_rejects_missing_path(self):
        result = discover_project("")
        self.assertFalse(result["ok"])
        self.assertIn("code", result["error"])

    def test_discover_project_rejects_path_not_found(self):
        with tempfile.TemporaryDirectory() as directory:
            result = discover_project(str(Path(directory) / "does-not-exist"))
        self.assertFalse(result["ok"])

    @unittest.skipUnless(GIT, "git executable is required")
    def test_discover_project_finds_real_git_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")

            result = discover_project(str(repo))

        self.assertTrue(result["ok"])
        self.assertTrue(result["git_repository"])
        sources = {item["source"] for item in result["results"]}
        self.assertIn("git", sources)

    @unittest.skipUnless(GIT, "git executable is required")
    def test_investigate_project_returns_bounded_response_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")
            self._commit_file(repo, "b.txt", "second\n", "Add second")

            result = investigate_project(str(repo), include="git")

        self.assertTrue(result["ok"])
        investigation = result["investigation"]
        self.assertNotIn("observations", investigation)
        self.assertNotIn("timeline", investigation)
        self.assertIn("observation_count", investigation)
        self.assertIn("executive_brief", investigation)
        self.assertIn("ai_fluency", investigation)
        self.assertEqual(len(investigation["ai_fluency"]["competencies"]), 4)
        for finding in investigation["findings"]:
            self.assertLessEqual(
                len(finding["evidence_ids"]), DEFAULT_EVIDENCE_ID_PREVIEW
            )
            self.assertIn("evidence_id_count", finding)
            self.assertGreaterEqual(
                finding["evidence_id_count"], len(finding["evidence_ids"])
            )

    @unittest.skipUnless(GIT, "git executable is required")
    def test_investigate_project_full_report_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")

            bounded = investigate_project(str(repo), include="git")
            full = investigate_project(
                str(repo),
                include="git",
                include_full_report=True,
                include_observations=True,
                include_timeline=True,
            )

        self.assertIn("observations", full["investigation"])
        self.assertIn("timeline", full["investigation"])
        self.assertIn("executive_report", full["investigation"])
        bounded_ids = bounded["investigation"]["findings"][0]["evidence_ids"]
        full_ids = full["investigation"]["findings"][0]["evidence_ids"]
        self.assertGreaterEqual(len(full_ids), len(bounded_ids))

    @unittest.skipUnless(GIT, "git executable is required")
    def test_investigate_project_respects_include_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._init_repo(Path(directory))
            self._commit_file(repo, "a.txt", "first\n", "Add first")
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                str(repo),
                "chatgpt.json",
            )

            git_only = investigate_project(str(repo), include="git")
            everything = investigate_project(str(repo), include="all")

        self.assertTrue(git_only["ok"])
        self.assertTrue(everything["ok"])
        self.assertLessEqual(
            git_only["investigation"]["observation_count"],
            everything["investigation"]["observation_count"],
        )

    def test_investigate_project_no_evidence_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = investigate_project(directory)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "no_evidence_selected")

    def test_desktop_chat_deep_parse_env_toggle_restores_previous_value(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(DESKTOP_CHAT_DEEP_PARSE_ENV, None)
            with _desktop_chat_deep_parse_enabled(True):
                self.assertEqual(os.environ.get(DESKTOP_CHAT_DEEP_PARSE_ENV), "1")
            self.assertNotIn(DESKTOP_CHAT_DEEP_PARSE_ENV, os.environ)

    def test_desktop_chat_deep_parse_disabled_is_a_no_op(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(DESKTOP_CHAT_DEEP_PARSE_ENV, None)
            with _desktop_chat_deep_parse_enabled(False):
                self.assertNotIn(DESKTOP_CHAT_DEEP_PARSE_ENV, os.environ)
            self.assertNotIn(DESKTOP_CHAT_DEEP_PARSE_ENV, os.environ)

    @staticmethod
    def _copy_fixture(source: str, directory: str, name: str) -> None:
        shutil.copy(Path(source), Path(directory) / name)

    @staticmethod
    def _init_repo(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        McpServerTests._git(path, "init")
        McpServerTests._git(path, "config", "user.name", "Workprint Tester")
        McpServerTests._git(path, "config", "user.email", "tester@example.com")
        return path.resolve()

    @staticmethod
    def _commit_file(repo: Path, relative_path: str, content: str, message: str) -> None:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        McpServerTests._git(repo, "add", relative_path)
        McpServerTests._git(
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

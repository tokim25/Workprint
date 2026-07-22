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

from workprint.cli import main
from workprint.discovery import discover_project, render_discovery


GIT = shutil.which("git")


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        # Claude Desktop Chat evidence is account-wide, not project-scoped
        # (see docs/claude-desktop-chat-adapter.md), so its default lookup
        # would otherwise pick up whatever real cache exists on the machine
        # running these tests. Point it at a path that cannot exist so
        # other tests stay hermetic; tests that specifically exercise this
        # adapter override the variable themselves.
        patcher = patch.dict(
            os.environ,
            {"WORKPRINT_CLAUDE_DESKTOP_HOME": "/nonexistent/workprint-test-path"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_empty_directory_reports_no_supported_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            discovery = discover_project(directory)
            rendered = render_discovery(discovery)

        self.assertFalse(discovery.ready)
        self.assertIn("No supported evidence found.", rendered)
        self.assertIn("- Chat Summary", rendered)
        self.assertIn("- ChatGPT", rendered)
        self.assertIn("- Figma", rendered)

    def test_detects_git_repository(self):
        if not GIT:
            self.skipTest("git executable is required")
        with tempfile.TemporaryDirectory() as directory:
            self._init_git(Path(directory))
            discovery = discover_project(directory)

        self.assertTrue(discovery.git_repository)
        self.assertEqual(discovery.evidence_sources, 1)
        result = self._result(discovery, "git")
        self.assertEqual(result.label, "Git")
        self.assertEqual(result.detected_files, (".",))

    def test_detects_chatgpt_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            discovery = discover_project(directory)

        result = self._result(discovery, "chatgpt")
        self.assertEqual(result.file_count, 1)
        self.assertEqual(result.metadata["record_count"], 1)

    def test_detects_chat_summary_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chat-summary/sample-summary.json",
                directory,
                "sample-summary.json",
            )
            discovery = discover_project(directory)
            rendered = render_discovery(discovery)

        result = self._result(discovery, "chat-summary")
        self.assertEqual(result.label, "Chat Summary")
        self.assertEqual(result.file_count, 1)
        self.assertEqual(result.detected_files, ("sample-summary.json",))
        self.assertIn("5 user-approved summary items", rendered)

    def test_detects_claude_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/claude/sample-conversations.json",
                directory,
                "claude.json",
            )
            discovery = discover_project(directory)

        result = self._result(discovery, "claude")
        self.assertEqual(result.file_count, 1)
        self.assertEqual(result.metadata["record_count"], 1)

    def test_detects_claude_code_session(self):
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as claude_home:
            project_root = str(Path(directory).resolve())
            self._write_claude_code_session(Path(claude_home), project_root)
            with patch.dict(os.environ, {"WORKPRINT_CLAUDE_HOME": claude_home}):
                discovery = discover_project(directory)

        result = self._result(discovery, "claude-code")
        self.assertEqual(result.label, "Claude Code")
        self.assertEqual(result.detected_files, (".",))
        self.assertEqual(result.metadata["record_count"], 1)

    def test_detects_claude_cowork_session(self):
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as cowork_home:
            project_root = str(Path(directory).resolve())
            self._write_claude_cowork_session(Path(cowork_home), project_root)
            with patch.dict(os.environ, {"WORKPRINT_COWORK_HOME": cowork_home}):
                discovery = discover_project(directory)

        result = self._result(discovery, "claude-cowork")
        self.assertEqual(result.label, "Claude Cowork")
        self.assertEqual(result.detected_files, (".",))
        self.assertEqual(result.metadata["record_count"], 1)

    def test_detects_claude_desktop_chat_presence(self):
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as indexeddb_home:
            with patch.dict(
                os.environ, {"WORKPRINT_CLAUDE_DESKTOP_HOME": indexeddb_home}
            ):
                discovery = discover_project(directory)
                rendered = render_discovery(discovery)

        result = self._result(discovery, "claude-desktop-chat")
        self.assertEqual(result.label, "Claude Desktop Chat")
        self.assertFalse(result.metadata["deep_parse"])
        self.assertIn("cache detected (deep parsing not enabled)", rendered)
        self.assertIn("account-wide, not specific to this project", rendered)
        self.assertIn("stays entirely on your machine", rendered)

    def test_detects_google_docs_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/google-docs/sample-document.json",
                directory,
                "sample-document.json",
            )
            discovery = discover_project(directory)

        result = self._result(discovery, "google-docs")
        self.assertEqual(result.file_count, 1)
        self.assertEqual(result.detected_files, ("sample-document.json",))

    def test_detects_figma_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/figma/sample-file.json",
                directory,
                "sample-file.json",
            )
            discovery = discover_project(directory)

        result = self._result(discovery, "figma")
        self.assertEqual(result.file_count, 1)
        self.assertEqual(result.detected_files, ("sample-file.json",))

    def test_mixed_project_detection_ignores_unsupported_files(self):
        if not GIT:
            self.skipTest("git executable is required")
        with tempfile.TemporaryDirectory() as directory:
            self._init_git(Path(directory))
            Path(directory, "notes.csv").write_text("unsupported", encoding="utf-8")
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            self._copy_fixture(
                "fixtures/chat-summary/sample-summary.json",
                directory,
                "chat-summary.json",
            )
            self._copy_fixture(
                "fixtures/google-docs/sample-document.md",
                directory,
                "doc.md",
            )
            self._prepend_google_docs_marker(Path(directory) / "doc.md")
            self._copy_fixture(
                "fixtures/figma/sample-file.json",
                directory,
                "design.json",
            )
            discovery = discover_project(directory)

        self.assertTrue(discovery.git_repository)
        self.assertEqual(
            [item.source for item in discovery.results],
            ["chat-summary", "chatgpt", "figma", "git", "google-docs"],
        )
        self.assertEqual(discovery.supported_files, 5)
        self.assertEqual(discovery.evidence_sources, 5)

    def test_malformed_candidate_does_not_abort_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "broken.json").write_text("{not json", encoding="utf-8")
            self._copy_fixture(
                "fixtures/figma/sample-file.json",
                directory,
                "sample-file.json",
            )
            discovery = discover_project(directory)

        result = self._result(discovery, "figma")
        self.assertEqual(result.file_count, 1)
        self.assertEqual(result.detected_files, ("sample-file.json",))

    def test_repository_markdown_is_project_notes_evidence_not_google_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "README.md").write_text(
                "# Project\n\nOrdinary repository documentation.",
                encoding="utf-8",
            )
            Path(directory, "docs").mkdir()
            Path(directory, "docs", "architecture.md").write_text(
                "# Architecture\n\nRegular project documentation.",
                encoding="utf-8",
            )

            discovery = discover_project(directory)

        self.assertTrue(discovery.ready)
        result = self._result(discovery, "project-notes")
        self.assertEqual(result.label, "Project Notes")
        self.assertEqual(result.detected_files, ("docs/architecture.md",))
        with self.assertRaises(AssertionError):
            self._result(discovery, "google-docs")

    def test_discovery_skips_generated_directories_for_project_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "notes.md").write_text(
                "# Real Notes\n\nThe project goal is to keep real docs visible.",
                encoding="utf-8",
            )
            Path(directory, "node_modules", "package").mkdir(parents=True)
            Path(directory, "node_modules", "package", "guide.md").write_text(
                "# Vendored Guide\n\nThis should not become project evidence.",
                encoding="utf-8",
            )

            discovery = discover_project(directory)

        result = self._result(discovery, "project-notes")
        self.assertEqual(result.detected_files, ("notes.md",))

    def test_cli_discover_command(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/figma/sample-file.json",
                directory,
                "sample-file.json",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                result = main(["discover", directory])

        self.assertEqual(result, 0)
        rendered = output.getvalue()
        self.assertIn("Project Discovery", rendered)
        self.assertIn("Figma", rendered)
        self.assertIn("1 file", rendered)
        self.assertIn("Ready for investigation.", rendered)

    def test_discovery_order_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/google-docs/sample-document.txt",
                directory,
                "z-doc.txt",
            )
            self._prepend_google_docs_marker(Path(directory) / "z-doc.txt")
            self._copy_fixture(
                "fixtures/google-docs/sample-document.md",
                directory,
                "a-doc.md",
            )
            self._prepend_google_docs_marker(Path(directory) / "a-doc.md")
            first = discover_project(directory)
            second = discover_project(directory)

        self.assertEqual(first.to_dict(), second.to_dict())
        result = self._result(first, "google-docs")
        self.assertEqual(result.detected_files, ("a-doc.md", "z-doc.txt"))

    @staticmethod
    def _copy_fixture(source: str, directory: str, name: str) -> None:
        shutil.copy(Path(source), Path(directory) / name)

    @staticmethod
    def _prepend_google_docs_marker(path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "workprint-source: google-docs\n\n" + text,
            encoding="utf-8",
        )

    @staticmethod
    def _init_git(path: Path) -> None:
        subprocess.run([GIT, "-C", str(path), "init"], check=True, capture_output=True)

    @staticmethod
    def _write_claude_code_session(claude_home: Path, project_root: str) -> None:
        session_dir = claude_home / "-tmp-project"
        session_dir.mkdir(parents=True)
        record = {
            "type": "user",
            "uuid": "u1",
            "sessionId": "session-1",
            "timestamp": "2026-01-01T00:00:00.000Z",
            "cwd": project_root,
            "isSidechain": False,
            "message": {"role": "user", "content": "hello"},
        }
        (session_dir / "session-1.jsonl").write_text(
            json.dumps(record) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _write_claude_cowork_session(cowork_home: Path, project_root: str) -> None:
        metadata_path = cowork_home / "local_abc123.json"
        metadata_path.write_text(
            json.dumps(
                {
                    "sessionId": "cowork-session-1",
                    "userSelectedFolders": [project_root],
                    "model": "claude-sonnet-5",
                    "sessionType": "scheduled",
                    "isArchived": False,
                }
            ),
            encoding="utf-8",
        )
        transcript_dir = (
            cowork_home / "local_abc123" / ".claude" / "projects" / "-sandbox-slug"
        )
        transcript_dir.mkdir(parents=True)
        record = {
            "type": "user",
            "uuid": "u1",
            "timestamp": "2026-01-01T00:00:00.000Z",
            "cwd": "/internal/sandbox/outputs",
            "isSidechain": False,
            "message": {"role": "user", "content": "hello"},
        }
        (transcript_dir / "cowork-session-1.jsonl").write_text(
            json.dumps(record) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _result(discovery, source: str):
        for item in discovery.results:
            if item.source == source:
                return item
        raise AssertionError(f"missing discovery result for {source}")


if __name__ == "__main__":
    unittest.main()

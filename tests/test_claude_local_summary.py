from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workprint.adapters import ClaudeCodeAdapter, ClaudeCoworkAdapter, ClaudeDesktopChatAdapter
from workprint.claude_local_summary import (
    ClaudeLocalSummaryError,
    build_claude_local_summary,
    main,
)


def _write_claude_code_session(claude_home: Path, project_root: str) -> None:
    session_dir = claude_home / "-tmp-project"
    session_dir.mkdir(parents=True)
    records = [
        {
            "type": "user",
            "uuid": "u1",
            "sessionId": "session-1",
            "timestamp": "2026-01-01T00:00:00.000Z",
            "cwd": project_root,
            "isSidechain": False,
            "message": {"role": "user", "content": "Please fix the bug"},
        },
        {
            "type": "assistant",
            "uuid": "a1",
            "sessionId": "session-1",
            "timestamp": "2026-01-01T00:01:00.000Z",
            "cwd": project_root,
            "isSidechain": False,
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Fixed."},
                    {"type": "tool_use", "name": "Edit", "input": {}},
                    {"type": "tool_use", "name": "Edit", "input": {}},
                ],
            },
        },
    ]
    with (session_dir / "session-1.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


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


class ClaudeLocalSummaryTests(unittest.TestCase):
    def test_empty_project_returns_zero_counts_not_an_error(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as desktop_home, \
                tempfile.TemporaryDirectory() as project_dir:
            summary = build_claude_local_summary(
                project_dir,
                claude_code_adapter=ClaudeCodeAdapter(claude_home=claude_home),
                claude_cowork_adapter=ClaudeCoworkAdapter(cowork_home=cowork_home),
                claude_desktop_chat_adapter=ClaudeDesktopChatAdapter(
                    indexeddb_home=Path(desktop_home) / "does-not-exist"
                ),
            )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["claude_code"]["session_count"], 0)
        self.assertEqual(summary["claude_cowork"]["session_count"], 0)
        self.assertFalse(summary["claude_desktop_chat"]["cache_detected"])

    def test_aggregates_real_claude_code_fixture(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as desktop_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_claude_code_session(Path(claude_home), project_root)

            summary = build_claude_local_summary(
                project_dir,
                claude_code_adapter=ClaudeCodeAdapter(claude_home=claude_home),
                claude_cowork_adapter=ClaudeCoworkAdapter(cowork_home=cowork_home),
                claude_desktop_chat_adapter=ClaudeDesktopChatAdapter(
                    indexeddb_home=Path(desktop_home) / "does-not-exist"
                ),
            )

        code = summary["claude_code"]
        self.assertEqual(code["session_count"], 1)
        self.assertEqual(code["turn_count"], 2)
        self.assertEqual(code["human_turn_count"], 1)
        self.assertEqual(code["assistant_turn_count"], 1)
        self.assertEqual(code["tool_use_counts"], {"Edit": 2})
        self.assertIsNotNone(code["earliest_turn_date"])
        self.assertIsNotNone(code["latest_turn_date"])

    def test_aggregates_real_claude_cowork_fixture(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as desktop_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_claude_cowork_session(Path(cowork_home), project_root)

            summary = build_claude_local_summary(
                project_dir,
                claude_code_adapter=ClaudeCodeAdapter(claude_home=claude_home),
                claude_cowork_adapter=ClaudeCoworkAdapter(cowork_home=cowork_home),
                claude_desktop_chat_adapter=ClaudeDesktopChatAdapter(
                    indexeddb_home=Path(desktop_home) / "does-not-exist"
                ),
            )

        cowork = summary["claude_cowork"]
        self.assertEqual(cowork["session_count"], 1)
        self.assertEqual(cowork["turn_count"], 1)
        self.assertEqual(cowork["human_turn_count"], 1)

    def test_desktop_chat_presence_only_by_default(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as desktop_home, \
                tempfile.TemporaryDirectory() as project_dir:
            summary = build_claude_local_summary(
                project_dir,
                include_desktop_chat_deep_parse=True,
                claude_code_adapter=ClaudeCodeAdapter(claude_home=claude_home),
                claude_cowork_adapter=ClaudeCoworkAdapter(cowork_home=cowork_home),
                claude_desktop_chat_adapter=ClaudeDesktopChatAdapter(
                    indexeddb_home=desktop_home
                ),
            )

        chat = summary["claude_desktop_chat"]
        self.assertTrue(chat["cache_detected"])
        self.assertIsNotNone(chat["last_modified"])
        self.assertFalse(chat["deep_parse_found_turns"])
        self.assertNotIn("turns", chat)

    def test_desktop_chat_deep_parse_reported_unavailable_without_dependency(self):
        # The optional dependency is not installed in the standard test
        # environment; this confirms deep_parse_available correctly reads
        # false and deep_parse_requested is therefore false even when the
        # caller asked for it, rather than silently attempting and failing.
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as desktop_home, \
                tempfile.TemporaryDirectory() as project_dir:
            summary = build_claude_local_summary(
                project_dir,
                include_desktop_chat_deep_parse=True,
                claude_code_adapter=ClaudeCodeAdapter(claude_home=claude_home),
                claude_cowork_adapter=ClaudeCoworkAdapter(cowork_home=cowork_home),
            )

        chat = summary["claude_desktop_chat"]
        self.assertFalse(chat["deep_parse_available"])
        self.assertFalse(chat["deep_parse_requested"])

    def test_rejects_missing_path(self):
        with self.assertRaises(ClaudeLocalSummaryError) as context:
            build_claude_local_summary("")
        self.assertEqual(context.exception.code, "missing_path")

    def test_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "not-a-directory.txt"
            file_path.write_text("x", encoding="utf-8")
            with self.assertRaises(ClaudeLocalSummaryError) as context:
                build_claude_local_summary(str(file_path))
        self.assertEqual(context.exception.code, "not_directory")

    def test_rejects_path_not_found(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "does-not-exist"
            with self.assertRaises(ClaudeLocalSummaryError) as context:
                build_claude_local_summary(str(missing))
        self.assertEqual(context.exception.code, "path_not_found")

    def test_cli_returns_json_for_empty_project(self):
        # Isolated from real machine state the same way test_discovery.py
        # and test_guided.py are, since main() constructs default adapters
        # rather than accepting injected ones.
        env = {
            "WORKPRINT_CLAUDE_HOME": "/nonexistent/workprint-test-path",
            "WORKPRINT_COWORK_HOME": "/nonexistent/workprint-test-path",
            "WORKPRINT_CLAUDE_DESKTOP_HOME": "/nonexistent/workprint-test-path",
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, env):
            exit_code = main(["--project", directory])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

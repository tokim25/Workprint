import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workprint.adapters import ClaudeCodeAdapter, get_adapter
from workprint.adapters import claude_code as claude_code_module
from workprint.extractor import extract_observations


def _write_session(
    directory: Path,
    project_slug: str,
    session_id: str,
    records: list[dict],
) -> Path:
    session_dir = directory / project_slug
    session_dir.mkdir(parents=True, exist_ok=True)
    session_path = session_dir / f"{session_id}.jsonl"
    with session_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    return session_path


def _user_turn(session_id: str, cwd: str, uuid: str, timestamp: str, text: str) -> dict:
    return {
        "type": "user",
        "uuid": uuid,
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
        "isSidechain": False,
        "message": {"role": "user", "content": text},
    }


def _assistant_turn(
    session_id: str,
    cwd: str,
    uuid: str,
    timestamp: str,
    text: str,
    tools: list[str],
    is_sidechain: bool = False,
) -> dict:
    content = [{"type": "thinking", "text": "considering the request"}]
    if text:
        content.append({"type": "text", "text": text})
    for tool in tools:
        content.append({"type": "tool_use", "name": tool, "input": {}})
    return {
        "type": "assistant",
        "uuid": uuid,
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
        "isSidechain": is_sidechain,
        "message": {"role": "assistant", "content": content},
    }


class ClaudeCodeAdapterTests(unittest.TestCase):
    def test_registry_returns_claude_code_adapter(self):
        adapter = get_adapter("claude-code")
        self.assertIsInstance(adapter, ClaudeCodeAdapter)
        self.assertEqual(adapter.adapter_id, "claude-code")
        self.assertEqual(adapter.source_type, "conversation")
        self.assertEqual(adapter.display_name, "Claude Code")

    def test_reads_matching_session_with_structural_content_by_default(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_session(
                Path(claude_home),
                "-tmp-project",
                "session-1",
                [
                    {"type": "queue-operation", "sessionId": "session-1", "timestamp": "t"},
                    _user_turn(
                        "session-1", project_root, "u1", "2026-01-01T00:00:00.000Z",
                        "Please fix the login bug",
                    ),
                    _assistant_turn(
                        "session-1", project_root, "a1", "2026-01-01T00:01:00.000Z",
                        "Fixed it.", ["Edit", "Bash", "Edit"],
                    ),
                    {"type": "attachment", "sessionId": "session-1", "cwd": project_root, "timestamp": "t"},
                ],
            )
            adapter = ClaudeCodeAdapter(claude_home=claude_home)
            messages = adapter.read(project_root)

        self.assertEqual(len(messages), 2)
        human, assistant = messages
        self.assertEqual(human.role, "human")
        self.assertEqual(human.source, "Claude Code")
        self.assertNotIn("fix the login bug", human.content)
        self.assertEqual(human.metadata["content_length"], len("Please fix the login bug"))

        self.assertEqual(assistant.role, "assistant")
        self.assertNotIn("Fixed it.", assistant.content)
        self.assertIn("Edit (2)", assistant.content)
        self.assertIn("Bash (1)", assistant.content)
        self.assertEqual(assistant.metadata["tool_use_counts"], {"Edit": 2, "Bash": 1})
        self.assertEqual(assistant.metadata["text_block_count"], 1)
        self.assertFalse(assistant.metadata["is_sidechain"])

    def test_non_matching_cwd_is_not_included(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir, \
                tempfile.TemporaryDirectory() as other_dir:
            _write_session(
                Path(claude_home),
                "-other-project",
                "session-1",
                [
                    _user_turn(
                        "session-1", str(Path(other_dir).resolve()), "u1",
                        "2026-01-01T00:00:00.000Z", "unrelated project message",
                    ),
                ],
            )
            adapter = ClaudeCodeAdapter(claude_home=claude_home)
            messages = adapter.read(project_dir)

        self.assertEqual(messages, [])
        self.assertIsNone(adapter.discover(project_dir))

    def test_missing_claude_home_returns_no_evidence(self):
        with tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeCodeAdapter(
                claude_home=Path(project_dir) / "does-not-exist"
            )
            self.assertEqual(adapter.read(project_dir), [])
            self.assertIsNone(adapter.discover(project_dir))

    def test_include_content_excerpts_opt_in(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_session(
                Path(claude_home),
                "-tmp-project",
                "session-1",
                [
                    _user_turn(
                        "session-1", project_root, "u1", "2026-01-01T00:00:00.000Z",
                        "Please fix the login bug",
                    ),
                ],
            )
            default_adapter = ClaudeCodeAdapter(claude_home=claude_home)
            opted_in_adapter = ClaudeCodeAdapter(
                claude_home=claude_home, include_content_excerpts=True
            )
            default_messages = default_adapter.read(project_root)
            opted_in_messages = opted_in_adapter.read(project_root)

        self.assertNotIn("login bug", default_messages[0].content)
        self.assertIn("login bug", opted_in_messages[0].content)

    def test_sidechain_turns_are_flagged_not_dropped(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_session(
                Path(claude_home),
                "-tmp-project",
                "session-1",
                [
                    _assistant_turn(
                        "session-1", project_root, "a1", "2026-01-01T00:00:00.000Z",
                        "delegating to subagent", ["Task"], is_sidechain=True,
                    ),
                ],
            )
            adapter = ClaudeCodeAdapter(claude_home=claude_home)
            messages = adapter.read(project_root)

        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].metadata["is_sidechain"])

    def test_session_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            for index in range(3):
                _write_session(
                    Path(claude_home),
                    "-tmp-project",
                    f"session-{index}",
                    [
                        _user_turn(
                            f"session-{index}", project_root, f"u{index}",
                            "2026-01-01T00:00:00.000Z", "hello",
                        ),
                    ],
                )
            adapter = ClaudeCodeAdapter(claude_home=claude_home)
            with patch.object(claude_code_module, "MAX_SESSIONS", 2):
                messages = adapter.read(project_root)

        self.assertEqual(len({item.conversation_id for item in messages}), 2)

    def test_malformed_lines_do_not_abort_reading(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            session_dir = Path(claude_home) / "-tmp-project"
            session_dir.mkdir(parents=True)
            session_path = session_dir / "session-1.jsonl"
            with session_path.open("w", encoding="utf-8") as handle:
                handle.write("{not json\n")
                handle.write(
                    json.dumps(
                        _user_turn(
                            "session-1", project_root, "u1",
                            "2026-01-01T00:00:00.000Z", "hello",
                        )
                    )
                    + "\n"
                )
            adapter = ClaudeCodeAdapter(claude_home=claude_home)
            messages = adapter.read(project_root)

        self.assertEqual(len(messages), 1)

    def test_registry_adapter_honors_claude_home_env_var(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_session(
                Path(claude_home),
                "-tmp-project",
                "session-1",
                [
                    _user_turn(
                        "session-1", project_root, "u1", "2026-01-01T00:00:00.000Z",
                        "hello",
                    ),
                ],
            )
            with patch.dict(os.environ, {"WORKPRINT_CLAUDE_HOME": claude_home}):
                adapter = get_adapter("claude-code")
                messages = adapter.read(project_root)

        self.assertEqual(len(messages), 1)

    def test_extracts_generic_observation_for_structural_content(self):
        with tempfile.TemporaryDirectory() as claude_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_session(
                Path(claude_home),
                "-tmp-project",
                "session-1",
                [
                    _assistant_turn(
                        "session-1", project_root, "a1", "2026-01-01T00:00:00.000Z",
                        "Done.", ["Edit"],
                    ),
                ],
            )
            adapter = ClaudeCodeAdapter(claude_home=claude_home)
            observations = extract_observations(adapter.read(project_root))

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].actor, "Claude Code")


if __name__ == "__main__":
    unittest.main()

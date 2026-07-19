import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workprint.adapters import ClaudeCoworkAdapter, get_adapter
from workprint.adapters import claude_cowork as claude_cowork_module
from workprint.extractor import extract_observations


def _write_cowork_session(
    cowork_home: Path,
    session_uuid: str,
    user_selected_folders: list[str],
    transcript_records: list[dict],
    *,
    session_id: str = "cowork-session-1",
    model: str = "claude-sonnet-5",
    session_type: str = "scheduled",
    is_archived: bool = False,
) -> None:
    metadata_path = cowork_home / f"local_{session_uuid}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "sessionId": session_id,
                "userSelectedFolders": user_selected_folders,
                "model": model,
                "sessionType": session_type,
                "isArchived": is_archived,
                "title": "should never be read by default",
                "initialMessage": "should never be read by default",
            }
        ),
        encoding="utf-8",
    )
    transcript_dir = (
        cowork_home / f"local_{session_uuid}" / ".claude" / "projects" / "-sandbox-slug"
    )
    transcript_dir.mkdir(parents=True)
    transcript_path = transcript_dir / f"{session_id}.jsonl"
    with transcript_path.open("w", encoding="utf-8") as handle:
        for record in transcript_records:
            handle.write(json.dumps(record) + "\n")


def _user_turn(cwd: str, uuid: str, timestamp: str, text: str) -> dict:
    return {
        "type": "user",
        "uuid": uuid,
        "timestamp": timestamp,
        "cwd": cwd,
        "isSidechain": False,
        "message": {"role": "user", "content": text},
    }


def _assistant_turn(
    cwd: str, uuid: str, timestamp: str, text: str, tools: list[str]
) -> dict:
    content = [{"type": "text", "text": text}] if text else []
    for tool in tools:
        content.append({"type": "tool_use", "name": tool, "input": {}})
    return {
        "type": "assistant",
        "uuid": uuid,
        "timestamp": timestamp,
        "cwd": cwd,
        "isSidechain": False,
        "message": {"role": "assistant", "content": content},
    }


class ClaudeCoworkAdapterTests(unittest.TestCase):
    def test_registry_returns_claude_cowork_adapter(self):
        adapter = get_adapter("claude-cowork")
        self.assertIsInstance(adapter, ClaudeCoworkAdapter)
        self.assertEqual(adapter.adapter_id, "claude-cowork")
        self.assertEqual(adapter.source_type, "conversation")
        self.assertEqual(adapter.display_name, "Claude Cowork")

    def test_matches_via_user_selected_folders_not_transcript_cwd(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            sandbox_cwd = "/internal/sandbox/outputs"
            _write_cowork_session(
                Path(cowork_home),
                "abc123",
                [project_root],
                [
                    _user_turn(sandbox_cwd, "u1", "2026-01-01T00:00:00.000Z", "Do the task"),
                    _assistant_turn(
                        sandbox_cwd, "a1", "2026-01-01T00:01:00.000Z",
                        "Done.", ["Edit", "Bash"],
                    ),
                ],
            )
            adapter = ClaudeCoworkAdapter(cowork_home=cowork_home)
            messages = adapter.read(project_root)

        self.assertEqual(len(messages), 2)
        human, assistant = messages
        self.assertEqual(human.source, "Claude Cowork")
        self.assertNotIn("Do the task", human.content)
        self.assertNotIn("Done.", assistant.content)
        self.assertIn("Edit (1)", assistant.content)
        self.assertEqual(assistant.metadata["model"], "claude-sonnet-5")
        self.assertEqual(assistant.metadata["session_type"], "scheduled")
        self.assertFalse(assistant.metadata["is_archived"])

    def test_non_matching_folder_is_not_included(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir, \
                tempfile.TemporaryDirectory() as other_dir:
            _write_cowork_session(
                Path(cowork_home),
                "abc123",
                [str(Path(other_dir).resolve())],
                [_user_turn("/sandbox", "u1", "2026-01-01T00:00:00.000Z", "hello")],
            )
            adapter = ClaudeCoworkAdapter(cowork_home=cowork_home)

            self.assertEqual(adapter.read(project_dir), [])
            self.assertIsNone(adapter.discover(project_dir))

    def test_title_and_initial_message_are_never_read(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_cowork_session(
                Path(cowork_home),
                "abc123",
                [project_root],
                [_user_turn("/sandbox", "u1", "2026-01-01T00:00:00.000Z", "hello")],
            )
            adapter = ClaudeCoworkAdapter(cowork_home=cowork_home)
            messages = adapter.read(project_root)

        self.assertEqual(len(messages), 1)
        rendered = json.dumps(messages[0].content) + json.dumps(messages[0].metadata)
        self.assertNotIn("should never be read by default", rendered)

    def test_include_content_excerpts_opt_in(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_cowork_session(
                Path(cowork_home),
                "abc123",
                [project_root],
                [_user_turn("/sandbox", "u1", "2026-01-01T00:00:00.000Z", "secret plan")],
            )
            default_messages = ClaudeCoworkAdapter(cowork_home=cowork_home).read(project_root)
            opted_in_messages = ClaudeCoworkAdapter(
                cowork_home=cowork_home, include_content_excerpts=True
            ).read(project_root)

        self.assertNotIn("secret plan", default_messages[0].content)
        self.assertIn("secret plan", opted_in_messages[0].content)

    def test_missing_cowork_home_returns_no_evidence(self):
        with tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeCoworkAdapter(
                cowork_home=Path(project_dir) / "does-not-exist"
            )
            self.assertEqual(adapter.read(project_dir), [])
            self.assertIsNone(adapter.discover(project_dir))

    def test_session_metadata_without_transcript_directory_is_skipped(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            metadata_path = Path(cowork_home) / "local_no-transcript.json"
            metadata_path.write_text(
                json.dumps({"userSelectedFolders": [project_root]}),
                encoding="utf-8",
            )
            adapter = ClaudeCoworkAdapter(cowork_home=cowork_home)

            self.assertEqual(adapter.read(project_root), [])

    def test_session_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            for index in range(3):
                _write_cowork_session(
                    Path(cowork_home),
                    f"session{index}",
                    [project_root],
                    [_user_turn("/sandbox", f"u{index}", "2026-01-01T00:00:00.000Z", "hi")],
                    session_id=f"cowork-session-{index}",
                )
            adapter = ClaudeCoworkAdapter(cowork_home=cowork_home)
            with patch.object(claude_cowork_module, "MAX_SESSIONS", 2):
                messages = adapter.read(project_root)

        self.assertEqual(len({item.conversation_id for item in messages}), 2)

    def test_registry_adapter_honors_cowork_home_env_var(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_cowork_session(
                Path(cowork_home),
                "abc123",
                [project_root],
                [_user_turn("/sandbox", "u1", "2026-01-01T00:00:00.000Z", "hello")],
            )
            with patch.dict(os.environ, {"WORKPRINT_COWORK_HOME": cowork_home}):
                adapter = get_adapter("claude-cowork")
                messages = adapter.read(project_root)

        self.assertEqual(len(messages), 1)

    def test_extracts_generic_observation_for_structural_content(self):
        with tempfile.TemporaryDirectory() as cowork_home, \
                tempfile.TemporaryDirectory() as project_dir:
            project_root = str(Path(project_dir).resolve())
            _write_cowork_session(
                Path(cowork_home),
                "abc123",
                [project_root],
                [_assistant_turn("/sandbox", "a1", "2026-01-01T00:00:00.000Z", "Done.", ["Edit"])],
            )
            adapter = ClaudeCoworkAdapter(cowork_home=cowork_home)
            observations = extract_observations(adapter.read(project_root))

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].actor, "Claude Cowork")


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from workprint.adapters import ClaudeDesktopChatAdapter, get_adapter
from workprint.adapters import claude_desktop_chat as module
from workprint.adapters.claude_desktop_chat import (
    DeepParseUnavailableError,
    _as_candidate_turn,
    _walk_candidate_turns,
)
from workprint.extractor import extract_observations


class ClaudeDesktopChatAdapterTests(unittest.TestCase):
    def test_registry_returns_adapter(self):
        adapter = get_adapter("claude-desktop-chat")
        self.assertIsInstance(adapter, ClaudeDesktopChatAdapter)
        self.assertEqual(adapter.adapter_id, "claude-desktop-chat")
        self.assertEqual(adapter.source_type, "conversation")
        self.assertEqual(adapter.display_name, "Claude Desktop Chat")

    def test_presence_only_when_cache_exists(self):
        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(indexeddb_home=cache_dir)
            messages = adapter.read(project_dir)

        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.role, "system")
        self.assertTrue(message.metadata["presence_only"])
        self.assertFalse(message.metadata["project_specific"])
        self.assertNotIn("keyval", message.content)

    def test_no_evidence_when_cache_missing(self):
        with tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(
                indexeddb_home=Path(project_dir) / "does-not-exist"
            )
            self.assertEqual(adapter.read(project_dir), [])
            self.assertIsNone(adapter.discover(project_dir))

    def test_discover_reports_presence_metadata(self):
        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(indexeddb_home=cache_dir)
            metadata = adapter.discover(project_dir)

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["source"], "claude-desktop-chat")
        self.assertFalse(metadata["deep_parse"])
        self.assertEqual(metadata["record_count"], 1)

    def test_deep_parse_without_dependency_raises_clear_error(self):
        # The optional dependency is genuinely not installed in this
        # environment, so this exercises the real graceful-degradation path
        # rather than a mocked one.
        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(indexeddb_home=cache_dir, deep_parse=True)
            with self.assertRaises(DeepParseUnavailableError) as ctx:
                adapter.read(project_dir)

        self.assertIn("claude-desktop-chat", str(ctx.exception))

    def test_deep_parse_env_var_controls_default(self):
        with patch.dict(os.environ, {module.DEEP_PARSE_ENV: "1"}):
            adapter = ClaudeDesktopChatAdapter()
            self.assertTrue(adapter._deep_parse)  # noqa: SLF001

        with patch.dict(os.environ, {}, clear=True):
            adapter = ClaudeDesktopChatAdapter()
            self.assertFalse(adapter._deep_parse)  # noqa: SLF001

    def test_explicit_deep_parse_overrides_env_var(self):
        with patch.dict(os.environ, {module.DEEP_PARSE_ENV: "1"}):
            adapter = ClaudeDesktopChatAdapter(deep_parse=False)
            self.assertFalse(adapter._deep_parse)  # noqa: SLF001

    def test_as_candidate_turn_recognizes_role_and_content_shapes(self):
        turn = _as_candidate_turn(
            {"sender": "human", "text": "hello", "uuid": "u1", "created_at": "t"}
        )
        self.assertIsNotNone(turn)
        self.assertEqual(turn.role, "human")
        self.assertEqual(turn.turn_id, "u1")

        turn = _as_candidate_turn({"role": "claude", "content": "hi there"})
        self.assertIsNotNone(turn)
        self.assertEqual(turn.role, "assistant")

    def test_as_candidate_turn_rejects_missing_fields(self):
        self.assertIsNone(_as_candidate_turn({"role": "human"}))
        self.assertIsNone(_as_candidate_turn({"content": "no role here"}))
        self.assertIsNone(_as_candidate_turn({"role": "system", "content": "not human or ai"}))

    def test_walk_candidate_turns_finds_nested_turns(self):
        payload = {
            "appState": {
                "unrelatedFlag": True,
                "cachedConversations": [
                    {"role": "human", "content": "Do the thing", "uuid": "a"},
                    {"not": "a turn"},
                    {"role": "assistant", "content": "Done", "uuid": "b"},
                ],
            }
        }
        turns = list(_walk_candidate_turns(payload))
        self.assertEqual({t.turn_id for t in turns}, {"a", "b"})

    def test_walk_candidate_turns_respects_depth_limit(self):
        nested: dict = {"role": "human", "content": "too deep", "uuid": "x"}
        for _ in range(20):
            nested = {"wrapper": nested}
        self.assertEqual(list(_walk_candidate_turns(nested)), [])

    def test_deep_parse_end_to_end_with_mocked_library(self):
        fake_record_human = SimpleNamespace(
            value={"role": "human", "content": "Plan the release", "uuid": "h1"}
        )
        fake_record_assistant = SimpleNamespace(
            value={"role": "assistant", "content": "Here is a plan", "uuid": "a1"}
        )

        def fake_iter_turns(_indexeddb_home):
            yield "keyval-store", fake_record_human
            yield "keyval-store", fake_record_assistant

        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(indexeddb_home=cache_dir, deep_parse=True)
            with patch.object(module, "_iter_deep_parsed_turns", fake_iter_turns):
                messages = adapter.read(project_dir)

        self.assertEqual(len(messages), 2)
        for message in messages:
            self.assertFalse(message.metadata["project_specific"])
            self.assertTrue(message.metadata["experimental_deep_parse"])
            self.assertTrue(message.metadata["may_include_deleted_records"])
        self.assertNotIn("Plan the release", messages[0].content)
        self.assertNotIn("Here is a plan", messages[1].content)

    def test_deep_parse_falls_back_to_presence_when_nothing_found(self):
        def fake_iter_turns(_indexeddb_home):
            yield "keyval-store", SimpleNamespace(value={"unrelated": "state"})
            return

        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(indexeddb_home=cache_dir, deep_parse=True)
            with patch.object(module, "_iter_deep_parsed_turns", fake_iter_turns):
                messages = adapter.read(project_dir)

        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].metadata["presence_only"])

    def test_include_content_excerpts_opt_in_on_deep_parse(self):
        fake_record = SimpleNamespace(
            value={"role": "human", "content": "a secret plan", "uuid": "h1"}
        )

        def fake_iter_turns(_indexeddb_home):
            yield "keyval-store", fake_record

        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            default_adapter = ClaudeDesktopChatAdapter(
                indexeddb_home=cache_dir, deep_parse=True
            )
            opted_in_adapter = ClaudeDesktopChatAdapter(
                indexeddb_home=cache_dir, deep_parse=True, include_content_excerpts=True
            )
            with patch.object(module, "_iter_deep_parsed_turns", fake_iter_turns):
                default_messages = default_adapter.read(project_dir)
                opted_in_messages = opted_in_adapter.read(project_dir)

        self.assertNotIn("a secret plan", default_messages[0].content)
        self.assertIn("a secret plan", opted_in_messages[0].content)

    def test_extracts_observation_for_presence_record(self):
        with tempfile.TemporaryDirectory() as cache_dir, \
                tempfile.TemporaryDirectory() as project_dir:
            adapter = ClaudeDesktopChatAdapter(indexeddb_home=cache_dir)
            observations = extract_observations(adapter.read(project_dir))

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].actor, "Claude Desktop Chat")


if __name__ == "__main__":
    unittest.main()

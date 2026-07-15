import json
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import ClaudeAdapter, get_adapter
from workprint.extractor import extract_observations


class ClaudeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path("fixtures/claude/sample-conversations.json")

    def test_registry_returns_claude_adapter(self):
        adapter = get_adapter("claude")
        self.assertIsInstance(adapter, ClaudeAdapter)
        self.assertEqual(adapter.adapter_id, "claude")
        self.assertEqual(adapter.source_type, "conversation")

    def test_reads_conversations_wrapper(self):
        messages = ClaudeAdapter().read(self.fixture)
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0].role, "human")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[0].source, "Claude")

    def test_extracts_expected_activities(self):
        observations = extract_observations(ClaudeAdapter().read(self.fixture))
        activities = [item.activity for item in observations]
        self.assertIn("question", activities)
        self.assertIn("suggestion", activities)
        self.assertIn("decision", activities)
        self.assertIn("implementation", activities)

    def test_reads_single_conversation_with_messages(self):
        payload = {
            "id": "single",
            "messages": [
                {
                    "id": "message-1",
                    "role": "user",
                    "created_at": "2026-01-01T00:00:00Z",
                    "content": "What should we build?"
                },
                {
                    "id": "message-2",
                    "role": "assistant",
                    "created_at": "2026-01-01T00:01:00Z",
                    "content": [
                        {"type": "text", "text": "I suggest a small adapter."}
                    ]
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claude.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            messages = ClaudeAdapter().read(path)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].content, "I suggest a small adapter.")

    def test_rejects_unsupported_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claude.json"
            path.write_text(json.dumps({"name": "empty"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported Claude export"):
                ClaudeAdapter().read(path)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claude.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                ClaudeAdapter().read(path)


if __name__ == "__main__":
    unittest.main()

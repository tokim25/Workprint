import json
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import ChatGPTAdapter
from workprint.extractor import extract_observations


class ChatGPTAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path("fixtures/chatgpt/sample-conversations.json")

    def test_reads_mapping_export(self):
        messages = ChatGPTAdapter().read(self.fixture)
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0].role, "human")
        self.assertEqual(messages[1].role, "assistant")

    def test_extracts_expected_activities(self):
        observations = extract_observations(ChatGPTAdapter().read(self.fixture))
        activities = [item.activity for item in observations]
        self.assertIn("question", activities)
        self.assertIn("suggestion", activities)
        self.assertIn("decision", activities)
        self.assertIn("implementation", activities)

    def test_reads_flat_message_list(self):
        payload = {
            "id": "flat",
            "messages": [
                {
                    "id": "one",
                    "role": "user",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "content": "What should we build?"
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "export.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            messages = ChatGPTAdapter().read(path)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "What should we build?")

    def test_invalid_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(ValueError):
                ChatGPTAdapter().read(path)


if __name__ == "__main__":
    unittest.main()

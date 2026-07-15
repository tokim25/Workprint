import json
import tempfile
import unittest
from pathlib import Path

from workprint.cli import main
from workprint.multisource import (
    EvidenceInput,
    load_observations,
    parse_evidence_spec,
)


class MultiSourceTests(unittest.TestCase):
    def setUp(self):
        self.chatgpt = Path("fixtures/chatgpt/sample-conversations.json")
        self.claude = Path("fixtures/claude/sample-conversations.json")

    def test_parse_evidence_spec(self):
        parsed = parse_evidence_spec(f"chatgpt={self.chatgpt}")
        self.assertEqual(parsed.source, "chatgpt")
        self.assertEqual(parsed.path, self.chatgpt)

    def test_parse_evidence_spec_rejects_bad_format(self):
        with self.assertRaisesRegex(ValueError, "SOURCE=PATH"):
            parse_evidence_spec("chatgpt")

    def test_loads_and_merges_multiple_sources(self):
        observations = load_observations([
            EvidenceInput("chatgpt", self.chatgpt),
            EvidenceInput("claude", self.claude),
        ])
        self.assertEqual({item.source for item in observations}, {"ChatGPT", "Claude"})
        self.assertEqual(len(observations), 8)

    def test_duplicate_inputs_are_suppressed(self):
        observations = load_observations([
            EvidenceInput("chatgpt", self.chatgpt),
            EvidenceInput("chatgpt", self.chatgpt),
        ])
        self.assertEqual(len(observations), 4)

    def test_cli_writes_multi_source_markdown_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            result = main([
                "investigate-multi",
                "--evidence", f"chatgpt={self.chatgpt}",
                "--evidence", f"claude={self.claude}",
                "--project", "Workprint",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            content = output.read_text(encoding="utf-8")
            self.assertIn("ChatGPT", content)
            self.assertIn("Claude", content)
            self.assertIn("Sources analyzed: 2", content)

    def test_cli_writes_multi_source_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            result = main([
                "investigate-multi",
                "--evidence", f"chatgpt={self.chatgpt}",
                "--evidence", f"claude={self.claude}",
                "--project", "Workprint",
                "--format", "json",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["source_files"]), 2)
            self.assertEqual(len(payload["observations"]), 8)
            self.assertEqual(payload["timeline_summary"]["event_count"], 8)


if __name__ == "__main__":
    unittest.main()

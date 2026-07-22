import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from workprint.adapters import ChatSummaryAdapter, get_adapter
from workprint.cli import main
from workprint.discovery import discover_project, render_discovery
from workprint.extractor import extract_observations
from workprint.multisource import load_observations, parse_evidence_spec


FIXTURE = Path("fixtures/chat-summary/sample-summary.json")


class ChatSummaryAdapterTests(unittest.TestCase):
    def test_registry_returns_chat_summary_adapter(self):
        adapter = get_adapter("chat-summary")

        self.assertIsInstance(adapter, ChatSummaryAdapter)
        self.assertEqual(adapter.adapter_id, "chat-summary")
        self.assertEqual(adapter.source_type, "summary")

    def test_json_summary_reads_user_approved_records(self):
        records = ChatSummaryAdapter().read(FIXTURE)

        self.assertEqual(records[0].source, "chat-summary")
        self.assertEqual(records[0].metadata["source_type"], "summary")
        self.assertTrue(records[0].metadata["summary_evidence"])
        self.assertTrue(records[0].metadata["approved_by_user"])
        self.assertTrue(records[0].metadata["not_full_transcript"])
        self.assertIn("Claude Code session", records[0].metadata["original_sources"])
        self.assertEqual(records[0].source_locator, "sample-summary.json#summary")
        self.assertIn(
            "not the full chat transcript",
            records[0].metadata["evidence_boundary"],
        )
        self.assertIn(
            "sample-summary.json#key_decisions-1",
            {record.source_locator for record in records},
        )

    def test_json_summary_requires_user_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(
                json.dumps(
                    {
                        "workprint_source": "chat-summary",
                        "summary": "This has not been approved.",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "approved_by_user"):
                ChatSummaryAdapter().read(path)

    def test_json_summary_requires_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(
                json.dumps(
                    {
                        "summary": "This is not marked as Workprint chat summary evidence.",
                        "approved_by_user": True,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing chat-summary marker"):
                ChatSummaryAdapter().read(path)

    def test_markdown_summary_import_requires_marker(self):
        records = ChatSummaryAdapter().read("fixtures/chat-summary/sample-summary.md")

        self.assertEqual(records[0].source, "chat-summary")
        self.assertEqual(records[0].metadata["summary_item_kind"], "summary_block")
        self.assertEqual(records[0].source_locator, "sample-summary.md#summary-block-1")

    def test_markdown_discovery_ignores_ordinary_repository_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            ordinary = Path(directory) / "README.md"
            ordinary.write_text("# Project\n\nOrdinary docs.", encoding="utf-8")

            self.assertIsNone(ChatSummaryAdapter().discover(ordinary))

    def test_discovery_detects_chat_summary_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "summary.json"
            target.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

            discovery = discover_project(directory)
            rendered = render_discovery(discovery)

        result = self._result(discovery, "chat-summary")
        self.assertEqual(result.label, "Chat Summary")
        self.assertEqual(result.file_count, 1)
        self.assertIn("5 user-approved summary items", rendered)

    def test_extract_observations_keeps_summary_boundary_visible(self):
        observations = extract_observations(ChatSummaryAdapter().read(FIXTURE))

        self.assertEqual({item.source_type for item in observations}, {"summary"})
        self.assertEqual({item.actor for item in observations}, {"User-approved summary"})
        self.assertTrue(
            any("not the full transcript" in item.statement for item in observations)
        )
        self.assertTrue(any(item.activity == "decision" for item in observations))

    def test_multi_source_accepts_chat_summary(self):
        inputs = [
            parse_evidence_spec(f"chat-summary={FIXTURE}"),
            parse_evidence_spec("project-notes=fixtures/project-notes/project-brief.md"),
        ]

        observations = load_observations(inputs)

        self.assertIn("chat-summary", {item.source for item in observations})
        self.assertIn("project-notes", {item.source for item in observations})

    def test_cli_creates_review_required_template(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "summary-template.json"
            result = main([
                "chat-summary-template",
                "--title",
                "Long chat summary",
                "--output",
                str(output),
            ])

            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["workprint_source"], "chat-summary")
            self.assertEqual(payload["title"], "Long chat summary")
            self.assertFalse(payload["approved_by_user"])
            self.assertIn("not the full transcript", payload["unknowns"][0])

    def test_cli_prints_summary_template_to_stdout(self):
        output = StringIO()
        with redirect_stdout(output):
            result = main(["chat-summary-template"])

        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["workprint_source"], "chat-summary")

    @staticmethod
    def _result(discovery, source: str):
        for item in discovery.results:
            if item.source == source:
                return item
        raise AssertionError(f"missing discovery result for {source}")


if __name__ == "__main__":
    unittest.main()

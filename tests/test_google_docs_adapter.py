import json
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import GoogleDocsAdapter, get_adapter
from workprint.extractor import extract_observations


class GoogleDocsAdapterTests(unittest.TestCase):
    def setUp(self):
        self.json_fixture = Path("fixtures/google-docs/sample-document.json")
        self.txt_fixture = Path("fixtures/google-docs/sample-document.txt")
        self.md_fixture = Path("fixtures/google-docs/sample-document.md")

    def test_registry_returns_google_docs_adapter(self):
        adapter = get_adapter("google-docs")
        self.assertIsInstance(adapter, GoogleDocsAdapter)
        self.assertEqual(adapter.adapter_id, "google-docs")
        self.assertEqual(adapter.source_type, "document")

    def test_reads_json_fixture(self):
        messages = GoogleDocsAdapter().read(self.json_fixture)

        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0].source, "google-docs")
        self.assertEqual(messages[0].role, "unknown")
        self.assertEqual(messages[0].created_at.isoformat(), "2026-02-01T10:00:00+00:00")
        self.assertEqual(messages[0].source_locator, "sample-document.json#paragraph/1")
        self.assertEqual(messages[0].metadata["document_id"], "doc-workprint-plan")
        self.assertEqual(messages[0].metadata["document_metadata"]["authors"], ["Tony Kim"])
        self.assertEqual(messages[0].metadata["block_id"], "intro")

    def test_reads_text_without_inferred_timestamps(self):
        messages = GoogleDocsAdapter().read(self.txt_fixture)

        self.assertEqual(len(messages), 3)
        self.assertIsNone(messages[0].created_at)
        self.assertEqual(messages[0].source, "google-docs")
        self.assertEqual(messages[0].source_locator, "sample-document.txt#paragraph/1")
        self.assertEqual(messages[0].metadata["export_format"], "text")

    def test_reads_markdown_without_inferred_timestamps(self):
        messages = GoogleDocsAdapter().read(self.md_fixture)

        self.assertEqual(len(messages), 4)
        self.assertIsNone(messages[0].created_at)
        self.assertEqual(messages[0].metadata["document_title"], "Workprint Markdown Notes")
        self.assertEqual(messages[0].source_locator, "sample-document.md#paragraph/1")

    def test_extracts_document_observations_with_canonical_source(self):
        observations = extract_observations(GoogleDocsAdapter().read(self.json_fixture))

        self.assertEqual({item.source for item in observations}, {"google-docs"})
        self.assertEqual({item.source_type for item in observations}, {"document"})
        self.assertIn("sample-document.json#paragraph/3", observations[2].evidence_refs)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                GoogleDocsAdapter().read(path)

    def test_rejects_unsupported_json_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.json"
            path.write_text(json.dumps({"title": "No body"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "paragraphs or body"):
                GoogleDocsAdapter().read(path)

    def test_rejects_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.html"
            path.write_text("<p>Hello</p>", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported Google Docs export"):
                GoogleDocsAdapter().read(path)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import FigmaAdapter, get_adapter
from workprint.extractor import extract_observations


class FigmaAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path("fixtures/figma/sample-file.json")

    def test_registry_returns_figma_adapter(self):
        adapter = get_adapter("figma")
        self.assertIsInstance(adapter, FigmaAdapter)
        self.assertEqual(adapter.adapter_id, "figma")
        self.assertEqual(adapter.source_type, "design")

    def test_reads_meaningful_nodes_only(self):
        messages = FigmaAdapter().read(self.fixture)

        self.assertEqual(len(messages), 5)
        self.assertEqual({item.source for item in messages}, {"figma"})
        self.assertNotIn("frame-empty", {item.id for item in messages})
        self.assertIn("frame-brief", {item.id for item in messages})
        self.assertIn("text-headline", {item.id for item in messages})
        self.assertIn("component-report-card", {item.id for item in messages})

    def test_preserves_hierarchy_and_metadata(self):
        messages = FigmaAdapter().read(self.fixture)
        text_node = next(item for item in messages if item.id == "text-headline")

        self.assertEqual(
            text_node.source_locator,
            "sample-file.json#page/page-discovery/node/text-headline",
        )
        self.assertEqual(text_node.created_at.isoformat(), "2026-03-01T12:20:00+00:00")
        self.assertEqual(
            text_node.metadata["hierarchy"]["node_path"],
            ["Discovery", "Brief Frame", "Headline"],
        )
        self.assertEqual(
            text_node.metadata["file_metadata"]["last_modified"],
            "2026-03-01T12:00:00Z",
        )
        self.assertEqual(
            text_node.metadata["page_metadata"]["last_modified"],
            "2026-03-01T12:10:00Z",
        )

    def test_does_not_apply_file_timestamp_to_nodes(self):
        messages = FigmaAdapter().read(self.fixture)
        component = next(item for item in messages if item.id == "component-report-card")

        self.assertIsNone(component.created_at)
        self.assertEqual(
            component.metadata["file_metadata"]["last_modified"],
            "2026-03-01T12:00:00Z",
        )

    def test_keeps_contributors_as_metadata_not_authorship(self):
        messages = FigmaAdapter().read(self.fixture)
        observations = extract_observations(messages)

        self.assertEqual({item.source for item in observations}, {"figma"})
        self.assertEqual({item.source_type for item in observations}, {"design"})
        self.assertNotIn("Design Lead", {item.actor for item in observations})
        self.assertIn(
            "sample-file.json#page/page-components/node/component-report-card",
            {
                ref
                for item in observations
                for ref in item.evidence_refs
            },
        )

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "figma.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                FigmaAdapter().read(path)

    def test_rejects_unsupported_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "figma.json"
            path.write_text(json.dumps({"name": "No pages"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected pages"):
                FigmaAdapter().read(path)

    def test_rejects_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "figma.txt"
            path.write_text("not json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported Figma export"):
                FigmaAdapter().read(path)


if __name__ == "__main__":
    unittest.main()

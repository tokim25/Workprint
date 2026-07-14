import unittest
from pathlib import Path

from workprint.adapters import ChatGPTAdapter
from workprint.engine import build_investigation
from workprint.extractor import extract_observations
from workprint.reports import render_markdown


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Path("fixtures/chatgpt/sample-conversations.json")
        self.observations = extract_observations(ChatGPTAdapter().read(self.fixture))

    def test_builds_investigation(self):
        investigation = build_investigation(
            project="Workprint",
            source_files=[self.fixture],
            observations=self.observations,
        )
        self.assertEqual(investigation.project, "Workprint")
        self.assertEqual(len(investigation.observations), 4)
        self.assertGreaterEqual(len(investigation.findings), 2)

    def test_renders_markdown(self):
        investigation = build_investigation(
            project="Workprint",
            source_files=[self.fixture],
            observations=self.observations,
        )
        rendered = render_markdown(investigation)
        self.assertIn("# Workprint Investigation: Workprint", rendered)
        self.assertIn("## Timeline", rendered)
        self.assertIn("## Unknowns", rendered)


if __name__ == "__main__":
    unittest.main()

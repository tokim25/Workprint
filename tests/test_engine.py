import json
import unittest
from pathlib import Path

from workprint.engine import InvestigationEngine, InvestigationError
from workprint.render import render_markdown


FIXTURE = Path(__file__).parents[1] / "fixtures" / "workprint-dogfood.json"


class InvestigationEngineTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_builds_timeline_and_decisions(self):
        report = InvestigationEngine().investigate(self.payload)
        self.assertEqual(report["evidence_count"], 6)
        self.assertEqual([item["id"] for item in report["timeline"]], [
            "EV-001", "EV-002", "EV-003", "EV-004", "EV-005", "EV-006"
        ])
        self.assertEqual(len(report["decisions"]), 2)
        self.assertEqual(report["decisions"][0]["outcome"], "adoption")

    def test_single_event_does_not_create_duration(self):
        payload = {
            "project": "Test",
            "evidence": [self.payload["evidence"][0]],
        }
        report = InvestigationEngine().investigate(payload)
        self.assertEqual(report["sessions"][0]["classification"], "unknown")
        self.assertEqual(report["sessions"][0]["observed_span_minutes"], 0)

    def test_rejects_duplicate_evidence_ids(self):
        payload = {
            "project": "Test",
            "evidence": [self.payload["evidence"][0], self.payload["evidence"][0]],
        }
        with self.assertRaises(InvestigationError):
            InvestigationEngine().investigate(payload)

    def test_markdown_contains_core_sections(self):
        report = InvestigationEngine().investigate(self.payload)
        markdown = render_markdown(report)
        self.assertIn("## Timeline", markdown)
        self.assertIn("## Decisions", markdown)
        self.assertIn("## Unknowns", markdown)


if __name__ == "__main__":
    unittest.main()

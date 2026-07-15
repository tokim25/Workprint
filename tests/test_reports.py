import unittest

from workprint.models import Investigation, Observation
from workprint.reports import render_markdown


class ReportTests(unittest.TestCase):
    def test_render_markdown_includes_core_sections_and_escapes_tables(self):
        investigation = Investigation(
            project="Workprint",
            source_files=("fixture.json",),
            observations=(
                Observation(
                    id="OBS-1",
                    timestamp=None,
                    source="ChatGPT",
                    source_type="conversation",
                    actor="Human",
                    activity="decision",
                    statement="Human chose A | B",
                    evidence_refs=("fixture.json#1",),
                ),
            ),
            findings=(
                {
                    "id": "F-001",
                    "statement": "A finding.",
                    "confidence": "high",
                    "evidence_ids": ["OBS-1"],
                },
            ),
            unknowns=("Unknown offline work.",),
            limitations=("Counts are not effort.",),
        )

        rendered = render_markdown(investigation)

        self.assertIn("# Workprint Investigation: Workprint", rendered)
        self.assertIn("## Timeline", rendered)
        self.assertIn("Human chose A \\| B", rendered)
        self.assertIn("## Limitations", rendered)


if __name__ == "__main__":
    unittest.main()

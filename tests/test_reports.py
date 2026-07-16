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
        self.assertIn("## At a Glance", rendered)
        self.assertIn("## Evidence Boundary", rendered)
        self.assertIn("## Timeline Overview", rendered)
        self.assertIn("## Timeline Event Details", rendered)
        self.assertIn("## Evidence Appendix", rendered)
        self.assertIn("Human chose A \\| B", rendered)
        self.assertIn("## Limitations", rendered)

    def test_render_markdown_includes_scannable_summary_and_appendix(self):
        investigation = Investigation(
            project="Workprint",
            source_files=("b.json", "a.json"),
            observations=(
                Observation(
                    id="OBS-1",
                    timestamp=None,
                    source="ChatGPT",
                    source_type="conversation",
                    actor="Human",
                    activity="decision",
                    statement="Human decided to keep evidence references visible.",
                    evidence_refs=("fixture.json#1",),
                ),
            ),
            findings=(
                {
                    "id": "F-001",
                    "statement": "A finding.",
                    "confidence": "medium",
                    "evidence_ids": ["OBS-1"],
                },
            ),
            unknowns=("Unknown offline work.",),
            limitations=("Counts are not effort.",),
        )

        rendered = render_markdown(investigation)

        self.assertIn("| Sources analyzed | 2 |", rendered)
        self.assertIn("| Unknown entries | 1 |", rendered)
        self.assertIn("| Medium-confidence findings | 1 |", rendered)
        self.assertIn(
            "This report reflects captured evidence only; no ownership, effort, "
            "authorship, value, or contribution percentages are inferred.",
            rendered,
        )
        self.assertLess(rendered.index("- `a.json`"), rendered.index("- `b.json`"))
        self.assertIn("| Event | Time | Stage | Confidence | Observations |", rendered)
        self.assertIn("**Captured user involvement:**", rendered)
        self.assertIn("| `OBS-1` | Unknown | ChatGPT | Human | decision |", rendered)
        self.assertIn("### Observation Statements", rendered)

    def test_large_evidence_reference_lists_are_summarized(self):
        refs = tuple(f"fixture.json#{index}" for index in range(12))
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
                    statement="Human decided to keep evidence references visible.",
                    evidence_refs=refs,
                ),
            ),
            findings=(),
            unknowns=(),
            limitations=(),
        )

        rendered = render_markdown(investigation)

        self.assertIn("and 7 more evidence reference(s) in JSON", rendered)
        self.assertIn("fixture.json#0", rendered)


if __name__ == "__main__":
    unittest.main()

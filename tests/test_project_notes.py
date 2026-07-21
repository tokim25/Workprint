import shutil
import tempfile
import unittest
from pathlib import Path

from workprint.adapters import ProjectNotesAdapter, get_adapter
from workprint.extractor import extract_observations


class ProjectNotesAdapterTests(unittest.TestCase):
    def test_registry_returns_project_notes_adapter(self):
        adapter = get_adapter("project-notes")

        self.assertIsInstance(adapter, ProjectNotesAdapter)
        self.assertEqual(adapter.adapter_id, "project-notes")
        self.assertEqual(adapter.source_type, "document")
        self.assertEqual(adapter.display_name, "Project Notes")

    def test_reads_supported_text_formats(self):
        for extension in (".md", ".mdx", ".txt", ".rst", ".adoc"):
            with self.subTest(extension=extension):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / f"project-plan{extension}"
                    path.write_text(
                        "# Project Plan\n\nThe project goal is to help users practice feedback.",
                        encoding="utf-8",
                    )

                    records = ProjectNotesAdapter().read(path)

                self.assertGreaterEqual(len(records), 2)
                self.assertEqual(records[0].source, "project-notes")
                self.assertEqual(records[0].metadata["source_type"], "document")
                expected_title = (
                    "Project Plan" if extension in {".md", ".mdx"} else "project-plan"
                )
                self.assertEqual(records[0].metadata["document_title"], expected_title)

    def test_discover_skips_boilerplate_filenames(self):
        adapter = ProjectNotesAdapter()
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(
                "# Project\n\nThe project goal is documented here.",
                encoding="utf-8",
            )
            real_notes = Path(directory) / "readme-for-stakeholders.md"
            real_notes.write_text(
                "# Stakeholder Notes\n\nThe project goal is documented here.",
                encoding="utf-8",
            )

            readme_metadata = adapter.discover(readme)
            real_notes_metadata = adapter.discover(real_notes)

        self.assertIsNone(readme_metadata)
        self.assertIsNotNone(real_notes_metadata)
        self.assertEqual(real_notes_metadata["source"], "project-notes")

    def test_direct_read_still_accepts_boilerplate_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(
                "# Project\n\nThe project goal is documented here.",
                encoding="utf-8",
            )

            records = ProjectNotesAdapter().read(readme)

        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(records[0].source, "project-notes")

    def test_rejects_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.html"
            path.write_text("<p>Project</p>", encoding="utf-8")

            with self.assertRaises(ValueError):
                ProjectNotesAdapter().read(path)

    def test_extracts_document_observations_with_project_notes_source(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "project-brief.md"
            shutil.copy("fixtures/project-notes/project-brief.md", fixture)

            observations = extract_observations(ProjectNotesAdapter().read(fixture))

        self.assertGreater(len(observations), 0)
        self.assertTrue(all(item.source == "project-notes" for item in observations))
        self.assertTrue(all(item.source_type == "document" for item in observations))
        self.assertIn("project-notes", observations[0].statement)


if __name__ == "__main__":
    unittest.main()

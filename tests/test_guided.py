import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workprint.cli import main
from workprint.discovery import discover_project
from workprint.guided import (
    evidence_files_from_discovery,
    guided_workflow,
    run_guided,
    select_evidence_files,
)


class GuidedInvestigationTests(unittest.TestCase):
    def test_guided_workflow_generates_markdown_and_json_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            output = io.StringIO()
            answers = iter(["", "", "Guided Project", "", "", "", ""])

            result = guided_workflow(
                input_func=lambda prompt: next(answers),
                output=output,
                cwd=directory,
            )

            self.assertIsNotNone(result)
            markdown = Path(directory) / "workprint-output" / "report.md"
            json_report = Path(directory) / "workprint-output" / "report.json"
            self.assertTrue(markdown.exists())
            self.assertTrue(json_report.exists())
            self.assertIn("Investigation complete.", output.getvalue())
            self.assertIn("Guided Project", markdown.read_text(encoding="utf-8"))
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            self.assertEqual(payload["project"], "Guided Project")
            self.assertIn("timeline", payload)

    def test_selection_can_remove_an_entire_source(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            self._copy_fixture(
                "fixtures/claude/sample-conversations.json",
                directory,
                "claude.json",
            )
            discovery = discover_project(directory)
            evidence_files = evidence_files_from_discovery(discovery)

        selected = select_evidence_files("-claude", evidence_files)

        self.assertEqual({item.source for item in selected}, {"chatgpt"})

    def test_selection_can_remove_an_individual_file(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/google-docs/sample-document.txt",
                directory,
                "a-doc.txt",
            )
            self._copy_fixture(
                "fixtures/google-docs/sample-document.md",
                directory,
                "b-doc.md",
            )
            discovery = discover_project(directory)
            evidence_files = evidence_files_from_discovery(discovery)

        selected = select_evidence_files("-1", evidence_files)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].relative_path, "b-doc.md")

    def test_git_repository_is_informational_only(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, ".git").mkdir()
            output = io.StringIO()
            answers = iter([""])

            result = guided_workflow(
                input_func=lambda prompt: next(answers),
                output=output,
                cwd=directory,
            )

        self.assertIsNone(result)
        rendered = output.getvalue()
        self.assertIn("Git repository: found", rendered)
        self.assertIn("cannot be selected", rendered)
        self.assertIn("No importable evidence was found.", rendered)

    def test_cancel_before_generation_leaves_outputs_uncreated(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            output = io.StringIO()
            answers = iter(["", "", "Canceled Project", "", "", "", "n"])

            result = guided_workflow(
                input_func=lambda prompt: next(answers),
                output=output,
                cwd=directory,
            )

            self.assertIsNone(result)
            self.assertFalse((Path(directory) / "workprint-output").exists())
            self.assertIn("Canceled. No files were changed.", output.getvalue())

    def test_cancel_overwrite_leaves_existing_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            output_dir = Path(directory) / "workprint-output"
            output_dir.mkdir()
            existing = output_dir / "report.md"
            existing.write_text("keep me", encoding="utf-8")
            answers = iter(["", "", "Overwrite Project", "", "", "", ""])

            result = guided_workflow(
                input_func=lambda prompt: next(answers),
                output=io.StringIO(),
                cwd=directory,
            )

            self.assertIsNone(result)
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep me")
            self.assertFalse((output_dir / "report.json").exists())

    def test_existing_outputs_can_use_new_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            default_dir = Path(directory) / "workprint-output"
            default_dir.mkdir()
            (default_dir / "report.md").write_text("old md", encoding="utf-8")
            (default_dir / "report.json").write_text("old json", encoding="utf-8")
            new_dir = Path(directory) / "custom-output"
            answers = iter([
                "",
                "",
                "New Paths Project",
                "",
                "",
                "",
                "new",
                str(new_dir),
                "",
                "",
                "",
            ])

            result = guided_workflow(
                input_func=lambda prompt: next(answers),
                output=io.StringIO(),
                cwd=directory,
            )

            self.assertIsNotNone(result)
            self.assertEqual(
                (default_dir / "report.md").read_text(encoding="utf-8"),
                "old md",
            )
            self.assertTrue((new_dir / "report.md").exists())
            self.assertTrue((new_dir / "report.json").exists())

    def test_selected_file_read_failure_reports_plain_language_error(self):
        with tempfile.TemporaryDirectory() as directory:
            selected_file = Path(directory) / "doc.md"
            selected_file.write_text(
                "This document captures project decisions.",
                encoding="utf-8",
            )
            output = io.StringIO()

            def answer(prompt):
                if prompt.startswith("Generate reports"):
                    selected_file.unlink()
                    return ""
                return {
                    "Project folder": "",
                    "Evidence to include": "",
                    "Project name": "Broken Project",
                    "Output directory": "",
                    "Markdown report": "",
                    "JSON report": "",
                }[prompt.split(" [", 1)[0]]

            result = run_guided(
                input_func=answer,
                output=output,
                cwd=directory,
            )

        self.assertEqual(result, 1)
        self.assertIn("Workprint could not continue:", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_cli_guide_command_delegates_to_guided_runner(self):
        with patch("workprint.cli.run_guided", return_value=0) as runner:
            result = main(["guide"])

        self.assertEqual(result, 0)
        runner.assert_called_once_with()

    @staticmethod
    def _copy_fixture(source: str, directory: str, name: str) -> None:
        shutil.copy(Path(source), Path(directory) / name)


if __name__ == "__main__":
    unittest.main()

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import workprint.guided as guided_module
from workprint.cli import main
from workprint.discovery import discover_project
from workprint.guided import (
    GuidedOptions,
    evidence_files_from_discovery,
    guided_workflow,
    run_guided,
    select_evidence_files,
)


GIT = shutil.which("git")


class GuidedInvestigationTests(unittest.TestCase):
    def setUp(self):
        # See the matching setUp in tests/test_discovery.py: Claude Desktop
        # Chat evidence is account-wide and would otherwise be picked up
        # from whatever real cache exists on the machine running these
        # tests. Tests that specifically exercise this adapter override the
        # variable themselves.
        patcher = patch.dict(
            os.environ,
            {"WORKPRINT_CLAUDE_DESKTOP_HOME": "/nonexistent/workprint-test-path"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

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
            self.assertIn("Selection Summary", output.getvalue())
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
            self._prepend_google_docs_marker(Path(directory) / "a-doc.txt")
            self._copy_fixture(
                "fixtures/google-docs/sample-document.md",
                directory,
                "b-doc.md",
            )
            self._prepend_google_docs_marker(Path(directory) / "b-doc.md")
            discovery = discover_project(directory)
            evidence_files = evidence_files_from_discovery(discovery)

        selected = select_evidence_files("-1", evidence_files)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].relative_path, "b-doc.md")

    def test_git_repository_can_be_selected(self):
        if not GIT:
            self.skipTest("git executable is required")
        with tempfile.TemporaryDirectory() as directory:
            self._init_git(Path(directory))
            output = io.StringIO()
            answers = iter(["", "", "Git Project", "", "", "", ""])

            result = guided_workflow(
                input_func=lambda prompt: next(answers),
                output=output,
                cwd=directory,
            )

        self.assertIsNotNone(result)
        rendered = output.getvalue()
        self.assertIn("Git repository: found", rendered)
        self.assertIn("(git)", rendered)
        self.assertIn("Investigation complete.", rendered)

    def test_claude_code_session_can_be_selected(self):
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as claude_home:
            project_root = str(Path(directory).resolve())
            session_dir = Path(claude_home) / "-tmp-project"
            session_dir.mkdir(parents=True)
            record = {
                "type": "user",
                "uuid": "u1",
                "sessionId": "session-1",
                "timestamp": "2026-01-01T00:00:00.000Z",
                "cwd": project_root,
                "isSidechain": False,
                "message": {"role": "user", "content": "hello"},
            }
            (session_dir / "session-1.jsonl").write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )
            output = io.StringIO()
            answers = iter(["", "", "Claude Code Project", "", "", "", ""])

            with patch.dict(os.environ, {"WORKPRINT_CLAUDE_HOME": claude_home}):
                result = guided_workflow(
                    input_func=lambda prompt: next(answers),
                    output=output,
                    cwd=directory,
                )

        self.assertIsNotNone(result)
        rendered = output.getvalue()
        self.assertIn("(claude-code)", rendered)
        self.assertIn("Investigation complete.", rendered)

    def test_claude_cowork_session_can_be_selected(self):
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as cowork_home:
            project_root = str(Path(directory).resolve())
            metadata_path = Path(cowork_home) / "local_abc123.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "sessionId": "cowork-session-1",
                        "userSelectedFolders": [project_root],
                        "model": "claude-sonnet-5",
                        "sessionType": "scheduled",
                        "isArchived": False,
                    }
                ),
                encoding="utf-8",
            )
            transcript_dir = (
                Path(cowork_home) / "local_abc123" / ".claude" / "projects" / "-sandbox-slug"
            )
            transcript_dir.mkdir(parents=True)
            record = {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2026-01-01T00:00:00.000Z",
                "cwd": "/internal/sandbox/outputs",
                "isSidechain": False,
                "message": {"role": "user", "content": "hello"},
            }
            (transcript_dir / "cowork-session-1.jsonl").write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )
            output = io.StringIO()
            answers = iter(["", "", "Claude Cowork Project", "", "", "", ""])

            with patch.dict(os.environ, {"WORKPRINT_COWORK_HOME": cowork_home}):
                result = guided_workflow(
                    input_func=lambda prompt: next(answers),
                    output=output,
                    cwd=directory,
                )

        self.assertIsNotNone(result)
        rendered = output.getvalue()
        self.assertIn("(claude-cowork)", rendered)
        self.assertIn("Investigation complete.", rendered)

    def test_claude_desktop_chat_offers_deep_parse_consent_and_defaults_to_declining(self):
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as indexeddb_home:
            output = io.StringIO()
            answers = iter(
                ["", "", "n", "Desktop Chat Project", "", "", "", ""]
            )
            prompts: list[str] = []

            def recording_input(prompt: str) -> str:
                prompts.append(prompt)
                return next(answers)

            env = {"WORKPRINT_CLAUDE_DESKTOP_HOME": indexeddb_home}
            os.environ.pop("WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE", None)
            with patch.dict(os.environ, env):
                result = guided_workflow(
                    input_func=recording_input,
                    output=output,
                    cwd=directory,
                )

        self.assertIsNotNone(result)
        self.assertTrue(
            any("Enable experimental deep parsing" in prompt for prompt in prompts)
        )
        rendered = output.getvalue()
        self.assertIn("account-wide, not specific to this project", rendered)
        self.assertNotIn("WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE", os.environ)
        self.assertIn("Investigation complete.", rendered)

    def test_claude_desktop_chat_consent_accepted_enables_deep_parse_for_the_run(self):
        # The optional ccl_chromium_reader dependency is not installed in
        # this environment, so accepting deep parsing here hits the same
        # real DeepParseUnavailableError path exercised in
        # test_claude_desktop_chat_adapter.py. This test only confirms the
        # "y" answer actually flips the environment variable before
        # load_observations runs, not that deep parsing succeeds.
        with tempfile.TemporaryDirectory() as directory, \
                tempfile.TemporaryDirectory() as indexeddb_home:
            output = io.StringIO()
            answers = iter(
                ["", "", "y", "Desktop Chat Project", "", "", "", ""]
            )
            observed_at_load_time: list[bool] = []
            real_load_observations = guided_module.load_observations

            def spying_load_observations(inputs):
                observed_at_load_time.append(
                    os.environ.get("WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE") == "1"
                )
                return real_load_observations(inputs)

            env = {"WORKPRINT_CLAUDE_DESKTOP_HOME": indexeddb_home}
            os.environ.pop("WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE", None)
            with patch.dict(os.environ, env), \
                    patch.object(guided_module, "load_observations", spying_load_observations):
                with self.assertRaises(guided_module.GuidedError) as ctx:
                    guided_workflow(
                        input_func=lambda prompt: next(answers),
                        output=output,
                        cwd=directory,
                    )

        self.assertIn("claude-desktop-chat", str(ctx.exception))
        # By the time evidence is actually loaded, the "y" answer should
        # have already taken effect; the env var is then cleaned up once
        # the patched environment unwinds.
        self.assertEqual(observed_at_load_time, [True])
        self.assertNotIn("WORKPRINT_CLAUDE_DESKTOP_DEEP_PARSE", os.environ)

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
                "workprint-source: google-docs\n\n"
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

    def test_keyboard_interrupt_cancels_cleanly(self):
        output = io.StringIO()

        def interrupt(prompt):
            raise KeyboardInterrupt

        result = run_guided(input_func=interrupt, output=output)

        self.assertEqual(result, 1)
        self.assertIn("Canceled. No files were changed.", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_eof_cancels_cleanly(self):
        output = io.StringIO()

        def eof(prompt):
            raise EOFError

        result = run_guided(input_func=eof, output=output)

        self.assertEqual(result, 1)
        self.assertIn("Canceled. No files were changed.", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_non_interactive_guide_generates_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            output_dir = Path(directory) / "reports"
            output = io.StringIO()

            result = run_guided(
                input_func=lambda prompt: "",
                output=output,
                cwd=directory,
                options=GuidedOptions(
                    path=directory,
                    include="chatgpt",
                    project="Noninteractive Project",
                    output_dir=output_dir,
                    yes=True,
                ),
            )

            self.assertEqual(result, 0)
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue((output_dir / "report.json").exists())
            self.assertIn("Selection Summary", output.getvalue())

    def test_non_interactive_without_yes_does_not_silently_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            self._copy_fixture(
                "fixtures/chatgpt/sample-conversations.json",
                directory,
                "chatgpt.json",
            )
            output_dir = Path(directory) / "workprint-output"
            output_dir.mkdir()
            existing = output_dir / "report.md"
            existing.write_text("existing", encoding="utf-8")
            answers = iter([""])

            result = run_guided(
                input_func=lambda prompt: next(answers),
                output=io.StringIO(),
                cwd=directory,
                options=GuidedOptions(
                    path=directory,
                    include="chatgpt",
                    project="No Silent Overwrite",
                    output_dir=output_dir,
                ),
            )

            self.assertEqual(result, 1)
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing")

    def test_cli_guide_command_accepts_non_interactive_options(self):
        with patch("workprint.cli.run_guided", return_value=0) as runner:
            result = main([
                "guide",
                "--path", ".",
                "--include", "chatgpt",
                "--project", "CLI Project",
                "--output-dir", "workprint-output",
                "--yes",
            ])

        self.assertEqual(result, 0)
        options = runner.call_args.kwargs["options"]
        self.assertEqual(options.path, ".")
        self.assertEqual(options.include, "chatgpt")
        self.assertEqual(options.project, "CLI Project")
        self.assertEqual(options.output_dir, "workprint-output")
        self.assertTrue(options.yes)

    def test_cli_guide_command_delegates_to_guided_runner(self):
        with patch("workprint.cli.run_guided", return_value=0) as runner:
            result = main(["guide"])

        self.assertEqual(result, 0)
        options = runner.call_args.kwargs["options"]
        self.assertIsNone(options.path)
        self.assertIsNone(options.include)
        self.assertIsNone(options.project)
        self.assertFalse(options.yes)

    @staticmethod
    def _copy_fixture(source: str, directory: str, name: str) -> None:
        shutil.copy(Path(source), Path(directory) / name)

    @staticmethod
    def _prepend_google_docs_marker(path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "workprint-source: google-docs\n\n" + text,
            encoding="utf-8",
        )

    @staticmethod
    def _init_git(path: Path) -> None:
        subprocess.run([GIT, "-C", str(path), "init"], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()

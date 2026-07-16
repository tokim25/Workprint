import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workprint.cli import main


GIT = shutil.which("git")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = "fixtures/chatgpt/sample-conversations.json"

    def test_import_writes_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "observations.json"
            result = main([
                "import", "chatgpt", self.fixture,
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 4)

    def test_investigate_writes_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            result = main([
                "investigate", "chatgpt", self.fixture,
                "--project", "Workprint",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            content = output.read_text(encoding="utf-8")
            self.assertIn("Workprint Investigation", content)
            self.assertIn("At a Glance", content)
            self.assertIn("Evidence Appendix", content)
            self.assertIn("Captured User Involvement Counts", content)

    def test_investigate_writes_json_with_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            result = main([
                "investigate", "chatgpt", self.fixture,
                "--project", "Workprint",
                "--format", "json",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("timeline", payload)
            self.assertEqual(payload["timeline_summary"]["event_count"], 4)

    def test_investigate_claude_writes_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "claude-report.md"
            result = main([
                "investigate", "claude", "fixtures/claude/sample-conversations.json",
                "--project", "Workprint",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            content = output.read_text(encoding="utf-8")
            self.assertIn("Claude", content)

    def test_investigate_google_docs_writes_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "google-docs-report.json"
            result = main([
                "investigate",
                "google-docs",
                "fixtures/google-docs/sample-document.json",
                "--project", "Workprint",
                "--format", "json",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                {item["source"] for item in payload["observations"]},
                {"google-docs"},
            )
            self.assertIn(
                "sample-document.json#paragraph/1",
                {
                    ref
                    for item in payload["observations"]
                    for ref in item["evidence_refs"]
                },
            )

    def test_investigate_figma_writes_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "figma-report.json"
            result = main([
                "investigate",
                "figma",
                "fixtures/figma/sample-file.json",
                "--project", "Workprint",
                "--format", "json",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                {item["source"] for item in payload["observations"]},
                {"figma"},
            )
            self.assertIn(
                "sample-file.json#page/page-discovery/node/text-headline",
                {
                    ref
                    for item in payload["observations"]
                    for ref in item["evidence_refs"]
                },
            )

    def test_import_google_docs_writes_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "google-docs-observations.json"
            result = main([
                "import",
                "google-docs",
                "fixtures/google-docs/sample-document.txt",
                "--output", str(output),
            ])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 3)
            self.assertEqual(payload[0]["source"], "google-docs")

    def test_validate(self):
        result = main(["validate", "chatgpt", self.fixture])
        self.assertEqual(result, 0)

    def test_validate_google_docs(self):
        result = main([
            "validate",
            "google-docs",
            "fixtures/google-docs/sample-document.md",
        ])
        self.assertEqual(result, 0)

    def test_validate_figma(self):
        result = main([
            "validate",
            "figma",
            "fixtures/figma/sample-file.json",
        ])
        self.assertEqual(result, 0)

    def test_import_git_writes_observations(self):
        if not GIT:
            self.skipTest("git executable is required")
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run([GIT, "-C", directory, "init"], check=True, capture_output=True)
            subprocess.run([GIT, "-C", directory, "config", "user.name", "Tester"], check=True)
            subprocess.run([GIT, "-C", directory, "config", "user.email", "tester@example.com"], check=True)
            (repo / "report.md").write_text("# Report\n", encoding="utf-8")
            subprocess.run([GIT, "-C", directory, "add", "report.md"], check=True)
            subprocess.run(
                [GIT, "-C", directory, "commit", "-m", "Add report"],
                check=True,
                capture_output=True,
                env={
                    **os.environ,
                    "GIT_AUTHOR_DATE": "2026-01-01T12:00:00+00:00",
                    "GIT_COMMITTER_DATE": "2026-01-01T12:00:00+00:00",
                },
            )
            output = repo / "observations.json"

            result = main(["import", "git", directory, "--output", str(output)])

            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual({item["source"] for item in payload}, {"git"})
            self.assertTrue(any(item["metadata"].get("commit_sha") for item in payload))


if __name__ == "__main__":
    unittest.main()

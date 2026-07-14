import json
import tempfile
import unittest
from pathlib import Path

from workprint.cli import main


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

    def test_validate(self):
        result = main(["validate", "chatgpt", self.fixture])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()

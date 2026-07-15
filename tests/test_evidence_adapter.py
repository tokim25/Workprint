import tempfile
import unittest
from pathlib import Path

from workprint.adapters import (
    ChatGPTAdapter,
    ClaudeAdapter,
    EvidenceAdapter,
    GoogleDocsAdapter,
    available_adapters,
    get_adapter,
)


class EvidenceAdapterTests(unittest.TestCase):
    def test_chatgpt_implements_contract(self):
        adapter = ChatGPTAdapter()
        self.assertIsInstance(adapter, EvidenceAdapter)
        self.assertEqual(adapter.adapter_id, "chatgpt")
        self.assertEqual(adapter.source_type, "conversation")

    def test_registry_returns_chatgpt_adapter(self):
        adapter = get_adapter("chatgpt")
        self.assertIsInstance(adapter, ChatGPTAdapter)
        self.assertEqual(available_adapters(), ("chatgpt", "claude", "google-docs"))

    def test_registry_returns_claude_adapter(self):
        adapter = get_adapter("claude")
        self.assertIsInstance(adapter, ClaudeAdapter)

    def test_registry_returns_google_docs_adapter(self):
        adapter = get_adapter("google-docs")
        self.assertIsInstance(adapter, GoogleDocsAdapter)

    def test_registry_rejects_unknown_adapter(self):
        with self.assertRaisesRegex(ValueError, "unsupported evidence source"):
            get_adapter("unknown")

    def test_validation_rejects_missing_file(self):
        with self.assertRaisesRegex(ValueError, "file not found"):
            ChatGPTAdapter().validate_input("does-not-exist.json")

    def test_validation_rejects_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "input is not a file"):
                ChatGPTAdapter().validate_input(Path(directory))


if __name__ == "__main__":
    unittest.main()

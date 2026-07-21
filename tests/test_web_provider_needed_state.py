from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebProviderNeededStateTests(unittest.TestCase):
    def test_active_discovery_requires_provider_for_real_local_evidence(self):
        source = (ROOT / "lib" / "active-discovery.ts").read_text(encoding="utf-8")

        self.assertIn("PROVIDER_NEEDED_DISCOVERY", source)
        self.assertIn(
            "Connect an AI reasoning provider to see your first insight.", source
        )
        self.assertIn(
            "if (gitSummary || claudeSummary || projectFileFacts.length > 0)",
            source,
        )

        retired_local_fallbacks = [
            "Your project materials describe",
            "Workprint read ${projectFileFacts.length} project",
            "gitDiscoveryClaim(gitSummary)",
            "claudeCodeDiscoveryClaim(claudeSummary.claude_code)",
            "claudeCoworkDiscoveryClaim(claudeSummary.claude_cowork)",
            "claudeDesktopChatDiscoveryClaim(chat)",
        ]
        for fallback in retired_local_fallbacks:
            self.assertNotIn(fallback, source)

    def test_discoveries_screen_shows_equal_provider_choices_without_default(self):
        source = (ROOT / "components" / "workprint-app.tsx").read_text(
            encoding="utf-8"
        )

        self.assertIn("AI reasoning needed", source)
        self.assertIn("OpenAI", source)
        self.assertIn("Claude", source)
        self.assertIn("Gemini", source)
        self.assertIn("no default selection", source)
        self.assertIn("before any selected evidence leaves", source)


if __name__ == "__main__":
    unittest.main()

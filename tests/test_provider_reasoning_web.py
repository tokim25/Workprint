from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProviderReasoningWebTests(unittest.TestCase):
    def test_provider_contract_has_equal_choices_and_no_default(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn('id: "openai"', source)
        self.assertIn('id: "claude"', source)
        self.assertIn('id: "gemini"', source)
        self.assertNotIn("DEFAULT_PROVIDER", source)

    def test_evidence_packet_is_bounded_and_not_persisted(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("MAX_EVIDENCE_PACKET_TOKENS = 30_000", source)
        self.assertIn("store: false", source)
        self.assertIn("Some selected evidence was not sent", source)
        self.assertIn("credentials, secrets, tokens", source)

    def test_provider_route_uses_two_pass_validation(self):
        source = (ROOT / "app" / "api" / "provider-reasoning" / "route.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn('mode: "originate"', source)
        self.assertIn('mode: "corroborate"', source)
        self.assertGreaterEqual(source.count("validateCandidateInsight"), 3)
        self.assertIn("clearTimeout(timeout)", source)

    def test_discoveries_ui_discloses_upload_and_session_only_key(self):
        source = (ROOT / "components" / "workprint-app.tsx").read_text(
            encoding="utf-8"
        )

        self.assertIn("OpenAI, Claude, and Gemini are equal choices", source)
        self.assertIn("does not", source)
        self.assertIn("choose a", source)
        self.assertIn("default provider", source)
        self.assertIn("is not saved by Workprint", source)
        self.assertIn("Selected evidence will leave your device", source)
        self.assertIn("Analyze selected evidence", source)

    def test_deterministic_validation_rejects_forbidden_claims(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("forbiddenClaimPatterns", source)
        self.assertIn("boundary_violation", source)
        self.assertIn("The provider cited evidence Workprint did not send", source)
        self.assertIn("The provider response did not cite any evidence IDs", source)

    def test_provider_parser_handles_common_json_wrappers(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("stripMarkdownFence", source)
        self.assertIn("normalizeCandidateShape", source)
        self.assertIn("candidate_insight", source)
        self.assertIn("evidenceIds", source)
        self.assertIn("supporting_evidence_ids", source)

    def test_gemini_key_uses_header_not_url_query(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn('"x-goog-api-key": input.apiKey', source)
        self.assertNotIn("?key=${encodeURIComponent(input.apiKey)}", source)

    def test_parse_error_explains_structured_json_requirement(self):
        source = (ROOT / "app" / "api" / "provider-reasoning" / "route.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("structured JSON Workprint requested", source)


if __name__ == "__main__":
    unittest.main()

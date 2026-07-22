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

        self.assertIn("MAX_EVIDENCE_PACKET_TOKENS = 45_000", source)
        self.assertIn("MAX_PROVIDER_OUTPUT_TOKENS = 2_000", source)
        self.assertIn("store: false", source)
        self.assertIn("Some selected evidence was not sent", source)
        self.assertIn("credentials, secrets, tokens", source)
        self.assertIn("balanced-context-v1", source)
        self.assertIn("PACKET_PRIORITY_ORDER", source)
        self.assertIn("source diversity", source)
        self.assertIn("human direction and judgment", source)
        self.assertIn("AI Fluency 4D signals", source)
        self.assertIn("omitted_by_source", source)
        self.assertIn("included_for", source)
        self.assertIn("assembleEvidenceCandidates", source)

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
        self.assertIn("Provider model:", source)
        self.assertIn("API key for selected provider", source)
        self.assertIn("What is this?", source)
        self.assertIn("Do not enter your account password", source)
        self.assertIn("Paste an API key, not your account password", source)
        self.assertIn("Bounded evidence", source)
        self.assertIn("selected excerpts", source)
        self.assertIn("evidence IDs", source)
        self.assertIn("source names", source)
        self.assertIn("basic metadata", source)
        self.assertIn("OpenAI API keys", source)
        self.assertIn("Anthropic Console API keys", source)
        self.assertIn("Google AI Studio API keys", source)

    def test_deterministic_validation_rejects_forbidden_claims(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("forbiddenClaimPatterns", source)
        self.assertIn("boundary_violation", source)
        self.assertIn("The provider cited evidence Workprint did not send", source)
        self.assertIn("The provider response did not cite any evidence IDs", source)

    def test_provider_validation_rejects_blank_display_fields(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("PROVIDER_CONFIDENCE_BANDS", source)
        self.assertIn('["confidence", insight.confidence]', source)
        self.assertIn('["explanation", insight.explanation]', source)
        self.assertIn('["unknowns", insight.unknowns]', source)
        self.assertIn("The provider returned an incomplete insight", source)
        self.assertIn(
            "The provider returned a confidence value Workprint could not display",
            source,
        )

    def test_provider_validation_requires_human_centered_first_insight(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("firstInsightRequiredPatterns", source)
        self.assertIn("sourceDetectionOnlyPatterns", source)
        self.assertIn(
            "what the user did OR where human judgment, review, or sequencing appears",
            source,
        )
        self.assertIn(
            "what AI/tooling appears to have done, how the work moved from idea to implementation, or what the evidence cannot separate",
            source,
        )
        self.assertIn("AI Fluency 4D lens", source)
        self.assertIn("Delegation, Description, Discernment, and Diligence", source)
        self.assertIn("what the user gave to AI, kept for themselves, or shaped together", source)
        self.assertIn("review, correction, evaluation, or selection", source)
        self.assertIn("aiFluencyLensPatterns", source)
        self.assertIn("The final claim passed Workprint's AI Fluency lens check", source)
        self.assertIn(
            "The provider insight did not align with an evidence-supported AI Fluency lens",
            source,
        )
        self.assertIn("Prof. Rick Dakan", source)
        self.assertIn("Prof. Joseph Feller", source)
        self.assertIn("Anthropic Academy resources", source)
        self.assertIn("source-detection statement rather than a Workprint first insight", source)
        self.assertIn(
            "The provider insight did not explain what the user did or where human judgment, review, or sequencing appears",
            source,
        )

    def test_provider_validation_rejects_presence_only_cache_headlines(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("presence-only Claude Desktop chat cache evidence", source)
        self.assertIn("presence of (?:an? )?(?:active )?", source)
        self.assertIn("available and utilized on the development system", source)
        self.assertIn("Do not use presence-only Claude Desktop chat cache evidence", source)

    def test_confidence_indicator_explains_confidence_bands(self):
        source = (ROOT / "components" / "confidence-indicator.tsx").read_text(
            encoding="utf-8"
        )

        self.assertIn("title={description}", source)
        self.assertIn("aria-label", source)
        self.assertIn("Strong direct evidence supports this claim", source)
        self.assertIn("limited corroboration", source)
        self.assertIn("coverage or corroboration is thin", source)
        self.assertIn("Evidence is weak, indirect, or incomplete", source)
        self.assertIn("Workprint has not assessed confidence yet", source)

    def test_provider_parser_handles_common_json_wrappers(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("stripMarkdownFence", source)
        self.assertIn("normalizeCandidateShape", source)
        self.assertIn("candidate_insight", source)
        self.assertIn("evidenceIds", source)
        self.assertIn("supporting_evidence_ids", source)

    def test_provider_parser_tolerates_common_gemini_shape_drift(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("stringifyCandidateValue", source)
        self.assertIn("extractEvidenceIds", source)
        self.assertIn("confidence_level", source)
        self.assertIn("record.evidence_id", source)
        self.assertIn("record.reference", source)
        self.assertIn(".flatMap(extractEvidenceIds)", source)

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

    def test_gemini_requests_structured_schema(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("PROVIDER_INSIGHT_RESPONSE_SCHEMA", source)
        self.assertIn('responseMimeType: "application/json"', source)
        self.assertIn("responseSchema: PROVIDER_INSIGHT_RESPONSE_SCHEMA", source)
        self.assertNotIn("responseFormat", source)

    def test_provider_route_repairs_plain_text_before_failing(self):
        source = (ROOT / "app" / "api" / "provider-reasoning" / "route.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("buildProviderRepairPrompt", source)
        self.assertIn("const repairResponse = await callProviderWithFallback", source)
        self.assertIn("const repaired = parseCandidateInsight(repairResponse.response)", source)

    def test_provider_route_saves_local_debug_file_after_parse_failure(self):
        source = (ROOT / "app" / "api" / "provider-reasoning" / "route.ts").read_text(
            encoding="utf-8"
        )
        electron_source = (ROOT / "electron" / "main.js").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("writeProviderDebugFile", source)
        self.assertIn("WORKPRINT_PROVIDER_DEBUG_DIR", source)
        self.assertIn("WORKPRINT_PROVIDER_DEBUG_DIR", electron_source)
        self.assertIn("provider-debug", electron_source)
        self.assertIn("workprint-debug/", gitignore)
        self.assertIn("API keys and evidence packets are not included", source)
        self.assertIn("original_response", source)
        self.assertIn("repair_response", source)
        self.assertNotIn("api_key", source)

    def test_gemini_capacity_errors_use_fallback_model(self):
        route_source = (ROOT / "app" / "api" / "provider-reasoning" / "route.ts").read_text(
            encoding="utf-8"
        )
        provider_source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn('GEMINI_FALLBACK_MODELS = ["gemini-2.5-flash"]', provider_source)
        self.assertIn("isProviderCapacityError", provider_source)
        self.assertIn("callProviderWithFallback", route_source)
        self.assertIn("Gemini reported", route_source)
        self.assertIn("temporarily busy", route_source)
        self.assertIn("Workprint tried the fallback model too", route_source)
        self.assertIn("model: secondPass.model", route_source)

    def test_repair_prompt_does_not_expand_attribution(self):
        source = (ROOT / "lib" / "provider-reasoning.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("Convert this provider response", source)
        self.assertIn("Do not add new claims", source)
        self.assertIn("contribution percentages", source)
        self.assertIn("use an empty array", source)

    def test_ai_reasoning_provider_docs_match_first_insight_contract(self):
        source = (ROOT / "docs" / "ai-reasoning-providers.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("capped at 45,000 tokens", source)
        self.assertIn("source diversity", source)
        self.assertIn("human direction, judgment, review, or sequencing", source)
        self.assertIn("AI Fluency 4D signals", source)
        self.assertIn("recency", source)
        self.assertIn("It must tell the user what they did OR where", source)
        self.assertIn("what AI or tooling appears to have done", source)
        self.assertIn("how the work moved from idea to implementation", source)
        self.assertIn("what the evidence cannot separate", source)
        self.assertIn("Source detection, not an insight", source)
        self.assertIn("Claude Desktop evidence was detected", source)


if __name__ == "__main__":
    unittest.main()

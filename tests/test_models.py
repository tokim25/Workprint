import unittest
from datetime import datetime, timezone

from workprint.models import NormalizedMessage, Observation, TimelineEvent


class ModelTests(unittest.TestCase):
    def test_normalized_message_rejects_bad_role(self):
        with self.assertRaises(ValueError):
            NormalizedMessage(
                id="m1",
                conversation_id="c1",
                role="robot",
                content="text",
                created_at=None,
                source="ChatGPT",
                source_locator="file#1",
                metadata={},
            )

    def test_observation_serializes(self):
        item = Observation(
            id="OBS-1",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source="ChatGPT",
            source_type="conversation",
            actor="Human",
            activity="decision",
            statement="Human selected a name.",
            evidence_refs=("file#1",),
        )
        data = item.to_dict()
        self.assertEqual(data["activity"], "decision")
        self.assertEqual(data["evidence_refs"], ["file#1"])

    def test_observation_requires_evidence(self):
        with self.assertRaises(ValueError):
            Observation(
                id="OBS-1",
                timestamp=None,
                source="ChatGPT",
                source_type="conversation",
                actor="Human",
                activity="observation",
                statement="A statement.",
                evidence_refs=(),
            )

    def test_timeline_event_serializes(self):
        item = TimelineEvent(
            id="TL-001",
            start_time=None,
            end_time=None,
            stage="decision",
            title="Decision",
            description="Human decided.",
            source_observation_ids=("OBS-1",),
            evidence_refs=("file#1",),
            confidence="medium",
            user_involvement=(),
            activity_breakdown={"user_activity": ("OBS-1",)},
            attribution_limits=("Evidence only.",),
        )

        data = item.to_dict()

        self.assertEqual(data["id"], "TL-001")
        self.assertEqual(data["activity_breakdown"]["user_activity"], ["OBS-1"])


if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime, timezone

from workprint.models import (
    Completeness,
    Observation,
    ObservationError,
    Reliability,
)


class ObservationTests(unittest.TestCase):
    def test_builds_valid_observation(self):
        observation = Observation(
            id="OBS-001",
            source_type="conversation",
            source_name="Claude",
            source_locator="conversation:1/message:2",
            event_time=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
            actor="Claude",
            activity="Suggestion",
            artifact="Observation model",
            observation="Proposed a canonical observation model.",
            reliability=Reliability.HIGH,
            completeness=Completeness.COMPLETE,
            metadata={"message_role": "assistant"},
        )

        self.assertEqual(observation.activity, "suggestion")
        self.assertEqual(observation.reliability, Reliability.HIGH)
        self.assertEqual(observation.metadata["message_role"], "assistant")

    def test_rejects_missing_required_fields(self):
        with self.assertRaisesRegex(ObservationError, "observation"):
            Observation(
                id="OBS-001",
                source_type="conversation",
                observation="   ",
                reliability=Reliability.HIGH,
            )

    def test_rejects_invalid_reliability(self):
        with self.assertRaisesRegex(ObservationError, "invalid reliability"):
            Observation.from_dict(
                {
                    "id": "OBS-001",
                    "source_type": "conversation",
                    "observation": "A recorded event.",
                    "reliability": "certain",
                }
            )

    def test_rejects_invalid_timestamp(self):
        with self.assertRaisesRegex(ObservationError, "invalid ISO-8601"):
            Observation.from_dict(
                {
                    "id": "OBS-001",
                    "source_type": "conversation",
                    "observation": "A recorded event.",
                    "reliability": "high",
                    "event_time": "not-a-date",
                }
            )

    def test_round_trip_preserves_values(self):
        record = {
            "id": "OBS-001",
            "source_type": "conversation",
            "source_name": "ChatGPT",
            "source_locator": "conversation:abc/message:123",
            "observed_at": "2026-07-14T12:05:00+00:00",
            "event_time": "2026-07-14T12:00:00+00:00",
            "actor": "Tony Kim",
            "activity": "decision",
            "artifact": "Product name",
            "observation": "Selected Workprint as the working name.",
            "reliability": "high",
            "completeness": "complete",
            "notes": None,
            "metadata": {"message_role": "user"},
        }

        observation = Observation.from_dict(record)
        self.assertEqual(observation.to_dict(), record)

    def test_metadata_must_be_an_object(self):
        with self.assertRaisesRegex(ObservationError, "metadata must be an object"):
            Observation.from_dict(
                {
                    "id": "OBS-001",
                    "source_type": "conversation",
                    "observation": "A recorded event.",
                    "reliability": "high",
                    "metadata": ["invalid"],
                }
            )


if __name__ == "__main__":
    unittest.main()

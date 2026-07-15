import unittest
from datetime import datetime, timezone

from workprint.models import Observation, TimelineEvent, TimelineInvolvement
from workprint.timeline import build_timeline, summarize_timeline


class TimelineTests(unittest.TestCase):
    def test_timeline_involvement_validates_activity_and_status(self):
        with self.assertRaises(ValueError):
            TimelineInvolvement(activity="owned", status="measured")

        with self.assertRaises(ValueError):
            TimelineInvolvement(activity="decided", status="certain")

    def test_builds_evidence_linked_timeline_events(self):
        observations = [
            Observation(
                id="OBS-1",
                timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                source="ChatGPT",
                source_type="conversation",
                actor="Human",
                activity="question",
                statement="Human asked: What should we build?",
                evidence_refs=("chatgpt.json#1",),
                metadata={"conversation_id": "c1"},
            ),
            Observation(
                id="OBS-2",
                timestamp=datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc),
                source="ChatGPT",
                source_type="conversation",
                actor="ChatGPT",
                activity="suggestion",
                statement="ChatGPT suggested: Build an importer.",
                evidence_refs=("chatgpt.json#2",),
                metadata={"conversation_id": "c1"},
            ),
            Observation(
                id="OBS-3",
                timestamp=datetime(2026, 1, 1, 12, 6, tzinfo=timezone.utc),
                source="ChatGPT",
                source_type="conversation",
                actor="Human",
                activity="suggestion",
                statement="Human suggested: Keep it deterministic.",
                evidence_refs=("chatgpt.json#3",),
                metadata={"conversation_id": "c1"},
            ),
        ]

        events = build_timeline(observations)

        self.assertEqual([event.stage for event in events], ["discovery", "planning"])
        self.assertEqual(events[0].user_involvement[0].activity, "initiated")
        self.assertEqual(events[0].user_involvement[0].status, "measured")
        self.assertEqual(events[1].activity_breakdown["user_activity"], ("OBS-3",))
        self.assertEqual(events[1].activity_breakdown["ai_tool_activity"], ("OBS-2",))
        self.assertEqual(
            events[1].activity_breakdown["joint_activity"],
            ("OBS-3", "OBS-2"),
        )

    def test_summarizes_counts_as_captured_evidence_only(self):
        event = TimelineEvent(
            id="TL-001",
            start_time=None,
            end_time=None,
            stage="decision",
            title="Decision",
            description="Human decided.",
            source_observation_ids=("OBS-1",),
            evidence_refs=("fixture#1",),
            confidence="medium",
            user_involvement=(
                TimelineInvolvement(
                    activity="decided",
                    status="measured",
                    evidence_ids=("OBS-1",),
                ),
            ),
            activity_breakdown={"user_activity": ("OBS-1",)},
            attribution_limits=("No percentages are inferred.",),
        )

        summary = summarize_timeline((event,))

        self.assertEqual(summary["event_count"], 1)
        self.assertEqual(summary["captured_user_involvement_counts"]["decided"], 1)
        self.assertIn("not ownership", summary["counting_note"])


if __name__ == "__main__":
    unittest.main()

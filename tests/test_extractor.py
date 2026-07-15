import unittest

from workprint.extractor import extract_observations
from workprint.models import NormalizedMessage


class ExtractorTests(unittest.TestCase):
    def test_classifies_question_decision_and_implementation(self):
        messages = [
            NormalizedMessage(
                id="m1",
                conversation_id="c1",
                role="human",
                content="What should we build?",
                created_at=None,
                source="ChatGPT",
                source_locator="fixture#m1",
                metadata={},
            ),
            NormalizedMessage(
                id="m2",
                conversation_id="c1",
                role="assistant",
                content="I suggest a small importer.",
                created_at=None,
                source="ChatGPT",
                source_locator="fixture#m2",
                metadata={},
            ),
            NormalizedMessage(
                id="m3",
                conversation_id="c1",
                role="human",
                content="Let's use that approach.",
                created_at=None,
                source="ChatGPT",
                source_locator="fixture#m3",
                metadata={},
            ),
            NormalizedMessage(
                id="m4",
                conversation_id="c1",
                role="assistant",
                content="I implemented the importer.",
                created_at=None,
                source="ChatGPT",
                source_locator="fixture#m4",
                metadata={},
            ),
        ]

        observations = extract_observations(messages)

        self.assertEqual(
            [item.activity for item in observations],
            ["question", "suggestion", "decision", "implementation"],
        )
        self.assertEqual(observations[0].metadata["sequence"], 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workprint.adapters import ClaudeAdapter, ClaudeAdapterError


FIXTURE = Path(__file__).parents[1] / "fixtures" / "claude" / "sample-conversations.json"


def test_reads_claude_export_into_normalized_messages() -> None:
    messages = ClaudeAdapter().read(FIXTURE)

    assert len(messages) == 4
    assert messages[0].actor == "Human"
    assert messages[1].actor == "Claude"
    assert messages[0].conversation_id == "conv-workprint-demo"
    assert messages[0].created_at is not None


def test_ingest_produces_valid_observations() -> None:
    observations = ClaudeAdapter().ingest(FIXTURE)

    activities = {observation.activity for observation in observations}
    assert "question" in activities
    assert "suggestion" in activities
    assert "decision" in activities
    assert "implementation" in activities
    assert all(observation.source_name == "Claude" for observation in observations)
    assert all(observation.source_locator for observation in observations)


def test_content_block_text_is_supported(tmp_path: Path) -> None:
    payload = {
        "conversations": [
            {
                "id": "conv-blocks",
                "messages": [
                    {
                        "id": "m1",
                        "role": "assistant",
                        "createdAt": "2026-07-14T17:00:00Z",
                        "content": [
                            {"type": "text", "text": "I suggest a smaller adapter."}
                        ],
                    }
                ],
            }
        ]
    }
    path = tmp_path / "claude.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    observations = ClaudeAdapter().ingest(path)

    assert observations[0].activity == "suggestion"
    assert "smaller adapter" in observations[0].observation


def test_invalid_export_raises_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(ClaudeAdapterError, match="does not contain"):
        ClaudeAdapter().read(path)

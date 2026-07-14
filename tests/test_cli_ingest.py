from __future__ import annotations

import json
from pathlib import Path

from workprint.cli import main


FIXTURE = Path(__file__).parents[1] / "fixtures" / "claude" / "sample-conversations.json"


def test_cli_ingests_claude_export(tmp_path: Path) -> None:
    output = tmp_path / "observations.json"

    result = main(["ingest", "claude", str(FIXTURE), "--output", str(output)])

    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload
    assert payload[0]["source_name"] == "Claude"


def test_legacy_investigation_command_still_works(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "workprint-dogfood.json"
    output = tmp_path / "report.md"

    result = main([str(fixture), "--output", str(output)])

    assert result == 0
    assert "## Timeline" in output.read_text(encoding="utf-8")

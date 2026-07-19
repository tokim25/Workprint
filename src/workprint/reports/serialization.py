from __future__ import annotations

from typing import Any

from workprint.ai_fluency import build_ai_fluency_reflection
from workprint.executive import build_executive_report
from workprint.models import Investigation


def render_json_dict(investigation: Investigation) -> dict[str, Any]:
    data = investigation.to_dict()
    data["executive_report"] = build_executive_report(investigation).to_dict()
    data["ai_fluency"] = build_ai_fluency_reflection(investigation).to_dict()
    return data

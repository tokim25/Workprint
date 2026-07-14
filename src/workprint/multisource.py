from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from workprint.adapters import get_adapter
from workprint.extractor import extract_observations
from workprint.models import Observation


@dataclass(frozen=True)
class EvidenceInput:
    source: str
    path: Path


def parse_evidence_spec(spec: str) -> EvidenceInput:
    source, separator, raw_path = spec.partition("=")
    if not separator or not source.strip() or not raw_path.strip():
        raise ValueError(
            "evidence inputs must use SOURCE=PATH, "
            "for example chatgpt=exports/conversations.json"
        )

    adapter = get_adapter(source.strip())
    path = adapter.validate_input(raw_path.strip())
    return EvidenceInput(source=adapter.adapter_id, path=path)


def load_observations(inputs: Iterable[EvidenceInput]) -> list[Observation]:
    merged: list[Observation] = []
    seen: set[tuple[str, str, str, str | None]] = set()

    for evidence_input in inputs:
        adapter = get_adapter(evidence_input.source)
        records = adapter.read(evidence_input.path)
        observations = extract_observations(records)

        for observation in observations:
            timestamp = (
                observation.timestamp.isoformat()
                if observation.timestamp is not None
                else None
            )
            fingerprint = (
                observation.source,
                observation.statement,
                "|".join(observation.evidence_refs),
                timestamp,
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            merged.append(observation)

    merged.sort(
        key=lambda item: (
            item.timestamp is None,
            item.timestamp.isoformat() if item.timestamp else "",
            item.source,
            item.id,
        )
    )
    return merged

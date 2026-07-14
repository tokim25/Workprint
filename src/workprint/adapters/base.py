from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar


EvidenceRecord = TypeVar("EvidenceRecord")


class EvidenceAdapter(ABC, Generic[EvidenceRecord]):
    """Base contract for every Workprint evidence source.

    Adapters are responsible only for reading a source-specific artifact and
    converting it into Workprint's normalized record type. They must not
    create project-level findings or conclusions.
    """

    source_name: str
    source_type: str

    @property
    def adapter_id(self) -> str:
        """Stable lowercase identifier used by the CLI and adapter registry."""
        return self.source_name.strip().lower().replace(" ", "-")

    def validate_input(self, path: str | Path) -> Path:
        """Return a readable file path or raise a user-facing ValueError."""
        source_path = Path(path)
        if not source_path.exists():
            raise ValueError(f"file not found: {source_path}")
        if not source_path.is_file():
            raise ValueError(f"input is not a file: {source_path}")
        return source_path

    @abstractmethod
    def read(self, path: str | Path) -> list[EvidenceRecord]:
        """Read source evidence and return normalized Workprint records."""
        raise NotImplementedError

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from workprint.conversations import NormalizedMessage
from workprint.models import Observation


class ConversationAdapter(ABC):
    """Contract for adapters that normalize vendor conversation exports."""

    source_name: str

    @abstractmethod
    def read(self, path: Path) -> list[NormalizedMessage]:
        """Read a vendor export and return normalized messages."""

    @abstractmethod
    def to_observations(
        self, messages: list[NormalizedMessage]
    ) -> list[Observation]:
        """Convert normalized messages into canonical observations."""

    def ingest(self, path: Path) -> list[Observation]:
        return self.to_observations(self.read(path))

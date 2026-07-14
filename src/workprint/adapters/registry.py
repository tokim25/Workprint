from __future__ import annotations

from collections.abc import Callable

from .base import EvidenceAdapter
from .chatgpt import ChatGPTAdapter
from .claude import ClaudeAdapter


AdapterFactory = Callable[[], EvidenceAdapter]


_ADAPTERS: dict[str, AdapterFactory] = {
    "chatgpt": ChatGPTAdapter,
    "claude": ClaudeAdapter,
}


def available_adapters() -> tuple[str, ...]:
    """Return supported adapter identifiers in stable order."""
    return tuple(sorted(_ADAPTERS))


def get_adapter(adapter_id: str) -> EvidenceAdapter:
    """Create an adapter by its stable identifier."""
    try:
        factory = _ADAPTERS[adapter_id]
    except KeyError as exc:
        supported = ", ".join(available_adapters())
        raise ValueError(
            f"unsupported evidence source: {adapter_id}. "
            f"Supported sources: {supported}"
        ) from exc
    return factory()

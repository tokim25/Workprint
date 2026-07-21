from __future__ import annotations

from collections.abc import Callable

from .base import EvidenceAdapter
from .chatgpt import ChatGPTAdapter
from .claude import ClaudeAdapter
from .claude_code import ClaudeCodeAdapter
from .claude_cowork import ClaudeCoworkAdapter
from .claude_desktop_chat import ClaudeDesktopChatAdapter
from .figma import FigmaAdapter
from .git import GitAdapter
from .google_docs import GoogleDocsAdapter
from .project_notes import ProjectNotesAdapter


AdapterFactory = Callable[[], EvidenceAdapter]


_ADAPTERS: dict[str, AdapterFactory] = {
    "chatgpt": ChatGPTAdapter,
    "claude": ClaudeAdapter,
    "claude-code": ClaudeCodeAdapter,
    "claude-cowork": ClaudeCoworkAdapter,
    "claude-desktop-chat": ClaudeDesktopChatAdapter,
    "figma": FigmaAdapter,
    "git": GitAdapter,
    "google-docs": GoogleDocsAdapter,
    "project-notes": ProjectNotesAdapter,
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

from .base import EvidenceAdapter
from .chatgpt import ChatGPTAdapter
from .claude import ClaudeAdapter
from .google_docs import GoogleDocsAdapter
from .registry import available_adapters, get_adapter

__all__ = [
    "EvidenceAdapter",
    "ChatGPTAdapter",
    "ClaudeAdapter",
    "GoogleDocsAdapter",
    "available_adapters",
    "get_adapter",
]

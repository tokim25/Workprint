from .base import EvidenceAdapter
from .chatgpt import ChatGPTAdapter
from .claude import ClaudeAdapter
from .claude_code import ClaudeCodeAdapter
from .claude_cowork import ClaudeCoworkAdapter
from .figma import FigmaAdapter
from .git import GitAdapter
from .google_docs import GoogleDocsAdapter
from .registry import available_adapters, get_adapter

__all__ = [
    "EvidenceAdapter",
    "ChatGPTAdapter",
    "ClaudeAdapter",
    "ClaudeCodeAdapter",
    "ClaudeCoworkAdapter",
    "FigmaAdapter",
    "GitAdapter",
    "GoogleDocsAdapter",
    "available_adapters",
    "get_adapter",
]

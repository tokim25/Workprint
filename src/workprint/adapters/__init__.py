from .base import EvidenceAdapter
from .chat_summary import ChatSummaryAdapter, build_chat_summary_template
from .chatgpt import ChatGPTAdapter
from .claude import ClaudeAdapter
from .claude_code import ClaudeCodeAdapter
from .claude_cowork import ClaudeCoworkAdapter
from .claude_desktop_chat import ClaudeDesktopChatAdapter
from .figma import FigmaAdapter
from .git import GitAdapter
from .google_docs import GoogleDocsAdapter
from .project_notes import ProjectNotesAdapter
from .registry import available_adapters, get_adapter

__all__ = [
    "EvidenceAdapter",
    "ChatSummaryAdapter",
    "build_chat_summary_template",
    "ChatGPTAdapter",
    "ClaudeAdapter",
    "ClaudeCodeAdapter",
    "ClaudeCoworkAdapter",
    "ClaudeDesktopChatAdapter",
    "FigmaAdapter",
    "GitAdapter",
    "GoogleDocsAdapter",
    "ProjectNotesAdapter",
    "available_adapters",
    "get_adapter",
]

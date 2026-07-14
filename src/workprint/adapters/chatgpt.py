"""ChatGPT adapter (scaffold)."""

from .base import BaseAdapter

class ChatGPTAdapter(BaseAdapter):
    name="chatgpt"

    def parse(self, export):
        """Convert a ChatGPT export into Observation objects."""
        raise NotImplementedError("WP-003 implementation placeholder")

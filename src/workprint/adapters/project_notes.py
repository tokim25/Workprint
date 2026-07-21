from __future__ import annotations

from pathlib import Path

from workprint.models import NormalizedMessage

from .base import EvidenceAdapter
from .google_docs import _split_blocks, _title_from_markdown


BOILERPLATE_STEMS = {
    "authors",
    "changelog",
    "code_of_conduct",
    "codeowners",
    "contributing",
    "license",
    "licence",
    "notice",
    "readme",
    "security",
}

SUPPORTED_SUFFIXES = {".adoc", ".md", ".mdx", ".rst", ".txt"}


class ProjectNotesAdapter(EvidenceAdapter[NormalizedMessage]):
    """Read ordinary project notes and docs without inferring authorship."""

    source_name = "project-notes"
    source_type = "document"

    @property
    def display_name(self) -> str:
        return "Project Notes"

    def discover(self, path: str | Path) -> dict[str, object] | None:
        source_path = Path(path)
        if source_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            return None
        if source_path.stem.lower() in BOILERPLATE_STEMS:
            return None
        return super().discover(path)

    def read(self, path: str | Path) -> list[NormalizedMessage]:
        source_path = self.validate_input(path)
        suffix = source_path.suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise ValueError(
                f"unsupported project notes format: {source_path.suffix}"
            )

        text = source_path.read_text(encoding="utf-8")
        blocks = _split_blocks(text)
        title = (
            _title_from_markdown(blocks, source_path.stem)
            if suffix in {".md", ".mdx"}
            else source_path.stem
        )
        document_id = source_path.stem

        return [
            self._message(
                source_path=source_path,
                document_id=document_id,
                title=title,
                block_id=f"paragraph-{index}",
                index=index,
                content=block,
                export_format=suffix.lstrip(".") or "text",
            )
            for index, block in enumerate(blocks, start=1)
        ]

    def _message(
        self,
        source_path: Path,
        document_id: str,
        title: str,
        block_id: str,
        index: int,
        content: str,
        export_format: str,
    ) -> NormalizedMessage:
        return NormalizedMessage(
            id=block_id,
            conversation_id=document_id,
            role="unknown",
            content=content.strip(),
            created_at=None,
            source=self.source_name,
            source_locator=f"{source_path.name}#paragraph/{index}",
            metadata={
                "document_id": document_id,
                "document_title": title,
                "block_id": block_id,
                "block_index": index,
                "export_format": export_format,
                "source_type": self.source_type,
                "document_metadata": {},
                "block_metadata": {},
            },
        )

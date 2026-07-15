from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workprint.adapters import available_adapters, get_adapter


@dataclass(frozen=True)
class DiscoveryResult:
    source: str
    label: str
    file_count: int
    detected_files: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "label": self.label,
            "file_count": self.file_count,
            "detected_files": list(self.detected_files),
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ProjectDiscovery:
    root: str
    git_repository: bool
    results: tuple[DiscoveryResult, ...]
    warnings: tuple[str, ...] = ()

    @property
    def evidence_sources(self) -> int:
        return len(self.results) + (1 if self.git_repository else 0)

    @property
    def supported_files(self) -> int:
        return sum(item.file_count for item in self.results)

    @property
    def ready(self) -> bool:
        return self.git_repository or bool(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "git_repository": self.git_repository,
            "evidence_sources": self.evidence_sources,
            "supported_files": self.supported_files,
            "ready": self.ready,
            "results": [item.to_dict() for item in self.results],
            "warnings": list(self.warnings),
        }


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _is_git_repository(root: Path) -> bool:
    return (root / ".git").exists()


def discover_project(path: str | Path = ".") -> ProjectDiscovery:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise ValueError(f"project path not found: {root}")
    if not root.is_dir():
        raise ValueError(f"project path is not a directory: {root}")

    adapters = [get_adapter(adapter_id) for adapter_id in available_adapters()]
    grouped: dict[str, dict[str, Any]] = {}

    for file_path in _iter_files(root):
        for adapter in adapters:
            metadata = adapter.discover(file_path)
            if metadata is None:
                continue
            source = str(metadata["source"])
            entry = grouped.setdefault(
                source,
                {
                    "label": metadata["label"],
                    "files": [],
                    "records": 0,
                },
            )
            entry["files"].append(file_path.relative_to(root).as_posix())
            entry["records"] += int(metadata.get("record_count", 0))
            break

    results = tuple(
        DiscoveryResult(
            source=source,
            label=entry["label"],
            file_count=len(entry["files"]),
            detected_files=tuple(sorted(entry["files"])),
            metadata={"record_count": entry["records"]},
        )
        for source, entry in sorted(grouped.items(), key=lambda item: item[0])
    )

    return ProjectDiscovery(
        root=str(root),
        git_repository=_is_git_repository(root),
        results=results,
    )


def render_discovery(discovery: ProjectDiscovery) -> str:
    lines: list[str] = ["Project Discovery", ""]

    if discovery.git_repository:
        lines.extend(["✓ Git repository", ""])

    for result in discovery.results:
        lines.append(result.label)
        lines.append(_summary_line(result))
        lines.append("")

    if not discovery.ready:
        lines.extend([
            "No supported evidence found.",
            "",
            "Supported sources:",
            "- ChatGPT",
            "- Claude",
            "- Google Docs",
            "- Figma",
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "Project Readiness",
        "",
        f"Evidence sources: {discovery.evidence_sources}",
        f"Supported files: {discovery.supported_files}",
        "",
        "Ready for investigation.",
        "",
    ])
    return "\n".join(lines)


def _summary_line(result: DiscoveryResult) -> str:
    if result.source in {"chatgpt", "claude"}:
        count = result.metadata.get("record_count", 0)
        noun = "conversation" if count == 1 else "conversations"
        return f"{count} {noun}"
    if result.source == "google-docs":
        noun = "document" if result.file_count == 1 else "documents"
        return f"{result.file_count} {noun}"
    if result.source == "figma":
        noun = "file" if result.file_count == 1 else "files"
        return f"{result.file_count} {noun}"
    noun = "file" if result.file_count == 1 else "files"
    return f"{result.file_count} {noun}"

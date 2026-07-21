from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workprint.adapters import available_adapters, get_adapter

EXCLUDED_DIRECTORIES = {
    ".cache",
    ".git",
    ".next",
    ".nuxt",
    ".parcel-cache",
    ".svelte-kit",
    ".turbo",
    ".venv",
    "__pycache__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "tmp",
    "vendor",
    "venv",
}


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
        return len(self.results)

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
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _is_git_repository(root: Path) -> bool:
    return (root / ".git").exists()


def _git_result(root: Path) -> DiscoveryResult | None:
    try:
        metadata = get_adapter("git").discover(root)
    except ValueError:
        return None
    if metadata is None:
        return None
    repository_root = str(metadata.get("repository_root") or root)
    return DiscoveryResult(
        source="git",
        label="Git",
        file_count=1,
        detected_files=(".",),
        metadata={
            "record_count": metadata.get("record_count", 1),
            "repository_root": repository_root,
            "current_branch": metadata.get("current_branch"),
            "is_shallow": metadata.get("is_shallow", False),
        },
    )


def _claude_code_result(root: Path) -> DiscoveryResult | None:
    try:
        metadata = get_adapter("claude-code").discover(root)
    except ValueError:
        return None
    if metadata is None:
        return None
    return DiscoveryResult(
        source="claude-code",
        label="Claude Code",
        file_count=1,
        detected_files=(".",),
        metadata={"record_count": metadata.get("record_count", 0)},
    )


def _claude_cowork_result(root: Path) -> DiscoveryResult | None:
    try:
        metadata = get_adapter("claude-cowork").discover(root)
    except ValueError:
        return None
    if metadata is None:
        return None
    return DiscoveryResult(
        source="claude-cowork",
        label="Claude Cowork",
        file_count=1,
        detected_files=(".",),
        metadata={"record_count": metadata.get("record_count", 0)},
    )


def _claude_desktop_chat_result(root: Path) -> DiscoveryResult | None:
    try:
        metadata = get_adapter("claude-desktop-chat").discover(root)
    except ValueError:
        return None
    if metadata is None:
        return None
    return DiscoveryResult(
        source="claude-desktop-chat",
        label="Claude Desktop Chat",
        file_count=1,
        detected_files=(".",),
        metadata={
            "record_count": metadata.get("record_count", 0),
            "deep_parse": metadata.get("deep_parse", False),
        },
    )


def discover_project(path: str | Path = ".") -> ProjectDiscovery:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise ValueError(f"project path not found: {root}")
    if not root.is_dir():
        raise ValueError(f"project path is not a directory: {root}")

    adapters = [
        get_adapter(adapter_id)
        for adapter_id in available_adapters()
        if adapter_id
        not in {"git", "claude-code", "claude-cowork", "claude-desktop-chat"}
    ]
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

    results_list = [
        DiscoveryResult(
            source=source,
            label=entry["label"],
            file_count=len(entry["files"]),
            detected_files=tuple(sorted(entry["files"])),
            metadata={"record_count": entry["records"]},
        )
        for source, entry in sorted(grouped.items(), key=lambda item: item[0])
    ]
    git_result = _git_result(root)
    if git_result is not None:
        results_list.append(git_result)
    claude_code_result = _claude_code_result(root)
    if claude_code_result is not None:
        results_list.append(claude_code_result)
    claude_cowork_result = _claude_cowork_result(root)
    if claude_cowork_result is not None:
        results_list.append(claude_cowork_result)
    claude_desktop_chat_result = _claude_desktop_chat_result(root)
    if claude_desktop_chat_result is not None:
        results_list.append(claude_desktop_chat_result)
    results = tuple(sorted(results_list, key=lambda item: item.source))

    return ProjectDiscovery(
        root=str(root),
        git_repository=git_result is not None or _is_git_repository(root),
        results=results,
    )


def render_discovery(discovery: ProjectDiscovery) -> str:
    lines: list[str] = ["Project Discovery", ""]

    if discovery.git_repository:
        lines.extend(["✓ Git repository", ""])

    for result in discovery.results:
        lines.append(result.label)
        lines.append(_summary_line(result))
        if result.source == "claude-desktop-chat" and not result.metadata.get(
            "deep_parse", False
        ):
            lines.extend(_claude_desktop_chat_disclosure())
        lines.append("")

    if not discovery.ready:
        lines.extend([
            "No supported evidence found.",
            "",
            "Supported sources:",
            "- ChatGPT",
            "- Claude",
            "- Claude Code",
            "- Claude Cowork",
            "- Claude Desktop Chat",
            "- Google Docs",
            "- Project Notes",
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


def _claude_desktop_chat_disclosure() -> list[str]:
    return [
        "  Workprint can optionally read this cache in more detail using an",
        "  experimental, opt-in parser (not on by default). Before turning it on,",
        "  it helps to know what that trade-off actually is:",
        "  - Without it: Workprint only notes that the cache exists and when it",
        "    last changed. No conversation content is read.",
        "  - With it: Workprint attempts to extract real chat turns, but this",
        "    evidence is account-wide, not specific to this project, because",
        "    claude.ai chat has no concept of a project folder. It skips",
        "    conversations already deleted from claude.ai, but it may still",
        "    find nothing readable even when chat history exists, since some",
        "    entries in this cache have been observed to be unrecoverable.",
        "  - Either way: this stays entirely on your machine. Nothing is",
        "    uploaded, and the output is visible only to whoever runs this",
        "    command.",
    ]


def _summary_line(result: DiscoveryResult) -> str:
    if result.source in {"chatgpt", "claude"}:
        count = result.metadata.get("record_count", 0)
        noun = "conversation" if count == 1 else "conversations"
        return f"{count} {noun}"
    if result.source in {"claude-code", "claude-cowork"}:
        count = result.metadata.get("record_count", 0)
        noun = "session" if count == 1 else "sessions"
        return f"{count} {noun}"
    if result.source == "claude-desktop-chat":
        if result.metadata.get("deep_parse", False):
            count = result.metadata.get("record_count", 0)
            noun = "turn" if count == 1 else "turns"
            return f"{count} candidate conversation {noun} (experimental, account-wide)"
        return "cache detected (deep parsing not enabled)"
    if result.source == "google-docs":
        noun = "document" if result.file_count == 1 else "documents"
        return f"{result.file_count} {noun}"
    if result.source == "project-notes":
        noun = "document" if result.file_count == 1 else "documents"
        return f"{result.file_count} {noun}"
    if result.source == "figma":
        noun = "file" if result.file_count == 1 else "files"
        return f"{result.file_count} {noun}"
    if result.source == "git":
        return "1 local repository"
    noun = "file" if result.file_count == 1 else "files"
    return f"{result.file_count} {noun}"

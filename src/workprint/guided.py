from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TextIO

from workprint.discovery import ProjectDiscovery, discover_project
from workprint.engine import build_investigation
from workprint.multisource import EvidenceInput, load_observations
from workprint.reports import render_json_dict, render_markdown


InputFunc = Callable[[str], str]


class GuidedError(ValueError):
    """Expected guided workflow error that should be shown without a traceback."""


@dataclass(frozen=True)
class GuidedEvidenceFile:
    index: int
    source: str
    label: str
    relative_path: str
    path: Path


@dataclass(frozen=True)
class GuidedOutputs:
    markdown: Path
    json: Path


@dataclass(frozen=True)
class GuidedResult:
    project: str
    selected_files: tuple[GuidedEvidenceFile, ...]
    outputs: GuidedOutputs


@dataclass(frozen=True)
class GuidedOptions:
    path: str | Path | None = None
    include: str | None = None
    project: str | None = None
    output_dir: str | Path | None = None
    markdown: str | Path | None = None
    json: str | Path | None = None
    yes: bool = False


def run_guided(
    *,
    input_func: InputFunc = input,
    output: TextIO = sys.stdout,
    cwd: str | Path = ".",
    options: GuidedOptions | None = None,
) -> int:
    try:
        result = guided_workflow(
            input_func=input_func,
            output=output,
            cwd=cwd,
            options=options,
        )
    except GuidedError as exc:
        print(f"Workprint could not continue: {exc}", file=output)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("", file=output)
        print("Canceled. No files were changed.", file=output)
        return 1

    if result is None:
        return 1
    return 0


def guided_workflow(
    *,
    input_func: InputFunc,
    output: TextIO,
    cwd: str | Path = ".",
    options: GuidedOptions | None = None,
) -> GuidedResult | None:
    options = options or GuidedOptions()
    cwd_path = Path(cwd).expanduser().resolve()
    print("Workprint Guided Investigation", file=output)
    print("", file=output)

    project_root = (
        _option_path(options.path, cwd_path)
        if options.path
        else _prompt_path(
            input_func,
            "Project folder",
            default=cwd_path,
        )
    )
    discovery = discover_project(project_root)
    evidence_files = evidence_files_from_discovery(discovery)

    _render_discovered_evidence(discovery, evidence_files, output)
    if not evidence_files:
        print("No importable evidence was found.", file=output)
        print(
            "Git repositories are shown for awareness, but Git investigation "
            "is not available until a Git evidence adapter exists.",
            file=output,
        )
        return None

    selected_files = (
        select_evidence_files(options.include, evidence_files)
        if options.include is not None
        else _prompt_selection(input_func, evidence_files)
    )
    if not selected_files:
        raise GuidedError("no evidence files were selected")

    project_name = options.project or _prompt_text(
        input_func,
        "Project name",
        default=project_root.name or "Workprint",
    )
    outputs = (
        _option_outputs(options, project_root)
        if _has_output_options(options)
        else _prompt_outputs(input_func, project_root)
    )

    _render_selection_summary(project_name, selected_files, outputs, output)

    overwrite = "ok" if options.yes else _confirm_overwrite(input_func, outputs)
    if overwrite == "paths":
        outputs = _prompt_outputs(input_func, project_root)
        _render_selection_summary(project_name, selected_files, outputs, output)
        overwrite = _confirm_overwrite(input_func, outputs)
    if overwrite == "cancel":
        print("Canceled. No files were changed.", file=output)
        return None

    if not options.yes and not _prompt_yes_no(
        input_func,
        "Generate reports now?",
        default=True,
    ):
        print("Canceled. No files were changed.", file=output)
        return None

    evidence_inputs = [
        EvidenceInput(source=item.source, path=item.path)
        for item in selected_files
    ]
    try:
        observations = load_observations(evidence_inputs)
    except ValueError as exc:
        raise GuidedError(str(exc)) from exc

    investigation = build_investigation(
        project=project_name,
        source_files=[item.path for item in evidence_inputs],
        observations=observations,
    )
    markdown = render_markdown(investigation)
    json_report = json.dumps(
        render_json_dict(investigation),
        indent=2,
        ensure_ascii=False,
    ) + "\n"

    outputs.markdown.parent.mkdir(parents=True, exist_ok=True)
    outputs.json.parent.mkdir(parents=True, exist_ok=True)
    outputs.markdown.write_text(markdown, encoding="utf-8")
    outputs.json.write_text(json_report, encoding="utf-8")

    print("", file=output)
    print("Investigation complete.", file=output)
    print(f"Markdown report: {outputs.markdown}", file=output)
    print(f"JSON report: {outputs.json}", file=output)
    return GuidedResult(
        project=project_name,
        selected_files=tuple(selected_files),
        outputs=outputs,
    )


def _option_path(raw_path: str | Path, default: Path) -> Path:
    path = Path(raw_path).expanduser() if raw_path else default
    path = path.resolve()
    if not path.exists():
        raise GuidedError(f"project folder does not exist: {path}")
    if not path.is_dir():
        raise GuidedError(f"project folder is not a directory: {path}")
    return path


def evidence_files_from_discovery(
    discovery: ProjectDiscovery,
) -> tuple[GuidedEvidenceFile, ...]:
    root = Path(discovery.root)
    files: list[GuidedEvidenceFile] = []
    index = 1
    for result in discovery.results:
        for relative_path in result.detected_files:
            files.append(
                GuidedEvidenceFile(
                    index=index,
                    source=result.source,
                    label=result.label,
                    relative_path=relative_path,
                    path=root / relative_path,
                )
            )
            index += 1
    return tuple(files)


def _render_discovered_evidence(
    discovery: ProjectDiscovery,
    evidence_files: tuple[GuidedEvidenceFile, ...],
    output: TextIO,
) -> None:
    print("Discovered Evidence", file=output)
    print("", file=output)
    if discovery.git_repository:
        print("Git repository: found", file=output)
        print(
            "Git is informational for now and cannot be selected until "
            "Workprint has a Git evidence adapter.",
            file=output,
        )
        print("", file=output)

    if not evidence_files:
        return

    print("Select evidence by number or source ID:", file=output)
    for item in evidence_files:
        print(
            f"[{item.index}] {item.label} ({item.source}) - {item.relative_path}",
            file=output,
        )
    print("", file=output)
    print("Selection examples:", file=output)
    print("- Press Enter to include all files.", file=output)
    print("- Enter numbers such as 1,3 to include specific files.", file=output)
    print(
        "- Enter source IDs such as chatgpt,figma to include whole sources.",
        file=output,
    )
    print(
        "- Prefix with - to remove files or sources, such as -2 or -google-docs.",
        file=output,
    )
    print("", file=output)


def _prompt_path(input_func: InputFunc, label: str, *, default: Path) -> Path:
    raw = input_func(f"{label} [{default}]: ").strip()
    path = Path(raw).expanduser() if raw else default
    path = path.resolve()
    if not path.exists():
        raise GuidedError(f"project folder does not exist: {path}")
    if not path.is_dir():
        raise GuidedError(f"project folder is not a directory: {path}")
    return path


def _prompt_selection(
    input_func: InputFunc,
    evidence_files: tuple[GuidedEvidenceFile, ...],
) -> tuple[GuidedEvidenceFile, ...]:
    prompt = (
        "Evidence to include [all] "
        "(use numbers/source IDs from the list above): "
    )
    raw = input_func(prompt).strip()
    return select_evidence_files(raw, evidence_files)


def select_evidence_files(
    selection: str | None,
    evidence_files: tuple[GuidedEvidenceFile, ...],
) -> tuple[GuidedEvidenceFile, ...]:
    text = (selection or "").strip()
    if not text or text.lower() == "all":
        return evidence_files
    if text.lower() in {"none", "cancel"}:
        return ()

    tokens = [
        token.strip()
        for token in text.replace(";", ",").split(",")
        if token.strip()
    ]
    positive = [token for token in tokens if not token.startswith("-")]
    selected = set()

    if positive:
        for token in positive:
            selected.update(_match_selection_token(token, evidence_files))
    else:
        selected.update(item.index for item in evidence_files)

    for token in tokens:
        if token.startswith("-"):
            selected.difference_update(
                _match_selection_token(token[1:], evidence_files)
            )

    return tuple(item for item in evidence_files if item.index in selected)


def _match_selection_token(
    token: str,
    evidence_files: tuple[GuidedEvidenceFile, ...],
) -> set[int]:
    normalized = token.strip().lower()
    if not normalized:
        raise GuidedError("empty selection token")
    if normalized.isdigit():
        index = int(normalized)
        if any(item.index == index for item in evidence_files):
            return {index}
        raise GuidedError(f"unknown evidence number: {token}")

    matches = {
        item.index
        for item in evidence_files
        if item.source.lower() == normalized
        or item.label.lower() == normalized
    }
    if not matches:
        raise GuidedError(f"unknown evidence source or number: {token}")
    return matches


def _prompt_text(input_func: InputFunc, label: str, *, default: str) -> str:
    raw = input_func(f"{label} [{default}]: ").strip()
    return raw or default


def _prompt_outputs(input_func: InputFunc, project_root: Path) -> GuidedOutputs:
    default_dir = project_root / "workprint-output"
    output_dir = _prompt_output_path(
        input_func,
        "Output directory",
        default=default_dir,
    )
    markdown = _prompt_output_path(
        input_func,
        "Markdown report",
        default=output_dir / "report.md",
    )
    json_report = _prompt_output_path(
        input_func,
        "JSON report",
        default=output_dir / "report.json",
    )
    return GuidedOutputs(markdown=markdown, json=json_report)


def _has_output_options(options: GuidedOptions) -> bool:
    return any([options.output_dir, options.markdown, options.json])


def _option_outputs(options: GuidedOptions, project_root: Path) -> GuidedOutputs:
    output_dir = (
        Path(options.output_dir).expanduser().resolve()
        if options.output_dir
        else project_root / "workprint-output"
    )
    markdown = (
        Path(options.markdown).expanduser().resolve()
        if options.markdown
        else output_dir / "report.md"
    )
    json_report = (
        Path(options.json).expanduser().resolve()
        if options.json
        else output_dir / "report.json"
    )
    return GuidedOutputs(markdown=markdown, json=json_report)


def _render_selection_summary(
    project_name: str,
    selected_files: tuple[GuidedEvidenceFile, ...],
    outputs: GuidedOutputs,
    output: TextIO,
) -> None:
    print("", file=output)
    print("Selection Summary", file=output)
    print("", file=output)
    print(f"Project: {project_name}", file=output)
    counts: dict[str, int] = {}
    for item in selected_files:
        counts[item.source] = counts.get(item.source, 0) + 1
    print("Selected sources:", file=output)
    for source, count in sorted(counts.items()):
        noun = "file" if count == 1 else "files"
        print(f"- {source}: {count} {noun}", file=output)
    print("Selected files:", file=output)
    for item in selected_files:
        print(f"- [{item.index}] {item.source}: {item.relative_path}", file=output)
    print(f"Markdown report: {outputs.markdown}", file=output)
    print(f"JSON report: {outputs.json}", file=output)
    print("", file=output)


def _prompt_output_path(input_func: InputFunc, label: str, *, default: Path) -> Path:
    raw = input_func(f"{label} [{default}]: ").strip()
    return (Path(raw).expanduser() if raw else default).resolve()


def _confirm_overwrite(input_func: InputFunc, outputs: GuidedOutputs) -> str:
    markdown_exists = outputs.markdown.exists()
    json_exists = outputs.json.exists()
    if not markdown_exists and not json_exists:
        return "ok"
    if markdown_exists and json_exists:
        raw = input_func(
            "Both output files already exist. "
            "Overwrite both, choose new paths, or cancel? [cancel]: "
        ).strip().lower()
        if raw in {"overwrite", "overwrite both", "o", "yes", "y"}:
            return "ok"
        if raw in {"new", "paths", "choose new paths", "n"}:
            return "paths"
        return "cancel"

    existing = outputs.markdown if markdown_exists else outputs.json
    if _prompt_yes_no(
        input_func,
        f"Output file already exists: {existing}. Replace it?",
        default=False,
    ):
        return "ok"
    return "cancel"


def _prompt_yes_no(input_func: InputFunc, label: str, *, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input_func(f"{label} {suffix}: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes"}

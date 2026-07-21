"use client";

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import type { ChangeEvent, DragEvent, RefObject } from "react";
import Image from "next/image";
import { ClaudeSessionEvidence } from "@/components/claude-session-evidence";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { EvidenceDrawer } from "@/components/evidence-drawer";
import { GitTimeline } from "@/components/git-timeline";
import { ProjectFileEvidence } from "@/components/project-file-evidence";
import { SourceStatusList } from "@/components/source-status-list";
import {
  pickActiveDiscovery,
  type ActiveDiscovery,
} from "@/lib/active-discovery";
import {
  chooseProjectFolderNative,
  isElectronBridgeAvailable,
} from "@/lib/electron-bridge";
import {
  claudeCodeDiscoveryClaim,
  claudeCoworkDiscoveryClaim,
  claudeDesktopChatDiscoveryClaim,
  sessionDiscoverySupport,
  type ClaudeLocalSummary,
  type ClaudeLocalSummaryResponse,
} from "@/lib/claude-local-summary";
import type { GitSummary, GitSummaryResponse } from "@/lib/git-summary";
import {
  summarizeLocalProject,
  type LocalProjectFile,
  type LocalProjectSummary,
} from "@/lib/local-project-sources";
import type { ProjectFileEvidenceFact } from "@/lib/project-file-evidence";
import {
  REASONING_PROVIDERS,
  type ReasoningProviderId,
  type ReasoningSuccess,
  type ReasoningFailure,
} from "@/lib/provider-reasoning";
import { evidenceItems, insight, projectSources } from "@/lib/sample-data";

type Screen = "start" | "sources" | "investigating" | "discoveries";
type SelectionMode = "sample" | "local";

type InvestigateResult = {
  project: string;
  sources: string[];
  markdown: string;
  json: unknown;
  playbookMarkdown: string;
};

type InvestigateResponse =
  | (InvestigateResult & { ok: true })
  | { ok: false; error: { code: string; message: string } };

type ProviderReasoningResponse = ReasoningSuccess | ReasoningFailure;

type BrowserFileSystemEntry = {
  isDirectory: boolean;
  isFile: boolean;
  name: string;
};

type BrowserFileSystemFileEntry = BrowserFileSystemEntry & {
  file: (successCallback: (file: File) => void, errorCallback?: () => void) => void;
};

type BrowserFileSystemDirectoryEntry = BrowserFileSystemEntry & {
  createReader: () => {
    readEntries: (
      successCallback: (entries: BrowserFileSystemEntry[]) => void,
      errorCallback?: () => void,
    ) => void;
  };
};

type DataTransferItemWithEntry = {
  webkitGetAsEntry?: () => BrowserFileSystemEntry | null;
};

const stages = [
  "Reading your project",
  "Finding important moments",
  "Preparing your discoveries",
];

export function WorkprintApp() {
  const [screen, setScreen] = useState<Screen>("start");
  const [projectAnswer, setProjectAnswer] = useState("");
  const [stageIndex, setStageIndex] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("sample");
  const [localProject, setLocalProject] = useState<LocalProjectSummary | null>(null);
  const [projectStatusMessage, setProjectStatusMessage] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [repositoryPath, setRepositoryPath] = useState("");
  const [gitSummary, setGitSummary] = useState<GitSummary | null>(null);
  const [gitSummaryError, setGitSummaryError] = useState("");
  const [gitSummaryLoading, setGitSummaryLoading] = useState(false);
  const [claudeSummary, setClaudeSummary] = useState<ClaudeLocalSummary | null>(null);
  const [claudeSummaryError, setClaudeSummaryError] = useState("");
  const [claudeSummaryLoading, setClaudeSummaryLoading] = useState(false);
  const [desktopChatDeepParseRequested, setDesktopChatDeepParseRequested] =
    useState(false);
  const [choosingProjectFolder, setChoosingProjectFolder] = useState(false);
  const [investigateResult, setInvestigateResult] = useState<InvestigateResult | null>(
    null,
  );
  const [investigateError, setInvestigateError] = useState("");
  const [investigateLoading, setInvestigateLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<ReasoningProviderId | "">("");
  const [providerApiKey, setProviderApiKey] = useState("");
  const [providerKeyHelpOpen, setProviderKeyHelpOpen] = useState(false);
  const [providerReasoningError, setProviderReasoningError] = useState("");
  const [providerReasoningLoading, setProviderReasoningLoading] = useState(false);
  const [providerReasoningResult, setProviderReasoningResult] =
    useState<ReasoningSuccess | null>(null);
  const [providerDiscovery, setProviderDiscovery] = useState<ActiveDiscovery | null>(
    null,
  );
  // window.workprintElectron is set once by the Electron preload script
  // before any page script runs and never changes afterward, so this only
  // needs a snapshot read, not a subscription -- useSyncExternalStore
  // gives a hydration-safe way to read it (server snapshot always false,
  // since window does not exist there) without the extra render pass an
  // effect-based useState would cause.
  const nativeFolderPickerAvailable = useSyncExternalStore(
    () => () => {},
    isElectronBridgeAvailable,
    () => false,
  );
  const [projectFileFacts, setProjectFileFacts] = useState<ProjectFileEvidenceFact[]>([]);
  const [projectFileSession, setProjectFileSession] = useState(0);
  const startHeadingRef = useRef<HTMLHeadingElement>(null);
  const sourcesHeadingRef = useRef<HTMLHeadingElement>(null);
  const investigatingHeadingRef = useRef<HTMLHeadingElement>(null);
  const discoveriesHeadingRef = useRef<HTMLHeadingElement>(null);
  const projectInputRef = useRef<HTMLInputElement>(null);
  const projectSummaryRef = useRef<HTMLDivElement>(null);
  const chooseProjectButtonRef = useRef<HTMLButtonElement>(null);
  const evidenceButtonRef = useRef<HTMLButtonElement>(null);
  const progressTimersRef = useRef<number[]>([]);

  const visibleSources = localProject?.sources ?? projectSources;
  const activeDiscovery =
    providerDiscovery ??
    pickActiveDiscovery({
      gitSummary,
      claudeSummary,
      projectFileFacts,
      sample: insight,
    });
  const activeClaim = activeDiscovery.claim;
  const activeSupport = activeDiscovery.support;
  const activeUnknown = activeDiscovery.unknown;
  const activeConfidence = activeDiscovery.confidence;
  const hasRealEvidence = Boolean(gitSummary) || Boolean(claudeSummary) || projectFileFacts.length > 0;
  const realEvidenceItems = [
    ...(gitSummary ? gitEvidenceItems(gitSummary) : []),
    ...projectFileEvidenceItems(projectFileFacts),
    ...(claudeSummary ? claudeSessionEvidenceItems(claudeSummary) : []),
  ];
  const providerKeyHelp = providerKeyHelpFor(selectedProvider);
  const activeEvidence = hasRealEvidence
    ? filterEvidenceForDiscovery(realEvidenceItems, activeDiscovery)
    : evidenceItems;
  const readyCount = useMemo(
    () => visibleSources.filter((source) => source.status !== "unsupported").length,
    [visibleSources],
  );
  const currentStage = stages[Math.min(stageIndex, stages.length - 1)];

  useEffect(() => {
    return () => {
      progressTimersRef.current.forEach((timer) => window.clearTimeout(timer));
      progressTimersRef.current = [];
    };
  }, []);

  useEffect(() => {
    const headingRefs: Record<Screen, RefObject<HTMLHeadingElement | null>> = {
      start: startHeadingRef,
      sources: sourcesHeadingRef,
      investigating: investigatingHeadingRef,
      discoveries: discoveriesHeadingRef,
    };

    window.requestAnimationFrame(() => {
      headingRefs[screen].current?.focus({ preventScroll: true });
    });
  }, [screen]);

  function clearProgressTimers() {
    progressTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    progressTimersRef.current = [];
  }

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function goTo(nextScreen: Screen) {
    clearProgressTimers();
    setScreen(nextScreen);
    scrollToTop();
  }

  function startInvestigation() {
    clearProgressTimers();
    setStageIndex(0);
    setScreen("investigating");
    scrollToTop();

    progressTimersRef.current = stages.map((_, index) =>
      window.setTimeout(() => setStageIndex(index), 350 + index * 850),
    );
    progressTimersRef.current.push(window.setTimeout(() => {
      setStageIndex(stages.length);
      goTo("discoveries");
    }, 3200));

    // Kick off the local report build in parallel with the stage animation.
    // The downloadable report remains useful, but the Discoveries headline
    // must come from provider-assisted reasoning rather than a local
    // mechanical fallback.
    //
    // Also read Git/Claude evidence directly here rather than relying on
    // the user having separately clicked "Read Git metadata"/"Read Claude
    // sessions" first -- those are easy-to-miss buttons elsewhere on the
    // sources screen, and this "Investigate" button has no guard
    // requiring them. Without this, gitSummary/claudeSummary stay null
    // for anyone who just connects a project and clicks the one obvious
    // CTA, so gitSummary/claudeSummary stay null for anyone who just
    // connects a project and clicks the one obvious button.
    if (repositoryPath.trim()) {
      void runInvestigation();
      void readGitSummary();
      void readClaudeSummary();
    }
  }

  function openSampleReport() {
    setProjectAnswer("Sample product prototype");
    goTo("discoveries");
  }

  function openProjectPicker() {
    if (projectInputRef.current) {
      projectInputRef.current.value = "";
    }
    projectInputRef.current?.click();
  }

  function selectSampleMode() {
    setSelectionMode("sample");
    setLocalProject(null);
    setGitSummary(null);
    setGitSummaryError("");
    setRepositoryPath("");
    setProjectFileFacts([]);
    setProjectFileSession((current) => current + 1);
    setClaudeSummary(null);
    setClaudeSummaryError("");
    setDesktopChatDeepParseRequested(false);
    setInvestigateResult(null);
    setInvestigateError("");
    clearProviderReasoning();
    setProjectStatusMessage("Showing sample project places.");
    window.requestAnimationFrame(() => {
      chooseProjectButtonRef.current?.focus();
    });
  }

  function removeLocalProject() {
    setLocalProject(null);
    setSelectionMode("sample");
    setGitSummary(null);
    setGitSummaryError("");
    setRepositoryPath("");
    setProjectFileFacts([]);
    setProjectFileSession((current) => current + 1);
    setClaudeSummary(null);
    setClaudeSummaryError("");
    setDesktopChatDeepParseRequested(false);
    setInvestigateResult(null);
    setInvestigateError("");
    clearProviderReasoning();
    setProjectStatusMessage("Removed the selected project. Sample project places are shown.");
    if (projectInputRef.current) {
      projectInputRef.current.value = "";
    }
    window.requestAnimationFrame(() => {
      chooseProjectButtonRef.current?.focus();
    });
  }

  function applyLocalFiles(files: LocalProjectFile[], fallbackFolderName: string) {
    if (files.length === 0) {
      setProjectStatusMessage("No local project files were found.");
      return;
    }

    const summary = summarizeLocalProject(files, fallbackFolderName);
    setLocalProject(summary);
    setSelectionMode("local");
    setGitSummary(null);
    setGitSummaryError("");
    setProjectFileFacts([]);
    setProjectFileSession((current) => current + 1);
    setClaudeSummary(null);
    setClaudeSummaryError("");
    setDesktopChatDeepParseRequested(false);
    setInvestigateResult(null);
    setInvestigateError("");
    clearProviderReasoning();
    setProjectStatusMessage(
      `Found ${summary.fileCount} ${summary.fileCount === 1 ? "file" : "files"} in ${summary.folderName}.`,
    );
    window.requestAnimationFrame(() => {
      projectSummaryRef.current?.focus({ preventScroll: true });
    });
  }

  function handleProjectInputChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []).map((file) => ({
      file,
      name: file.name,
      path: file.webkitRelativePath || file.name,
      size: file.size,
    }));

    applyLocalFiles(files, "Selected project");
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setDragActive(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setDragActive(false);
    }
  }

  async function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);

    const droppedFiles = await getDroppedProjectFiles(event.dataTransfer);
    const fallbackFolderName =
      Array.from(event.dataTransfer.items)
        .map((item) => (item as DataTransferItemWithEntry).webkitGetAsEntry?.()?.name)
        .find(Boolean) ?? "Dropped project";

    applyLocalFiles(droppedFiles, fallbackFolderName);
  }

  async function readGitSummary() {
    setGitSummaryLoading(true);
    setGitSummaryError("");
    setGitSummary(null);

    try {
      const response = await fetch("/api/git-summary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repositoryPath,
          commitLimit: 5,
        }),
      });
      const payload = (await response.json()) as GitSummaryResponse;

      if (!response.ok || !payload.ok) {
        setGitSummaryError(
          payload.ok
            ? "Workprint could not read Git metadata for this repository."
            : payload.error.message,
        );
        return;
      }

      setGitSummary(payload);
      setProjectStatusMessage(
        `Git records ${payload.summary.total_commit_count} ${payload.summary.total_commit_count === 1 ? "commit" : "commits"}.`,
      );
    } catch {
      setGitSummaryError("Workprint could not reach the local Git summary route.");
    } finally {
      setGitSummaryLoading(false);
    }
  }

  async function readClaudeSummary() {
    setClaudeSummaryLoading(true);
    setClaudeSummaryError("");
    setClaudeSummary(null);

    try {
      const response = await fetch("/api/claude-local-summary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectPath: repositoryPath,
          includeDesktopChatDeepParse: desktopChatDeepParseRequested,
        }),
      });
      const payload = (await response.json()) as ClaudeLocalSummaryResponse;

      if (!response.ok || !payload.ok) {
        setClaudeSummaryError(
          payload.ok
            ? "Workprint could not read local Claude session evidence."
            : payload.error.message,
        );
        return;
      }

      setClaudeSummary(payload);
      const sessionCount =
        payload.claude_code.session_count + payload.claude_cowork.session_count;
      setProjectStatusMessage(
        `Found ${sessionCount} local Claude ${sessionCount === 1 ? "session" : "sessions"}.`,
      );
    } catch {
      setClaudeSummaryError(
        "Workprint could not reach the local Claude session summary route.",
      );
    } finally {
      setClaudeSummaryLoading(false);
    }
  }

  async function chooseProjectFolderNativeDialog() {
    setChoosingProjectFolder(true);
    try {
      const path = await chooseProjectFolderNative();
      if (path) {
        setRepositoryPath(path);
      }
    } finally {
      setChoosingProjectFolder(false);
    }
  }

  async function runInvestigation() {
    setInvestigateLoading(true);
    setInvestigateError("");
    setInvestigateResult(null);

    const projectName =
      projectAnswer.trim() || localProject?.folderName || repositoryPath || "Workprint Project";

    try {
      const response = await fetch("/api/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          projectPath: repositoryPath,
          projectName,
          includeDesktopChatDeepParse: desktopChatDeepParseRequested,
        }),
      });
      const payload = (await response.json()) as InvestigateResponse;

      if (!response.ok || !payload.ok) {
        setInvestigateError(
          payload.ok
            ? "Workprint could not generate a report for this project."
            : payload.error.message,
        );
        return;
      }

      setInvestigateResult(payload);
    } catch {
      setInvestigateError("Workprint could not reach the local investigation route.");
    } finally {
      setInvestigateLoading(false);
    }
  }

  async function runProviderReasoning() {
    setProviderReasoningError("");
    setProviderReasoningResult(null);
    setProviderDiscovery(null);

    if (!selectedProvider) {
      setProviderReasoningError("Choose OpenAI, Claude, or Gemini first.");
      return;
    }

    if (!providerApiKey.trim()) {
      setProviderReasoningError("Enter the API key for the provider you chose.");
      return;
    }

    if (realEvidenceItems.length === 0) {
      setProviderReasoningError(
        "Add evidence before asking a provider to reason over it.",
      );
      return;
    }

    setProviderReasoningLoading(true);

    try {
      const response = await fetch("/api/provider-reasoning", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: selectedProvider,
          apiKey: providerApiKey,
          project:
            projectAnswer.trim() || localProject?.folderName || repositoryPath || "Workprint Project",
          evidence: realEvidenceItems,
        }),
      });
      const payload = (await response.json()) as ProviderReasoningResponse;

      if (!response.ok || !payload.ok) {
        setProviderReasoningError(
          payload.ok
            ? "Workprint could not reason over this evidence."
            : payload.error.message,
        );
        return;
      }

      setProviderReasoningResult(payload);
      setProviderDiscovery({
        claim: payload.insight.claim,
        evidenceIds: payload.insight.evidence_ids,
        support: payload.insight.explanation,
        unknown: payload.insight.unknowns,
        confidence: payload.insight.confidence,
        kind: "insight",
      });
    } catch {
      setProviderReasoningError(
        "Workprint could not reach the provider reasoning route.",
      );
    } finally {
      setProviderReasoningLoading(false);
    }
  }

  function clearProviderReasoning() {
    setProviderApiKey("");
    setProviderReasoningError("");
    setProviderReasoningResult(null);
    setProviderReasoningLoading(false);
    setProviderDiscovery(null);
  }

  function downloadReport(format: "markdown" | "json" | "playbook") {
    if (!investigateResult) {
      return;
    }
    const safeName = investigateResult.project.replace(/[^a-z0-9-]+/gi, "-").toLowerCase() || "report";
    if (format === "markdown") {
      downloadTextFile(`${safeName}.md`, investigateResult.markdown, "text/markdown");
    } else if (format === "playbook") {
      downloadTextFile(
        `${safeName}-ai-fluency-playbook.md`,
        investigateResult.playbookMarkdown,
        "text/markdown",
      );
    } else {
      downloadTextFile(
        `${safeName}.json`,
        JSON.stringify(investigateResult.json, null, 2),
        "application/json",
      );
    }
  }

  function closeDrawer() {
    setDrawerOpen(false);
    window.requestAnimationFrame(() => {
      evidenceButtonRef.current?.focus();
    });
  }

  // In Electron, the native folder connection below is strictly more
  // capable than the browser file picker (it unlocks Git and Claude
  // history), so it renders first there; in a plain browser it stays
  // second since it is only a manual path field. See localHistorySection.
  const fileEvidenceSection = (
    <>
      <div className="mt-10 rounded-[32px] border border-dashed border-[var(--line)] bg-[var(--surface-soft)] p-8">
        <p className="text-xl font-semibold">
          {localProject ? "Selected project" : "Add files for evidence"}
        </p>
        <p className="mt-3 max-w-2xl leading-7 text-[var(--muted)]">
          Files remain on your device. For most files, Workprint only
          looks at filenames, folder paths, extensions, and counts --
          but a ChatGPT export, a Google Docs export, or a Figma file
          export are read as real evidence. See what&rsquo;s recognized below.
        </p>
        <details className="mt-4 max-w-2xl rounded-2xl border border-[var(--line)] p-4 text-sm leading-6 text-[var(--muted)]">
          <summary className="cursor-pointer font-semibold text-[var(--foreground)]">
            What files does this recognize?
          </summary>
          <div className="mt-3 space-y-2">
            <p>
              <strong className="text-[var(--foreground)]">ChatGPT:</strong>{" "}
              the official{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                conversations.json
              </code>{" "}
              export from ChatGPT&rsquo;s data export feature.
            </p>
            <p>
              <strong className="text-[var(--foreground)]">
                Google Docs:
              </strong>{" "}
              an exported{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                .md
              </code>
              ,{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                .txt
              </code>
              , or{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                .json
              </code>{" "}
              file. A{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                .md
              </code>{" "}
              or{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                .txt
              </code>{" "}
              export needs a first line of{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                workprint-source: google-docs
              </code>{" "}
              to be recognized -- without it, Workprint treats the file
              as a plain project file instead.
            </p>
            <p>
              <strong className="text-[var(--foreground)]">Figma:</strong>{" "}
              the raw Figma REST API file response (the JSON you get
              back from{" "}
              <code className="rounded bg-[var(--surface-soft)] px-1 py-0.5">
                GET /v1/files/:key
              </code>{" "}
              with a personal access token) -- not a file you can
              produce from Figma&rsquo;s own export menu. A real
              &ldquo;Connect Figma&rdquo; flow that does this for you
              isn&rsquo;t built yet.
            </p>
          </div>
        </details>
        <div
          className={`mt-6 rounded-[24px] border border-dashed p-6 transition ${
            dragActive
              ? "border-[var(--accent)] bg-[var(--accent-soft)]"
              : "border-[var(--line)]"
          }`}
          data-local-project-dropzone
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <p className="font-semibold">
            Drop project files here, or add them with the button.
          </p>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
            Drag-and-drop is optional. The folder picker is the keyboard
            path and asks for access only after you choose it.
          </p>
          <input
            aria-describedby="folder-picker-help"
            className="sr-only"
            id="project-folder-input"
            multiple
            onChange={handleProjectInputChange}
            ref={projectInputRef}
            tabIndex={-1}
            type="file"
            {...{ webkitdirectory: "", directory: "" }}
          />
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              className="rounded-full bg-[var(--accent)] px-6 py-4 font-semibold text-white transition hover:bg-[var(--accent-strong)]"
              onClick={openProjectPicker}
              ref={chooseProjectButtonRef}
              type="button"
            >
              Add files for evidence
            </button>
            <button
              className="rounded-full border border-[var(--line)] px-6 py-4 font-semibold"
              onClick={selectSampleMode}
              type="button"
            >
              Use sample project
            </button>
          </div>
          <p
            className="mt-4 text-sm leading-6 text-[var(--muted)]"
            id="folder-picker-help"
          >
            Local collection does not upload or persist file contents. If you
            later choose an AI reasoning provider, selected excerpts and
            metadata must be sent to that provider for processing.
          </p>
        </div>
        <p aria-live="polite" className="sr-only" role="status">
          {projectStatusMessage}
        </p>
      </div>
      <section className="mt-10 rounded-[28px] bg-[var(--surface-soft)] p-6 sm:p-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div ref={projectSummaryRef} tabIndex={-1}>
            <h2 className="text-2xl font-semibold tracking-[-0.03em]">
              {localProject ? localProject.folderName : "Sample project places"}
            </h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {localProject
                ? `${localProject.fileCount} ${localProject.fileCount === 1 ? "file" : "files"} visible to the browser. ${readyCount} source categories found.`
                : `${readyCount} sample places are readable. One item shows a recovery state.`}
            </p>
          </div>
          <p className="max-w-sm text-sm leading-6 text-[var(--muted)]">
            {selectionMode === "local"
              ? "Found means recognized by local metadata, not analyzed."
              : "Found means readable sample evidence, not a complete project history."}
          </p>
        </div>
        <SourceStatusList sources={visibleSources} />
        {localProject ? (
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-semibold"
              onClick={openProjectPicker}
              type="button"
            >
              Replace project
            </button>
            <button
              className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-semibold text-[var(--muted)]"
              onClick={removeLocalProject}
              type="button"
            >
              Remove project
            </button>
          </div>
        ) : null}
      </section>
      {localProject ? (
        <ProjectFileEvidence
          files={localProject.files}
          key={projectFileSession}
          onFactsChange={setProjectFileFacts}
        />
      ) : null}
      <details className="mt-6 max-w-3xl text-sm leading-6 text-[var(--muted)]">
        <summary className="cursor-pointer font-semibold text-[var(--foreground)]">
          What these sources may miss
        </summary>
        <p className="mt-3">
          Static files may omit revision history. Repository metadata does
          not prove who wrote every line. Conversation exports show only
          the captured conversation.
        </p>
      </details>
    </>
  );

  const localHistorySection = (
    <section
      aria-labelledby="local-history-heading"
      className="mt-10 max-w-3xl rounded-[24px] bg-[var(--surface-soft)] p-6"
    >
      <h2
        className="text-xl font-semibold tracking-[-0.02em]"
        id="local-history-heading"
      >
        Local project history
      </h2>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
        {nativeFolderPickerAvailable
          ? "Connect your project folder to read Git commit history and local Claude session evidence directly from your computer. This works only while Workprint is running as a desktop app. You can also add specific files below for evidence Workprint can show inline."
          : "Choosing a browser folder above does not grant this access. Reading Git history or local Claude sessions works only while Workprint is running on your computer."}
      </p>
      {nativeFolderPickerAvailable ? (
        <div className="mt-5">
          <button
            className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-strong)]"
            disabled={choosingProjectFolder}
            onClick={chooseProjectFolderNativeDialog}
            type="button"
          >
            {choosingProjectFolder
              ? "Waiting for folder…"
              : "Connect Project Folder"}
          </button>
          {repositoryPath ? (
            <p className="mt-3 rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--foreground)]">
              Selected: <span className="break-words">{repositoryPath}</span>
            </p>
          ) : (
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              No folder chosen yet.
            </p>
          )}
        </div>
      ) : (
        <>
          <label
            className="mt-5 block text-sm font-semibold"
            htmlFor="repository-path"
          >
            Local project path
          </label>
          <input
            className="mt-2 w-full rounded-full border border-[var(--line)] bg-[var(--surface)] px-5 py-3 text-sm"
            id="repository-path"
            onChange={(event) => setRepositoryPath(event.target.value)}
            placeholder="/Users/you/path/to/project"
            type="text"
            value={repositoryPath}
          />
        </>
      )}
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-strong)]"
          disabled={gitSummaryLoading || !repositoryPath.trim()}
          onClick={readGitSummary}
          type="button"
        >
          {gitSummaryLoading ? "Reading Git metadata" : "Read Git metadata"}
        </button>
        <button
          className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-semibold"
          disabled={claudeSummaryLoading || !repositoryPath.trim()}
          onClick={readClaudeSummary}
          type="button"
        >
          {claudeSummaryLoading
            ? "Reading Claude sessions"
            : "Read Claude sessions"}
        </button>
      </div>
      {gitSummaryError ? (
        <p className="mt-4 rounded-2xl bg-[var(--danger-soft)] p-4 text-sm leading-6 text-[var(--danger)]">
          {gitSummaryError}
        </p>
      ) : null}
      {gitSummary ? (
        <div className="mt-4 rounded-2xl border border-[var(--line)] p-4 text-sm leading-6 text-[var(--muted)]">
          <p className="font-semibold text-[var(--foreground)]">
            Found Git metadata for {gitSummary.repository.name}.
          </p>
          <p className="mt-2">
            Git records {gitSummary.summary.total_commit_count}{" "}
            {gitSummary.summary.total_commit_count === 1 ? "commit" : "commits"}.
            {gitSummary.repository.current_branch
              ? ` Current branch: ${gitSummary.repository.current_branch}.`
              : " Current branch not available."}
          </p>
        </div>
      ) : null}
      <details className="mt-5 rounded-2xl border border-[var(--line)] p-4 text-sm leading-6 text-[var(--muted)]">
        <summary className="cursor-pointer font-semibold text-[var(--foreground)]">
          Claude Desktop chat: read in more detail? (experimental)
        </summary>
        <div className="mt-3 space-y-2">
          <p>
            Workprint can optionally read your local Claude Desktop
            chat cache in more detail using an experimental, opt-in
            parser. Before turning it on, it helps to know the
            trade-off:
          </p>
          <p>
            <strong className="text-[var(--foreground)]">
              Without it:
            </strong>{" "}
            Workprint only notes that the cache exists and when it last
            changed. No conversation content is read.
          </p>
          <p>
            <strong className="text-[var(--foreground)]">
              With it:
            </strong>{" "}
            Workprint attempts to extract real chat turns, but this
            evidence is account-wide, not specific to this project,
            because claude.ai chat has no concept of a project folder.
          </p>
          <p>
            <strong className="text-[var(--foreground)]">
              Local evidence reading:
            </strong>{" "}
            this step stays on your machine. If you later choose an AI
            reasoning provider, selected evidence will be sent to that
            provider only after a separate confirmation.
          </p>
        </div>
        <label className="mt-4 flex items-center gap-2 text-sm font-semibold text-[var(--foreground)]">
          <input
            checked={desktopChatDeepParseRequested}
            onChange={(event) =>
              setDesktopChatDeepParseRequested(event.target.checked)
            }
            type="checkbox"
          />
          Enable detailed reading for the next &ldquo;Read Claude
          sessions&rdquo;
        </label>
      </details>
      {claudeSummaryError ? (
        <p className="mt-4 rounded-2xl bg-[var(--danger-soft)] p-4 text-sm leading-6 text-[var(--danger)]">
          {claudeSummaryError}
        </p>
      ) : null}
      {claudeSummary ? (
        <div className="mt-4 space-y-2 rounded-2xl border border-[var(--line)] p-4 text-sm leading-6 text-[var(--muted)]">
          <p className="font-semibold text-[var(--foreground)]">
            {claudeCodeDiscoveryClaim(claudeSummary.claude_code)}
          </p>
          <p className="font-semibold text-[var(--foreground)]">
            {claudeCoworkDiscoveryClaim(claudeSummary.claude_cowork)}
          </p>
          <p className="font-semibold text-[var(--foreground)]">
            {claudeDesktopChatDiscoveryClaim(claudeSummary.claude_desktop_chat)}
          </p>
        </div>
      ) : null}
    </section>
  );

  return (
    <>
      <main
        aria-hidden={drawerOpen}
        className="min-h-screen px-5 py-6 text-[var(--foreground)] sm:px-8 lg:px-12"
        inert={drawerOpen}
      >
      <header className="mx-auto flex max-w-6xl items-center justify-between">
        <button
          className="flex items-center gap-2 text-lg font-semibold tracking-[-0.02em]"
          onClick={() => goTo("start")}
          type="button"
        >
          <Image
            alt=""
            className="h-6 w-9"
            height={24}
            src="/brand/workprint-trace-color.svg"
            width={36}
          />
          Workprint
        </button>
        {screen !== "start" ? (
          <button
            className="text-sm font-semibold text-[var(--muted)]"
            onClick={() => goTo("start")}
            type="button"
          >
            Start over
          </button>
        ) : null}
      </header>

      {screen === "start" ? (
        <section
          aria-labelledby="start-heading"
          className="mx-auto flex min-h-[calc(100vh-96px)] max-w-4xl flex-col justify-center py-16"
        >
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            Warm Investigator
          </p>
          <h1
            className="max-w-4xl text-5xl font-semibold leading-[1.02] tracking-[-0.055em] sm:text-7xl"
            id="start-heading"
            ref={startHeadingRef}
            tabIndex={-1}
          >
            Turn project evidence into AI-assisted insights you can inspect.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)]">
            Workprint gathers the evidence, sends selected evidence to the AI
            reasoning provider you choose, and keeps every insight tied to what
            the evidence can actually support.
          </p>
          <label
            className="mt-12 block text-lg font-semibold"
            htmlFor="project-answer"
          >
            What are you working on?
          </label>
          <input
            className="mt-4 w-full rounded-full border border-[var(--line)] bg-[var(--surface-soft)] px-6 py-4 text-lg shadow-sm"
            id="project-answer"
            onChange={(event) => setProjectAnswer(event.target.value)}
            placeholder="A product prototype, design sprint, client project..."
            type="text"
            value={projectAnswer}
          />
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              className="rounded-full bg-[var(--accent)] px-6 py-4 font-semibold text-white transition hover:bg-[var(--accent-strong)]"
              disabled={!projectAnswer.trim()}
              onClick={() => goTo("sources")}
              type="button"
            >
              Add where the work happened
            </button>
            <button
              className="rounded-full border border-[var(--line)] px-6 py-4 font-semibold"
              onClick={openSampleReport}
              type="button"
            >
              View a sample report
            </button>
          </div>
          {!projectAnswer.trim() ? (
            <p className="mt-4 text-sm text-[var(--muted)]">
              Tell Workprint what you are working on to continue.
            </p>
          ) : null}
          <details className="mt-8 max-w-2xl text-sm leading-6 text-[var(--muted)]">
            <summary className="cursor-pointer font-semibold text-[var(--foreground)]">
              What Workprint can show
            </summary>
            <p className="mt-3">
              Workprint uses your project history and a chosen AI reasoning
              provider to produce clearer findings. It should show which
              evidence was sent, which provider processed it, why each claim is
              supported, and what the evidence cannot determine. It does not
              assign contribution percentages or claim authorship.
            </p>
          </details>
        </section>
      ) : null}

      {screen === "sources" ? (
        <section
          aria-labelledby="sources-heading"
          className="mx-auto max-w-5xl py-16 sm:py-24"
        >
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            Add where the work happened
          </p>
          <h1
            className="max-w-3xl text-4xl font-semibold tracking-[-0.04em] sm:text-6xl"
            id="sources-heading"
            ref={sourcesHeadingRef}
            tabIndex={-1}
          >
            Give Workprint the places where the work happened.
          </h1>
          {nativeFolderPickerAvailable ? (
            <>
              {localHistorySection}
              {fileEvidenceSection}
            </>
          ) : (
            <>
              {fileEvidenceSection}
              {localHistorySection}
            </>
          )}
          <div className="mt-10 flex flex-wrap gap-3">
            <button
              className="rounded-full bg-[var(--accent)] px-6 py-4 font-semibold text-white transition hover:bg-[var(--accent-strong)]"
              onClick={startInvestigation}
              type="button"
            >
              Investigate
            </button>
            <button
              className="rounded-full border border-[var(--line)] px-6 py-4 font-semibold text-[var(--muted)]"
              disabled
              type="button"
            >
              Add another place later
            </button>
          </div>
        </section>
      ) : null}

      {screen === "investigating" ? (
        <section
          aria-labelledby="investigating-heading"
          className="mx-auto flex min-h-[calc(100vh-96px)] max-w-3xl flex-col justify-center py-16"
        >
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            Investigating
          </p>
          <h1
            className="text-4xl font-semibold tracking-[-0.04em] sm:text-6xl"
            id="investigating-heading"
            ref={investigatingHeadingRef}
            tabIndex={-1}
          >
            Workprint is reading your project history.
          </h1>
          <p
            aria-atomic="true"
            aria-live="polite"
            className="sr-only"
            role="status"
          >
            {currentStage}
          </p>
          <ol className="mt-12 space-y-6">
            {stages.map((stage, index) => {
              const complete = stageIndex > index;
              const active = stageIndex === index;
              return (
                <li
                  className="flex items-center gap-4 text-xl text-[var(--muted)]"
                  key={stage}
                >
                  <span
                    aria-hidden="true"
                    className={`h-4 w-4 rounded-full border-2 ${
                      complete || active
                        ? "border-[var(--accent)] bg-[var(--accent)]"
                        : "border-current"
                    }`}
                  />
                  <span
                    className={
                      complete || active
                        ? "font-semibold text-[var(--foreground)]"
                        : ""
                    }
                  >
                    {stage}
                  </span>
                </li>
              );
            })}
          </ol>
          <p className="mt-10 max-w-2xl text-sm leading-6 text-[var(--muted)]">
            Workprint is organizing evidence, not filling gaps with guesses.
          </p>
        </section>
      ) : null}

      {screen === "discoveries" ? (
        <section
          aria-labelledby="discoveries-heading"
          className="mx-auto max-w-6xl py-16 sm:py-24"
        >
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            {activeDiscovery.kind === "provider_needed"
              ? "AI reasoning needed"
              : activeDiscovery.kind === "insight"
              ? "First supported insight"
              : "What's connected so far"}
          </p>
          <div className="max-w-5xl">
            <h1
              className="text-5xl font-semibold leading-[1.04] tracking-[-0.055em] sm:text-7xl"
              id="discoveries-heading"
              ref={discoveriesHeadingRef}
              tabIndex={-1}
            >
              {activeClaim}
            </h1>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              {activeDiscovery.kind !== "provider_needed" ? (
                <ConfidenceIndicator label={activeConfidence} />
              ) : null}
              {investigateLoading && !providerDiscovery ? (
                <span className="text-sm text-[var(--muted)]">
                  Investigating further&hellip;
                </span>
              ) : null}
            </div>
            <section className="mt-10 max-w-3xl border-l-2 border-[var(--accent)] pl-6">
              <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                {activeDiscovery.kind === "provider_needed"
                  ? "What happens before an insight"
                  : "Why Workprint believes this"}
              </h2>
              <p className="mt-4 text-lg leading-8 text-[var(--muted)]">
                {activeSupport}
              </p>
              <p className="mt-5 rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6 text-[var(--muted)]">
                <strong className="text-[var(--foreground)]">
                  What Workprint cannot determine:
                </strong>{" "}
                {activeUnknown}
              </p>
            </section>
            {activeDiscovery.kind === "provider_needed" ? (
              <section className="mt-10 max-w-4xl rounded-[28px] border border-[var(--line)] bg-[var(--surface-soft)] p-6 sm:p-8">
                <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                  Choose a reasoning provider
                </h2>
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                  OpenAI, Claude, and Gemini are equal choices. Workprint does
                  not choose a default provider. Your API key is used for this
                  request only and is not saved by Workprint.
                </p>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {REASONING_PROVIDERS.map((provider) => (
                    <button
                      aria-pressed={selectedProvider === provider.id}
                      className={`rounded-2xl border p-4 text-left transition ${
                        selectedProvider === provider.id
                          ? "border-[var(--accent)] bg-[var(--accent-soft)]"
                          : "border-[var(--line)] bg-[var(--surface)]"
                      }`}
                      key={provider.id}
                      onClick={() => {
                        setSelectedProvider(provider.id);
                        setProviderReasoningError("");
                        setProviderReasoningResult(null);
                        setProviderDiscovery(null);
                      }}
                      type="button"
                    >
                      <p className="font-semibold">{provider.label}</p>
                      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                        {selectedProvider === provider.id
                          ? "Selected for this report."
                          : "Available with your own API key."}
                      </p>
                    </button>
                  ))}
                </div>
                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <label className="block text-sm font-semibold" htmlFor="provider-key">
                    API key for selected provider
                  </label>
                  <button
                    aria-expanded={providerKeyHelpOpen}
                    className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1 text-xs font-semibold text-[var(--accent)] transition hover:border-[var(--accent)]"
                    onClick={() => setProviderKeyHelpOpen((open) => !open)}
                    type="button"
                  >
                    What is this?
                  </button>
                </div>
                {providerKeyHelpOpen ? (
                  <div className="mt-3 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 text-sm leading-6 text-[var(--muted)]">
                    <p>
                      <strong className="text-[var(--foreground)]">
                        Do not enter your account password.
                      </strong>{" "}
                      An API key is a separate access key you create in your{" "}
                      {providerKeyHelp.name} account so Workprint can ask that
                      provider to analyze the evidence you approve.
                    </p>
                    <p className="mt-3">
                      Workprint uses the key for this request only. It is not
                      saved by Workprint.
                    </p>
                    <p className="mt-3">
                      <strong className="text-[var(--foreground)]">
                        Bounded evidence
                      </strong>{" "}
                      means Workprint sends a limited packet: selected excerpts,
                      evidence IDs, source names, and basic metadata. It does not
                      send your whole project folder, hidden environment files,
                      API keys, passwords, or files you did not select.
                    </p>
                    <p className="mt-3">
                      Some excerpts may contain sensitive information if that
                      information appears in evidence you selected. Review the
                      selected evidence before sending it to a provider.
                    </p>
                    <p className="mt-3">
                      Get a key from{" "}
                      <a
                        className="font-semibold text-[var(--accent)] underline underline-offset-4"
                        href={providerKeyHelp.url}
                        rel="noreferrer"
                        target="_blank"
                      >
                        {providerKeyHelp.linkLabel}
                      </a>
                      . You can delete or rotate the key in your provider account
                      later.
                    </p>
                  </div>
                ) : null}
                <input
                  autoComplete="off"
                  className="mt-2 w-full rounded-full border border-[var(--line)] bg-[var(--surface)] px-5 py-3 text-sm"
                  id="provider-key"
                  onChange={(event) => setProviderApiKey(event.target.value)}
                  placeholder="Paste an API key, not your account password"
                  type="password"
                  value={providerApiKey}
                />
                <p className="mt-5 text-sm leading-6 text-[var(--muted)]">
                  Selected evidence will leave your device and be processed by
                  the provider you choose. Workprint sends only a bounded
                  evidence packet: selected excerpts and metadata, not your whole
                  project folder. Provider processing is governed by that
                  provider&apos;s terms, policies, and account settings. Make
                  sure you have permission to process this evidence with the
                  selected provider.
                </p>
                <button
                  className="mt-5 rounded-full bg-[var(--accent)] px-6 py-4 font-semibold text-white transition hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={
                    providerReasoningLoading ||
                    !selectedProvider ||
                    !providerApiKey.trim() ||
                    realEvidenceItems.length === 0
                  }
                  onClick={runProviderReasoning}
                  type="button"
                >
                  {providerReasoningLoading
                    ? "Reasoning with provider..."
                    : "Analyze selected evidence"}
                </button>
                {providerReasoningError ? (
                  <p className="mt-4 rounded-2xl bg-[var(--danger-soft)] p-4 text-sm leading-6 text-[var(--danger)]">
                    {providerReasoningError}
                  </p>
                ) : null}
                {providerReasoningResult ? (
                  <div className="mt-4 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 text-sm leading-6 text-[var(--muted)]">
                    <p className="font-semibold text-[var(--foreground)]">
                      {providerReasoningResult.providerLabel} processed{" "}
                      {providerReasoningResult.packet.evidenceCount} selected{" "}
                      {providerReasoningResult.packet.evidenceCount === 1
                        ? "evidence item"
                        : "evidence items"}
                      .
                    </p>
                    <p className="mt-2">
                      Workprint validated cited evidence IDs and attribution
                      boundaries before showing the insight.
                    </p>
                    <p className="mt-2">
                      Provider model: {providerReasoningResult.model}.
                    </p>
                    {providerReasoningResult.packet.truncated ? (
                      <p className="mt-2">
                        Some evidence was omitted to stay under the 30,000-token
                        packet ceiling.
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </section>
            ) : null}
            {projectFileFacts.length > 0 ? (
              <section className="mt-10 max-w-4xl border-t border-[var(--line)] pt-8">
                <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                  Project files read in this browser
                </h2>
                <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                  Workprint read {projectFileFacts.length} selected{" "}
                  {projectFileFacts.length === 1 ? "file" : "files"} after
                  confirmation and recorded only filenames, paths, byte sizes,
                  line counts, and bounded plain-text excerpts.
                </p>
                <div className="mt-5 space-y-4">
                  {projectFileFacts.slice(0, 3).map((fact) => (
                    <article
                      className="border-l-2 border-[var(--line)] pl-5"
                      key={fact.path}
                    >
                      <p className="break-words font-semibold">{fact.path}</p>
                      <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
                        {fact.manifestType ?? (fact.extension || "No extension")};{" "}
                        {fact.size} {fact.size === 1 ? "byte" : "bytes"};{" "}
                        {fact.lineCount}{" "}
                        {fact.lineCount === 1 ? "line" : "lines"}.
                      </p>
                    </article>
                  ))}
                </div>
                {projectFileFacts.length > 3 ? (
                  <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                    {projectFileFacts.length - 3} additional read{" "}
                    {projectFileFacts.length - 3 === 1 ? "file is" : "files are"}{" "}
                    available in the evidence drawer.
                  </p>
                ) : null}
                <p className="mt-5 rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6 text-[var(--muted)]">
                  These file facts do not determine authorship, effort,
                  ownership, importance, correctness, completeness,
                  originality, or AI involvement.
                </p>
              </section>
            ) : null}
            {gitSummary ? <GitTimeline summary={gitSummary} /> : null}
            {claudeSummary ? (
              <ClaudeSessionEvidence summary={claudeSummary} />
            ) : null}
            <div className="mt-8">
              <button
                className="rounded-full border border-[var(--line)] px-6 py-4 font-semibold"
                onClick={() => setDrawerOpen(true)}
                ref={evidenceButtonRef}
                type="button"
              >
                See evidence
              </button>
            </div>
          </div>

          <div className="my-16 max-w-4xl border-t border-[var(--line)] pt-10">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
              Full report
            </p>
            <div className="mt-5 rounded-2xl border border-[var(--line)] bg-[var(--surface-soft)] p-5 text-sm leading-6 text-[var(--muted)]">
              <p className="font-semibold text-[var(--foreground)]">
                AI reasoning is the analysis step
              </p>
              <p className="mt-2">
                Workprint is being designed around a chosen AI reasoning
                provider. When provider reasoning is enabled, Workprint will
                send a bounded evidence packet to that provider for processing:
                selected excerpts, evidence IDs, source labels, file names,
                relative paths, and relevant metadata.
              </p>
              <p className="mt-2">
                Workprint should never send your whole project folder, blocked
                sensitive files, credentials, keys, tokens, certificates, or
                files you did not select. Provider reasoning will be governed by
                the provider you choose and your account settings with that
                provider.
              </p>
              <p className="mt-2 font-semibold text-[var(--foreground)]">
                Make sure you have permission to process the selected evidence
                with that provider. Workprint&apos;s license covers Workprint
                software; it does not grant rights to upload client, employer,
                collaborator, confidential, copyrighted, regulated, or
                proprietary evidence to an AI provider.
              </p>
            </div>
            <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
              {repositoryPath
                ? "Workprint will read every evidence source found for this project and build a full report, including findings, a timeline, confidence, and what the evidence cannot determine."
                : "Choose a local project above first — the full report is generated from the same local project path used for Git and Claude session evidence."}
            </p>
            <button
              className="mt-5 rounded-full bg-[var(--accent)] px-6 py-4 font-semibold text-white transition hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
              disabled={investigateLoading || !repositoryPath.trim()}
              onClick={runInvestigation}
              type="button"
            >
              {investigateLoading ? "Building report…" : "Build full report"}
            </button>
            {investigateError ? (
              <p className="mt-4 max-w-2xl rounded-2xl bg-[var(--danger-soft)] p-4 text-sm leading-6 text-[var(--danger)]">
                {investigateError}
              </p>
            ) : null}
          </div>

          {investigateResult ? (
            <section className="max-w-4xl border-t border-[var(--line)] pt-10">
              <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                Report for {investigateResult.project}
              </h2>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                Built from {investigateResult.sources.length}{" "}
                {investigateResult.sources.length === 1 ? "source" : "sources"}:{" "}
                {investigateResult.sources.join(", ")}.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-strong)]"
                  onClick={() => downloadReport("markdown")}
                  type="button"
                >
                  Download as Markdown
                </button>
                <button
                  className="rounded-full border border-[var(--line)] px-5 py-3 text-sm font-semibold"
                  onClick={() => downloadReport("json")}
                  type="button"
                >
                  Download as JSON
                </button>
              </div>
              <div className="mt-6 rounded-[24px] border border-dashed border-[var(--line)] bg-[var(--surface-soft)] p-6">
                <p className="text-lg font-semibold">AI Fluency Playbook Worksheet</p>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  Organized under Anthropic&rsquo;s AI Fluency Framework
                  (Delegation, Description, Discernment, Diligence). Workprint
                  fills in real evidence from this project; you fill in the
                  reflection and next-time columns yourself &mdash; or bring
                  this into a Claude chat to think through it together.
                  Workprint does not score or rate AI fluency.
                </p>
                <button
                  className="mt-4 rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-strong)]"
                  onClick={() => downloadReport("playbook")}
                  type="button"
                >
                  Download Playbook Worksheet
                </button>
              </div>
              <details className="mt-6 rounded-[24px] bg-[var(--surface-soft)] p-6">
                <summary className="cursor-pointer font-semibold text-[var(--foreground)]">
                  Preview the report
                </summary>
                <pre className="mt-4 max-h-[32rem] overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-[var(--surface)] p-4 text-xs leading-6 text-[var(--foreground)]">
                  {investigateResult.markdown}
                </pre>
              </details>
            </section>
          ) : null}
        </section>
      ) : null}
      </main>
          <EvidenceDrawer
        evidence={activeEvidence}
        isSample={!hasRealEvidence}
        onClose={closeDrawer}
        open={drawerOpen}
      />
    </>
  );
}

function downloadTextFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function providerKeyHelpFor(provider: ReasoningProviderId | "") {
  if (provider === "claude") {
    return {
      linkLabel: "Anthropic Console API keys",
      name: "Claude",
      url: "https://console.anthropic.com/settings/keys",
    };
  }

  if (provider === "gemini") {
    return {
      linkLabel: "Google AI Studio API keys",
      name: "Gemini",
      url: "https://aistudio.google.com/app/apikey",
    };
  }

  return {
    linkLabel: "OpenAI API keys",
    name: "OpenAI",
    url: "https://platform.openai.com/api-keys",
  };
}

function gitEvidenceItems(summary: GitSummary) {
  if (summary.recent_commits.length === 0) {
    return [
      {
        id: "git-empty",
        source: "Git",
        title: "Git repository has no recorded commits",
        excerpt: `Repository: ${summary.repository.name}`,
        supports:
          "This supports the Git discovery because Workprint read local Git metadata and found zero commits.",
        doesNotProve:
          "It does not prove no work happened outside Git, and it does not determine authorship, effort, ownership, intent, or AI involvement.",
      },
    ];
  }

  return summary.recent_commits.map((commit) => ({
    id: `git-${commit.commit_sha}`,
    source: "Git",
    title: `${commit.abbreviated_sha}: ${commit.message}`,
    excerpt: `The commit author field contains "${commit.author}" and Git records timestamp ${commit.committed_at}.`,
    supports:
      `This supports the Git discovery because the repository records commit ${commit.commit_sha}: "${commit.message}".`,
    doesNotProve:
      "It does not prove verified identity, authorship, ownership, effort, contribution, intent, or human-versus-AI involvement.",
  }));
}

function projectFileEvidenceItems(facts: ProjectFileEvidenceFact[]) {
  return facts.map((fact) => ({
    id: `project-file-${fact.path}`,
    source: "Project file",
    title: fact.path,
    excerpt: fact.excerpt || "(Empty file)",
    supports:
      `This supports the file evidence section because ${fact.path} says: "${firstMeaningfulLine(fact.excerpt) || "(empty file)"}"`,
    doesNotProve:
      "It does not prove authorship, effort, ownership, importance, correctness, originality, completeness, intent, or AI involvement.",
  }));
}

function firstMeaningfulLine(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line && line !== "...");
}

function filterEvidenceForDiscovery(
  items: ReturnType<typeof projectFileEvidenceItems>,
  discovery: ActiveDiscovery,
) {
  if (!discovery.evidenceIds || discovery.evidenceIds.length === 0) {
    return items;
  }

  const evidenceIds = new Set(discovery.evidenceIds);
  const matchingItems = items.filter((item) => evidenceIds.has(item.id));

  return matchingItems.length > 0 ? matchingItems : items;
}

function claudeSessionEvidenceItems(summary: ClaudeLocalSummary) {
  const items: {
    id: string;
    source: string;
    title: string;
    excerpt: string;
    supports: string;
    doesNotProve: string;
  }[] = [];

  if (summary.claude_code.turn_count > 0) {
    items.push({
      id: "claude-code",
      source: "Claude Code",
      title: claudeCodeDiscoveryClaim(summary.claude_code),
      excerpt: sessionDiscoverySupport(summary.claude_code),
      supports:
        `This supports the Claude Code discovery because Workprint read ${summary.claude_code.session_count} local ${summary.claude_code.session_count === 1 ? "session" : "sessions"} and recorded ${summary.claude_code.turn_count} structural turns.`,
      doesNotProve:
        "It does not prove effort, ownership, value, contribution, or the content of any conversation.",
    });
  }

  if (summary.claude_cowork.turn_count > 0) {
    items.push({
      id: "claude-cowork",
      source: "Claude Cowork",
      title: claudeCoworkDiscoveryClaim(summary.claude_cowork),
      excerpt: sessionDiscoverySupport(summary.claude_cowork),
      supports:
        `This supports the Claude Cowork discovery because Workprint read ${summary.claude_cowork.session_count} local ${summary.claude_cowork.session_count === 1 ? "session" : "sessions"} and recorded ${summary.claude_cowork.turn_count} structural turns.`,
      doesNotProve:
        "It does not prove effort, ownership, value, contribution, or the content of any conversation.",
    });
  }

  if (summary.claude_desktop_chat.cache_detected) {
    items.push({
      id: "claude-desktop-chat",
      source: "Claude Desktop Chat",
      title: claudeDesktopChatDiscoveryClaim(summary.claude_desktop_chat),
      excerpt:
        summary.claude_desktop_chat.deep_parse_found_turns &&
        summary.claude_desktop_chat.turns
          ? sessionDiscoverySupport(summary.claude_desktop_chat.turns)
          : "Presence-only: no conversation content was read.",
      supports:
        "This supports that a local Claude Desktop chat cache exists on this machine.",
      doesNotProve:
        "It does not prove this evidence relates to this specific project, since claude.ai chat has no project-folder concept, and it does not prove effort, ownership, value, or contribution.",
    });
  }

  return items;
}

async function getDroppedProjectFiles(dataTransfer: DataTransfer) {
  const entries = Array.from(dataTransfer.items)
    .map(getEntryFromDataTransferItem)
    .filter((entry): entry is BrowserFileSystemEntry => entry !== null);

  if (entries.length === 0) {
    return Array.from(dataTransfer.files).map((file) => ({
      file,
      name: file.name,
      path: file.webkitRelativePath || file.name,
      size: file.size,
    }));
  }

  const entryFiles = await Promise.all(
    entries.map((entry) => readEntryMetadata(entry)),
  );

  return entryFiles.flat();
}

function getEntryFromDataTransferItem(
  item: DataTransferItem,
): BrowserFileSystemEntry | null {
  const itemWithEntry = item as unknown as DataTransferItemWithEntry;
  return itemWithEntry.webkitGetAsEntry?.() ?? null;
}

async function readEntryMetadata(
  entry: BrowserFileSystemEntry,
  parentPath = "",
): Promise<LocalProjectFile[]> {
  const entryPath = `${parentPath}${entry.name}`;

  if (entry.isFile) {
    return new Promise((resolve) => {
      (entry as BrowserFileSystemFileEntry).file(
        (file) => resolve([{
          file,
          name: file.name,
          path: entryPath,
          size: file.size,
        }]),
        () => resolve([]),
      );
    });
  }

  if (!entry.isDirectory) {
    return [];
  }

  const directoryEntry = entry as BrowserFileSystemDirectoryEntry;
  const reader = directoryEntry.createReader();
  const childEntries = await readAllDirectoryEntries(reader);
  const childFiles = await Promise.all(
    childEntries.map((childEntry) =>
      readEntryMetadata(childEntry, `${entryPath}/`),
    ),
  );

  return childFiles.flat();
}

async function readAllDirectoryEntries(
  reader: ReturnType<BrowserFileSystemDirectoryEntry["createReader"]>,
) {
  const entries: BrowserFileSystemEntry[] = [];

  while (true) {
    const batch = await new Promise<BrowserFileSystemEntry[]>((resolve) => {
      reader.readEntries(resolve, () => resolve([]));
    });

    if (batch.length === 0) {
      return entries;
    }

    entries.push(...batch);
  }
}

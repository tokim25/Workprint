"use client";

import { useMemo, useState } from "react";
import {
  describeFileKind,
  getProjectFileCandidates,
  PROJECT_FILE_EVIDENCE_LIMITS,
  readProjectFileEvidence,
  type ProjectFileEvidenceFact,
  type ProjectFileEvidenceStatus,
} from "@/lib/project-file-evidence";
import type { LocalProjectFile } from "@/lib/local-project-sources";

type ProjectFileEvidenceProps = {
  files: LocalProjectFile[];
  onFactsChange: (facts: ProjectFileEvidenceFact[]) => void;
};

const statusLabels: Record<ProjectFileEvidenceStatus, string> = {
  eligible: "Eligible and unread",
  read: "Read",
  excluded: "Excluded",
  unsupported: "Unsupported",
  blocked_sensitive: "Blocked as sensitive",
  blocked_oversized: "Blocked as oversized",
};

const statusStyles: Record<ProjectFileEvidenceStatus, string> = {
  eligible: "bg-[var(--warning-soft)] text-[var(--warning)]",
  read: "bg-[var(--accent-soft)] text-[var(--accent-strong)]",
  excluded: "bg-[var(--surface)] text-[var(--muted)]",
  unsupported: "bg-[var(--danger-soft)] text-[var(--danger)]",
  blocked_sensitive: "bg-[var(--danger-soft)] text-[var(--danger)]",
  blocked_oversized: "bg-[var(--danger-soft)] text-[var(--danger)]",
};

export function ProjectFileEvidence({
  files,
  onFactsChange,
}: ProjectFileEvidenceProps) {
  const [excludedPaths, setExcludedPaths] = useState<Set<string>>(new Set());
  const [readFacts, setReadFacts] = useState<ProjectFileEvidenceFact[]>([]);
  const [readStatus, setReadStatus] = useState("");
  const candidates = useMemo(() => getProjectFileCandidates(files), [files]);
  const readPaths = useMemo(
    () => new Set(readFacts.map((fact) => fact.path)),
    [readFacts],
  );
  const eligibleCandidates = candidates.filter((item) => item.status === "eligible");
  const visibleCandidates = candidates.filter((item, index) => {
    if (item.status !== "unsupported") {
      return true;
    }

    return index < 12;
  });
  const hiddenUnsupportedCount = candidates.length - visibleCandidates.length;
  const selectedEligibleCount = eligibleCandidates.filter(
    (item) => !excludedPaths.has(item.path),
  ).length;

  async function readSelectedFiles() {
    setReadStatus("Reading eligible project files in this browser.");
    const facts = await readProjectFileEvidence(candidates, excludedPaths);
    setReadFacts(facts);
    onFactsChange(facts);
    setReadStatus(
      `Read ${facts.length} ${facts.length === 1 ? "file" : "files"} in this browser.`,
    );
  }

  function toggleExcluded(path: string) {
    setReadFacts([]);
    onFactsChange([]);
    setReadStatus("File choices changed. Read project files again to refresh facts.");
    setExcludedPaths((current) => {
      const next = new Set(current);

      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }

      return next;
    });
  }

  return (
    <section
      aria-labelledby="project-file-evidence-heading"
      className="mt-8 rounded-[24px] border border-[var(--line)] bg-[var(--surface)] p-6"
    >
      <div className="max-w-3xl">
        <h2
          className="text-xl font-semibold tracking-[-0.02em]"
          id="project-file-evidence-heading"
        >
          Project file evidence
        </h2>
        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
          Workprint can read a small set of selected text and manifest files
          after you confirm. Source-code files are counted by metadata only in
          this milestone.
        </p>
      </div>

      <div className="mt-5 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <Limit label="Eligible files" value={PROJECT_FILE_EVIDENCE_LIMITS.maxEligibleFiles} />
        <Limit label="Bytes per file" value={PROJECT_FILE_EVIDENCE_LIMITS.maxBytesPerFile} />
        <Limit label="Total bytes read" value={PROJECT_FILE_EVIDENCE_LIMITS.maxTotalBytesRead} />
        <Limit label="Excerpt size" value={`${PROJECT_FILE_EVIDENCE_LIMITS.maxExcerptLines} lines`} />
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-strong)]"
          disabled={selectedEligibleCount === 0}
          onClick={readSelectedFiles}
          type="button"
        >
          Read selected project files
        </button>
        <p className="self-center text-sm leading-6 text-[var(--muted)]">
          {selectedEligibleCount} eligible{" "}
          {selectedEligibleCount === 1 ? "file" : "files"} selected.
        </p>
      </div>
      <p aria-live="polite" className="sr-only" role="status">
        {readStatus}
      </p>

      {visibleCandidates.length === 0 ? (
        <p className="mt-6 rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6 text-[var(--muted)]">
          No eligible project files were found. Workprint still recognizes
          project structure from filenames and source categories.
        </p>
      ) : (
        <>
          <ul className="mt-6 space-y-3">
            {visibleCandidates.map((item) => {
            const excluded = excludedPaths.has(item.path);
            const status = readPaths.has(item.path)
              ? "read"
              : excluded
                ? "excluded"
                : item.status;
            const canExclude = item.status === "eligible";

            return (
              <li
                className="rounded-2xl border border-[var(--line)] p-4"
                key={item.path}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="break-words font-semibold text-[var(--foreground)]">
                      {item.path}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
                      {describeFileKind(item)}.{" "}
                      {item.size === null
                        ? "Byte size unavailable."
                        : `${item.size} ${item.size === 1 ? "byte" : "bytes"}.`}{" "}
                      {item.reason}
                    </p>
                  </div>
                  <span
                    className={`w-fit rounded-full px-3 py-1 text-sm font-semibold ${statusStyles[status]}`}
                  >
                    {statusLabels[status]}
                  </span>
                </div>
                {canExclude ? (
                  <label className="mt-3 flex w-fit items-center gap-2 text-sm font-semibold">
                    <input
                      checked={excluded}
                      onChange={() => toggleExcluded(item.path)}
                      type="checkbox"
                    />
                    Exclude this file
                  </label>
                ) : null}
              </li>
            );
            })}
          </ul>
          {hiddenUnsupportedCount > 0 ? (
            <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
              {hiddenUnsupportedCount} additional unsupported{" "}
              {hiddenUnsupportedCount === 1 ? "file is" : "files are"} counted
              by metadata but not shown in this preview.
            </p>
          ) : null}
        </>
      )}

      {readFacts.length > 0 ? (
        <section
          aria-labelledby="project-file-facts-heading"
          className="mt-8 border-t border-[var(--line)] pt-6"
        >
          <h3
            className="text-lg font-semibold tracking-[-0.02em]"
            id="project-file-facts-heading"
          >
            Factual file notes
          </h3>
          <div className="mt-4 space-y-5">
            {readFacts.map((fact) => (
              <article key={fact.path}>
                <p className="break-words font-semibold">{fact.path}</p>
                <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
                  {fact.manifestType ?? (fact.extension || "No extension")};{" "}
                  {fact.size} {fact.size === 1 ? "byte" : "bytes"};{" "}
                  {fact.lineCount} {fact.lineCount === 1 ? "line" : "lines"}.
                </p>
                <pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6 text-[var(--foreground)]">
                  {fact.excerpt || "(Empty file)"}
                </pre>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

function Limit({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl bg-[var(--surface-soft)] p-4">
      <p className="font-semibold text-[var(--foreground)]">{value}</p>
      <p className="mt-1 text-[var(--muted)]">{label}</p>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { RefObject } from "react";
import { ConfidenceIndicator } from "@/components/confidence-indicator";
import { EvidenceDrawer } from "@/components/evidence-drawer";
import { SourceStatusList } from "@/components/source-status-list";
import { evidenceItems, insight, projectSources } from "@/lib/sample-data";

type Screen = "start" | "sources" | "investigating" | "discoveries";

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
  const startHeadingRef = useRef<HTMLHeadingElement>(null);
  const sourcesHeadingRef = useRef<HTMLHeadingElement>(null);
  const investigatingHeadingRef = useRef<HTMLHeadingElement>(null);
  const discoveriesHeadingRef = useRef<HTMLHeadingElement>(null);
  const evidenceButtonRef = useRef<HTMLButtonElement>(null);
  const progressTimersRef = useRef<number[]>([]);

  const readyCount = useMemo(
    () => projectSources.filter((source) => source.status !== "unsupported").length,
    [],
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
  }

  function openSampleReport() {
    setProjectAnswer("Sample product prototype");
    goTo("discoveries");
  }

  function closeDrawer() {
    setDrawerOpen(false);
    window.requestAnimationFrame(() => {
      evidenceButtonRef.current?.focus();
    });
  }

  return (
    <>
      <main
        aria-hidden={drawerOpen}
        className="min-h-screen px-5 py-6 text-[var(--foreground)] sm:px-8 lg:px-12"
        inert={drawerOpen}
      >
      <header className="mx-auto flex max-w-6xl items-center justify-between">
        <button
          className="text-lg font-semibold tracking-[-0.02em]"
          onClick={() => goTo("start")}
          type="button"
        >
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
            See what you did, what AI did, and how the work came together.
          </h1>
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
              Workprint uses your project history to support every conclusion
              and clearly marks what it cannot determine. It does not assign
              contribution percentages or claim authorship.
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
          <div className="mt-10 rounded-[32px] border border-dashed border-[var(--line)] bg-[var(--surface-soft)] p-8">
            <p className="text-xl font-semibold">Sample project places</p>
            <p className="mt-3 max-w-2xl leading-7 text-[var(--muted)]">
              This prototype uses sample evidence. It does not upload files,
              parse folders, call APIs, or inspect your computer.
            </p>
          </div>
          <section className="mt-10 rounded-[28px] bg-[var(--surface-soft)] p-6 sm:p-8">
            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                  Added places
                </h2>
                <p className="mt-2 text-sm text-[var(--muted)]">
                  {readyCount} sample places are readable. One item shows a
                  recovery state.
                </p>
              </div>
              <p className="max-w-sm text-sm leading-6 text-[var(--muted)]">
                Ready means readable evidence, not a complete project history.
              </p>
            </div>
            <SourceStatusList sources={projectSources} />
          </section>
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
            First supported insight
          </p>
          <div className="max-w-5xl">
            <h1
              className="text-5xl font-semibold leading-[1.04] tracking-[-0.055em] sm:text-7xl"
              id="discoveries-heading"
              ref={discoveriesHeadingRef}
              tabIndex={-1}
            >
              {insight.claim}
            </h1>
            <div className="mt-8">
              <ConfidenceIndicator label={insight.confidence} />
            </div>
            <section className="mt-10 max-w-3xl border-l-2 border-[var(--accent)] pl-6">
              <h2 className="text-2xl font-semibold tracking-[-0.03em]">
                Why Workprint believes this
              </h2>
              <p className="mt-4 text-lg leading-8 text-[var(--muted)]">
                {insight.support}
              </p>
              <p className="mt-5 rounded-2xl bg-[var(--surface-soft)] p-4 text-sm leading-6 text-[var(--muted)]">
                <strong className="text-[var(--foreground)]">
                  What Workprint cannot determine:
                </strong>{" "}
                {insight.unknown}
              </p>
            </section>
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

          <div className="my-16 border-t border-[var(--line)] pt-10">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
              Continue to report
            </p>
            <button
              className="mt-5 rounded-full bg-[var(--accent)] px-6 py-4 font-semibold text-white transition hover:bg-[var(--accent-strong)]"
              type="button"
            >
              View full report
            </button>
          </div>

          <section className="grid gap-4 lg:grid-cols-4">
            {[
              "What happened",
              "Human, AI, and joint activity",
              "Decisions and timeline",
              "Confidence and gaps",
            ].map((section) => (
              <div className="border-t border-[var(--line)] pt-4" key={section}>
                <h3 className="font-semibold">{section}</h3>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  Report section preview. The full report keeps evidence
                  references and unknowns visible.
                </p>
              </div>
            ))}
          </section>

          <details className="mt-12 max-w-3xl rounded-[24px] bg-[var(--surface-soft)] p-6">
            <summary className="cursor-pointer font-semibold">
              Export report
            </summary>
            <div className="mt-5 space-y-4 text-sm leading-6 text-[var(--muted)]">
              <p>
                Export is represented for the prototype only. No file is
                generated in this milestone.
              </p>
              <p>
                Exports should include evidence references, source limitations,
                confidence, and unknowns by default.
              </p>
            </div>
          </details>
        </section>
      ) : null}
      </main>
      <EvidenceDrawer
        evidence={evidenceItems}
        onClose={closeDrawer}
        open={drawerOpen}
      />
    </>
  );
}

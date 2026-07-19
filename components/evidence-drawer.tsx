"use client";

import { useEffect, useRef } from "react";
import type { EvidenceItem } from "@/lib/sample-data";

type EvidenceDrawerProps = {
  evidence: EvidenceItem[];
  isSample: boolean;
  open: boolean;
  onClose: () => void;
};

export function EvidenceDrawer({
  evidence,
  isSample,
  open,
  onClose,
}: EvidenceDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      closeButtonRef.current?.focus();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const drawer = drawerRef.current;

      if (!drawer) {
        return;
      }

      const focusableElements = drawer.querySelectorAll<HTMLElement>(
        [
          "a[href]",
          "button:not([disabled])",
          "textarea:not([disabled])",
          "input:not([disabled])",
          "select:not([disabled])",
          "details summary",
          "[tabindex]:not([tabindex='-1'])",
        ].join(","),
      );

      const focusable = Array.from(focusableElements).filter(
        (element) =>
          !element.hasAttribute("disabled") &&
          element.getAttribute("aria-hidden") !== "true",
      );

      if (focusable.length === 0) {
        event.preventDefault();
        drawer.focus();
        return;
      }

      const firstElement = focusable[0];
      const lastElement = focusable[focusable.length - 1];
      const activeElement = document.activeElement;

      if (!drawer.contains(activeElement)) {
        event.preventDefault();
        if (event.shiftKey) {
          lastElement.focus();
        } else {
          firstElement.focus();
        }
        return;
      }

      if (event.shiftKey && activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
        return;
      }

      if (!event.shiftKey && activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  return (
    <div
      aria-describedby="evidence-description"
      aria-labelledby="evidence-title"
      aria-modal="true"
      className="fixed inset-0 z-30 bg-black/30 p-4 backdrop-blur-sm"
      ref={drawerRef}
      role="dialog"
      tabIndex={-1}
    >
      <div className="ml-auto flex h-full w-full max-w-2xl flex-col overflow-hidden rounded-[28px] bg-[var(--surface)] shadow-2xl">
        <div className="flex items-start justify-between gap-6 border-b border-[var(--line)] p-6 sm:p-8">
          <div>
            <p
              className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]"
            >
              {isSample ? "Sample evidence" : "Evidence"}
            </p>
            <p className="sr-only" id="evidence-description">
              {isSample
                ? "This drawer lists the sample evidence behind the first supported insight and explains what the evidence does not prove."
                : "This drawer lists the evidence Workprint read from your local project and explains what the evidence does not prove."}
            </p>
            <h2
              className="text-3xl font-semibold tracking-[-0.03em] text-[var(--foreground)]"
              id="evidence-title"
            >
              Why Workprint believes this
            </h2>
          </div>
          <button
            className="rounded-full border border-[var(--line)] px-4 py-2 text-sm font-semibold text-[var(--foreground)]"
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            Close
          </button>
        </div>
        <div className="space-y-6 overflow-auto p-6 sm:p-8">
          {evidence.map((item) => (
            <article
              className="border-b border-[var(--line)] pb-6 last:border-b-0"
              key={item.id}
            >
              <p className="text-sm font-semibold text-[var(--accent)]">
                {item.source}
              </p>
              <h3 className="mt-2 text-xl font-semibold text-[var(--foreground)]">
                {item.title}
              </h3>
              <blockquote className="mt-4 border-l-2 border-[var(--accent)] pl-4 text-[var(--foreground)]">
                {item.excerpt}
              </blockquote>
              <p className="mt-4 text-sm leading-6 text-[var(--muted)]">
                {item.supports}
              </p>
              <p className="mt-3 rounded-2xl bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted)]">
                <strong className="text-[var(--foreground)]">
                  What this does not prove:
                </strong>{" "}
                {item.doesNotProve}
              </p>
            </article>
          ))}
          <p className="rounded-2xl border border-[var(--line)] p-4 text-sm leading-6 text-[var(--muted)]">
            {isSample
              ? "These examples are sample evidence for the prototype. They are not generated from live uploads or project parsing."
              : "This evidence was read from your local project on this machine. It is not uploaded or shared."}
          </p>
        </div>
      </div>
    </div>
  );
}

import type { ProjectSource, SourceStatus } from "@/lib/sample-data";

type SourceStatusListProps = {
  sources: ProjectSource[];
};

const statusLabels: Record<SourceStatus, string> = {
  ready: "Ready",
  limited: "Limited",
  unsupported: "Needs action",
};

const statusStyles: Record<SourceStatus, string> = {
  ready: "bg-[var(--accent-soft)] text-[var(--accent-strong)]",
  limited: "bg-[var(--warning-soft)] text-[var(--warning)]",
  unsupported: "bg-[var(--danger-soft)] text-[var(--danger)]",
};

export function SourceStatusList({ sources }: SourceStatusListProps) {
  return (
    <div className="space-y-3" aria-label="Added places">
      {sources.map((source) => (
        <details
          className="border-b border-[var(--line)] py-4 last:border-b-0"
          key={source.id}
          open={source.status === "unsupported"}
        >
          <summary className="flex cursor-pointer list-none flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <span>
              <span className="block font-semibold text-[var(--foreground)]">
                {source.name}
              </span>
              <span className="mt-1 block text-sm leading-6 text-[var(--muted)]">
                {source.description}
              </span>
            </span>
            <span
              className={`w-fit rounded-full px-3 py-1 text-sm font-semibold ${statusStyles[source.status]}`}
            >
              {statusLabels[source.status]}
            </span>
          </summary>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">
            {source.note}
          </p>
        </details>
      ))}
    </div>
  );
}

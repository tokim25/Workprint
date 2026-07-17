type ConfidenceIndicatorProps = {
  label: string;
};

export function ConfidenceIndicator({ label }: ConfidenceIndicatorProps) {
  return (
    <span className="inline-flex rounded-full border border-[var(--line)] bg-[var(--accent-soft)] px-3 py-1 text-sm font-semibold text-[var(--accent-strong)]">
      Confidence: {label}
    </span>
  );
}

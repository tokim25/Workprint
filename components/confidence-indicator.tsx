type ConfidenceIndicatorProps = {
  label: string;
};

export function ConfidenceIndicator({ label }: ConfidenceIndicatorProps) {
  const normalizedLabel = label.trim() || "Not assessed";
  const description = confidenceDescriptionFor(normalizedLabel);

  return (
    <span
      aria-label={`Confidence: ${normalizedLabel}. ${description}`}
      className="inline-flex cursor-help rounded-full border border-[var(--line)] bg-[var(--accent-soft)] px-3 py-1 text-sm font-semibold text-[var(--accent-strong)]"
      tabIndex={0}
      title={description}
    >
      Confidence: {normalizedLabel}
    </span>
  );
}

function confidenceDescriptionFor(label: string) {
  switch (label.toLowerCase()) {
    case "high":
      return "Strong direct evidence supports this claim, with few unresolved gaps.";
    case "moderate":
      return "Evidence supports this claim, but some gaps or limited corroboration remain.";
    case "limited":
      return "Some evidence points this way, but coverage or corroboration is thin.";
    case "low":
      return "Evidence is weak, indirect, or incomplete; treat this claim cautiously.";
    default:
      return "Workprint has not assessed confidence yet because no supported insight has been produced.";
  }
}

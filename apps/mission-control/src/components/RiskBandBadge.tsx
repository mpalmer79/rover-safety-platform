import { cn } from "@/lib/utils";

const RISK_CLASSES: Record<string, string> = {
  low: "border-risk-low/40 bg-risk-low/10 text-risk-low",
  guarded: "border-risk-guarded/40 bg-risk-guarded/10 text-risk-guarded",
  restricted: "border-risk-restricted/40 bg-risk-restricted/10 text-risk-restricted",
  blocked: "border-risk-blocked/40 bg-risk-blocked/10 text-risk-blocked",
};

interface RiskBandBadgeProps {
  band: string;
  className?: string;
}

/**
 * Small typed badge for a risk band. Unknown bands degrade to
 * "guarded" colouring so we never silently treat an unfamiliar
 * value as low risk.
 */
export function RiskBandBadge({ band, className }: RiskBandBadgeProps) {
  const tone = RISK_CLASSES[band] ?? RISK_CLASSES.guarded;
  return (
    <span
      title={`Risk band: ${band}`}
      className={cn(
        "inline-flex items-center gap-1 rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-widest",
        tone,
        className,
      )}
    >
      <span aria-hidden>●</span>
      {band}
    </span>
  );
}

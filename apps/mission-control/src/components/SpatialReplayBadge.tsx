import type { SpatialDerivationSource } from "@/adapters/types";
import { describeDerivationSource } from "@/adapters/spatial";
import { cn } from "@/lib/utils";

interface SpatialReplayBadgeProps {
  source: SpatialDerivationSource;
  className?: string;
}

const TONE: Record<SpatialDerivationSource, string> = {
  bag_backed: "border-status-completed text-status-completed",
  fixture: "border-status-pending text-status-pending",
  bounded_inputs: "border-base-400 text-base-700",
  topology_only: "border-base-400 text-base-700",
  unavailable: "border-status-rejected text-status-rejected",
};

/**
 * Tiny badge that surfaces the spatial-replay derivation source.
 *
 * The badge text is the verbatim output of
 * :func:`describeDerivationSource`; the chip's colour communicates
 * the honesty class at a glance. ``bag_backed`` is green ONLY when
 * the artifact validates; the upstream adapter is responsible for
 * never passing ``"bag_backed"`` unless the validator gates it.
 */
export function SpatialReplayBadge({
  source,
  className,
}: SpatialReplayBadgeProps) {
  return (
    <span
      data-testid="spatial-replay-badge"
      data-source={source}
      className={cn(
        "inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        TONE[source],
        className,
      )}
    >
      <span aria-hidden="true">•</span>
      <span>{describeDerivationSource(source)}</span>
    </span>
  );
}

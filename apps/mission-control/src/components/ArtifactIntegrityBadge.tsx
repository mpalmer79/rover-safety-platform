import type { ArtifactIntegrity, ArtifactLifecycle } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface ArtifactIntegrityBadgeProps {
  integrity: ArtifactIntegrity | string;
  lifecycle?: ArtifactLifecycle | string;
  className?: string;
}

const TONE: Record<string, string> = {
  passed: "border-status-completed text-status-completed",
  partial: "border-status-pending text-status-pending",
  failed: "border-status-rejected text-status-rejected",
  missing: "border-status-rejected text-status-rejected",
  unverified: "border-base-400 text-base-600",
};

const LABEL: Record<string, string> = {
  passed: "integrity passed",
  partial: "integrity partial",
  failed: "integrity failed",
  missing: "artifact missing",
  unverified: "integrity unverified",
};

/**
 * Tiny chip that surfaces a registered artifact's integrity state
 * (and optionally the lifecycle rung). Honesty rule: the badge text
 * is the verbatim integrity string; ``failed`` is never re-coded as
 * ``partial``.
 */
export function ArtifactIntegrityBadge({
  integrity,
  lifecycle,
  className,
}: ArtifactIntegrityBadgeProps) {
  const tone = TONE[integrity] ?? "border-base-400 text-base-600";
  const label = LABEL[integrity] ?? integrity;
  return (
    <span
      data-testid="artifact-integrity-badge"
      data-integrity={integrity}
      data-lifecycle={lifecycle ?? ""}
      className={cn(
        "inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[11px] font-mono uppercase tracking-wide",
        tone,
        className,
      )}
    >
      <span aria-hidden="true">●</span>
      <span>{label}</span>
      {lifecycle ? (
        <span className="opacity-70">· {lifecycle}</span>
      ) : null}
    </span>
  );
}

import { ShieldCheck } from "lucide-react";

/**
 * Persistent banner that pins the safety boundary at the top of
 * every operator surface. The text is intentionally unambiguous:
 * this UI is simulation-only and does not authorise live motion.
 */
export function SafetyBoundaryBanner() {
  return (
    <div
      role="note"
      aria-label="Safety boundary disclaimer"
      data-testid="safety-boundary-banner"
      className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-base-200 bg-base-50/80 px-4 py-2 text-sm text-base-700"
    >
      <ShieldCheck aria-hidden className="h-4 w-4 text-accent" />
      <span className="label">Simulation-only</span>
      <span className="text-base-700">
        ProjectBoundary demonstrates deterministic mission validation,
        safety-supervisor authority, replay evidence, and audit
        traceability. It does not control real hardware and is not
        safety-certified.
      </span>
    </div>
  );
}

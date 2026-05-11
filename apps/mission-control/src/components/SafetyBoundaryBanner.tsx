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
      className="flex items-center gap-3 border-b border-base-200 bg-base-50/80 px-4 py-2 text-sm text-base-700"
    >
      <ShieldCheck aria-hidden className="h-4 w-4 text-accent" />
      <span className="label">Safety boundary</span>
      <span className="text-base-700">
        Simulation-only platform. Not safety-certified. The runtime
        safety supervisor and motion arbitration remain authoritative
        for any real robot motion.
      </span>
    </div>
  );
}

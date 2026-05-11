import type { RehearsalAudit } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface ZoneBoundaryOverlayProps {
  audit: RehearsalAudit;
  className?: string;
}

/**
 * Surfaces the boundary-related rejection codes from the audit's
 * validation diagnostics. The Phase 16 safety scan tags
 * restricted-zone / forbidden-zone attempts; this card lists them so
 * a reviewer immediately sees the boundary-related rejections.
 */
export function ZoneBoundaryOverlay({ audit, className }: ZoneBoundaryOverlayProps) {
  const boundaryDiagnostics = audit.validation_diagnostics.filter((d) =>
    typeof d.code === "string" &&
    (d.code === "restricted_zone" ||
      d.code === "direct_actuator_command" ||
      d.code === "safety_override" ||
      d.code === "estop_override"),
  );
  return (
    <div className={cn("space-y-1.5 text-xs", className)}>
      <p className="label">Zone / authority boundaries</p>
      {boundaryDiagnostics.length === 0 ? (
        <p className="text-base-500">No boundary violations recorded.</p>
      ) : (
        <ul className="space-y-1 text-status-rejected">
          {boundaryDiagnostics.map((d, idx) => (
            <li key={`bnd-${idx}-${d.code}`}>
              <span className="font-mono">{d.code}</span>{" "}
              <span className="text-base-800">— {d.message}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

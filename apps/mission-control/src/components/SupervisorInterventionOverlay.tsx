import type { RehearsalEvent } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface SupervisorInterventionOverlayProps {
  events: readonly RehearsalEvent[];
  className?: string;
}

/**
 * Lists every supervisor or safety event with severity 'rejection' or
 * 'warning'. Used on the mission detail page so a reviewer sees the
 * exact moment the supervisor intervened — never silently dropped.
 */
export function SupervisorInterventionOverlay({
  events,
  className,
}: SupervisorInterventionOverlayProps) {
  const interventions = events.filter(
    (e) =>
      (e.event_type === "supervisor" || e.event_type === "safety") &&
      e.severity !== "info",
  );

  if (interventions.length === 0) {
    return (
      <p className={cn("text-xs text-base-500", className)}>
        No supervisor interventions recorded for this rehearsal.
      </p>
    );
  }
  return (
    <ul className={cn("space-y-1 text-xs text-status-rejected", className)}>
      {interventions.map((event) => (
        <li key={event.event_id}>
          <span className="font-mono text-[11px] text-base-500">
            t+{(event.event_time_ns / 1_000_000_000).toFixed(1)}s
          </span>{" "}
          <span className="font-mono">
            {event.event_type}/{event.event_subtype}
          </span>{" "}
          <span className="text-base-800">— {event.description}</span>
        </li>
      ))}
    </ul>
  );
}

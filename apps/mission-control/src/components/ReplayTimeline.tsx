import type { RehearsalEvent } from "@/adapters/types";
import { cn } from "@/lib/utils";

const SEVERITY_CLASS: Record<RehearsalEvent["severity"], string> = {
  info: "border-l-base-400 text-base-700",
  warning: "border-l-status-pending text-status-pending",
  rejection: "border-l-status-rejected text-status-rejected",
};

interface ReplayTimelineProps {
  events: readonly RehearsalEvent[];
  className?: string;
}

/**
 * Vertical event timeline. Each event row preserves the verbatim
 * deterministic hash and severity from the audit bundle so the UI
 * cannot silently drop or downgrade a rejection.
 */
export function ReplayTimeline({ events, className }: ReplayTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="body-mono text-base-500">No rehearsal events recorded.</p>
    );
  }
  return (
    <ol className={cn("space-y-2", className)} aria-label="Rehearsal event timeline">
      {events.map((event) => (
        <li
          key={event.event_id}
          className={cn(
            "border-l-2 pl-3 py-1.5",
            SEVERITY_CLASS[event.severity] ?? SEVERITY_CLASS.info,
          )}
        >
          <div className="flex flex-wrap items-baseline gap-2">
            <span className="font-mono text-[11px] text-base-500">
              t+{(event.event_time_ns / 1_000_000_000).toFixed(1)}s
            </span>
            <span className="label">{event.event_type}/{event.event_subtype}</span>
            <span
              className="ml-auto font-mono text-[10px] text-base-500"
              title={event.deterministic_hash}
            >
              {event.deterministic_hash.slice(0, 12)}
            </span>
          </div>
          <p className="text-sm leading-snug text-base-800">{event.description}</p>
        </li>
      ))}
    </ol>
  );
}

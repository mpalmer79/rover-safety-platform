import type { RehearsalEvent } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface MissionSpatialTimelineProps {
  events: readonly RehearsalEvent[];
  className?: string;
}

const EVENT_TYPE_COLOR: Record<string, string> = {
  mission: "bg-accent",
  motion: "bg-base-600",
  safety: "bg-status-pending",
  supervisor: "bg-status-completed",
  validation: "bg-base-500",
  audit: "bg-base-400",
  replay: "bg-base-500",
  analytics: "bg-base-500",
};

/**
 * Horizontal proportional timeline of every event in the audit. The
 * width of each bar is proportional to the event's sequence index;
 * the colour is keyed off the event_type. Used at the top of the
 * mission detail page so a reviewer sees the entire ordered flow at
 * a glance.
 */
export function MissionSpatialTimeline({
  events,
  className,
}: MissionSpatialTimelineProps) {
  if (events.length === 0) {
    return (
      <p className={cn("text-xs text-base-500", className)}>
        No events to plot.
      </p>
    );
  }
  return (
    <div className={cn("space-y-1.5", className)} aria-label="Mission timeline">
      <div className="flex w-full overflow-hidden rounded border border-base-200 bg-base-100">
        {events.map((event) => (
          <span
            key={event.event_id}
            title={`${event.event_type}/${event.event_subtype}: ${event.description}`}
            className={cn(
              "h-3 flex-1 border-r border-base-0 last:border-none",
              EVENT_TYPE_COLOR[event.event_type] ?? "bg-base-500",
              event.severity === "rejection" ? "opacity-90" : "opacity-70",
            )}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-3 text-[11px] text-base-600">
        {Array.from(new Set(events.map((e) => e.event_type))).map((type) => (
          <span key={type} className="inline-flex items-center gap-1.5">
            <span
              aria-hidden
              className={cn(
                "inline-block h-2.5 w-2.5 rounded-sm",
                EVENT_TYPE_COLOR[type] ?? "bg-base-500",
              )}
            />
            <span>{type}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

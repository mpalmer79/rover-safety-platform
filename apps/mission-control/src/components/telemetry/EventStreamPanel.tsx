"use client";

import { typography } from "@/design-system/typography";
import { cn } from "@/lib/utils";
import type { RehearsalEvent } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface EventStreamPanelProps {
  events: readonly RehearsalEvent[];
  /** Maximum rows to render. Default 20. */
  limit?: number;
}

const SEVERITY_STYLE: Record<RehearsalEvent["severity"], string> = {
  info: "text-[color:var(--mc-text)]",
  warning: "text-[color:var(--mc-status-warning)]",
  rejection: "text-[color:var(--mc-status-rejected)]",
};

/**
 * Reads from rehearsal_runtime.events on disk and renders them in
 * deterministic order. The word "stream" refers to the row layout —
 * there is no live source.
 */
export function EventStreamPanel({ events, limit = 20 }: EventStreamPanelProps) {
  const visible = events.slice(0, limit);
  return (
    <TelemetryPanelFrame
      kicker="Event stream"
      title={`${events.length} event${events.length === 1 ? "" : "s"}`}
      derivation="rehearsal_runtime.events"
      integrity={events.some((e) => e.severity === "rejection") ? "rejected" : "passed"}
    >
      {events.length === 0 ? (
        <p className={typography("bodyDense")}>
          No events on disk for this audit.
        </p>
      ) : (
        <ol className="space-y-1.5 text-[12px]">
          {visible.map((event) => (
            <li
              key={event.event_id}
              className="flex items-baseline gap-2 rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1"
            >
              <span className="font-mono text-[11px] text-[color:var(--mc-text-muted)]">
                {event.event_time_ns}
              </span>
              <span
                className={cn(
                  "uppercase tracking-[0.12em] text-[10px]",
                  SEVERITY_STYLE[event.severity],
                )}
              >
                {event.severity}
              </span>
              <span className="text-[color:var(--mc-text)]">{event.description}</span>
            </li>
          ))}
          {events.length > visible.length ? (
            <li className={typography("caption")}>
              {events.length - visible.length} more event(s) not shown.
            </li>
          ) : null}
        </ol>
      )}
    </TelemetryPanelFrame>
  );
}

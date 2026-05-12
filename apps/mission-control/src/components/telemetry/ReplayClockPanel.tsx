"use client";

import { typography } from "@/design-system/typography";
import type { RehearsalEvent } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface ReplayClockPanelProps {
  events: readonly RehearsalEvent[];
  /** Optional 0..1 cursor for the scrubber, supplied by parent. */
  cursor?: number;
}

/**
 * Renders the replay clock derived from the first/last event
 * timestamp on disk. The clock NEVER ticks on its own; it reflects
 * the parent-supplied cursor only.
 */
export function ReplayClockPanel({ events, cursor = 0 }: ReplayClockPanelProps) {
  if (events.length === 0) {
    return (
      <TelemetryPanelFrame
        kicker="Replay clock"
        title="no events"
        derivation="rehearsal_runtime.events"
        integrity="not_evaluated"
      >
        <p className={typography("bodyDense")}>
          No events on disk for this audit. Clock is unavailable.
        </p>
      </TelemetryPanelFrame>
    );
  }
  const start = events[0].event_time_ns;
  const end = events[events.length - 1].event_time_ns;
  const span = Math.max(1, end - start);
  const positionNs = start + Math.round(span * Math.max(0, Math.min(1, cursor)));
  const elapsedSec = ((positionNs - start) / 1_000_000_000).toFixed(3);
  const totalSec = (span / 1_000_000_000).toFixed(3);

  return (
    <TelemetryPanelFrame
      kicker="Replay clock"
      title={`${elapsedSec}s / ${totalSec}s`}
      derivation="rehearsal_runtime.events"
      integrity="passed"
    >
      <div className="flex flex-col gap-2">
        <div className="flex justify-between text-[11px] text-[color:var(--mc-text-muted)]">
          <span>t₀ · {start}</span>
          <span>tₙ · {end}</span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={Math.round(cursor * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Replay cursor position"
          className="h-2 w-full overflow-hidden rounded-full bg-[color:var(--mc-surface-overlay)]"
        >
          <div
            className="h-full rounded-full bg-[color:var(--mc-accent)]"
            style={{ width: `${Math.round(cursor * 100)}%` }}
          />
        </div>
        <p className={typography("caption")}>
          Cursor is parent-controlled. The panel does not tick on its own.
        </p>
      </div>
    </TelemetryPanelFrame>
  );
}

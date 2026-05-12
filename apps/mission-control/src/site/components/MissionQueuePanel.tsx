"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { MissionQueue, ReadinessState } from "@/site/models";

interface MissionQueuePanelProps {
  queue: MissionQueue;
  className?: string;
}

const READINESS_STYLE: Record<ReadinessState, string> = {
  ready_to_rehearse: "text-[color:var(--mc-status-completed)]",
  needs_review: "text-[color:var(--mc-status-warning)]",
  blocked: "text-[color:var(--mc-status-rejected)]",
  evidence_missing: "text-[color:var(--mc-status-pending)]",
  not_evaluated: "text-[color:var(--mc-text-muted)]",
};

export function MissionQueuePanel({ queue, className }: MissionQueuePanelProps) {
  return (
    <section
      data-testid="mission-queue-panel"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <p className={typography("label")}>Mission queue</p>
        <span className={typography("caption")}>
          {queue.entries.length} entr{queue.entries.length === 1 ? "y" : "ies"}
        </span>
      </header>
      {queue.entries.length === 0 ? (
        <p className={typography("bodyDense")}>
          No queued missions for this site.
        </p>
      ) : (
        <ul className="space-y-1.5 text-[12px]">
          {queue.entries.map((entry) => (
            <li
              key={entry.mission_id}
              className="rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1.5"
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
                  {entry.mission_id}
                </span>
                <span
                  className={cn(
                    "uppercase tracking-[0.12em] text-[10px]",
                    READINESS_STYLE[entry.readiness],
                  )}
                >
                  {entry.readiness}
                </span>
              </div>
              <p className="mt-0.5 text-[11px] text-[color:var(--mc-text)]">
                {entry.description}
              </p>
              <p className={cn(typography("caption"), "mt-0.5")}>
                {entry.readiness_reason}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { ZoneStatus } from "@/site/models";

interface ZoneStatusPanelProps {
  statuses: readonly ZoneStatus[];
  className?: string;
}

const STATUS_COLOR: Record<ZoneStatus["status"], string> = {
  nominal: "var(--mc-status-completed)",
  needs_review: "var(--mc-status-warning)",
  blocked: "var(--mc-status-rejected)",
};

export function ZoneStatusPanel({ statuses, className }: ZoneStatusPanelProps) {
  return (
    <section
      data-testid="zone-status-panel"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <p className={typography("label")}>Zone status</p>
      <ul className="space-y-1.5 text-[12px]">
        {statuses.map((zs) => (
          <li
            key={zs.zone_id}
            className="rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1.5"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
                {zs.zone_id}
              </span>
              <span
                className="uppercase tracking-[0.12em] text-[10px]"
                style={{ color: STATUS_COLOR[zs.status] }}
              >
                {zs.status}
              </span>
            </div>
            <p className="mt-0.5 text-[11px] text-[color:var(--mc-text)]">
              active missions · {zs.active_missions}
            </p>
            {zs.forbidden_topics.length > 0 ? (
              <p className={cn(typography("caption"), "mt-0.5 font-mono")}>
                forbidden · {zs.forbidden_topics.join(", ")}
              </p>
            ) : null}
            {zs.notes.length > 0 ? (
              <p className={cn(typography("caption"), "mt-0.5")}>
                {zs.notes[0]}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

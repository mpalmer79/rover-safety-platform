"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { Site } from "@/site/models";

interface FleetOverviewPanelProps {
  site: Site;
  /** Number of robots ready to rehearse (derived externally). */
  readyCount: number;
  /** Number of robots blocked. */
  blockedCount: number;
  className?: string;
}

export function FleetOverviewPanel({
  site,
  readyCount,
  blockedCount,
  className,
}: FleetOverviewPanelProps) {
  return (
    <section
      data-testid="fleet-overview-panel"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className={typography("label")}>Fleet overview</p>
          <h2 className={typography("heading")}>{site.label}</h2>
          <p className={typography("caption")}>{site.description}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-[11px]">
          <span className="rounded-sm border border-[color:var(--mc-status-completed)] px-2 py-0.5 text-[color:var(--mc-status-completed)]">
            ready · {readyCount}
          </span>
          <span className="rounded-sm border border-[color:var(--mc-status-rejected)] px-2 py-0.5 text-[color:var(--mc-status-rejected)]">
            blocked · {blockedCount}
          </span>
          <span className="rounded-sm border border-[color:var(--mc-status-warning)] px-2 py-0.5 text-[color:var(--mc-status-warning)]">
            site · {site.site_id}
          </span>
        </div>
      </header>
      <p className={cn(typography("caption"), "mt-1")}>{site.disclaimer}</p>
    </section>
  );
}

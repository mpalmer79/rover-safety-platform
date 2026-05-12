"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { Site } from "@/site/models";

interface SiteMapOverviewProps {
  site: Site;
  className?: string;
}

const ZONE_COLOR: Record<Site["zones"][number]["zone_type"], string> = {
  operations: "var(--mc-accent)",
  transit: "var(--mc-status-pending)",
  exclusion: "var(--mc-status-rejected)",
  dock_apron: "var(--mc-status-completed)",
};

/**
 * Illustrative site overview. Renders the zones, docks, and lanes
 * as a deterministic grid layout, NOT as surveyed coordinates.
 */
export function SiteMapOverview({ site, className }: SiteMapOverviewProps) {
  return (
    <section
      data-testid="site-map-overview"
      className={cn(
        "flex flex-col gap-3 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <p className={typography("label")}>Site map</p>
        <span className={typography("caption")}>
          illustrative · not surveyed coordinates
        </span>
      </header>
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {site.zones.map((zone) => (
          <li
            key={zone.zone_id}
            className="rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] p-3"
          >
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: ZONE_COLOR[zone.zone_type] }}
                aria-hidden
              />
              <span className="text-sm font-medium text-[color:var(--mc-text)]">
                {zone.label}
              </span>
            </div>
            <p className={cn(typography("caption"), "mt-1")}>
              {zone.description}
            </p>
            <p className="mt-1 font-mono text-[11px] text-[color:var(--mc-text-muted)]">
              {zone.docks.length} dock(s) · {zone.lanes.length} lane(s)
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

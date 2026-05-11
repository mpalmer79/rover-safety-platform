import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface ResponsiveGridProps {
  children: ReactNode;
  className?: string;
  /**
   * Layout shape.
   *
   * - `stack`       → 1 column at every breakpoint
   * - `auto`        → 1 column on mobile, 2 columns from `md`, 3 from `xl`
   * - `mission`     → 1 column on mobile, 2 columns from `md`, the mission
   *                   detail page uses this shape (left: playback, right: audit)
   */
  shape?: "stack" | "auto" | "mission";
  /** Tailwind gap classes; defaults to a comfortable rhythm. */
  gap?: string;
}

const SHAPE_CLASS: Record<NonNullable<ResponsiveGridProps["shape"]>, string> = {
  stack: "grid grid-cols-1",
  auto: "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3",
  mission: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr]",
};

/**
 * Predictable responsive grid. Components prefer this over raw
 * `md:grid-cols-...` so the layout is consistent across pages and
 * future breakpoint tuning happens in ONE place.
 */
export function ResponsiveGrid({
  children,
  className,
  shape = "auto",
  gap = "gap-3 sm:gap-4 lg:gap-5",
}: ResponsiveGridProps) {
  return (
    <div
      data-testid="responsive-grid"
      data-shape={shape}
      className={cn(SHAPE_CLASS[shape], gap, className)}
    >
      {children}
    </div>
  );
}

"use client";

import { cn } from "@/lib/utils";
import { typography } from "@/design-system/typography";
import { WALKTHROUGH_STEP_COUNT } from "@/reviewer/steps";

interface WalkthroughProgressProps {
  /** Current step index (1-based). */
  current: number;
  className?: string;
}

export function WalkthroughProgress({
  current,
  className,
}: WalkthroughProgressProps) {
  const total = WALKTHROUGH_STEP_COUNT;
  return (
    <div
      data-testid="walkthrough-progress"
      className={cn("flex flex-col gap-2", className)}
      role="group"
      aria-label="Walkthrough progress"
    >
      <div className="flex items-baseline justify-between">
        <span className={typography("label")}>walkthrough progress</span>
        <span className="font-mono text-[12px] text-[color:var(--mc-text)]">
          {current} / {total}
        </span>
      </div>
      <div className="flex gap-1">
        {Array.from({ length: total }, (_, idx) => {
          const filled = idx < current;
          return (
            <div
              key={idx}
              aria-hidden
              data-filled={filled}
              className={cn(
                "h-1.5 flex-1 rounded-full",
                filled
                  ? "bg-[color:var(--mc-accent)]"
                  : "bg-[color:var(--mc-surface-overlay)]",
              )}
            />
          );
        })}
      </div>
    </div>
  );
}

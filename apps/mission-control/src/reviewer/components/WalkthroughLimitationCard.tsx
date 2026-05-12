"use client";

import { TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { StepBinding } from "@/reviewer/contextualWalkthrough";

interface WalkthroughLimitationCardProps {
  binding: StepBinding;
  className?: string;
}

export function WalkthroughLimitationCard({
  binding,
  className,
}: WalkthroughLimitationCardProps) {
  if (binding.limitations.length === 0) {
    return (
      <section
        data-testid="walkthrough-limitation-card"
        data-empty="true"
        className={cn(
          "rounded-lg border p-4",
          "border-[color:var(--mc-border)]",
          surface("panel"),
          className,
        )}
      >
        <p className={typography("label")}>Limitations</p>
        <p className={typography("bodyDense") + " mt-1"}>
          No unresolved limitations for this step.
        </p>
      </section>
    );
  }
  return (
    <section
      data-testid="walkthrough-limitation-card"
      data-empty="false"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-status-warning)]",
        surface("panel"),
        className,
      )}
    >
      <header className="inline-flex items-center gap-1.5 text-[color:var(--mc-status-warning)]">
        <TriangleAlert aria-hidden className="h-4 w-4" />
        <span className={typography("label")}>Limitations</span>
      </header>
      <ul className="list-inside list-disc text-[12px] text-[color:var(--mc-text)]">
        {binding.limitations.map((l, idx) => (
          <li key={idx}>{l}</li>
        ))}
      </ul>
    </section>
  );
}

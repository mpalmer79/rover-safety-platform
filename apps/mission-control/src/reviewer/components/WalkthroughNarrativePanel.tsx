"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { WalkthroughStep } from "@/reviewer/steps";

interface WalkthroughNarrativePanelProps {
  step: WalkthroughStep;
  className?: string;
}

export function WalkthroughNarrativePanel({
  step,
  className,
}: WalkthroughNarrativePanelProps) {
  return (
    <section
      data-testid="walkthrough-narrative-panel"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <span className={typography("label")}>Narrative</span>
      <p className={typography("body")}>{step.narrative}</p>
      <p className={cn(typography("caption"), "mt-1")}>
        outcome · {step.outcome}
      </p>
    </section>
  );
}

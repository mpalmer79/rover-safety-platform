"use client";

import { CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { WalkthroughStep } from "@/reviewer/steps";

interface WalkthroughOutcomePanelProps {
  step: WalkthroughStep;
  className?: string;
}

export function WalkthroughOutcomePanel({
  step,
  className,
}: WalkthroughOutcomePanelProps) {
  return (
    <section
      data-testid="walkthrough-outcome-panel"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <span
        className={cn(
          typography("label"),
          "inline-flex items-center gap-1.5 text-[color:var(--mc-status-completed)]",
        )}
      >
        <CheckCircle2 aria-hidden className="h-3.5 w-3.5" />
        Outcome
      </span>
      <p className={typography("body")}>{step.outcome}</p>
    </section>
  );
}

"use client";

import { ShieldAlert } from "lucide-react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { WalkthroughStep } from "@/reviewer/steps";

interface WalkthroughSafetyPanelProps {
  step: WalkthroughStep;
  className?: string;
}

export function WalkthroughSafetyPanel({
  step,
  className,
}: WalkthroughSafetyPanelProps) {
  return (
    <section
      data-testid="walkthrough-safety-panel"
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
          "inline-flex items-center gap-1.5 text-[color:var(--mc-status-warning)]",
        )}
      >
        <ShieldAlert aria-hidden className="h-3.5 w-3.5" />
        Safety boundary
      </span>
      <p className={typography("body")}>{step.safety}</p>
    </section>
  );
}

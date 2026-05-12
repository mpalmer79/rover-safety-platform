"use client";

import { Target } from "lucide-react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { StepBinding } from "@/reviewer/contextualWalkthrough";

interface WalkthroughProofStepProps {
  binding: StepBinding;
  className?: string;
}

export function WalkthroughProofStep({
  binding,
  className,
}: WalkthroughProofStepProps) {
  return (
    <section
      data-testid="walkthrough-proof-step"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="inline-flex items-center gap-1.5 text-[color:var(--mc-accent)]">
        <Target aria-hidden className="h-4 w-4" />
        <span className={typography("label")}>Next required proof</span>
      </header>
      <p className={typography("body")}>
        {binding.nextProof ?? "No further proof required at this step."}
      </p>
    </section>
  );
}

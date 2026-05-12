"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { STEP_VARIANTS } from "@/design-system/motion";
import { typography } from "@/design-system/typography";
import type { WalkthroughStep } from "@/reviewer/steps";

interface WalkthroughStepCardProps {
  step: WalkthroughStep;
  className?: string;
}

export function WalkthroughStepCard({ step, className }: WalkthroughStepCardProps) {
  return (
    <motion.article
      data-testid="walkthrough-step-card"
      data-step-id={step.id}
      data-step-index={step.index}
      initial="hidden"
      animate="visible"
      variants={STEP_VARIANTS}
      className={cn(
        "rounded-lg border border-[color:var(--mc-border)] p-4",
        surface("walkthrough"),
        className,
      )}
    >
      <header className="flex items-baseline justify-between gap-2">
        <span className={typography("label")}>
          Step {step.index} of 10
        </span>
        <span className="font-mono text-[11px] text-[color:var(--mc-text-muted)]">
          {step.id}
        </span>
      </header>
      <h2 className={cn(typography("heading"), "mt-1")}>{step.title}</h2>
      <p className={cn(typography("body"), "mt-2 text-[color:var(--mc-text)]")}>
        {step.narrative}
      </p>
    </motion.article>
  );
}

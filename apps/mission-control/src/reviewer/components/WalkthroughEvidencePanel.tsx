"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { WalkthroughStep } from "@/reviewer/steps";

interface WalkthroughEvidencePanelProps {
  step: WalkthroughStep;
  className?: string;
}

export function WalkthroughEvidencePanel({
  step,
  className,
}: WalkthroughEvidencePanelProps) {
  return (
    <section
      data-testid="walkthrough-evidence-panel"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <span className={typography("label")}>Evidence references</span>
      <ul className="space-y-1">
        {step.evidence.map((ref) => (
          <li
            key={ref}
            className="rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1 font-mono text-[12px]"
          >
            {ref}
          </li>
        ))}
      </ul>
    </section>
  );
}

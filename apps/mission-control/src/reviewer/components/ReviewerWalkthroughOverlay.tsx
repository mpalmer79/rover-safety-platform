"use client";

import { ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import { useCallback, useState } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import { WALKTHROUGH_STEPS } from "@/reviewer/steps";

import { WalkthroughEvidencePanel } from "./WalkthroughEvidencePanel";
import { WalkthroughNarrativePanel } from "./WalkthroughNarrativePanel";
import { WalkthroughOutcomePanel } from "./WalkthroughOutcomePanel";
import { WalkthroughProgress } from "./WalkthroughProgress";
import { WalkthroughSafetyPanel } from "./WalkthroughSafetyPanel";
import { WalkthroughStepCard } from "./WalkthroughStepCard";

interface ReviewerWalkthroughOverlayProps {
  /** 0-based starting index. Defaults to 0. */
  startIndex?: number;
  className?: string;
}

export function ReviewerWalkthroughOverlay({
  startIndex = 0,
  className,
}: ReviewerWalkthroughOverlayProps) {
  const [index, setIndex] = useState(() =>
    Math.max(0, Math.min(WALKTHROUGH_STEPS.length - 1, startIndex)),
  );

  const step = WALKTHROUGH_STEPS[index];

  const next = useCallback(() => {
    setIndex((i) => Math.min(WALKTHROUGH_STEPS.length - 1, i + 1));
  }, []);
  const previous = useCallback(() => {
    setIndex((i) => Math.max(0, i - 1));
  }, []);
  const reset = useCallback(() => setIndex(0), []);

  return (
    <div
      data-testid="reviewer-walkthrough-overlay"
      className={cn(
        "flex h-full min-h-[480px] flex-col gap-3 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("walkthrough"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className={typography("label")}>Reviewer walkthrough</p>
          <h1 className={typography("display")}>
            Understand the platform in 10 deterministic steps
          </h1>
          <p className={cn(typography("caption"), "mt-1 max-w-prose")}>
            Each step explains a stage of the pipeline, the artefacts it
            produces, the safety boundary it enforces, and its outcome — all
            from committed JSON.
          </p>
        </div>
        <WalkthroughProgress current={index + 1} className="w-full max-w-xs" />
      </header>

      <WalkthroughStepCard step={step} />

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <WalkthroughNarrativePanel step={step} />
        <WalkthroughEvidencePanel step={step} />
        <WalkthroughSafetyPanel step={step} />
        <WalkthroughOutcomePanel step={step} />
      </div>

      <footer className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-[color:var(--mc-border)] pt-3">
        <span className={typography("caption")}>
          Simulation-only · no live telemetry, no autonomous authority.
        </span>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={reset}
            disabled={index === 0}
            data-testid="walkthrough-reset"
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm",
              "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "hover:bg-[color:var(--mc-surface-overlay)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
            )}
          >
            <RotateCcw aria-hidden className="h-4 w-4" />
            Reset
          </button>
          <button
            type="button"
            onClick={previous}
            disabled={index === 0}
            data-testid="walkthrough-previous"
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm",
              "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "hover:bg-[color:var(--mc-surface-overlay)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
            )}
          >
            <ArrowLeft aria-hidden className="h-4 w-4" />
            Back
          </button>
          <button
            type="button"
            onClick={next}
            disabled={index === WALKTHROUGH_STEPS.length - 1}
            data-testid="walkthrough-next"
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium",
              "border-[color:var(--mc-accent)] text-[color:var(--mc-accent)]",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "hover:bg-[color:var(--mc-accent-soft)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
            )}
          >
            Continue
            <ArrowRight aria-hidden className="h-4 w-4" />
          </button>
        </div>
      </footer>
    </div>
  );
}

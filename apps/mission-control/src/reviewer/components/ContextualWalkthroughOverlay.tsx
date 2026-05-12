"use client";

import { ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import { useCallback, useMemo, useState } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type {
  ArtifactRegistryRecord,
  RehearsalAudit,
  SpatialReplayArtifact,
} from "@/adapters/types";
import { planCameraCue } from "@/3d/orchestration/cameraCuePlanner";

import {
  buildStepBindings,
  type StepBinding,
} from "@/reviewer/contextualWalkthrough";
import { WALKTHROUGH_STEPS } from "@/reviewer/steps";

import { WalkthroughEvidenceFocus } from "./WalkthroughEvidenceFocus";
import { WalkthroughLimitationCard } from "./WalkthroughLimitationCard";
import { WalkthroughMissionFocus } from "./WalkthroughMissionFocus";
import { WalkthroughProgress } from "./WalkthroughProgress";
import { WalkthroughProofStep } from "./WalkthroughProofStep";
import { WalkthroughSceneCue } from "./WalkthroughSceneCue";
import { WalkthroughStepCard } from "./WalkthroughStepCard";

interface ContextualWalkthroughOverlayProps {
  audit: RehearsalAudit | null;
  spatial?: SpatialReplayArtifact | null;
  registry?: ArtifactRegistryRecord | null;
  startIndex?: number;
  className?: string;
}

/**
 * Contextual reviewer walkthrough.
 *
 * Binds each step to the selected mission's evidence and renders
 * mission focus, step evidence, limitations, next required proof,
 * and the active scene cue.
 */
export function ContextualWalkthroughOverlay({
  audit,
  spatial = null,
  registry = null,
  startIndex = 0,
  className,
}: ContextualWalkthroughOverlayProps) {
  const [index, setIndex] = useState(() =>
    Math.max(0, Math.min(WALKTHROUGH_STEPS.length - 1, startIndex)),
  );
  const bindings = useMemo(
    () => buildStepBindings({ audit, spatial, registry }),
    [audit, spatial, registry],
  );
  const step = WALKTHROUGH_STEPS[index];
  const binding: StepBinding = bindings[index];
  const cue = useMemo(() => planCameraCue(step.id), [step.id]);

  const next = useCallback(
    () => setIndex((i) => Math.min(WALKTHROUGH_STEPS.length - 1, i + 1)),
    [],
  );
  const previous = useCallback(
    () => setIndex((i) => Math.max(0, i - 1)),
    [],
  );
  const reset = useCallback(() => setIndex(0), []);

  return (
    <div
      data-testid="contextual-walkthrough-overlay"
      data-mission-id={audit?.request.mission_id ?? ""}
      className={cn(
        "flex h-full min-h-[480px] flex-col gap-3 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("walkthrough"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className={typography("label")}>Contextual walkthrough</p>
          <h1 className={typography("display")}>
            {audit
              ? `Reviewing ${audit.request.mission_id}`
              : "Pick a mission to begin"}
          </h1>
          <p className={cn(typography("caption"), "mt-1 max-w-prose")}>
            Every step binds to committed evidence. Missing inputs show as
            limitations.
          </p>
        </div>
        <WalkthroughProgress current={index + 1} className="w-full max-w-xs" />
      </header>

      <WalkthroughStepCard step={step} />
      <WalkthroughMissionFocus audit={audit} />

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <WalkthroughEvidenceFocus binding={binding} />
        <WalkthroughLimitationCard binding={binding} />
        <WalkthroughProofStep binding={binding} />
        <WalkthroughSceneCue cue={cue} />
      </div>

      <footer className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-[color:var(--mc-border)] pt-3">
        <span className={typography("caption")}>
          Simulation-only · evidence is preserved verbatim from committed JSON.
        </span>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={reset}
            disabled={index === 0}
            data-testid="contextual-walkthrough-reset"
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
            data-testid="contextual-walkthrough-previous"
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
            data-testid="contextual-walkthrough-next"
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

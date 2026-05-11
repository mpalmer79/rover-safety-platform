import { Check, AlertTriangle, X, CircleDashed, CircleEllipsis } from "lucide-react";

import { cn } from "@/lib/utils";

export const REHEARSAL_STEPS = [
  "created",
  "validated",
  "approved",
  "rehearsing",
  "completed",
] as const;

type StepKind = (typeof REHEARSAL_STEPS)[number];

interface MissionStateStepperProps {
  status: string;
  failureReason?: string;
  className?: string;
}

function stepState(step: StepKind, status: string): "done" | "current" | "pending" | "rejected" | "aborted" {
  if (status === "rejected") {
    // Mark every step up to the rejection point as "done"; the
    // remaining steps are shown as "rejected" so a reviewer sees
    // exactly where the pipeline halted.
    const order: readonly StepKind[] = REHEARSAL_STEPS;
    const haltIndex = ["created", "validated", "approved"].indexOf(step);
    return haltIndex >= 0 && haltIndex <= 1 ? "rejected" : "rejected";
  }
  if (status === "aborted") return "aborted";

  const order: readonly StepKind[] = REHEARSAL_STEPS;
  const idx = order.indexOf(step);
  const currentIdx = order.indexOf(status as StepKind);
  if (currentIdx === -1) return "pending";
  if (idx < currentIdx) return "done";
  if (idx === currentIdx) return "current";
  return "pending";
}

const ICONS = {
  done: <Check className="h-3.5 w-3.5" aria-hidden />,
  current: <CircleEllipsis className="h-3.5 w-3.5 animate-pulse" aria-hidden />,
  pending: <CircleDashed className="h-3.5 w-3.5" aria-hidden />,
  rejected: <X className="h-3.5 w-3.5" aria-hidden />,
  aborted: <AlertTriangle className="h-3.5 w-3.5" aria-hidden />,
};

const COLORS = {
  done: "border-status-completed/40 text-status-completed",
  current: "border-accent/40 text-accent",
  pending: "border-base-300 text-base-500",
  rejected: "border-status-rejected/40 text-status-rejected",
  aborted: "border-status-aborted/40 text-status-aborted",
};

/**
 * Visual stepper for the deterministic rehearsal state machine.
 *
 * The component never invents progress — if the audit recorded
 * ``status='rejected'``, every step renders with the rejected
 * style; if the runtime never ran, the stepper still shows the
 * ``created → completed`` path with the right markers.
 */
export function MissionStateStepper({
  status,
  failureReason,
  className,
}: MissionStateStepperProps) {
  return (
    <ol
      className={cn("flex flex-wrap items-center gap-2", className)}
      aria-label="Rehearsal state machine"
    >
      {REHEARSAL_STEPS.map((step, idx) => {
        const state = stepState(step, status);
        return (
          <li key={step} className="flex items-center gap-2">
            <div
              className={cn(
                "flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest",
                COLORS[state],
              )}
              title={
                state === "rejected" && failureReason
                  ? `Rejected: ${failureReason}`
                  : `${step}: ${state}`
              }
            >
              {ICONS[state]}
              <span>{step}</span>
            </div>
            {idx < REHEARSAL_STEPS.length - 1 ? (
              <span aria-hidden className="text-base-400">›</span>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

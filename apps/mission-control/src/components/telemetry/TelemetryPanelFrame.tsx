"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";

interface TelemetryPanelFrameProps {
  /** Always-visible kicker line above the title. */
  kicker: string;
  /** Title (single line, sentence case). */
  title: string;
  /** Derivation source — derivation_source / evidence_origin / fixture. */
  derivation: string;
  /** Optional integrity indicator. */
  integrity?: "passed" | "partial" | "rejected" | "not_evaluated";
  /** Body. */
  children: ReactNode;
  /** Optional density-class override. */
  className?: string;
}

const INTEGRITY_COLOR: Record<
  NonNullable<TelemetryPanelFrameProps["integrity"]>,
  string
> = {
  passed: "text-[color:var(--mc-status-completed)]",
  partial: "text-[color:var(--mc-status-warning)]",
  rejected: "text-[color:var(--mc-status-rejected)]",
  not_evaluated: "text-[color:var(--mc-text-muted)]",
};

/**
 * Common chrome for every telemetry-density panel. Renders the
 * derivation source verbatim so reviewers always see how the values
 * were produced — no "live" implication anywhere.
 */
export function TelemetryPanelFrame({
  kicker,
  title,
  derivation,
  integrity,
  children,
  className,
}: TelemetryPanelFrameProps) {
  return (
    <div
      data-testid="telemetry-panel"
      className={cn(
        "flex h-full flex-col rounded-lg border",
        "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
        surface("telemetry"),
        className,
      )}
    >
      <header className="flex items-start justify-between gap-2 border-b border-[color:var(--mc-border)] px-4 py-3">
        <div className="space-y-0.5">
          <p className={typography("label")}>{kicker}</p>
          <h3 className={typography("heading")}>{title}</h3>
        </div>
        <div className="flex flex-col items-end gap-0.5 text-right">
          <span className={typography("caption")}>derivation</span>
          <span className={cn(typography("mono"), "text-[color:var(--mc-text)]")}>
            {derivation}
          </span>
          {integrity ? (
            <span
              className={cn(
                typography("caption"),
                "uppercase tracking-[0.16em]",
                INTEGRITY_COLOR[integrity],
              )}
            >
              integrity · {integrity}
            </span>
          ) : null}
        </div>
      </header>
      <div className="flex-1 px-4 py-3">{children}</div>
    </div>
  );
}

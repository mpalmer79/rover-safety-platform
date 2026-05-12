"use client";

import { typography } from "@/design-system/typography";
import type { SupervisorDecision } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface SupervisorDecisionLogProps {
  decisions: readonly SupervisorDecision[];
}

export function SupervisorDecisionLog({ decisions }: SupervisorDecisionLogProps) {
  return (
    <TelemetryPanelFrame
      kicker="Supervisor authority"
      title={`${decisions.length} decision${decisions.length === 1 ? "" : "s"}`}
      derivation="supervisor"
      integrity={
        decisions.some((d) => d.decision_status === "rejected")
          ? "rejected"
          : "passed"
      }
    >
      {decisions.length === 0 ? (
        <p className={typography("bodyDense")}>
          No supervisor decisions on disk.
        </p>
      ) : (
        <ul className="space-y-2 text-sm">
          {decisions.slice(0, 6).map((d) => (
            <li
              key={d.decision_id}
              className="rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-2"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-mono text-[12px] text-[color:var(--mc-text)]">
                  {d.decision_id}
                </span>
                <span
                  className={
                    d.decision_status === "rejected"
                      ? "text-[11px] uppercase tracking-[0.16em] text-[color:var(--mc-status-rejected)]"
                      : d.decision_status === "needs_review"
                        ? "text-[11px] uppercase tracking-[0.16em] text-[color:var(--mc-status-warning)]"
                        : "text-[11px] uppercase tracking-[0.16em] text-[color:var(--mc-status-completed)]"
                  }
                >
                  {d.decision_status}
                </span>
              </div>
              {d.rejected_reasons.length > 0 ? (
                <p className="mt-1 text-[12px] text-[color:var(--mc-text-muted)]">
                  reasons · {d.rejected_reasons.join(", ")}
                </p>
              ) : null}
              {d.rationale.length > 0 ? (
                <p className="mt-1 text-[12px] text-[color:var(--mc-text)]">
                  {d.rationale[0]}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </TelemetryPanelFrame>
  );
}

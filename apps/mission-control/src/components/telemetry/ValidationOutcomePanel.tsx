"use client";

import { typography } from "@/design-system/typography";
import type { ValidationDiagnostic } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface ValidationOutcomePanelProps {
  diagnostics: readonly ValidationDiagnostic[];
}

export function ValidationOutcomePanel({
  diagnostics,
}: ValidationOutcomePanelProps) {
  const rejection = diagnostics.filter((d) => d.severity === "rejection").length;
  const warnings = diagnostics.filter((d) => d.severity === "warning").length;
  const info = diagnostics.filter((d) => d.severity === "info").length;

  return (
    <TelemetryPanelFrame
      kicker="Validation outcome"
      title={
        rejection > 0
          ? `${rejection} rejection${rejection === 1 ? "" : "s"}`
          : warnings > 0
            ? `${warnings} warning${warnings === 1 ? "" : "s"}`
            : "no diagnostics"
      }
      derivation="rehearsal_audit.validation_diagnostics"
      integrity={rejection > 0 ? "rejected" : warnings > 0 ? "partial" : "passed"}
    >
      <div className="flex flex-wrap gap-2 text-[11px]">
        <span className="rounded-sm border border-[color:var(--mc-status-rejected)] px-2 py-0.5 text-[color:var(--mc-status-rejected)]">
          rejection · {rejection}
        </span>
        <span className="rounded-sm border border-[color:var(--mc-status-warning)] px-2 py-0.5 text-[color:var(--mc-status-warning)]">
          warning · {warnings}
        </span>
        <span className="rounded-sm border border-[color:var(--mc-accent)] px-2 py-0.5 text-[color:var(--mc-accent)]">
          info · {info}
        </span>
      </div>
      {diagnostics.length === 0 ? (
        <p className={typography("bodyDense") + " mt-2"}>
          No diagnostics emitted.
        </p>
      ) : (
        <ul className="mt-2 space-y-1.5 text-[12px]">
          {diagnostics.slice(0, 8).map((d, idx) => (
            <li
              key={`${d.code}-${idx}`}
              className="rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1"
            >
              <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
                {d.code}
              </span>
              <span className="ml-2 text-[color:var(--mc-text)]">{d.message}</span>
            </li>
          ))}
        </ul>
      )}
    </TelemetryPanelFrame>
  );
}

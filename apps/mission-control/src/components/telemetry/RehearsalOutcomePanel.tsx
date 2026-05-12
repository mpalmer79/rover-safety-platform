"use client";

import { typography } from "@/design-system/typography";
import type { RehearsalAudit } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface RehearsalOutcomePanelProps {
  audits: readonly RehearsalAudit[];
}

export function RehearsalOutcomePanel({ audits }: RehearsalOutcomePanelProps) {
  const sorted = [...audits].sort((a, b) =>
    a.request.mission_id.localeCompare(b.request.mission_id),
  );
  return (
    <TelemetryPanelFrame
      kicker="Rehearsal outcome"
      title={`${sorted.length} audit${sorted.length === 1 ? "" : "s"}`}
      derivation="rehearsal_audit"
      integrity={
        sorted.some((a) => a.final_status === "rejected" || a.final_status === "aborted")
          ? "partial"
          : "passed"
      }
    >
      {sorted.length === 0 ? (
        <p className={typography("bodyDense")}>No audits on disk.</p>
      ) : (
        <ul className="space-y-1.5 text-[12px]">
          {sorted.slice(0, 8).map((audit) => (
            <li
              key={audit.request.request_id}
              className="flex flex-wrap items-baseline justify-between gap-2 rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1"
            >
              <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
                {audit.request.mission_id}
              </span>
              <span className="font-mono text-[11px] text-[color:var(--mc-text-muted)]">
                {audit.final_status} · {audit.safety_status}
              </span>
            </li>
          ))}
        </ul>
      )}
    </TelemetryPanelFrame>
  );
}

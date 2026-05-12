"use client";

import { typography } from "@/design-system/typography";
import type { RehearsalAudit } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface MissionTelemetryPanelProps {
  audit: RehearsalAudit | null;
}

/**
 * High-level mission telemetry derived from the rehearsal audit.
 *
 * Honesty:
 *   * if no audit is supplied, an explicit "no artefact" line is
 *     shown — never a fake value;
 *   * every metric mirrors a field on disk and never recodes it.
 */
export function MissionTelemetryPanel({ audit }: MissionTelemetryPanelProps) {
  const derivation = audit?.runtime ? "rehearsal_runtime" : "rehearsal_audit";
  const integrity =
    audit?.final_status === "completed"
      ? "passed"
      : audit?.final_status === "rejected" || audit?.final_status === "aborted"
        ? "rejected"
        : "partial";

  return (
    <TelemetryPanelFrame
      kicker="Mission telemetry"
      title={audit?.request.mission_id ?? "no audit selected"}
      derivation={derivation}
      integrity={integrity}
    >
      {audit ? (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
          <Metric label="final_status" value={audit.final_status} />
          <Metric label="safety_status" value={audit.safety_status} />
          <Metric
            label="failure_reason"
            value={audit.final_failure_reason || "—"}
          />
          <Metric
            label="proposal_source"
            value={audit.request.proposal_source}
          />
          <Metric
            label="odd_profile"
            value={audit.request.odd_profile_id}
          />
          <Metric
            label="event_count"
            value={String(audit.runtime?.events.length ?? 0)}
          />
        </dl>
      ) : (
        <p className={typography("bodyDense")}>
          No rehearsal audit selected. Telemetry panels render only from
          committed artefacts.
        </p>
      )}
    </TelemetryPanelFrame>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className={typography("label")}>{label}</dt>
      <dd className="font-mono text-[12px] text-[color:var(--mc-text)] break-all">
        {value}
      </dd>
    </div>
  );
}

import Link from "next/link";

import type { RehearsalAudit } from "@/adapters/types";
import { DeterministicHashDisplay } from "./DeterministicHashDisplay";
import { EvidenceStatusChip } from "./EvidenceStatusChip";
import { MissionStateStepper } from "./MissionStateStepper";
import { RiskBandBadge } from "./RiskBandBadge";
import { StatusPill } from "./StatusPill";
import { formatTimestamp } from "@/lib/utils";

interface MissionCardProps {
  audit: RehearsalAudit;
}

/**
 * Compact summary card for a single rehearsal audit. Used on the
 * dashboard and the replay viewer's list pane.
 */
export function MissionCard({ audit }: MissionCardProps) {
  const replay = audit.replay;
  const plan = audit.plan;
  return (
    <Link
      href={`/missions/${audit.request.mission_id}`}
      className="panel block transition-colors hover:border-accent/40"
    >
      <div className="space-y-3 px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="label">{audit.request.request_id}</p>
            <h3 className="display-2">{audit.request.description || audit.request.mission_id}</h3>
          </div>
          <div className="flex flex-col items-end gap-2">
            <StatusPill label={String(audit.final_status)} />
            {plan ? <RiskBandBadge band={plan.risk_band} /> : null}
          </div>
        </div>
        <MissionStateStepper
          status={String(audit.final_status)}
          failureReason={audit.final_failure_reason}
        />
        <div className="flex flex-wrap items-center gap-2 text-xs text-base-600">
          <EvidenceStatusChip
            status={replay?.evidence_status ?? "not_evaluated"}
            bagBacked={Boolean(replay?.bag_backed)}
          />
          {plan ? (
            <DeterministicHashDisplay label="plan" hash={plan.deterministic_hash} />
          ) : null}
          {audit.runtime ? (
            <DeterministicHashDisplay
              label="runtime"
              hash={audit.runtime.deterministic_hash}
            />
          ) : null}
        </div>
        <div className="flex items-baseline justify-between gap-3 text-xs text-base-500">
          <span>generated {formatTimestamp(audit.generated_at_utc)}</span>
          <span>safety: {audit.safety_status}</span>
        </div>
      </div>
    </Link>
  );
}

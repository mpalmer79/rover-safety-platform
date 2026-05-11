import type { RehearsalAudit } from "@/adapters/types";
import { DeterministicHashDisplay } from "./DeterministicHashDisplay";
import { EvidenceStatusChip } from "./EvidenceStatusChip";
import { Panel } from "./Panel";
import { formatTimestamp } from "@/lib/utils";

interface AuditPanelProps {
  audit: RehearsalAudit;
}

/** Right-rail audit summary used on the mission detail screen. */
export function AuditPanel({ audit }: AuditPanelProps) {
  const replay = audit.replay;
  return (
    <Panel
      eyebrow="Audit"
      title="Evidence lineage"
    >
      <dl className="space-y-3 text-sm">
        <div>
          <dt className="label">Generated</dt>
          <dd className="font-mono text-base-700">
            {formatTimestamp(audit.generated_at_utc)}
          </dd>
        </div>
        <div>
          <dt className="label">Final status</dt>
          <dd className="font-mono">{audit.final_status}</dd>
        </div>
        <div>
          <dt className="label">Safety status</dt>
          <dd className="font-mono">{audit.safety_status}</dd>
        </div>
        {audit.final_failure_reason ? (
          <div>
            <dt className="label">Failure reason</dt>
            <dd className="font-mono text-status-rejected">
              {audit.final_failure_reason}
            </dd>
          </div>
        ) : null}
        <div className="space-y-1.5">
          <dt className="label">Deterministic hashes</dt>
          <dd className="space-y-1">
            {audit.plan ? (
              <DeterministicHashDisplay label="plan" hash={audit.plan.deterministic_hash} />
            ) : null}
            {audit.runtime ? (
              <DeterministicHashDisplay
                label="runtime"
                hash={audit.runtime.deterministic_hash}
              />
            ) : null}
            {replay ? (
              <DeterministicHashDisplay
                label="replay"
                hash={replay.deterministic_hash}
              />
            ) : null}
          </dd>
        </div>
        <div>
          <dt className="label">Evidence origin</dt>
          <dd>
            <EvidenceStatusChip
              status={replay?.evidence_status ?? "not_evaluated"}
              bagBacked={Boolean(replay?.bag_backed)}
            />
          </dd>
        </div>
        <div>
          <dt className="label">Disclaimer</dt>
          <dd className="text-xs leading-snug text-base-600">{audit.disclaimer}</dd>
        </div>
      </dl>
    </Panel>
  );
}

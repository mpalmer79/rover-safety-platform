import type { RehearsalAudit, TraceabilitySummary } from "@/adapters/types";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface GovernanceHealthPanelProps {
  audits: readonly RehearsalAudit[];
  traceability: TraceabilitySummary | null;
}

/**
 * Roll-up health snapshot for the dashboard. Aggregates counts
 * across rehearsal audits and reports the deterministic
 * traceability status. Aggregates are integer counts only — no
 * AI-derived metrics, no probabilistic scoring.
 */
export function GovernanceHealthPanel({ audits, traceability }: GovernanceHealthPanelProps) {
  let completed = 0;
  let rejected = 0;
  let aborted = 0;
  let validatorRejections = 0;
  let supervisorRejections = 0;
  for (const audit of audits) {
    const status = String(audit.final_status);
    if (status === "completed") completed += 1;
    else if (status === "rejected") rejected += 1;
    else if (status === "aborted") aborted += 1;
    if (audit.analytics) {
      validatorRejections += audit.analytics.validator_rejection_count;
      supervisorRejections += audit.analytics.supervisor_rejection_count;
    }
  }

  return (
    <Panel
      eyebrow="Programme review"
      title="Governance health"
      trailing={
        traceability ? (
          <StatusPill
            label={traceability.overall_status}
            tone={
              traceability.overall_status === "passed"
                ? "completed"
                : traceability.overall_status === "failed"
                ? "rejected"
                : "pending"
            }
          />
        ) : null
      }
    >
      <dl className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <div>
          <dt className="label">Completed</dt>
          <dd className="display-2 text-status-completed">{completed}</dd>
        </div>
        <div>
          <dt className="label">Rejected</dt>
          <dd className="display-2 text-status-rejected">{rejected}</dd>
        </div>
        <div>
          <dt className="label">Aborted</dt>
          <dd className="display-2 text-status-aborted">{aborted}</dd>
        </div>
        <div>
          <dt className="label">Requirements</dt>
          <dd className="display-2">{traceability?.row_count ?? 0}</dd>
        </div>
        <div>
          <dt className="label">Validator rejections</dt>
          <dd className="font-mono text-base-800">{validatorRejections}</dd>
        </div>
        <div>
          <dt className="label">Supervisor rejections</dt>
          <dd className="font-mono text-base-800">{supervisorRejections}</dd>
        </div>
        <div className="col-span-2">
          <dt className="label">Bag-backed evidence</dt>
          <dd className="font-mono text-base-700">
            0 (Phase 13 maturity remains <span className="text-status-pending">not_established</span>)
          </dd>
        </div>
      </dl>
    </Panel>
  );
}

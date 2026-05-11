import { ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";

import type { SupervisorDecision } from "@/adapters/types";
import { formatTimestamp } from "@/lib/utils";

const STATUS_ICON = {
  approved: <ShieldCheck className="h-5 w-5 text-status-completed" aria-hidden />,
  rejected: <ShieldAlert className="h-5 w-5 text-status-rejected" aria-hidden />,
  needs_review: <ShieldQuestion className="h-5 w-5 text-status-pending" aria-hidden />,
};

interface SupervisorAuthorityPanelProps {
  decision: SupervisorDecision;
}

export function SupervisorAuthorityPanel({ decision }: SupervisorAuthorityPanelProps) {
  const icon = STATUS_ICON[decision.decision_status] ?? STATUS_ICON.needs_review;
  return (
    <section className="panel">
      <header className="flex items-center gap-3 border-b border-base-200 px-4 py-3">
        {icon}
        <div className="space-y-0.5">
          <p className="label">Safety supervisor</p>
          <h2 className="display-2">{decision.decision_status}</h2>
          <p className="text-xs text-base-500">{formatTimestamp(decision.decided_at_utc)}</p>
        </div>
        <span
          className="ml-auto rounded border border-base-300 bg-base-100 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-base-700"
          title={`Safety status: ${decision.safety_status}`}
        >
          {decision.safety_status}
        </span>
      </header>
      <div className="space-y-3 px-4 py-4 text-sm">
        {decision.rationale.length > 0 ? (
          <div>
            <p className="label mb-1">Rationale</p>
            <ul className="space-y-1 text-base-800">
              {decision.rationale.map((line, idx) => (
                <li key={idx} className="leading-snug">{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {decision.rejected_reasons.length > 0 ? (
          <div>
            <p className="label mb-1 text-status-rejected">Rejection reasons</p>
            <ul className="space-y-0.5 font-mono text-xs text-status-rejected">
              {decision.rejected_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <p className="label mb-1">Allowed topics</p>
            <ul className="space-y-0.5 font-mono text-xs">
              {decision.allowed_topics.length === 0 ? (
                <li className="text-base-500">_(none)_</li>
              ) : (
                decision.allowed_topics.map((t) => <li key={t}>{t}</li>)
              )}
            </ul>
          </div>
          <div>
            <p className="label mb-1 text-status-rejected">Forbidden topics</p>
            <ul className="space-y-0.5 font-mono text-xs">
              {decision.forbidden_topics.length === 0 ? (
                <li className="text-base-500">_(none)_</li>
              ) : (
                decision.forbidden_topics.map((t) => (
                  <li key={t} className="text-status-rejected">{t}</li>
                ))
              )}
            </ul>
          </div>
        </div>
        <p className="text-xs text-base-500">
          Human review required: {decision.requires_human_review ? "yes" : "no"}
        </p>
      </div>
    </section>
  );
}

import type { RehearsalAnalytics } from "@/adapters/types";
import { Panel } from "./Panel";

interface ReplayAnalyticsPanelProps {
  analytics: RehearsalAnalytics | null;
}

export function ReplayAnalyticsPanel({ analytics }: ReplayAnalyticsPanelProps) {
  if (!analytics) {
    return (
      <Panel eyebrow="Replay analytics" title="Not evaluated">
        <p className="body-mono">No analytics artefact for this rehearsal.</p>
      </Panel>
    );
  }
  return (
    <Panel eyebrow="Replay analytics" title="Counts">
      <dl className="grid grid-cols-2 gap-3 text-sm">
        {(
          [
            ["Rehearsals", analytics.rehearsal_count],
            ["Approved", analytics.approved_count],
            ["Rejected", analytics.rejected_count],
            ["Aborted", analytics.aborted_count],
            ["Completed", analytics.completed_count],
            ["Validator rejections", analytics.validator_rejection_count],
            ["Supervisor rejections", analytics.supervisor_rejection_count],
            ["Deterministic stable", analytics.deterministic_replay_stable ? "yes" : "no"],
          ] as const
        ).map(([label, value]) => (
          <div key={label}>
            <dt className="label">{label}</dt>
            <dd className="font-mono text-base-800">{String(value)}</dd>
          </div>
        ))}
      </dl>
      {analytics.notes.length > 0 ? (
        <ul className="mt-4 space-y-1 text-xs text-base-600">
          {analytics.notes.map((note) => (
            <li key={note}>• {note}</li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}

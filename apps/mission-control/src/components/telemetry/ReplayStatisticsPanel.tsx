"use client";

import { typography } from "@/design-system/typography";
import type { RehearsalAnalytics, ReplayBundle } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface ReplayStatisticsPanelProps {
  bundle: ReplayBundle | null;
  analytics: RehearsalAnalytics | null;
}

export function ReplayStatisticsPanel({
  bundle,
  analytics,
}: ReplayStatisticsPanelProps) {
  return (
    <TelemetryPanelFrame
      kicker="Replay statistics"
      title={bundle?.mission_id ?? "no bundle"}
      derivation={bundle ? "replay_bundle" : "—"}
      integrity={bundle?.review_status === "passed" ? "passed" : "partial"}
    >
      {bundle === null && analytics === null ? (
        <p className={typography("bodyDense")}>
          No replay bundle or analytics on disk.
        </p>
      ) : (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
          <Stat
            label="evidence_status"
            value={bundle?.evidence_status ?? "—"}
          />
          <Stat
            label="bag_backed"
            value={bundle ? String(bundle.bag_backed) : "—"}
          />
          <Stat
            label="review_status"
            value={bundle?.review_status ?? "—"}
          />
          <Stat
            label="markers"
            value={String(bundle?.replay_markers.length ?? 0)}
          />
          <Stat
            label="rehearsal_count"
            value={String(analytics?.rehearsal_count ?? 0)}
          />
          <Stat
            label="rejection_count"
            value={String(
              (analytics?.supervisor_rejection_count ?? 0) +
                (analytics?.validator_rejection_count ?? 0),
            )}
          />
          <Stat
            label="replay_stable"
            value={
              analytics ? String(analytics.deterministic_replay_stable) : "—"
            }
          />
        </dl>
      )}
    </TelemetryPanelFrame>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className={typography("label")}>{label}</dt>
      <dd className="font-mono text-[12px] text-[color:var(--mc-text)] break-all">
        {value}
      </dd>
    </div>
  );
}

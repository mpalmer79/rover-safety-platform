import Link from "next/link";

import type { RehearsalAudit } from "@/adapters/types";
import { DeterministicHashDisplay } from "./DeterministicHashDisplay";
import { EvidenceStatusChip } from "./EvidenceStatusChip";
import { MissionRouteGlyph } from "./MissionRouteGlyph";
import { MissionStateStepper } from "./MissionStateStepper";
import { RiskBandBadge } from "./RiskBandBadge";
import { StatusPill } from "./StatusPill";
import { formatTimestamp } from "@/lib/utils";

interface MissionCardProps {
  audit: RehearsalAudit;
}

function accentVar(audit: RehearsalAudit): string {
  const status = String(audit.final_status);
  if (status === "rejected") return "var(--mc-status-rejected)";
  if (status === "aborted") return "var(--mc-status-aborted)";
  if (String(audit.safety_status ?? "") === "guarded") {
    return "var(--mc-status-pending)";
  }
  return "var(--mc-accent)";
}

/**
 * Compact summary card for a single rehearsal audit. Used on the
 * dashboard and the replay viewer's list pane. Each card includes a
 * deterministic route-glyph so reviewers can scan the index at a
 * glance without reading every hash.
 */
export function MissionCard({ audit }: MissionCardProps) {
  const replay = audit.replay;
  const plan = audit.plan;
  const accent = accentVar(audit);
  return (
    <Link
      href={`/missions/${audit.request.mission_id}`}
      data-testid="mission-card"
      className="group panel relative block overflow-hidden transition-[transform,box-shadow,border-color] duration-200 hover:-translate-y-0.5 hover:border-[color:var(--mc-accent)]/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]/60"
      style={{
        ["--mc-card-accent" as string]: accent,
      }}
    >
      <span
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px opacity-80"
        style={{
          background:
            "linear-gradient(90deg, transparent 0%, var(--mc-card-accent) 50%, transparent 100%)",
        }}
      />
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(circle at 12% -10%, color-mix(in srgb, var(--mc-card-accent) 22%, transparent) 0%, transparent 55%), radial-gradient(circle at 110% 110%, color-mix(in srgb, var(--mc-card-accent) 14%, transparent) 0%, transparent 60%)",
        }}
      />
      <div className="relative space-y-3 px-4 py-4">
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
        <MissionRouteGlyph audit={audit} className="h-14" />
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

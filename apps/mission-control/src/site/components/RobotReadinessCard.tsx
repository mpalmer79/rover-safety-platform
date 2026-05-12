"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type {
  ReadinessState,
  RobotProfile,
  RobotReadiness,
} from "@/site/models";

interface RobotReadinessCardProps {
  profile: RobotProfile;
  readiness: RobotReadiness;
  className?: string;
}

const READINESS_LABEL: Record<ReadinessState, string> = {
  ready_to_rehearse: "Ready",
  needs_review: "Needs review",
  blocked: "Blocked",
  evidence_missing: "Evidence missing",
  not_evaluated: "Not evaluated",
};

const READINESS_COLOR: Record<ReadinessState, string> = {
  ready_to_rehearse: "var(--mc-status-completed)",
  needs_review: "var(--mc-status-warning)",
  blocked: "var(--mc-status-rejected)",
  evidence_missing: "var(--mc-status-pending)",
  not_evaluated: "var(--mc-text-muted)",
};

export function RobotReadinessCard({
  profile,
  readiness,
  className,
}: RobotReadinessCardProps) {
  return (
    <article
      data-testid="robot-readiness-card"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className={typography("label")}>Robot readiness</p>
          <h3 className={typography("heading")}>{profile.label}</h3>
        </div>
        <span
          className="rounded-full border px-2 py-0.5 text-[11px]"
          style={{
            borderColor: READINESS_COLOR[readiness.state],
            color: READINESS_COLOR[readiness.state],
          }}
        >
          {READINESS_LABEL[readiness.state]}
        </span>
      </header>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[12px]">
        <Info label="platform" value={profile.platform} />
        <Info label="odd_profile" value={profile.odd_profile_id} />
        <Info
          label="bounded_speed_mps"
          value={String(profile.limits.bounded_speed_mps)}
        />
        <Info
          label="bounded_distance_m"
          value={String(profile.limits.bounded_distance_m)}
        />
        <Info
          label="last_rehearsal"
          value={readiness.last_rehearsal_id ?? "—"}
        />
        <Info
          label="rehearsal_status"
          value={readiness.last_rehearsal_status ?? "—"}
        />
      </dl>
      <p className={typography("bodyDense")}>{readiness.reason}</p>
      {readiness.open_issues.length > 0 ? (
        <ul className="list-inside list-disc text-[11px] text-[color:var(--mc-text-muted)]">
          {readiness.open_issues.map((issue, idx) => (
            <li key={idx}>{issue}</li>
          ))}
        </ul>
      ) : null}
      {profile.notes.length > 0 ? (
        <ul className="list-inside list-disc text-[11px] text-[color:var(--mc-text-muted)]">
          {profile.notes.map((note, idx) => (
            <li key={idx}>{note}</li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <dt className={typography("label")}>{label}</dt>
      <dd className="font-mono text-[12px] text-[color:var(--mc-text)] break-all">
        {value}
      </dd>
    </div>
  );
}

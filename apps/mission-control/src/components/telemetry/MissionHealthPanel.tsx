"use client";

import { typography } from "@/design-system/typography";
import type { RehearsalAudit } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface MissionHealthPanelProps {
  audits: readonly RehearsalAudit[];
}

export function MissionHealthPanel({ audits }: MissionHealthPanelProps) {
  const completed = audits.filter((a) => a.final_status === "completed").length;
  const rejected = audits.filter((a) => a.final_status === "rejected").length;
  const aborted = audits.filter((a) => a.final_status === "aborted").length;
  const needsReview = audits.filter(
    (a) => a.safety_status === "requires_review",
  ).length;

  const total = audits.length || 1;
  const ratio = (n: number) => `${Math.round((n / total) * 100)}%`;

  return (
    <TelemetryPanelFrame
      kicker="Mission health"
      title={`${audits.length} rehearsal audit${audits.length === 1 ? "" : "s"}`}
      derivation="rehearsal_audit.*"
      integrity={rejected + aborted > 0 ? "partial" : "passed"}
    >
      <ul className="space-y-1.5 text-[12px]">
        <Bar label="completed" value={completed} ratio={ratio(completed)} tone="completed" />
        <Bar label="rejected" value={rejected} ratio={ratio(rejected)} tone="rejected" />
        <Bar label="aborted" value={aborted} ratio={ratio(aborted)} tone="aborted" />
        <Bar
          label="needs_review"
          value={needsReview}
          ratio={ratio(needsReview)}
          tone="pending"
        />
      </ul>
      {audits.length === 0 ? (
        <p className={typography("caption") + " mt-2"}>
          No audits available. Regenerate with `tools/generate_rehearsal_examples.py`.
        </p>
      ) : null}
    </TelemetryPanelFrame>
  );
}

function Bar({
  label,
  value,
  ratio,
  tone,
}: {
  label: string;
  value: number;
  ratio: string;
  tone: "completed" | "rejected" | "aborted" | "pending";
}) {
  const color =
    tone === "completed"
      ? "var(--mc-status-completed)"
      : tone === "rejected"
        ? "var(--mc-status-rejected)"
        : tone === "aborted"
          ? "var(--mc-status-aborted)"
          : "var(--mc-status-pending)";
  return (
    <li className="space-y-0.5">
      <div className="flex items-baseline justify-between">
        <span className={typography("label")}>{label}</span>
        <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
          {value} · {ratio}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--mc-surface-overlay)]">
        <div
          className="h-full"
          style={{ width: ratio, background: color }}
        />
      </div>
    </li>
  );
}

"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { StepBinding } from "@/reviewer/contextualWalkthrough";

interface WalkthroughEvidenceFocusProps {
  binding: StepBinding;
  className?: string;
}

const STATUS_COLOR: Record<StepBinding["status"], string> = {
  ok: "var(--mc-status-completed)",
  rejected: "var(--mc-status-rejected)",
  partial: "var(--mc-status-warning)",
  unavailable: "var(--mc-text-muted)",
  not_evaluated: "var(--mc-status-pending)",
};

export function WalkthroughEvidenceFocus({
  binding,
  className,
}: WalkthroughEvidenceFocusProps) {
  return (
    <section
      data-testid="walkthrough-evidence-focus"
      data-step={binding.step}
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <p className={typography("label")}>Step evidence</p>
        <span
          className="rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-[0.12em]"
          style={{
            borderColor: STATUS_COLOR[binding.status],
            color: STATUS_COLOR[binding.status],
          }}
        >
          {binding.status}
        </span>
      </header>
      <p className={typography("body")}>{binding.headline}</p>
      <dl className="grid grid-cols-1 gap-x-3 gap-y-1 text-[12px] sm:grid-cols-2">
        <Row label="derivation" value={binding.derivation} />
        <Row label="artifact_status" value={binding.artifactStatus ?? "—"} />
        <Row
          label="artifact_ref"
          value={binding.artifactRef ?? "—"}
          className="sm:col-span-2"
        />
      </dl>
    </section>
  );
}

function Row({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col", className)}>
      <dt className={typography("label")}>{label}</dt>
      <dd className="font-mono text-[12px] text-[color:var(--mc-text)] break-all">
        {value}
      </dd>
    </div>
  );
}

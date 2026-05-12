"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { RehearsalAudit } from "@/adapters/types";

interface WalkthroughMissionFocusProps {
  audit: RehearsalAudit | null;
  className?: string;
}

export function WalkthroughMissionFocus({
  audit,
  className,
}: WalkthroughMissionFocusProps) {
  return (
    <section
      data-testid="walkthrough-mission-focus"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("walkthrough"),
        className,
      )}
    >
      <p className={typography("label")}>Mission focus</p>
      {audit ? (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[12px]">
          <Row label="mission_id" value={audit.request.mission_id} />
          <Row label="request_id" value={audit.request.request_id} />
          <Row label="final_status" value={String(audit.final_status)} />
          <Row label="safety_status" value={String(audit.safety_status)} />
        </dl>
      ) : (
        <p className={typography("bodyDense")}>
          No mission selected. Pick a workspace that targets a mission to bind
          this walkthrough to evidence.
        </p>
      )}
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <dt className={typography("label")}>{label}</dt>
      <dd className="font-mono text-[12px] text-[color:var(--mc-text)] break-all">
        {value}
      </dd>
    </div>
  );
}

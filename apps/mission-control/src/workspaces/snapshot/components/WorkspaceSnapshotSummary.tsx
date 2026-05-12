"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { WorkspaceSnapshotV1 } from "../models";

interface WorkspaceSnapshotSummaryProps {
  snapshot: WorkspaceSnapshotV1;
  className?: string;
}

/**
 * Compact summary of a workspace snapshot — the five fields a
 * reviewer most often needs at a glance.
 */
export function WorkspaceSnapshotSummary({
  snapshot,
  className,
}: WorkspaceSnapshotSummaryProps) {
  return (
    <section
      data-testid="workspace-snapshot-summary"
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <p className={typography("label")}>Snapshot summary</p>
        <span className={typography("caption")}>
          schema · {snapshot.schemaVersion}
        </span>
      </header>
      <dl className="grid grid-cols-1 gap-x-3 gap-y-1 text-[12px] sm:grid-cols-2">
        <Row label="preset" value={snapshot.presetId} />
        <Row label="mission" value={snapshot.missionId ?? "—"} />
        <Row label="replay_run" value={snapshot.replayRunId ?? "—"} />
        <Row label="event" value={snapshot.selectedEventId ?? "—"} />
        <Row label="camera" value={snapshot.cameraMode} />
        <Row
          label="walkthrough_step"
          value={
            snapshot.walkthroughStep === null
              ? "—"
              : `${snapshot.walkthroughStep} / 10`
          }
        />
        <Row label="theme" value={snapshot.theme} />
        <Row label="density" value={snapshot.density} />
        <Row label="evidence" value={snapshot.evidenceFocus.kind} />
        <Row label="evidence_ref" value={snapshot.evidenceFocus.ref ?? "—"} />
      </dl>
      <p className={cn(typography("caption"), "mt-2")}>{snapshot.disclaimer}</p>
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

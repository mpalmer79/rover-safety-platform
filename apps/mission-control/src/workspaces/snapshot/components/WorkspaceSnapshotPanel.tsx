"use client";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";

import type { WorkspaceSnapshotV1 } from "../models";
import { snapshotToJsonString } from "../serializeWorkspaceSnapshot";
import { SnapshotIntegrityBadge } from "./SnapshotIntegrityBadge";

interface WorkspaceSnapshotPanelProps {
  snapshot: WorkspaceSnapshotV1;
  /** When true, displays the integrity badge as "drifted". */
  drifted?: boolean;
  className?: string;
}

/**
 * Renders a snapshot as a copyable JSON block. Pure presentational
 * — no network, no clipboard side effects; the export button is a
 * separate component.
 */
export function WorkspaceSnapshotPanel({
  snapshot,
  drifted = false,
  className,
}: WorkspaceSnapshotPanelProps) {
  return (
    <section
      data-testid="workspace-snapshot-panel"
      data-preset={snapshot.presetId}
      className={cn(
        "flex flex-col gap-3 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className={typography("label")}>Workspace snapshot</p>
          <h2 className={typography("heading")}>{snapshot.presetId}</h2>
        </div>
        <SnapshotIntegrityBadge ok={!drifted} hash={snapshot.snapshotHash} />
      </header>
      <pre
        data-testid="workspace-snapshot-json"
        className={cn(
          "overflow-x-auto rounded-md border px-3 py-2 font-mono text-[11px] leading-relaxed",
          "border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] text-[color:var(--mc-text)]",
        )}
      >
        {snapshotToJsonString(snapshot)}
      </pre>
      <p className={typography("caption")}>
        Copy the JSON above and paste it into a reviewer handoff. The
        snapshot is deterministic — no server, no network, no clipboard
        side effects from this panel.
      </p>
    </section>
  );
}

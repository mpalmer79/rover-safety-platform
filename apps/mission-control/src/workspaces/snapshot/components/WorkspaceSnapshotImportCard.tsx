"use client";

import { useCallback, useMemo, useState } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";

import { parseWorkspaceSnapshot } from "../parseWorkspaceSnapshot";
import { WorkspaceSnapshotSummary } from "./WorkspaceSnapshotSummary";
import { SnapshotIntegrityBadge } from "./SnapshotIntegrityBadge";

interface WorkspaceSnapshotImportCardProps {
  /** Optional initial JSON for tests. */
  initialJson?: string;
  className?: string;
}

/**
 * Paste-and-validate import card. Pure client-side; no network.
 * The card renders the validation result without applying it to
 * any workspace — applying would require route navigation.
 */
export function WorkspaceSnapshotImportCard({
  initialJson = "",
  className,
}: WorkspaceSnapshotImportCardProps) {
  const [text, setText] = useState(initialJson);
  const result = useMemo(() => {
    if (!text.trim()) return null;
    return parseWorkspaceSnapshot(text);
  }, [text]);

  const onChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => setText(e.target.value),
    [],
  );

  return (
    <section
      data-testid="workspace-snapshot-import-card"
      className={cn(
        "flex flex-col gap-3 rounded-lg border p-4",
        "border-[color:var(--mc-border)]",
        surface("panel"),
        className,
      )}
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <p className={typography("label")}>Import snapshot</p>
        {result?.ok && result.snapshot ? (
          <SnapshotIntegrityBadge ok hash={result.snapshot.snapshotHash} />
        ) : null}
      </header>
      <label htmlFor="snapshot-import-textarea" className="sr-only">
        Paste workspace snapshot JSON
      </label>
      <textarea
        id="snapshot-import-textarea"
        value={text}
        onChange={onChange}
        placeholder='{ "schemaVersion": "workspace-snapshot/1", ... }'
        data-testid="workspace-snapshot-import-input"
        className={cn(
          "min-h-[140px] rounded-md border px-3 py-2 font-mono text-[11px]",
          "border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] text-[color:var(--mc-text)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
        )}
      />
      {result && !result.ok ? (
        <ul
          data-testid="workspace-snapshot-import-issues"
          className="list-inside list-disc text-[12px] text-[color:var(--mc-status-rejected)]"
        >
          {result.issues.map((issue, idx) => (
            <li key={idx}>
              <span className="font-mono">{issue.field}</span> — {issue.message}
            </li>
          ))}
        </ul>
      ) : null}
      {result?.ok && result.snapshot ? (
        <WorkspaceSnapshotSummary snapshot={result.snapshot} />
      ) : null}
    </section>
  );
}

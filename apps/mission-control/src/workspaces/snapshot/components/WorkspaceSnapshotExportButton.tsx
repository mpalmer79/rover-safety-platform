"use client";

import { Clipboard, ClipboardCheck } from "lucide-react";
import { useCallback, useState } from "react";

import { cn } from "@/lib/utils";
import type { WorkspaceSnapshotV1 } from "../models";
import { snapshotToJsonString } from "../serializeWorkspaceSnapshot";

interface WorkspaceSnapshotExportButtonProps {
  snapshot: WorkspaceSnapshotV1;
  className?: string;
}

/**
 * Copies the snapshot JSON to the clipboard. Falls back gracefully
 * when the Clipboard API is unavailable (e.g. SSR or sandbox).
 */
export function WorkspaceSnapshotExportButton({
  snapshot,
  className,
}: WorkspaceSnapshotExportButtonProps) {
  const [copied, setCopied] = useState(false);

  const onClick = useCallback(async () => {
    const text = snapshotToJsonString(snapshot);
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1200);
        return;
      } catch {
        // Clipboard write blocked — fall back silently.
      }
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }, [snapshot]);

  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="workspace-snapshot-export"
      data-copied={copied}
      aria-label="Copy snapshot JSON to clipboard"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm",
        "border-[color:var(--mc-accent)] text-[color:var(--mc-accent)]",
        "hover:bg-[color:var(--mc-accent-soft)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
        className,
      )}
    >
      {copied ? (
        <ClipboardCheck aria-hidden className="h-4 w-4" />
      ) : (
        <Clipboard aria-hidden className="h-4 w-4" />
      )}
      {copied ? "Copied" : "Copy JSON"}
    </button>
  );
}

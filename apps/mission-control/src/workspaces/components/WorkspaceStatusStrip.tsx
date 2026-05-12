"use client";

import { Database, GitCommit, ShieldAlert, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";

interface WorkspaceStatusStripProps {
  /** Rehearsal-audit count derived from disk. */
  rehearsalCount: number;
  /** Bag-backed evidence count. Passed verbatim from adapter. */
  bagBackedCount: number;
  /** Requirement row count. */
  requirementCount: number;
  /** Selected mission id (or null when fleet-level). */
  missionId: string | null;
  /** Last bundle generation timestamp (ISO). */
  generatedAtUtc: string | null;
  className?: string;
}

/**
 * The status strip sits just under the workspace topbar. It states
 * the honesty boundary for the active workspace verbatim so the
 * reviewer never has to dig for it.
 */
export function WorkspaceStatusStrip({
  rehearsalCount,
  bagBackedCount,
  requirementCount,
  missionId,
  generatedAtUtc,
  className,
}: WorkspaceStatusStripProps) {
  return (
    <div
      data-testid="workspace-status-strip"
      className={cn(
        "flex flex-wrap items-center gap-2 border-b border-[color:var(--mc-border)] px-3 py-2 text-xs sm:px-5",
        surface("glass"),
        className,
      )}
    >
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5",
          "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
        )}
      >
        <Database aria-hidden className="h-3 w-3 text-[color:var(--mc-accent)]" />
        {rehearsalCount} rehearsal audits
      </span>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5",
          bagBackedCount === 0
            ? "border-[color:var(--mc-status-warning)] text-[color:var(--mc-status-warning)]"
            : "border-[color:var(--mc-status-completed)] text-[color:var(--mc-status-completed)]",
        )}
      >
        <ShieldAlert aria-hidden className="h-3 w-3" />
        bag-backed · {bagBackedCount}
      </span>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5",
          "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
        )}
      >
        <Sparkles aria-hidden className="h-3 w-3 text-[color:var(--mc-accent)]" />
        {requirementCount} requirements
      </span>
      {missionId ? (
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5",
            "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
          )}
        >
          <GitCommit aria-hidden className="h-3 w-3 text-[color:var(--mc-accent)]" />
          mission · {missionId}
        </span>
      ) : (
        <span className={typography("caption")}>fleet-level workspace</span>
      )}
      {generatedAtUtc ? (
        <span className={typography("caption")}>generated · {generatedAtUtc}</span>
      ) : null}
    </div>
  );
}

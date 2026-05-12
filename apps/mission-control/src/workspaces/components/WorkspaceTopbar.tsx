"use client";

import { Activity, ChevronDown, Gauge, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import type { WorkspacePreset } from "@/workspaces/types";

interface WorkspaceTopbarProps {
  preset: WorkspacePreset;
  /** Optional trailing action node (theme toggle, mission switcher). */
  trailing?: ReactNode;
  /** Optional click handler for the preset chip. */
  onOpenSwitcher?: () => void;
}

/**
 * The workspace top bar. Renders the active preset, audience hint,
 * a density indicator, and an honesty pill ("Simulation-only").
 */
export function WorkspaceTopbar({
  preset,
  trailing,
  onOpenSwitcher,
}: WorkspaceTopbarProps) {
  return (
    <header
      data-testid="workspace-topbar"
      data-preset={preset.id}
      className={cn(
        "flex flex-col gap-3 border-b border-[color:var(--mc-border)] px-3 py-3",
        "sm:flex-row sm:items-center sm:justify-between sm:px-5 sm:py-3",
        surface("topbar"),
      )}
    >
      <div className="flex flex-col gap-1">
        <span className={typography("label")}>Operator workspace</span>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onOpenSwitcher}
            data-testid="workspace-topbar-preset"
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-sm font-medium",
              "border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)]",
              "text-[color:var(--mc-text)]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
            )}
            aria-label={`Switch workspace (current: ${preset.title})`}
          >
            <Activity aria-hidden className="h-4 w-4 text-[color:var(--mc-accent)]" />
            {preset.title}
            <ChevronDown aria-hidden className="h-4 w-4 text-[color:var(--mc-text-muted)]" />
          </button>
          <span className={typography("caption")}>{preset.audience}</span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
            "border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] text-[color:var(--mc-text)]",
          )}
        >
          <Gauge aria-hidden className="h-3.5 w-3.5 text-[color:var(--mc-accent)]" />
          density · {preset.density}
        </span>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
            "border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] text-[color:var(--mc-text)]",
          )}
        >
          <ShieldAlert
            aria-hidden
            className="h-3.5 w-3.5 text-[color:var(--mc-status-warning)]"
          />
          Simulation-only · not safety-certified
        </span>
        {trailing}
      </div>
    </header>
  );
}

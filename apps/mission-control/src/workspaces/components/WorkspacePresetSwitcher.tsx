"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import { WORKSPACE_PRESET_IDS, workspacePreset } from "@/workspaces/presets";
import type { WorkspacePresetId } from "@/workspaces/types";

interface WorkspacePresetSwitcherProps {
  active: WorkspacePresetId;
  /** Optional preset filter (e.g. only show review-oriented presets). */
  filter?: (preset: WorkspacePresetId) => boolean;
  className?: string;
}

/**
 * Compact preset switcher. Renders as a list of links so deep links
 * survive a browser refresh.
 */
export function WorkspacePresetSwitcher({
  active,
  filter,
  className,
}: WorkspacePresetSwitcherProps) {
  const ids = filter
    ? WORKSPACE_PRESET_IDS.filter(filter)
    : WORKSPACE_PRESET_IDS;
  return (
    <ul
      data-testid="workspace-preset-switcher"
      className={cn(
        "grid grid-cols-1 gap-2 rounded-md border p-2",
        "border-[color:var(--mc-border)] sm:grid-cols-2 lg:grid-cols-3",
        surface("glass"),
        className,
      )}
    >
      {ids.map((id) => {
        const preset = workspacePreset(id);
        const isActive = active === id;
        return (
          <li key={id}>
            <Link
              href={`/workspaces/${id}`}
              data-active={isActive}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "flex flex-col rounded-md border px-3 py-2 transition-colors",
                "border-[color:var(--mc-border)]",
                isActive
                  ? "bg-[color:var(--mc-accent-soft)] text-[color:var(--mc-accent)]"
                  : "text-[color:var(--mc-text)] hover:bg-[color:var(--mc-surface-overlay)]",
              )}
            >
              <span className="text-sm font-medium">{preset.title}</span>
              <span className={typography("caption")}>{preset.subtitle}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

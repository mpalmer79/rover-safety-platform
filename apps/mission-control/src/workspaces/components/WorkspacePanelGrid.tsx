"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { PANEL_VARIANTS } from "@/design-system/motion";
import { typography } from "@/design-system/typography";
import type {
  WorkspacePanelId,
  WorkspacePanelLayout,
  WorkspacePreset,
} from "@/workspaces/types";

interface WorkspacePanelGridProps {
  preset: WorkspacePreset;
  /**
   * Mapping from panel id to a rendered React node. The grid does
   * NOT take render functions — Next.js server components cannot
   * pass functions across the boundary. Resolve nodes server-side.
   */
  nodes: Partial<Record<WorkspacePanelId, ReactNode>>;
}

function panelClass(layout: WorkspacePanelLayout): string {
  // 12-column desktop grid with deterministic spans. Mobile collapses
  // to a single column; tablet uses six columns.
  const col = layout.colSpan;
  const desktop =
    col >= 12
      ? "xl:col-span-12"
      : col >= 8
        ? "xl:col-span-8"
        : col >= 6
          ? "xl:col-span-6"
          : col >= 5
            ? "xl:col-span-5"
            : col >= 4
              ? "xl:col-span-4"
              : "xl:col-span-3";
  return cn("col-span-1 md:col-span-6", desktop);
}

export function WorkspacePanelGrid({
  preset,
  nodes,
}: WorkspacePanelGridProps) {
  return (
    <div
      data-testid="workspace-panel-grid"
      data-preset={preset.id}
      className={cn(
        "grid gap-3 px-3 py-3 sm:px-5 sm:py-4 md:grid-cols-6 xl:grid-cols-12",
      )}
    >
      {preset.panels.map((layout, idx) => {
        const node = nodes[layout.panel];
        return (
          <motion.section
            key={`${layout.panel}-${idx}`}
            data-testid={`workspace-panel-${layout.panel}`}
            data-panel-id={layout.panel}
            data-col-span={layout.colSpan}
            data-row-span={layout.rowSpan}
            initial="hidden"
            animate="visible"
            variants={PANEL_VARIANTS}
            transition={{ delay: idx * 0.04 }}
            className={cn(
              panelClass(layout),
              "rounded-lg border border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
              surface("panel"),
            )}
            style={
              layout.minHeight
                ? { minHeight: `${layout.minHeight}px` }
                : undefined
            }
          >
            {node ?? (
              <div className="flex h-full min-h-[120px] flex-col items-start justify-center gap-1 px-4 py-4">
                <span className={typography("label")}>panel placeholder</span>
                <span className={typography("bodyDense")}>
                  Renderer for <code>{layout.panel}</code> is not registered for
                  this workspace.
                </span>
              </div>
            )}
          </motion.section>
        );
      })}
    </div>
  );
}

"use client";

import Link from "next/link";
import {
  ClipboardCheck,
  Compass,
  Eye,
  PlayCircle,
  ShieldCheck,
  Users,
} from "lucide-react";
import type { ComponentType, SVGProps } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { typography } from "@/design-system/typography";
import { WORKSPACE_PRESET_IDS, workspacePreset } from "@/workspaces/presets";
import type { WorkspacePresetId } from "@/workspaces/types";

const PRESET_ICON: Record<
  WorkspacePresetId,
  ComponentType<SVGProps<SVGSVGElement>>
> = {
  "mission-review": PlayCircle,
  "safety-review": ShieldCheck,
  "replay-analysis": Compass,
  "evidence-audit": ClipboardCheck,
  "fleet-readiness": Users,
  "reviewer-walkthrough": Eye,
};

interface WorkspaceSidebarProps {
  active: WorkspacePresetId;
  className?: string;
}

export function WorkspaceSidebar({ active, className }: WorkspaceSidebarProps) {
  return (
    <nav
      aria-label="Workspace presets"
      data-testid="workspace-sidebar"
      className={cn(
        "flex w-full flex-col gap-4 border-r border-[color:var(--mc-border)] px-3 py-4",
        surface("sidebar"),
        className,
      )}
    >
      <Link href="/" className="block">
        <p className={typography("label")}>Mission Control</p>
        <p className="font-semibold leading-tight text-[color:var(--mc-text)]">
          Operator Workspace
        </p>
      </Link>
      <ul className="space-y-1 text-sm">
        {WORKSPACE_PRESET_IDS.map((id) => {
          const preset = workspacePreset(id);
          const Icon = PRESET_ICON[id];
          const isActive = active === id;
          return (
            <li key={id}>
              <Link
                href={`/workspaces/${id}`}
                data-active={isActive}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-start gap-2 rounded-md px-2 py-1.5 transition-colors",
                  isActive
                    ? "bg-[color:var(--mc-accent-soft)] text-[color:var(--mc-accent)]"
                    : "text-[color:var(--mc-text)] hover:bg-[color:var(--mc-surface-overlay)]",
                )}
              >
                <Icon aria-hidden className="mt-0.5 h-4 w-4" />
                <span className="flex flex-col leading-tight">
                  <span>{preset.title}</span>
                  <span className={typography("caption")}>{preset.audience}</span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
      <div
        className={cn(
          "mt-3 rounded-md border px-3 py-3 text-[11px] leading-snug",
          "border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] text-[color:var(--mc-text-muted)]",
        )}
      >
        <p className={cn(typography("label"), "mb-1")}>Honesty</p>
        Every panel reads from committed artefacts. No live telemetry, no
        websockets, no cloud APIs.
      </div>
    </nav>
  );
}

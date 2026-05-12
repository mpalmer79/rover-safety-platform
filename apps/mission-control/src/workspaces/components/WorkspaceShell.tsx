"use client";

import { Menu } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";
import { ResponsiveWorkspaceDrawer } from "./ResponsiveWorkspaceDrawer";
import { WorkspaceSidebar } from "./WorkspaceSidebar";
import type { WorkspacePreset } from "@/workspaces/types";

interface WorkspaceShellProps {
  preset: WorkspacePreset;
  topbar: ReactNode;
  statusStrip: ReactNode;
  breadcrumbs?: ReactNode;
  children: ReactNode;
}

/**
 * Operator workspace shell.
 *
 * Layout:
 *   * desktop (xl): persistent 14rem sidebar + main column with
 *     12-column grid;
 *   * tablet (md / lg): persistent 12rem sidebar + 6-column grid;
 *   * tablet portrait + mobile: sticky top bar with drawer trigger.
 *
 * The shell does NOT manage panel state — workspaces are
 * deterministic presets. The drawer is for nav only, never for
 * faking panel persistence.
 */
export function WorkspaceShell({
  preset,
  topbar,
  statusStrip,
  breadcrumbs,
  children,
}: WorkspaceShellProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    setDrawerOpen(false);
  }, [preset.id]);

  return (
    <div
      data-testid="workspace-shell"
      data-preset={preset.id}
      className="grid min-h-[calc(100dvh-2.5rem)] grid-cols-1 md:grid-cols-[12rem_1fr] xl:grid-cols-[14rem_1fr]"
    >
      <MobileBar onToggle={() => setDrawerOpen((v) => !v)} />
      <WorkspaceSidebar
        active={preset.id}
        className="hidden md:flex"
      />
      <main className="min-w-0 overflow-x-hidden">
        {topbar}
        {statusStrip}
        {breadcrumbs ? (
          <div className="border-b border-[color:var(--mc-border)] px-3 py-2 sm:px-5">
            {breadcrumbs}
          </div>
        ) : null}
        {children}
      </main>
      <ResponsiveWorkspaceDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Workspace presets"
      >
        <WorkspaceSidebar active={preset.id} />
      </ResponsiveWorkspaceDrawer>
    </div>
  );
}

function MobileBar({ onToggle }: { onToggle: () => void }) {
  return (
    <div
      data-testid="workspace-mobile-bar"
      className={cn(
        "md:hidden sticky top-0 z-30 flex items-center justify-between border-b border-[color:var(--mc-border)] px-3 py-2",
        surface("topbar"),
      )}
    >
      <span className="text-sm font-semibold text-[color:var(--mc-text)]">
        Operator Workspace
      </span>
      <button
        type="button"
        onClick={onToggle}
        aria-label="Open workspace drawer"
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm",
          "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
        )}
      >
        <Menu aria-hidden className="h-4 w-4" />
        Workspace
      </button>
    </div>
  );
}

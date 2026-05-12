"use client";

import { X } from "lucide-react";
import { useEffect, type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { surface } from "@/design-system/gradients";

interface ResponsiveWorkspaceDrawerProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}

/**
 * Mobile / tablet-portrait drawer. The workspace shell mounts this
 * when the viewport collapses below the multi-panel desktop layout.
 * It is closed by default; opening it never fakes a state change in
 * the underlying workspace.
 */
export function ResponsiveWorkspaceDrawer({
  open,
  onClose,
  title,
  children,
}: ResponsiveWorkspaceDrawerProps) {
  useEffect(() => {
    if (!open) return;
    function handleKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      data-testid="responsive-workspace-drawer"
      role="dialog"
      aria-modal="true"
      aria-label={title ?? "Workspace drawer"}
      className="fixed inset-0 z-40 flex"
    >
      <button
        type="button"
        aria-label="Dismiss workspace drawer"
        onClick={onClose}
        className="flex-1 bg-[color:var(--mc-surface-overlay)] backdrop-blur-sm"
      />
      <aside
        className={cn(
          "flex w-80 max-w-[85vw] flex-col border-l border-[color:var(--mc-border)]",
          surface("sidebar"),
        )}
      >
        <header className="flex items-center justify-between border-b border-[color:var(--mc-border)] px-3 py-2">
          <span className="text-sm font-medium text-[color:var(--mc-text)]">
            {title ?? "Workspace"}
          </span>
          <button
            type="button"
            aria-label="Close drawer"
            onClick={onClose}
            className="rounded-md p-1 text-[color:var(--mc-text)] hover:bg-[color:var(--mc-surface-overlay)]"
          >
            <X aria-hidden className="h-4 w-4" />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto px-3 py-3">{children}</div>
      </aside>
    </div>
  );
}

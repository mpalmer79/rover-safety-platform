"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Folder,
  Layers,
  Menu,
  PlayCircle,
  ShieldCheck,
  X,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: Activity },
  { href: "/workbench", label: "Proposal Workbench", icon: Layers },
  { href: "/replay", label: "Replay Viewer", icon: PlayCircle },
  { href: "/safety", label: "Safety Authority", icon: ShieldCheck },
  { href: "/evidence", label: "Evidence & Audit", icon: Folder },
] as const;

interface ResponsiveShellProps {
  children: ReactNode;
}

/**
 * Responsive layout shell.
 *
 * Desktop / tablet wide:
 *   - persistent left sidebar (14 rem on `lg`, 12 rem on `md`)
 *   - scrollable main column
 *
 * Mobile (< `md`):
 *   - sticky top bar with a hamburger trigger
 *   - drawer-style nav that slides in
 *   - main column fills the viewport with no horizontal overflow
 *
 * Sidebar contents are theme-aware via CSS variables; no harsh
 * black/white surface is rendered.
 */
export function ResponsiveShell({ children }: ResponsiveShellProps) {
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  return (
    <div
      data-testid="responsive-shell"
      className="grid min-h-[calc(100dvh-2.5rem)] grid-cols-1 md:grid-cols-[12rem_1fr] lg:grid-cols-[14rem_1fr]"
    >
      <MobileTopBar
        open={drawerOpen}
        onToggle={() => setDrawerOpen((v) => !v)}
      />
      <Sidebar pathname={pathname} className="hidden md:flex" />
      <main
        className={cn(
          "min-w-0 overflow-y-auto",
          "[scrollbar-gutter:stable_both-edges]",
        )}
      >
        {children}
      </main>

      <MobileDrawer
        open={drawerOpen}
        pathname={pathname}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}

function MobileTopBar({
  open,
  onToggle,
}: {
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      data-testid="mobile-top-bar"
      className={cn(
        "md:hidden",
        "sticky top-0 z-30 flex items-center justify-between px-3 py-2",
        "border-b border-[color:var(--mc-border)]",
        "bg-[linear-gradient(120deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
      )}
    >
      <Link href="/" className="flex flex-col leading-tight">
        <span className="text-[10px] uppercase tracking-[0.2em] text-muted">
          Mission Control
        </span>
        <span className="text-sm font-semibold text-[color:var(--mc-text)]">
          Phase 19
        </span>
      </Link>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-label={open ? "Close navigation drawer" : "Open navigation drawer"}
        data-testid="mobile-nav-toggle"
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm",
          "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
          "bg-[linear-gradient(135deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
        )}
      >
        {open ? <X size={16} aria-hidden /> : <Menu size={16} aria-hidden />}
        Menu
      </button>
    </div>
  );
}

function Sidebar({
  pathname,
  className,
}: {
  pathname: string;
  className?: string;
}) {
  return (
    <nav
      aria-label="Primary"
      data-testid="primary-sidebar"
      className={cn(
        "flex-col gap-4 border-r border-[color:var(--mc-border)] px-3 py-4",
        "bg-[linear-gradient(180deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
        className,
      )}
    >
      <Link href="/" className="block">
        <p className="text-[10px] uppercase tracking-[0.2em] text-muted">
          Mission Control
        </p>
        <p className="font-semibold leading-tight text-[color:var(--mc-text)]">
          Phase 19
        </p>
      </Link>
      <ul className="space-y-1 text-sm">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active =
            pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                data-active={active}
                className={cn(
                  "flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors",
                  active
                    ? "bg-[color:var(--mc-accent-soft)] text-[color:var(--mc-accent)]"
                    : "text-[color:var(--mc-text)] hover:bg-[color:var(--mc-surface-overlay)]",
                )}
              >
                <Icon aria-hidden className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-4 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-3 text-[11px] leading-snug text-muted">
        <p className="mb-1 text-[10px] uppercase tracking-[0.18em]">Honesty</p>
        Simulation-only. Not safety-certified. Bag-backed evidence count remains 0.
      </div>
    </nav>
  );
}

function MobileDrawer({
  open,
  pathname,
  onClose,
}: {
  open: boolean;
  pathname: string;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div
      data-testid="mobile-drawer"
      className={cn(
        "md:hidden",
        "fixed inset-0 z-40 flex",
      )}
    >
      <button
        type="button"
        aria-label="Dismiss navigation drawer"
        onClick={onClose}
        className="flex-1 bg-[color:var(--mc-surface-overlay)] backdrop-blur-sm"
      />
      <div className="w-72 max-w-[80vw] border-l border-[color:var(--mc-border)] bg-[linear-gradient(180deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]">
        <Sidebar pathname={pathname} className="flex" />
      </div>
    </div>
  );
}

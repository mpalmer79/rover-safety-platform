"use client";

import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/lib/theme-provider";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
  /** Medium-sized when ``true`` (used on the dashboard hero). */
  emphasis?: "default" | "medium";
}

/**
 * Light / dark theme toggle.
 *
 * Accessibility:
 *   - ``role=switch`` so screen readers announce the on/off state;
 *   - keyboard activation via Space / Enter (native button behaviour);
 *   - a verbatim ``aria-label`` describing the next state;
 *   - focus ring uses the accent token, which is visible in both
 *     themes.
 *
 * The toggle never flashes harsh black/white during load — the
 * inline bootstrap script in ``layout.tsx`` resolves the initial
 * theme class before the page paints.
 */
export function ThemeToggle({
  className,
  emphasis = "default",
}: ThemeToggleProps) {
  const { theme, toggle, ready } = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  const isMedium = emphasis === "medium";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={theme === "dark"}
      aria-label={`Switch to ${next} theme`}
      data-testid="theme-toggle"
      data-theme={theme}
      data-ready={ready}
      onClick={toggle}
      className={cn(
        "group inline-flex items-center gap-2 rounded-full border transition-colors",
        "border-[color:var(--mc-border)] text-[color:var(--mc-text)]",
        "hover:border-[color:var(--mc-border-strong)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]",
        isMedium
          ? "px-3 py-2 text-sm shadow-sm"
          : "px-2 py-1 text-xs",
        "bg-[linear-gradient(135deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
        className,
      )}
    >
      <span
        aria-hidden
        className={cn(
          "relative inline-flex items-center rounded-full bg-[color:var(--mc-border)] transition-colors",
          isMedium ? "h-6 w-11" : "h-4 w-7",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 left-0.5 rounded-full transition-transform",
            isMedium ? "h-5 w-5" : "h-3 w-3",
            "bg-[linear-gradient(135deg,var(--mc-accent)_0%,var(--mc-accent-soft)_100%)]",
            theme === "dark" ? "translate-x-0" : isMedium ? "translate-x-5" : "translate-x-3",
          )}
        />
      </span>
      <span className="flex items-center gap-1.5 font-medium tracking-tight">
        {theme === "dark" ? (
          <Moon size={isMedium ? 16 : 12} aria-hidden />
        ) : (
          <Sun size={isMedium ? 16 : 12} aria-hidden />
        )}
        <span data-testid="theme-toggle-label">
          {theme === "dark" ? "Dark" : "Light"}
        </span>
        <span className="text-muted text-[10px] uppercase tracking-[0.18em]">
          theme
        </span>
      </span>
    </button>
  );
}

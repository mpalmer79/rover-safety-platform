import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface GradientPanelProps {
  children: ReactNode;
  className?: string;
  /**
   * Tone of the panel surface.
   *
   * - `default` — neutral slate-to-graphite (most panels)
   * - `accent`  — soft teal wash, used for "active" or
   *   authoritative content
   * - `warning` — pending amber wash (use sparingly)
   * - `rejected` — desaturated red wash for failure surfaces
   */
  tone?: "default" | "accent" | "warning" | "rejected";
  /** When `true`, the panel uses the elevated surface (more
   *  shadow, brighter border). */
  elevated?: boolean;
}

const TONE_STYLE: Record<NonNullable<GradientPanelProps["tone"]>, string> = {
  default:
    "bg-[linear-gradient(150deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
  accent:
    "bg-[linear-gradient(150deg,color-mix(in_srgb,var(--mc-accent)_18%,var(--mc-panel-grad-0))_0%,var(--mc-panel-grad-1)_100%)]",
  warning:
    "bg-[linear-gradient(150deg,color-mix(in_srgb,var(--mc-status-warning)_16%,var(--mc-panel-grad-0))_0%,var(--mc-panel-grad-1)_100%)]",
  rejected:
    "bg-[linear-gradient(150deg,color-mix(in_srgb,var(--mc-status-rejected)_14%,var(--mc-panel-grad-0))_0%,var(--mc-panel-grad-1)_100%)]",
};

/**
 * Single-source gradient panel.
 *
 * Components import this rather than re-implementing
 * `bg-[linear-gradient(...)]` ad-hoc, so the design system stays
 * consistent across the dashboard, workbench, replay, and mission
 * detail surfaces.
 */
export function GradientPanel({
  children,
  className,
  tone = "default",
  elevated = false,
}: GradientPanelProps) {
  return (
    <div
      data-testid="gradient-panel"
      data-tone={tone}
      data-elevated={elevated}
      className={cn(
        "rounded-lg border text-[color:var(--mc-text)]",
        "border-[color:var(--mc-border)]",
        TONE_STYLE[tone],
        elevated && "shadow-[0_8px_24px_-12px_rgba(7,9,14,0.6)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

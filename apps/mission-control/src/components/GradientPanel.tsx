import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface GradientPanelProps {
  children: ReactNode;
  className?: string;
  tone?: "default" | "accent" | "warning" | "rejected";
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

/** Shared gradient panel - import instead of re-implementing `bg-[linear-gradient(...)]`. */
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

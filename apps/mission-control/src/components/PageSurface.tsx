import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageSurfaceProps {
  children: ReactNode;
  className?: string;
  /** When set, the surface renders as the dashboard hero. */
  variant?: "page" | "hero";
}

/**
 * Wrapper used by every Mission Control route. Provides:
 *
 *   * a layered gradient background (theme-aware via tokens);
 *   * mobile-first padding (small on phones, generous on desktop);
 *   * a `max-w-7xl` cap so long lines stay readable on wide screens.
 *
 * Components inside the surface inherit the theme tokens through
 * CSS variables — no theme-specific class names required.
 */
export function PageSurface({
  children,
  className,
  variant = "page",
}: PageSurfaceProps) {
  return (
    <div
      data-testid="page-surface"
      data-variant={variant}
      className={cn(
        "relative mx-auto w-full",
        "px-3 py-4 sm:px-5 sm:py-5 lg:px-8 lg:py-7",
        "max-w-7xl",
        variant === "hero" && "surface-hero pt-5 pb-7 sm:pt-6 sm:pb-9",
        className,
      )}
      style={
        variant === "hero"
          ? undefined
          : {
              // Subtle vignette so the page surface separates from
              // the layout background without solid-fill flat.
              background:
                "linear-gradient(180deg, color-mix(in srgb, var(--mc-surface) 0%, transparent) 0%, color-mix(in srgb, var(--mc-surface) 12%, transparent) 100%)",
            }
      }
    >
      {children}
    </div>
  );
}

/**
 * Phase 20 gradient + semantic surface tokens.
 *
 * The dashboard uses gradients for depth, not decoration. Each
 * surface token resolves to a Tailwind class string that consumes
 * the underlying CSS variables (``--mc-*``) declared in
 * ``styles/theme.css``.
 *
 * Surfaces never use pure black/white. Tokens are validated by
 * ``tests/design-tokens.test.ts`` and ``tests/workspace.test.tsx``.
 */

export type SurfaceKey =
  | "panel"
  | "panelElevated"
  | "glass"
  | "hero"
  | "topbar"
  | "sidebar"
  | "telemetry"
  | "walkthrough";

export const SURFACES: Record<SurfaceKey, string> = {
  panel:
    "bg-[linear-gradient(150deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
  panelElevated:
    "bg-[linear-gradient(160deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_60%,color-mix(in_srgb,var(--mc-accent)_8%,var(--mc-panel-grad-1))_100%)]",
  glass: "bg-[color:var(--mc-surface-overlay)] backdrop-blur-md",
  hero:
    "bg-[linear-gradient(140deg,var(--mc-hero-grad-0)_0%,var(--mc-hero-grad-1)_100%)]",
  topbar:
    "bg-[linear-gradient(120deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
  sidebar:
    "bg-[linear-gradient(180deg,var(--mc-panel-grad-0)_0%,var(--mc-panel-grad-1)_100%)]",
  telemetry:
    "bg-[linear-gradient(165deg,var(--mc-panel-grad-0)_0%,color-mix(in_srgb,var(--mc-accent)_6%,var(--mc-panel-grad-1))_100%)]",
  walkthrough:
    "bg-[linear-gradient(155deg,color-mix(in_srgb,var(--mc-accent)_12%,var(--mc-panel-grad-0))_0%,var(--mc-panel-grad-1)_100%)]",
};

export function surface(key: SurfaceKey): string {
  return SURFACES[key];
}

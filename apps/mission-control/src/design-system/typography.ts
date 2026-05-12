/**
 * Phase 20 typography scale.
 *
 * Operator consoles read like flight software: a small set of
 * deliberately differentiated sizes, never an ad-hoc font-size in
 * a component. Each entry maps to a Tailwind className so usage
 * stays consistent across the workspace.
 */

export type TypographyKey =
  | "display"
  | "heading"
  | "subheading"
  | "body"
  | "bodyDense"
  | "mono"
  | "label"
  | "caption";

export const TYPOGRAPHY: Record<TypographyKey, string> = {
  display: "text-2xl sm:text-3xl font-semibold tracking-tight",
  heading: "text-lg sm:text-xl font-semibold tracking-tight",
  subheading: "text-sm sm:text-base font-medium",
  body: "text-sm sm:text-[0.95rem] leading-relaxed",
  bodyDense: "text-[13px] leading-snug",
  mono: "font-mono text-[12px] leading-snug",
  label:
    "text-[10px] uppercase tracking-[0.18em] font-medium text-[color:var(--mc-text-muted)]",
  caption: "text-[11px] text-[color:var(--mc-text-muted)]",
};

export function typography(key: TypographyKey): string {
  return TYPOGRAPHY[key];
}

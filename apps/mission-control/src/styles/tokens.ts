/**
 * Phase 19 design tokens.
 *
 * The platform is **not safety-certified.** Tokens defined here are
 * the SINGLE source of truth for the Mission Control UI. Components
 * import the named tokens (or read the corresponding CSS variables
 * via the ``var(--mc-*)`` accessors) instead of writing raw hex.
 *
 * Hard rules baked into the token set:
 *   * no pure black (#000) anywhere; the darkest dark surface is
 *     `slate-950` ≈ `#0d1117` — an off-black graphite;
 *   * no pure white (#fff) anywhere; the brightest light surface is
 *     `mist-50` ≈ `#f6f8fb` — a warm off-white;
 *   * harsh contrast is avoided; text-on-surface always lands in the
 *     WCAG AA band but never sits on solid black/white;
 *   * gradients are used sparingly and always for depth, never for
 *     decoration.
 */

export type ThemeName = "light" | "dark";

export interface ThemeTokenSet {
  /** Page-level background gradient stops (`from`, `via`, `to`). */
  background: readonly [string, string, string];
  /** Primary surface (cards / panels). */
  surface: string;
  /** Elevated surface (hero panels, immersive frames). */
  surfaceElevated: string;
  /** Translucent overlay surface for hover / glass effects. */
  surfaceOverlay: string;
  /** Default border. */
  border: string;
  /** Strong border for active / authoritative elements. */
  borderStrong: string;
  /** Body text. Never pure black / pure white. */
  text: string;
  /** Muted text (labels, captions). */
  textMuted: string;
  /** Inverted text for accent surfaces. */
  textInverse: string;
  /** Single accent (operator authority signal). */
  accent: string;
  /** Soft accent fill / glow. */
  accentSoft: string;
  /** Status colour ramp. */
  status: {
    completed: string;
    pending: string;
    warning: string;
    rejected: string;
    aborted: string;
  };
  /** Gradient stops for panel / hero surfaces (light + dark). */
  panelGradient: readonly [string, string];
  heroGradient: readonly [string, string];
}

/**
 * Off-black graphite palette. Every dark-mode surface lives on this
 * ramp; the darkest value is `#0d1117` — deliberately not `#000000`.
 */
const DARK: ThemeTokenSet = {
  background: ["#10141c", "#0e1320", "#0c1018"],
  surface: "#161b26",
  surfaceElevated: "#1c2230",
  surfaceOverlay: "rgba(28, 34, 48, 0.72)",
  border: "#262d3e",
  borderStrong: "#3a4258",
  text: "#dbe0ec",
  textMuted: "#8b93a8",
  textInverse: "#0d1117",
  accent: "#5dd6c4",
  accentSoft: "#143733",
  status: {
    completed: "#5fd987",
    pending: "#facc56",
    warning: "#fb923c",
    rejected: "#f87171",
    aborted: "#b39bff",
  },
  panelGradient: ["rgba(28, 34, 48, 0.92)", "rgba(20, 26, 38, 0.92)"],
  heroGradient: ["rgba(31, 41, 59, 0.85)", "rgba(15, 23, 34, 0.95)"],
};

/**
 * Warm off-white pearl palette. Every light-mode surface lives on
 * this ramp; the brightest value is `#f6f8fb` — deliberately not
 * `#ffffff`.
 */
const LIGHT: ThemeTokenSet = {
  background: ["#eef1f6", "#e5e9f1", "#dde2eb"],
  surface: "#f1f4f8",
  surfaceElevated: "#f5f7fb",
  surfaceOverlay: "#e8ecf3",
  border: "#c8cfdb",
  borderStrong: "#9aa4b5",
  text: "#1a2230",
  textMuted: "#4a5468",
  textInverse: "#f1f4f8",
  accent: "#1d8f86",
  accentSoft: "#d5ede9",
  status: {
    completed: "#2f8f4f",
    pending: "#c79018",
    warning: "#c2570f",
    rejected: "#c64545",
    aborted: "#6f57c5",
  },
  panelGradient: ["rgba(251, 252, 254, 0.96)", "rgba(241, 244, 250, 0.96)"],
  heroGradient: ["rgba(247, 250, 255, 0.92)", "rgba(228, 234, 247, 0.92)"],
};

export const TOKENS: Record<ThemeName, ThemeTokenSet> = {
  dark: DARK,
  light: LIGHT,
};

/**
 * The complete set of CSS variable names. Components that need raw
 * CSS values import this map rather than referencing strings.
 */
export const CSS_VAR = {
  background0: "--mc-bg-0",
  background1: "--mc-bg-1",
  background2: "--mc-bg-2",
  surface: "--mc-surface",
  surfaceElevated: "--mc-surface-elevated",
  surfaceOverlay: "--mc-surface-overlay",
  border: "--mc-border",
  borderStrong: "--mc-border-strong",
  text: "--mc-text",
  textMuted: "--mc-text-muted",
  textInverse: "--mc-text-inverse",
  accent: "--mc-accent",
  accentSoft: "--mc-accent-soft",
  statusCompleted: "--mc-status-completed",
  statusPending: "--mc-status-pending",
  statusWarning: "--mc-status-warning",
  statusRejected: "--mc-status-rejected",
  statusAborted: "--mc-status-aborted",
  panelGradient0: "--mc-panel-grad-0",
  panelGradient1: "--mc-panel-grad-1",
  heroGradient0: "--mc-hero-grad-0",
  heroGradient1: "--mc-hero-grad-1",
} as const;

export type CssVarName = (typeof CSS_VAR)[keyof typeof CSS_VAR];

/** All theme names. Useful for tests + the toggle component. */
export const THEME_NAMES: readonly ThemeName[] = ["light", "dark"] as const;

/** Default theme when no preference exists. */
export const DEFAULT_THEME: ThemeName = "dark";

/**
 * Phase 19 honesty rule: no token returned by ``tokenSet`` may
 * resolve to a solid black / solid white value. The tests in
 * ``tests/design-tokens.test.ts`` assert this invariant.
 */
export function tokenSet(theme: ThemeName): ThemeTokenSet {
  return TOKENS[theme];
}

export function cssVarValue(name: CssVarName): string {
  return `var(${name})`;
}

/** Inline-style helper used by client-only components. */
export function gradient(stops: readonly string[]): string {
  return `linear-gradient(135deg, ${stops.join(", ")})`;
}

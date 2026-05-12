/**
 * Phase 20 spacing + operator-density scale.
 *
 * The frontend supports three operator-density modes: ``comfortable``
 * (mobile / reviewer mode), ``standard`` (default desktop), and
 * ``dense`` (mission-review cockpit). Each density resolves to a
 * Tailwind padding scale that components consume via the helpers
 * below.
 */

export type Density = "comfortable" | "standard" | "dense";

export const DENSITY_KEYS: readonly Density[] = [
  "comfortable",
  "standard",
  "dense",
] as const;

interface DensitySpec {
  panelPadding: string;
  panelPaddingTight: string;
  gap: string;
  rowGap: string;
}

export const DENSITY_SCALE: Record<Density, DensitySpec> = {
  comfortable: {
    panelPadding: "px-5 py-4",
    panelPaddingTight: "px-4 py-3",
    gap: "gap-4",
    rowGap: "gap-y-3",
  },
  standard: {
    panelPadding: "px-4 py-3",
    panelPaddingTight: "px-3 py-2",
    gap: "gap-3",
    rowGap: "gap-y-2",
  },
  dense: {
    panelPadding: "px-3 py-2",
    panelPaddingTight: "px-2 py-1.5",
    gap: "gap-2",
    rowGap: "gap-y-1.5",
  },
};

export function densitySpec(density: Density): DensitySpec {
  return DENSITY_SCALE[density];
}

/** Spacing scale used by the design-system. Pure numbers in rem. */
export const SPACING_SCALE: Readonly<Record<string, string>> = {
  "0": "0rem",
  "0.5": "0.125rem",
  "1": "0.25rem",
  "1.5": "0.375rem",
  "2": "0.5rem",
  "3": "0.75rem",
  "4": "1rem",
  "5": "1.25rem",
  "6": "1.5rem",
  "8": "2rem",
  "12": "3rem",
};

/**
 * Phase 20 design-system tests.
 *
 * Pins the typography / spacing / motion / gradient / accessibility
 * tokens so changes are intentional. Asserts contrast helpers
 * compute WCAG-correct values on the canonical token set.
 */

import { describe, it, expect } from "vitest";

import {
  contrastRatio,
  DENSITY_KEYS,
  densitySpec,
  MOTION,
  PANEL_VARIANTS,
  STEP_VARIANTS,
  SURFACES,
  SPACING_SCALE,
  TYPOGRAPHY,
  meetsAA,
  meetsAALarge,
  motionPreset,
  surface,
  typography,
} from "@/design-system";
import { tokenSet } from "@/styles/tokens";

describe("typography scale", () => {
  it("exposes a deterministic set of keys", () => {
    expect(Object.keys(TYPOGRAPHY).sort()).toEqual(
      [
        "body",
        "bodyDense",
        "caption",
        "display",
        "heading",
        "label",
        "mono",
        "subheading",
      ].sort(),
    );
  });

  it("typography() returns the registered class string", () => {
    expect(typography("display")).toBe(TYPOGRAPHY.display);
  });
});

describe("spacing + density", () => {
  it("exposes three density modes", () => {
    expect(DENSITY_KEYS).toEqual(["comfortable", "standard", "dense"]);
  });

  it("density spec ramps tighter as density increases", () => {
    expect(densitySpec("comfortable").panelPadding).toContain("py-4");
    expect(densitySpec("standard").panelPadding).toContain("py-3");
    expect(densitySpec("dense").panelPadding).toContain("py-2");
  });

  it("spacing scale contains the base rungs", () => {
    expect(SPACING_SCALE["0"]).toBe("0rem");
    expect(SPACING_SCALE["4"]).toBe("1rem");
  });
});

describe("motion tokens", () => {
  it("exposes a deterministic preset map", () => {
    expect(motionPreset("panelEnter").duration).toBeGreaterThan(0);
    expect(Object.keys(MOTION)).toContain("scrubber");
  });

  it("panel + step variants have hidden / visible states", () => {
    expect(PANEL_VARIANTS.hidden).toBeDefined();
    expect(PANEL_VARIANTS.visible).toBeDefined();
    expect(STEP_VARIANTS.hidden).toBeDefined();
    expect(STEP_VARIANTS.visible).toBeDefined();
  });
});

describe("gradient surfaces", () => {
  it("every surface resolves to a Tailwind gradient class", () => {
    for (const key of Object.keys(SURFACES) as Array<keyof typeof SURFACES>) {
      const v = surface(key);
      expect(v.length).toBeGreaterThan(0);
      // Pure black/white must never appear in a generated surface.
      expect(v).not.toMatch(/#000(\b|0+)/);
      expect(v).not.toMatch(/#fff(\b|0+)/i);
    }
  });
});

describe("accessibility helpers", () => {
  it("contrastRatio matches the WCAG formula on black + white sentinels", () => {
    // Off-black / off-white sentinels from our token set: at the
    // extreme the contrast is high but not 21:1 because we avoid
    // pure black/white.
    const ratio = contrastRatio("#0d1117", "#f6f8fb");
    expect(ratio).toBeGreaterThan(15);
  });

  it("body text on each theme passes WCAG AA against the surface", () => {
    for (const theme of ["light", "dark"] as const) {
      const set = tokenSet(theme);
      // The off-black/off-white surfaces are hex strings; the panel
      // gradients are rgba and skipped here.
      expect(meetsAA(set.text, set.surface)).toBe(true);
    }
  });

  it("large text passes the relaxed AA-large floor", () => {
    const set = tokenSet("dark");
    expect(meetsAALarge(set.textMuted, set.surface)).toBe(true);
  });
});

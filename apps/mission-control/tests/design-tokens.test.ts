import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";

import {
  CSS_VAR,
  DEFAULT_THEME,
  THEME_NAMES,
  TOKENS,
  tokenSet,
} from "@/styles/tokens";

const SRC_ROOT = path.resolve(__dirname, "../src");

async function* walk(dir: string): AsyncGenerator<string> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(full);
    } else if (
      entry.isFile() &&
      (entry.name.endsWith(".ts") ||
        entry.name.endsWith(".tsx") ||
        entry.name.endsWith(".css"))
    ) {
      yield full;
    }
  }
}

describe("Phase 19 design tokens", () => {
  it("no token resolves to pure black or pure white", () => {
    const forbidden = new Set([
      "#000",
      "#000000",
      "#FFF",
      "#FFFFFF",
      "#fff",
      "#ffffff",
      "black",
      "white",
    ]);
    for (const name of THEME_NAMES) {
      const set = tokenSet(name);
      const all: string[] = [
        ...set.background,
        set.surface,
        set.surfaceElevated,
        set.surfaceOverlay,
        set.border,
        set.borderStrong,
        set.text,
        set.textMuted,
        set.textInverse,
        set.accent,
        set.accentSoft,
        set.status.completed,
        set.status.pending,
        set.status.warning,
        set.status.rejected,
        set.status.aborted,
        ...set.panelGradient,
        ...set.heroGradient,
      ];
      for (const v of all) {
        expect(forbidden.has(v.toLowerCase())).toBe(false);
      }
    }
  });

  it("exports both light and dark token sets", () => {
    expect(TOKENS.light).toBeDefined();
    expect(TOKENS.dark).toBeDefined();
    expect(DEFAULT_THEME).toBe("dark");
  });

  it("declares the full CSS variable map", () => {
    expect(Object.keys(CSS_VAR).length).toBeGreaterThan(15);
    for (const key of Object.values(CSS_VAR)) {
      expect(key.startsWith("--mc-")).toBe(true);
    }
  });
});

describe("source-level honesty rules", () => {
  it("no source file uses bg-black / bg-white / text-black / text-white classes", async () => {
    const forbidden = [
      /\bbg-black\b/,
      /\bbg-white\b/,
      /\btext-black\b/,
      /\btext-white\b/,
    ];
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      for (const pat of forbidden) {
        expect(
          pat.test(text),
          `${file} must not use ${pat}`,
        ).toBe(false);
      }
    }
  });

  it("no source file uses raw #000 / #fff hex values (token violations)", async () => {
    // Tokens themselves are exempt; everything else MUST go through
    // CSS variables / Tailwind tokens.
    const forbidden = [
      /(?<![0-9a-fA-F])#000(?![0-9a-fA-F])/,
      /(?<![0-9a-fA-F])#fff(?![0-9a-fA-F])/i,
      /#000000(?![0-9a-fA-F])/,
      /#ffffff(?![0-9a-fA-F])/i,
    ];
    for await (const file of walk(SRC_ROOT)) {
      // tokens.ts + theme.css are allowed to declare the canonical
      // off-black / off-white values; everything else must use them.
      if (file.endsWith("/tokens.ts") || file.endsWith("/theme.css")) continue;
      const text = await fs.readFile(file, "utf-8");
      for (const pat of forbidden) {
        expect(pat.test(text), `${file} must not use ${pat}`).toBe(false);
      }
    }
  });

  it("dark theme background is off-black, not solid black", () => {
    const dark = tokenSet("dark");
    for (const stop of dark.background) {
      expect(stop.toLowerCase()).not.toBe("#000");
      expect(stop.toLowerCase()).not.toBe("#000000");
    }
  });

  it("light theme background is off-white, not solid white", () => {
    const light = tokenSet("light");
    for (const stop of light.background) {
      expect(stop.toLowerCase()).not.toBe("#fff");
      expect(stop.toLowerCase()).not.toBe("#ffffff");
    }
  });

  it("no light-mode background or surface token reads as near-white", () => {
    // Codify the spirit of the no-pure-white rule: HSL lightness
    // above ~0.974 is visually indistinguishable from white. The
    // current light-mode token values sit at or below 0.973; the
    // pre-Item-5 values (#fbfcfe / #fdfefe / #f6f8fb) all sat
    // above this threshold.
    const NEAR_WHITE_THRESHOLD = 0.974;
    const light = tokenSet("light");
    const surfaceTokens: Array<{ name: string; value: string }> = [
      { name: "background[0]", value: light.background[0] },
      { name: "background[1]", value: light.background[1] },
      { name: "background[2]", value: light.background[2] },
      { name: "surface", value: light.surface },
      { name: "surfaceElevated", value: light.surfaceElevated },
      { name: "surfaceOverlay", value: light.surfaceOverlay },
    ];
    for (const { name, value } of surfaceTokens) {
      const L = hexLightness(value);
      expect(
        L,
        `${name} (${value}) HSL L=${L.toFixed(3)} should be < ${NEAR_WHITE_THRESHOLD}`,
      ).toBeLessThan(NEAR_WHITE_THRESHOLD);
    }
  });
});

function hexLightness(hex: string): number {
  const m = /^#([0-9a-f]{6})$/i.exec(hex);
  if (!m) return 0;
  const v = parseInt(m[1], 16);
  const r = ((v >> 16) & 0xff) / 255;
  const g = ((v >> 8) & 0xff) / 255;
  const b = (v & 0xff) / 255;
  return (Math.max(r, g, b) + Math.min(r, g, b)) / 2;
}

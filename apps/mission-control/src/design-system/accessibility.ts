/**
 * Phase 20 accessibility contrast helpers.
 *
 * These helpers operate on hex strings emitted by the token set and
 * compute WCAG-style relative luminance / contrast ratios. They are
 * used by ``tests/workspace.test.tsx`` to assert every workspace
 * preset stays above the WCAG AA 4.5:1 floor for body text.
 */

function hexToRgb(hex: string): [number, number, number] {
  const normalized = hex.replace(/^#/, "");
  if (normalized.length !== 6) return [0, 0, 0];
  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  return [r, g, b];
}

function channel(c: number): number {
  const v = c / 255;
  return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

export function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex);
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

export function contrastRatio(a: string, b: string): number {
  const la = relativeLuminance(a);
  const lb = relativeLuminance(b);
  const lighter = Math.max(la, lb);
  const darker = Math.min(la, lb);
  return (lighter + 0.05) / (darker + 0.05);
}

export function meetsAA(foreground: string, background: string): boolean {
  return contrastRatio(foreground, background) >= 4.5;
}

export function meetsAALarge(foreground: string, background: string): boolean {
  return contrastRatio(foreground, background) >= 3.0;
}

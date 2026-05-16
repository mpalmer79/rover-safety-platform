/**
 * Visual regression: every primary route, both themes.
 *
 * Baselines live under visual/__screenshots__/ and are committed.
 * CI fails when the rendered route drifts > 0.1% from baseline.
 *
 * To regenerate baselines after an intentional visual change:
 *   npx playwright test visual/routes.spec.ts --update-snapshots
 */

import { expect, test, type Page } from "@playwright/test";

const ROUTES: ReadonlyArray<{ name: string; path: string }> = [
  { name: "dashboard", path: "/" },
  { name: "workbench", path: "/workbench" },
  { name: "replay", path: "/replay" },
  { name: "safety", path: "/safety" },
  { name: "evidence", path: "/evidence" },
  // The mission detail page is dynamic; this is the canonical
  // committed example.
  { name: "mission-warehouse", path: "/missions/warehouse_pickup_route_alpha" },
  // Permanent component catalog (Item 5).
  { name: "catalog", path: "/catalog" },
];

/**
 * Block screenshot capture until MermaidView's async render settles.
 * Without this, full-page screenshots can catch a mid-swap layout
 * shift and Playwright reports per-pixel height jitter between
 * consecutive captures.
 */
async function waitForMermaid(page: Page): Promise<void> {
  await page.waitForFunction(() => {
    const nodes = document.querySelectorAll('[data-mermaid-state]');
    if (nodes.length === 0) return true;
    return Array.from(nodes).every(
      (n) => n.getAttribute("data-mermaid-state") !== "pending",
    );
  });
}

for (const route of ROUTES) {
  test(`${route.name} renders consistently`, async ({ page }) => {
    await page.goto(route.path, { waitUntil: "networkidle" });
    await waitForMermaid(page);
    // Wait for theme bootstrap to finish so light/dark snapshot
    // matches the configured colorScheme.
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));
    await expect(page).toHaveScreenshot(`${route.name}.png`, {
      fullPage: true,
    });
  });
}

/**
 * Visual regression: every primary route, both themes.
 *
 * Baselines live under visual/__screenshots__/ and are committed.
 * CI fails when the rendered route drifts > 0.1% from baseline.
 *
 * To regenerate baselines after an intentional visual change:
 *   npx playwright test visual/routes.spec.ts --update-snapshots
 */

import { expect, test } from "@playwright/test";

const ROUTES: ReadonlyArray<{ name: string; path: string }> = [
  { name: "dashboard", path: "/" },
  { name: "workbench", path: "/workbench" },
  { name: "replay", path: "/replay" },
  { name: "safety", path: "/safety" },
  { name: "evidence", path: "/evidence" },
  // The mission detail page is dynamic; this is the canonical
  // committed example.
  { name: "mission-warehouse", path: "/missions/warehouse_pickup_route_alpha" },
  // Component catalog (Item 5 wires this in for permanent use).
  { name: "catalog", path: "/__visual__" },
];

for (const route of ROUTES) {
  test(`${route.name} renders consistently`, async ({ page }) => {
    await page.goto(route.path, { waitUntil: "networkidle" });
    // Wait for theme bootstrap to finish so light/dark snapshot
    // matches the configured colorScheme.
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));
    await expect(page).toHaveScreenshot(`${route.name}.png`, {
      fullPage: true,
    });
  });
}

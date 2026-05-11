/**
 * Visual regression: per-component snapshots from the catalog.
 *
 * The catalog at /__visual__ (Item 4) — replaced by /catalog in
 * Item 5 — renders every component in its documented state
 * variants. This spec screenshots each catalog card individually
 * so a change to a single component produces a targeted baseline
 * diff rather than a full-page churn.
 *
 * To regenerate baselines after an intentional visual change:
 *   npx playwright test visual/components.spec.ts --update-snapshots
 */

import { expect, test } from "@playwright/test";

test("component catalog page snapshot", async ({ page }) => {
  await page.goto("/__visual__", { waitUntil: "networkidle" });
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));
  await expect(page).toHaveScreenshot("catalog.png", { fullPage: true });
});

test("each catalog card is independently snapshotted", async ({ page }) => {
  await page.goto("/__visual__", { waitUntil: "networkidle" });
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));

  const cards = page.locator('[data-testid^="catalog-card-"]');
  const count = await cards.count();
  for (let i = 0; i < count; i += 1) {
    const card = cards.nth(i);
    const name = (await card.getAttribute("data-testid")) ?? `card-${i}`;
    await expect(card).toHaveScreenshot(`${name}.png`);
  }
});

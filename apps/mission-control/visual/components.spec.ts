/**
 * Visual regression: per-component snapshots from the catalog.
 *
 * The catalog at /catalog renders every component in its documented
 * state variants. This spec screenshots each catalog card
 * individually so a change to a single component produces a
 * targeted baseline diff rather than a full-page churn.
 *
 * To regenerate baselines after an intentional visual change:
 *   npx playwright test visual/components.spec.ts --update-snapshots
 */

import { expect, test, type Page } from "@playwright/test";

/**
 * Wait until every MermaidView on the page has finished its async
 * render (or surfaced an error). MermaidView renders a `<pre>` on the
 * server and swaps it for an SVG after a dynamic import resolves,
 * which produces a layout shift Playwright would otherwise catch in
 * the middle of "stable consecutive screenshot" comparisons. The
 * helper short-circuits when no MermaidView is present.
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

test("component catalog page snapshot", async ({ page }) => {
  await page.goto("/catalog", { waitUntil: "networkidle" });
  await waitForMermaid(page);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));
  await expect(page).toHaveScreenshot("catalog.png", { fullPage: true });
});

test("each catalog card is independently snapshotted", async ({ page }) => {
  await page.goto("/catalog", { waitUntil: "networkidle" });
  await waitForMermaid(page);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(r)));

  const cards = page.locator('[data-testid^="catalog-card-"]');
  const count = await cards.count();
  for (let i = 0; i < count; i += 1) {
    const card = cards.nth(i);
    const name = (await card.getAttribute("data-testid")) ?? `card-${i}`;
    await expect(card).toHaveScreenshot(`${name}.png`);
  }
});

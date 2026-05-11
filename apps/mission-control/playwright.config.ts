import { defineConfig, devices } from "@playwright/test";

/**
 * Visual-regression configuration for the Mission Control frontend.
 *
 * Runs Chromium only (light + dark) at desktop viewport. Screenshots
 * are committed under visual/__screenshots__/ and gated by CI.
 *
 * Hard rules:
 *   - chromium only; firefox / webkit are out of scope to keep CI
 *     time bounded.
 *   - maxDiffPixelRatio 0.001 (≤ 0.1% pixel drift per screenshot).
 *   - the dev server is `next start` against the production build;
 *     no client-side data fetching, the entire UI is static export.
 *
 * Operator bootstrap (run once on a machine with browser-download
 * access; this sandbox cannot reach playwright.azureedge.net):
 *
 *     npx playwright install chromium
 *     npm run build
 *     npx playwright test --update-snapshots
 *
 * Commit the generated PNGs under visual/__screenshots__/.
 */
export default defineConfig({
  testDir: "./visual",
  snapshotDir: "./visual/__screenshots__",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ["html", { outputFolder: "visual/playwright-report", open: "never" }],
    ["list"],
  ],
  use: {
    baseURL: "http://localhost:3000",
    viewport: { width: 1440, height: 900 },
    trace: "retain-on-failure",
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.001,
      animations: "disabled",
    },
  },
  projects: [
    {
      name: "light",
      use: {
        ...devices["Desktop Chrome"],
        colorScheme: "light",
      },
    },
    {
      name: "dark",
      use: {
        ...devices["Desktop Chrome"],
        colorScheme: "dark",
      },
    },
  ],
  webServer: {
    command: "npm run start -- --hostname 127.0.0.1 --port 3000",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});

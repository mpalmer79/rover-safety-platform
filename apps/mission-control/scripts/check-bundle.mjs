#!/usr/bin/env node
/**
 * Bundle budget gate.
 *
 * Reads .next/app-build-manifest.json after `npm run build`,
 * computes the gzipped size of every JS chunk loaded by each
 * route, and exits non-zero if any route exceeds its budget.
 *
 * Budgets are in `apps/mission-control/scripts/bundle-budgets.json`
 * (KB gzipped). They are honest, observed-based starting points;
 * raise them deliberately when an intentional change pushes a
 * route over.
 */

import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import url from "node:url";

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(__dirname, "..");
const NEXT_ROOT = path.join(APP_ROOT, ".next");
const APP_MANIFEST = path.join(NEXT_ROOT, "app-build-manifest.json");
const BUDGETS_PATH = path.join(__dirname, "bundle-budgets.json");

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function gzippedSize(absolutePath) {
  const bytes = fs.readFileSync(absolutePath);
  return zlib.gzipSync(bytes, { level: 9 }).length;
}

function formatKB(bytes) {
  return `${(bytes / 1024).toFixed(1)} KB`;
}

if (!fs.existsSync(APP_MANIFEST)) {
  console.error(
    `error: ${APP_MANIFEST} not found. Run \`npm run build\` first.`,
  );
  process.exit(2);
}

const manifest = readJson(APP_MANIFEST);
const budgets = readJson(BUDGETS_PATH);

// Pages in the manifest end in "/page" for app routes (e.g.
// "/missions/[id]/page"). The budget keys are the user-facing
// route names. Map manifest keys → budget keys.
function manifestKeyToBudgetKey(key) {
  if (key === "/page") return "/";
  if (key.endsWith("/page")) return key.slice(0, -"/page".length);
  return key;
}

const observed = {};
for (const [manifestKey, chunks] of Object.entries(manifest.pages)) {
  // Skip non-route shim entries.
  if (
    manifestKey === "/not-found" ||
    manifestKey === "/_not-found/page" ||
    manifestKey === "/layout" ||
    manifestKey === "/error"
  ) {
    continue;
  }
  if (!manifestKey.endsWith("/page") && manifestKey !== "/page") continue;
  const route = manifestKeyToBudgetKey(manifestKey);
  let total = 0;
  const missing = [];
  for (const chunkRel of chunks) {
    const abs = path.join(NEXT_ROOT, chunkRel);
    if (fs.existsSync(abs)) {
      total += gzippedSize(abs);
    } else {
      missing.push(chunkRel);
    }
  }
  // For parameterised routes, every concrete page (e.g.
  // /missions/warehouse_pickup_route_alpha) shares the same set
  // of chunks. We collapse them under the budget's wildcard key
  // by reporting the max observed size.
  const collapsed =
    route.startsWith("/missions/") && route !== "/missions"
      ? "/missions/[id]"
      : route;
  if (!observed[collapsed] || total > observed[collapsed].bytes) {
    observed[collapsed] = { bytes: total, missing, sampleRoute: route };
  }
}

const results = [];
let anyOver = false;
for (const [route, budget] of Object.entries(budgets)) {
  const obs = observed[route];
  if (!obs) {
    results.push({
      route,
      observed: "—",
      budget: `${budget} KB`,
      status: "MISSING",
    });
    anyOver = true;
    continue;
  }
  const kb = obs.bytes / 1024;
  const over = kb > budget;
  if (over) anyOver = true;
  results.push({
    route,
    observed: `${kb.toFixed(1)} KB`,
    budget: `${budget} KB`,
    status: over ? "OVER" : "ok",
    sample: obs.sampleRoute !== route ? obs.sampleRoute : "",
    missing: obs.missing,
  });
}

console.log("Per-route gzipped JS payload vs. committed budget");
console.log("─".repeat(72));
for (const r of results) {
  const tail = r.sample ? `  (sampled from ${r.sample})` : "";
  console.log(
    `  ${r.status === "OVER" ? "✗" : r.status === "MISSING" ? "?" : "✓"} ` +
      `${r.route.padEnd(20)}  observed ${r.observed.padStart(8)}  /  budget ${r.budget.padStart(8)}${tail}`,
  );
  if (r.missing && r.missing.length > 0) {
    for (const m of r.missing) console.log(`      missing chunk: ${m}`);
  }
}
console.log("─".repeat(72));

if (anyOver) {
  console.error(
    "error: one or more routes exceed their bundle budget. Either reduce the per-route payload OR raise the budget in scripts/bundle-budgets.json with a written justification.",
  );
  process.exit(1);
}
console.log("All routes within budget.");
process.exit(0);

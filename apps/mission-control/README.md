# Mission Control workspace

Phase 17A/17B operator-facing UI for the deterministic autonomy
platform. Static-export Next.js 14, TypeScript, Tailwind, Framer
Motion, Lucide, Mermaid.

The platform is **not safety-certified.** Phase 17B is
simulation-only. The runtime safety supervisor and motion arbitration
remain authoritative.

## Quick start

```
npm install
npm run typecheck   # strict TypeScript
npm run test        # vitest (no network needed)
npm run build       # Next.js static export
npm run dev         # http://localhost:3000
```

## Vercel deployment

The mission-control workspace deploys as a Next.js static
export on Vercel. Vercel auto-detects the framework via Root
Directory set to `apps/mission-control` in the project
settings; `vercel.json` pins the build pipeline in version
control:

```json
{
  "framework": "nextjs",
  "buildCommand": "next build",
  "installCommand": "npm ci",
  "outputDirectory": ".next"
}
```

Every push to `main` that touches `apps/mission-control/**` or
the evidence directories read by the adapter triggers a Vercel
production deploy. Preview deploys run on every branch push.

The deployed container serves prerendered HTML; the adapter's
disk reads happen at build time, so the running site never
touches the evidence files at runtime.

See `docs/adr/ADR-009-vercel-deploy-target.md` for the
migration history.

## Honesty rules

* `src/` never imports a cloud LLM SDK, a generic HTTP client, or
  Node's `child_process` / `net` / `dgram` modules.
* No file calls `publish("/cmd_vel"…)`.
* The `SafetyBoundaryBanner` renders on every page.
* `EvidenceStatusChip` preserves `bag_backed` verbatim.
* Spatial visualisations declare the derivation source on every
  caption — there are no real-world coordinates.
* Rejected missions stay visible across the dashboard, replay
  viewer, and per-mission detail page.
* No frontend deploy may toggle these rules; the CI workflow at
  `.github/workflows/mission-control-ci.yml` enforces them on every
  PR.

## Coverage gating

Frontend test coverage is measured by `@vitest/coverage-v8` and
enforced in CI on every push and pull request.

### Observed baseline

| Pin point | Lines | Statements | Functions | Branches |
|-----------|------:|-----------:|----------:|---------:|
| Item 1 (gate wired in)                                | 59.82 % | 59.82 % | 77.96 % | 63.4 %  |
| Item 2 (route loading.tsx + error.tsx + not-found.tsx) | 59.70 % | 59.70 % | 74.80 % | 64.26 % |
| **Pinned floor (current)**                            | **57 %** | **57 %** | **72 %** | **61 %** |

The pinned floors are honest current floors (`observed − 2`), not
targets. They prevent **regression**; high coverage of trivial
code is worse than honest coverage of safety-relevant components.
Item 2 lowered the functions floor from 75 to 72 because adding
the route-level loading.tsx + not-found.tsx files (deliberately
untested static markup) introduced ~18 new functions. The
error.tsx files ARE exercised by `tests/route-error.test.tsx`.

### Per-file floors on safety-relevant components

The canonical target is **95 % lines + statements + functions, 90 %
branches**. Any file below that target today is pinned at
`observed − 1` and flagged as remediation work below.

| File                                                | Pinned (lines / branches) | Observed | Note |
|-----------------------------------------------------|--------------------------:|---------:|------|
| `src/components/SafetyBoundaryBanner.tsx`           | 95 / 90                   | 100 / 100 | meets target |
| `src/components/SupervisorAuthorityPanel.tsx`       | 0 / 0                     | 0 / 0     | **REMEDIATION**: no test renders the panel today |
| `src/components/SupervisorInterventionOverlay.tsx`  | 95 / 79                   | 100 / 80  | remediation: cover the supervisor-event-subtype branch |
| `src/components/EvidenceStatusChip.tsx`             | 95 / 19                   | 100 / 20  | remediation: cover every `(status, bagBacked)` pair |
| `src/components/RequirementBadge.tsx`               | 95 / 65                   | 100 / 66.66 | remediation: cover the `not_executed` status branch |
| `src/adapters/loader.ts`                            | 89 / 35                   | 90.52 / 36.07 | remediation: cover the deprecated-record-skipped + legacy fallback branches |

### Local invocation

```
npm run test               # runs vitest with the coverage gate
npm run test:no-coverage   # runs vitest WITHOUT the gate (developer iteration)
```

`coverage/lcov.info` + `coverage/index.html` are uploaded as a CI
workflow artifact on every run. Reviewers download from the run's
"Artifacts" section.

### Honesty rules

- The pinned floors are honest current floors, not aspirational
  targets.
- A floor breach fails CI; nothing silently lowers a floor.
- Adding low-value tests to push a number up is explicitly
  discouraged. The remediation entries above name the SPECIFIC
  branch that needs a test, not a coverage chase.

## Visual regression evidence

Mission Control screenshots are committed under
`visual/__screenshots__/` and gated by a Playwright job in CI
(`mission-control-ci.yml::visual-regression`). The baselines are
**evidence artifacts**, not generated files; CI fails when a
rendered page drifts more than 0.1 % from the committed PNG.

Coverage: every primary route (light + dark theme) plus the
`/__visual__` component catalog (Item 5 will promote this to
`/catalog`).

### Operator bootstrap (one-time)

The sandbox that produced Item 4 could not download the Playwright
Chromium binary (the upstream CDN is blocked). The baseline PNGs
are therefore **not yet committed**. An operator with network
access to `playwright.azureedge.net` runs once:

```
cd apps/mission-control
npm ci
npx playwright install chromium
npm run build
npx playwright test --update-snapshots
git add visual/__screenshots__/
git commit -m "frontend: commit Playwright visual-regression baselines"
```

After this bootstrap the gate enforces drift; no further manual
step is needed.

### Regenerating after an intentional visual change

```
npx playwright test --update-snapshots                          # all
npx playwright test visual/routes.spec.ts --update-snapshots    # routes only
```

Review the diff against the previous PNGs before committing.

## Bundle budgets

Per-route gzipped JS payload is gated in CI
(`mission-control-ci.yml::bundle-budget`). Budgets live in
`apps/mission-control/scripts/bundle-budgets.json` and the check
runs via `npm run bundle:check` after a production build.

### Current budgets

| Route             | Observed | Budget   |
|-------------------|---------:|---------:|
| `/`               | 101.5 KB | 250 KB   |
| `/workbench`      | 134.9 KB | 250 KB   |
| `/replay`         |  92.7 KB | 300 KB   |
| `/missions/[id]`  | 105.6 KB | 350 KB   |
| `/safety`         |  86.7 KB | 250 KB   |
| `/evidence`       |  86.1 KB | 250 KB   |
| `/catalog`        | 141.2 KB | 400 KB   |

All observed values are gzipped first-load JS at the time the
gate was wired in. The `/missions/[id]` budget is wider because
the route lazy-loads the Three.js scene (R3F + drei + three)
when the browser supports WebGL. The `/catalog` budget is wider
because the page renders every component in its state variants.

CI fails when any route exceeds its budget. Raising a budget is
a deliberate edit to `scripts/bundle-budgets.json`; the script's
error message explicitly requests a written justification.

### Bundle analyzer (local)

```
ANALYZE=true npm run build      # writes .next/analyze/<route>.html
```

The `bundle-budget` CI job uploads `.next/analyze/` as a workflow
artifact only when invoked with `ANALYZE=true`.

## Where to read next

* **`/catalog`** (local dev) — every component in its documented
  state variants, grouped by concern (safety-authority, mission,
  replay, evidence, spatial, chrome). The fastest way to see what
  Mission Control actually renders. Fixture files at
  `src/components/__fixtures__/<Name>.fixtures.ts` are the single
  source of truth for each component's prop combinations.
* [`docs/MISSION_CONTROL_UI.md`](../../docs/MISSION_CONTROL_UI.md)
* [`docs/MISSION_SPATIAL_VISUALIZATION.md`](../../docs/MISSION_SPATIAL_VISUALIZATION.md)
* [`docs/MISSION_REPLAY_MAPS.md`](../../docs/MISSION_REPLAY_MAPS.md)
* [`docs/SPATIAL_REPLAY_ARCHITECTURE.md`](../../docs/SPATIAL_REPLAY_ARCHITECTURE.md)
* [`docs/OPERATOR_EXPERIENCE_GUIDELINES.md`](../../docs/OPERATOR_EXPERIENCE_GUIDELINES.md)

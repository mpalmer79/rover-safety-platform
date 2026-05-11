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

## Railway deployment

```
railway link
railway up         # uses apps/mission-control/railway.json
```

`railway.json` declares:

* `buildCommand`: `npm ci && npm run typecheck && npm run test && npm run build`;
* `startCommand`: `npm run start -- --hostname 0.0.0.0 --port $PORT`;
* `healthcheckPath`: `/`.

See [`docs/RAILWAY_DEPLOYMENT_GUIDE.md`](../../docs/RAILWAY_DEPLOYMENT_GUIDE.md)
for the operator runbook, including the honesty rules every Railway
deploy preserves.

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

At the time the gate was wired in:

| Metric      | Observed | Pinned floor |
|-------------|---------:|-------------:|
| Lines       | 59.82 %  | **57 %**     |
| Statements  | 59.82 %  | **57 %**     |
| Functions   | 77.96 %  | **75 %**     |
| Branches    | 63.4 %   | **61 %**     |

The pinned floors are honest current floors (`observed − 2`), not
targets. They prevent **regression**; high coverage of trivial
code is worse than honest coverage of safety-relevant components.

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
workflow artefact on every run. Reviewers download from the run's
"Artifacts" section.

### Honesty rules

- The pinned floors are honest current floors, not aspirational
  targets.
- A floor breach fails CI; nothing silently lowers a floor.
- Adding low-value tests to push a number up is explicitly
  discouraged. The remediation entries above name the SPECIFIC
  branch that needs a test, not a coverage chase.

## Where to read next

* [`docs/MISSION_CONTROL_UI.md`](../../docs/MISSION_CONTROL_UI.md)
* [`docs/MISSION_SPATIAL_VISUALIZATION.md`](../../docs/MISSION_SPATIAL_VISUALIZATION.md)
* [`docs/MISSION_REPLAY_MAPS.md`](../../docs/MISSION_REPLAY_MAPS.md)
* [`docs/RAILWAY_DEPLOYMENT_GUIDE.md`](../../docs/RAILWAY_DEPLOYMENT_GUIDE.md)
* [`docs/SPATIAL_REPLAY_ARCHITECTURE.md`](../../docs/SPATIAL_REPLAY_ARCHITECTURE.md)
* [`docs/OPERATOR_EXPERIENCE_GUIDELINES.md`](../../docs/OPERATOR_EXPERIENCE_GUIDELINES.md)

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

## Where to read next

* [`docs/MISSION_CONTROL_UI.md`](../../docs/MISSION_CONTROL_UI.md)
* [`docs/MISSION_SPATIAL_VISUALIZATION.md`](../../docs/MISSION_SPATIAL_VISUALIZATION.md)
* [`docs/MISSION_REPLAY_MAPS.md`](../../docs/MISSION_REPLAY_MAPS.md)
* [`docs/RAILWAY_DEPLOYMENT_GUIDE.md`](../../docs/RAILWAY_DEPLOYMENT_GUIDE.md)
* [`docs/SPATIAL_REPLAY_ARCHITECTURE.md`](../../docs/SPATIAL_REPLAY_ARCHITECTURE.md)
* [`docs/OPERATOR_EXPERIENCE_GUIDELINES.md`](../../docs/OPERATOR_EXPERIENCE_GUIDELINES.md)

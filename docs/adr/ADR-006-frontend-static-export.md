# ADR-006: Frontend Static Export (Next.js App Router, no server runtime)

## Status

Accepted

## Context

The Mission Control workspace at `apps/mission-control/` must
surface the deterministic-autonomy platform's evidence to
reviewers without coupling the UI to a live backend. The platform
already enforces a strict honesty discipline: every claim must be
backed by a committed artefact on disk
(`mission-rehearsals/audits/`, `spatial-replay/runs/`,
`verification/traceability.json`, etc.). A UI that fetched data
over the network at runtime would create a class of behaviours
the rest of the platform deliberately rejects:

- a backend outage could appear to "improve" the page (no failing
  states render);
- a reviewer's session could see different data than another
  reviewer's session;
- the visual regression suite in
  `apps/mission-control/playwright.config.ts` would have to mock
  the backend, defeating the point of rendering the real surface.

Railway hosts the UI today and would not host a Python runtime
without enlarging the trust + deploy surface.

## Decision

The Mission Control UI is shipped as a **fully static export**
from Next.js 14 App Router:

- every server component reads JSON from disk at **build time**
  via the adapter at `apps/mission-control/src/adapters/loader.ts`;
- every route under `apps/mission-control/src/app/` declares
  `export const dynamic = "force-static"` and uses
  `generateStaticParams` for parameterised paths
  (`/missions/[id]`);
- there is **no** `app/api/`, **no** route handler, **no**
  middleware, **no** server-runtime data fetching;
- client components exist only where interactivity is required
  (theme toggle, scrubber, 3-D scene, error.tsx); none of them
  call the backend;
- the Railway service runs `next start` against the prerendered
  output, not against a live Node runtime that talks to a backend.

The adapter is the **only** I/O surface; everything else reads
the adapter's typed return values.

## Consequences

### Positive

- The UI is reproducible bit-for-bit by anyone with the repo;
  visual regression baselines under
  `apps/mission-control/visual/__screenshots__/` are
  deterministic.
- The frontend cannot be undermined by a backend change at
  runtime — only at build time, where the change is observable
  in the diff.
- The honesty test in
  `apps/mission-control/tests/honesty.test.ts` can reasonably ban
  `child_process`, `node:net`, `node:dgram`, and cloud SDK imports
  because no production code needs them.
- The CI workflow at
  `.github/workflows/mission-control-ci.yml` is fast (Node-only,
  no Python service, no database) and stable.

### Negative

- Data changes require a rebuild. A reviewer who lands a new
  audit cannot see it on the deployed Railway URL until the next
  build runs.
- The adapter must handle every missing-file case explicitly (see
  ADR-008). A naive `await fs.readFile` would crash the build.
- Heavy client modules (Three.js, Mermaid) cannot be loaded
  conditionally on the server; they are dynamic-imported on the
  client with `ssr: false` (see
  `apps/mission-control/src/3d/MissionTimelineBridge.tsx`).

### Operational

- Railway's `buildCommand` includes `npm run typecheck`,
  `npm run test`, and `npm run build`. A failing build never
  reaches production.
- The Mission Control CI workflow verifies the prerendered HTML
  contains the `Simulation-only` banner on every page and never
  contains `bag-backed: yes` for fixture runs.

## References

- `apps/mission-control/next.config.mjs`
- `apps/mission-control/railway.json`
- `apps/mission-control/src/adapters/loader.ts`
- `apps/mission-control/src/app/missions/[id]/page.tsx` (canonical
  use of `generateStaticParams`)
- `apps/mission-control/src/app/__visual__` was removed in favour
  of `apps/mission-control/src/app/catalog/page.tsx` (Item 5)
- `apps/mission-control/playwright.config.ts` — visual regression
  runs against the static build, not a stub
- ADR-008 — adapter-level null-on-missing contract

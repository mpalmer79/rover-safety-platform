# ADR-009: Vercel as Deploy Target

## Status
Accepted

## Context
Phase 17B selected Railway as the deploy target on the assumption
that `next start` against committed evidence was the simplest
hosting path. The actual deploy revealed two structural
mismatches with how the app is architected:

1. Railway's Nixpacks builder does not auto-detect a Node project
   in a monorepo subdirectory. The workspace's `package.json`
   lives at `apps/mission-control/package.json`, which Nixpacks
   cannot see from the repo root; without an explicit
   `nixpacksPlan` declaring the Node setup phase, the build
   container has no `npm` available when the build command runs.

2. The app uses `force-static` on every route. The adapter's
   disk reads happen during `next build`, and the resulting
   output is prerendered HTML that needs no Node runtime to
   serve. Railway's per-second compute billing optimises for the
   wrong thing for a static site.

ADR-006 established that the frontend is a static export reading
committed JSON evidence. Vercel's hosting model — automatic
framework detection in subdirectories via Root Directory,
CDN-backed static serving, build-time data baking — matches that
model directly. Railway is a good platform for long-running
services; this app is not one.

## Decision
Migrate frontend hosting to Vercel. Configure the Vercel project
with Root Directory set to `apps/mission-control` and the Next.js
framework preset. Pin the build pipeline in version control via
`apps/mission-control/vercel.json`.

## Consequences
- `apps/mission-control/railway.json` removed.
- `apps/mission-control/.env.example` removed (Railway-specific
  variables; Vercel injects its own runtime environment).
- `docs/RAILWAY_DEPLOYMENT_GUIDE.md` removed.
- `apps/mission-control/vercel.json` added.
- `apps/mission-control/tests/deployment.test.ts` rewritten to
  gate on `vercel.json`.
- The Vercel-issued URL becomes the canonical reviewer entry
  point; referenced in the workspace README.
- Preview deploys run on every branch push, removing the need
  for a separate staging environment.
- `REQ-MVIS-007` updated to reference Vercel artifacts. The
  requirement's intent — frontend deployment preserves honesty-
  boundary rendering — is unchanged; only the deploy mechanism
  it gates is.

## References
- ADR-006: Frontend Static Export
- apps/mission-control/vercel.json
- apps/mission-control/tests/deployment.test.ts

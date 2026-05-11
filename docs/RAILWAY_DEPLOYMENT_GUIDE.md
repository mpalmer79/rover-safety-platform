# Railway Deployment Guide (Phase 17B)

The platform is **not safety-certified.** Phase 17B adds a Railway
deployment lane for the mission-control workspace at
`apps/mission-control/`. Railway hosts the operator UI only;
nothing in the rest of the platform (ROS 2 Jazzy, Gazebo Harmonic,
bag capture, runtime supervisor) runs on Railway, and the
deployment surface has no path to live actuator authority.

## 1. What ships to Railway

```
Railway service: mission-control
├── source: apps/mission-control/
├── runtime: Node.js 22 (NIXPACKS builder)
├── build:   npm ci && npm run typecheck && npm run test && npm run build
└── serve:   npm run start -- --hostname 0.0.0.0 --port $PORT
```

The deployed artefact is the Next.js production server. It reads
committed JSON artefacts from the repository at build time and
serves prerendered HTML + small client bundles. There are no API
routes, no server-side database, no external API calls, and no
ROS / Gazebo dependencies.

## 2. What never ships to Railway

* ROS 2 Jazzy nodes;
* Gazebo Harmonic simulation;
* bag capture / replay-bag tooling;
* the deterministic mission compiler / validator (these run only
  to *produce* the audit JSON the UI reads — they don't run on the
  Railway worker);
* the runtime safety supervisor;
* any cloud LLM SDK.

The Railway deploy is read-only with respect to runtime state.

## 3. `railway.json`

```jsonc
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm ci && npm run typecheck && npm run test && npm run build",
    "watchPatterns": ["src/**", "tests/**", "package.json", ...]
  },
  "deploy": {
    "startCommand": "npm run start -- --hostname 0.0.0.0 --port $PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

The `buildCommand` runs the same honesty gate the CI workflow runs:
typecheck + vitest + Next.js build. A Railway deploy that fails the
gate never reaches the start command.

## 4. Environment variables

`apps/mission-control/.env.example` is the canonical template. The
only variables Railway needs are:

```
PORT=3000
HOSTNAME=0.0.0.0
NEXT_TELEMETRY_DISABLED=1
```

The template explicitly notes the forbidden variables:

* `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, any
  `GENERATIVE_AI_*` key;
* any URL pointing at a non-loopback host.

The Phase 17B honesty tests at
`apps/mission-control/tests/honesty.test.ts` and the deployment
tests at `apps/mission-control/tests/deployment.test.ts` reject
those at lint / build time.

## 5. CI workflow

`.github/workflows/mission-control-ci.yml` runs on every PR
that touches `apps/mission-control/`, `verification/traceability.json`,
`mission-rehearsals/`, or `skill-library/`. The job:

1. installs Node.js 22 with the locked `package-lock.json`;
2. runs `npm ci`;
3. runs `npm run typecheck`;
4. runs `npm run test` (vitest suites);
5. runs `npm run build`;
6. greps every prerendered HTML file for the `Simulation-only`
   safety banner;
7. greps every prerendered HTML file to ensure none claims
   `bag-backed: yes`.

Steps 6 and 7 are the deployment-level honesty gate: a PR that
removes the banner or introduces a fake bag-backed claim fails
this workflow before Railway sees the change.

## 6. Deploying

```
cd apps/mission-control
railway link <project>      # one-time
railway up                   # build + deploy
```

The project's safety boundary is preserved by code, not by
process. If a future operator strips `SafetyBoundaryBanner` from
the layout, both the frontend CI and the Next.js build's
prerendered HTML will fail the disclaimer grep.

## 7. Rollback

```
railway rollback <deployment-id>
```

Rollback is a Railway-native operation; nothing about the platform
needs special handling because the UI is read-only.

## 8. What changes in a future phase

A follow-up phase that wires the UI to a live data source must:

* update `apps/mission-control/.env.example` to document the new
  variable;
* update the AST honesty test to whitelist the new SDK if it lives
  on loopback or behind a documented allowlist;
* update `docs/MISSION_CONTROL_UI.md` and this file with the new
  boundary;
* land an ADR before merging.

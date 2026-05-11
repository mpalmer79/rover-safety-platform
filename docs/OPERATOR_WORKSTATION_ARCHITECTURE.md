# Operator Workstation Architecture (Phase 17A)

The platform is **not safety-certified.** This page documents how
the Phase 17A mission-control workspace at `apps/mission-control/`
is wired together. The architecture is intentionally narrow: a
static-export Next.js app that reads JSON artefacts from disk and
renders them.

## 1. Data flow

```
   deterministic backend pipelines (Phase 13..16)
                       │
                       ▼
   committed JSON artefacts on disk
       mission-rehearsals/audits/<id>/rehearsal-audit.json
       mission-rehearsals/examples/<id>.json
       skill-library/audits/<id>/generated-skill.json
       verification/traceability.json
       live-runtime/live-runtime-maturity.json
                       │
                       ▼
   src/adapters/loader.ts  (Node fs.readFile)
                       │
                       ▼
   typed value objects   (src/adapters/types.ts)
                       │
                       ▼
   server components in src/app/**/page.tsx
                       │
                       ▼
   statically prerendered HTML + CSS + small JS
                       │
                       ▼
   operator browser
```

No API routes, no client-side data fetching, no server-side
runtime fetch.

## 2. Why static export

* **Reproducibility.** Building the workspace twice against the
  same backend artefacts produces identical HTML — the audit's
  deterministic hashes appear in the page source.
* **No network surface.** The compiled bundle never opens a socket;
  removing the entire dev/server runtime from the deployment
  surface keeps the operator workstation safe.
* **No telemetry.** Next.js telemetry is disabled via
  `next.config.mjs`. Tailwind and shadcn-style primitives are
  vendored; no CDN fetches.

## 3. Adapter contract

All artefact reads go through three exports:

| Function                          | Returns                                  |
|-----------------------------------|------------------------------------------|
| `listRehearsalIds`                | sorted directory entries under `audits/` |
| `loadRehearsalAudit(id)`          | `RehearsalAudit` or `null`               |
| `loadRehearsalAudits`             | every audit; rejected ones included      |
| `listMissionLibraryEntries`       | every example file under `examples/`     |
| `loadAcceptedSkills`              | every Phase 15A skill audit              |
| `loadTraceability`                | the canonical `traceability.json`        |
| `loadLiveRuntimeMaturity`         | the Phase 13 maturity file (or `null`)   |

Adapters never invent data:

* A missing artefact returns `null` or an empty array.
* Required JSON fields with bad types are coerced defensively.
* Fields the UI never displays (e.g. arbitrary `payload` blobs)
  are passed through opaquely so a downstream component cannot
  silently rewrite them.

## 4. Component layering

```
   app/<route>/page.tsx
            │  reads + composes
            ▼
   src/components/*.tsx
            │  visual logic
            ▼
   src/lib/utils.ts  (cn, formatTimestamp, shortHash)
```

Server components are the boundary between adapters and the UI.
Client components are reserved for surfaces that genuinely need
browser-side behaviour: the navigation highlight (`SiteNav`), the
staged fade-in on the `CodeCard`, and the Mermaid renderer
(`MermaidView`).

## 5. Testing

Three vitest suites under `apps/mission-control/tests/`:

| Suite                  | Asserts                                                    |
|------------------------|------------------------------------------------------------|
| `adapter.test.ts`      | adapters read the committed artefacts verbatim             |
| `components.test.tsx`  | individual components render the labels they receive       |
| `honesty.test.ts`      | no source file imports a cloud SDK / network module / etc. |

Run with `npm run test`. Tests do not require ROS, Gazebo,
network access, or any real model.

## 6. Deployment shape

Phase 17A does not ship a deployment configuration. The static
output sits under `apps/mission-control/.next/`; a future phase
could publish it via static hosting (Vercel, Netlify, S3, GitHub
Pages, or just `python3 -m http.server` in front of `next export`).
The platform's honesty rules forbid wiring up a real cloud LLM or a
live ROS bridge from the operator console — that is Phase 18+
territory and requires an ADR.

## 7. Future direction

The Workbench currently routes mission requests by selecting from
the committed library. A follow-up phase could add:

* a free-text intent box that exercises the Phase 14A compiler
  via a deterministic Node-side adapter (no API routes; pure
  Python invocation at build time);
* a digital-twin preview that consumes the Phase 16 simulated
  motion stream;
* an operator-attended replay-review flow that surfaces Phase 7
  replay bundles.

All of those require new ADRs and explicit safety-boundary updates
before they ship.

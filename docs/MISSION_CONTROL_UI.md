# Mission Control UI (Phase 17A)

The platform is **not safety-certified.** Phase 17A introduces the
first operator-facing surface for the deterministic autonomy
platform: a static-export Next.js 14 workspace that renders the
backend's deterministic artifacts as a believable mission-control
console.

## 1. Where it lives

```
apps/mission-control/
  package.json
  tsconfig.json
  tailwind.config.ts
  next.config.mjs
  src/
    app/
      layout.tsx
      page.tsx                # Dashboard
      workbench/page.tsx      # Mission Proposal Workbench
      replay/page.tsx         # Replay index
      missions/[id]/page.tsx  # Mission detail view
      safety/page.tsx         # Safety authority diagram
      evidence/page.tsx       # Evidence + traceability explorer
    adapters/
      paths.ts
      loader.ts               # Reads JSON artifacts on disk
      types.ts                # Shared TypeScript shapes
    components/
      SafetyBoundaryBanner.tsx
      SiteNav.tsx
      Panel.tsx
      StatusPill.tsx
      RiskBandBadge.tsx
      EvidenceStatusChip.tsx
      DeterministicHashDisplay.tsx
      MissionStateStepper.tsx
      MissionCard.tsx
      ReplayTimeline.tsx
      CodeCard.tsx
      CompilerDecisionCard.tsx
      SupervisorAuthorityPanel.tsx
      RequirementBadge.tsx
      AuditPanel.tsx
      GovernanceHealthPanel.tsx
      ReplayAnalyticsPanel.tsx
      MermaidView.tsx
    lib/
      utils.ts
  tests/
    setup.ts
    adapter.test.ts
    components.test.tsx
    honesty.test.ts
```

## 2. Stack

* **Next.js 14 App Router** with static export, no API routes.
* **TypeScript** in strict mode.
* **Tailwind CSS** with a calm operator-console palette (slate base,
  muted teal accent, risk + status colour scales).
* **Framer Motion** for sparse, deliberate transitions on the code
  card.
* **Lucide icons** throughout.
* **Mermaid** rendered client-side for state-machine diagrams; the
  server-side fallback is always the raw Mermaid source inside a
  `<pre>` block so the operator can still read the diagram offline.

The dependency footprint is intentionally small: no design system
beyond Tailwind primitives, no global state library, no client-side
data fetching. Pages are server components that read JSON via
`fs.readFile` at build time and prerender statically.

## 3. Five primary screens

| Route               | Purpose                                                                          |
|---------------------|----------------------------------------------------------------------------------|
| `/`                 | Mission-control dashboard. Governance health, recent rehearsals, runtime maturity. |
| `/workbench`        | Mission proposal + skill workbench. Library + code cards.                        |
| `/replay`           | Replay viewer index. Every rehearsal, rejected ones included.                    |
| `/missions/[id]`    | Per-mission detail. Plan + diagnostics + supervisor + timeline + replay + audit. |
| `/safety`           | Safety authority visualisation. Diagram + rules.                                 |
| `/evidence`         | Traceability matrix + requirement explorer.                                      |

All routes are statically generated; the `/missions/[id]` route
generates one static page per committed rehearsal audit at build
time via `generateStaticParams`.

## 4. Adapters

The frontend never invents data. Every panel sources its content
through `src/adapters/loader.ts`, which reads:

* `mission-rehearsals/audits/<id>/rehearsal-audit.json`
* `mission-rehearsals/examples/<id>.json`
* `skill-library/audits/<id>/generated-skill.json`
* `verification/traceability.json`
* `live-runtime/live-runtime-maturity.json` (when present)

When an artifact is missing, the adapter returns `null` and the
panel renders an honest placeholder. No hardcoded fallbacks.

## 5. Honesty rules

The mission-control UI is enforced by tests:

* `tests/honesty.test.ts` walks every `.ts` / `.tsx` file under
  `src/` and asserts none imports a cloud LLM SDK, a generic HTTP
  client, `node:child_process`, `node:net`, or `node:dgram`.
* It also asserts no file contains a `publish("/cmd_vel"` call.
* `tests/components.test.tsx` asserts the `SafetyBoundaryBanner`
  renders the "not safety-certified" line.
* `tests/adapter.test.ts` asserts every replay bundle is
  `bag_backed=false` and `evidence_status=simulated`.

## 6. Run + build

```
cd apps/mission-control
npm install                # one-time
npm run typecheck          # strict TypeScript
npm run test               # vitest (26 tests, no network needed)
npm run build              # next build (static export)
npm run dev                # local dev server on http://localhost:3000
```

The `build` step generates 18 static pages (10 per-mission detail
pages + the 5 primary screens + 1 not-found page + the workbench's
internal subpaths). It runs without ROS, Gazebo, a network, or any
of the deterministic backend pipelines.

## 7. Where to read next

* `docs/AUTONOMY_VISUALIZATION_GUIDE.md` — design rationale for
  each component.
* `docs/OPERATOR_WORKSTATION_ARCHITECTURE.md` — adapter layer + data
  flow.
* `docs/REPLAY_VIEWER_GUIDE.md` — what each row in the replay viewer
  means.
* `docs/SAFETY_AUTHORITY_VISUALIZATION.md` — the strict rules behind
  the safety authority diagram.

## 8. Phase 17B additions

Phase 17B layers a deterministic 2D spatial visualisation on top
of this architecture, plus a Vercel deployment and a
frontend CI workflow:

* `docs/MISSION_SPATIAL_VISUALIZATION.md` — derivation algorithm
  + honesty contract.
* `docs/MISSION_REPLAY_MAPS.md` — per-mission detail composition.
* `docs/SPATIAL_REPLAY_ARCHITECTURE.md` — data flow + determinism
  guarantees.
* `docs/adr/ADR-009-vercel-deploy-target.md` — deploy target
  rationale.
* `docs/OPERATOR_EXPERIENCE_GUIDELINES.md` — UX rules.
* `.github/workflows/mission-control-ci.yml` — typecheck +
  vitest + build + prerendered-HTML honesty grep.
* `apps/mission-control/vercel.json`.

The spatial layer never changes a Phase 17A rule; it adds new
rendering surfaces (`MissionMap`, `MissionPlaybackPanel`,
`ReplayScrubber`, `WhyRejectedDrilldown`, etc.) and new vitest
suites (`tests/spatial.test.ts`, `tests/deployment.test.ts`).

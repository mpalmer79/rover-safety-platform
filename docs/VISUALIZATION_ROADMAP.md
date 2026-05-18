# Visualization Roadmap

This document records the current 3D / pseudo-3D replay status, the
artifact structure required by the public demo route, and the
acceptance criteria for future visualization work.

## Current status (May 2026)

- **Public 3D demo route**: `/demo/warehouse-replay` — canonical
  warehouse mission, rendered in React Three Fiber, driven by
  deterministic pose-sample artifacts. Includes:
  - Animated rover that interpolates between waypoints
  - Play / pause control + timeline scrubber + restart
  - Narrative beats keyed to fractional timeline position
  - Zone overlays (dock, aisle, pickup, restricted)
  - Safety boundary volume + warehouse environment
  - Evidence links back into the mission audit
  - 2D fallback when WebGL is unavailable
- **Per-mission 3D scene**: `/missions/[id]` — existing
  `MissionScene` driven by the rehearsal event scrubber. Falls back
  to the 2D `MissionPlaybackPanel` when the mission has no spatial
  artifact registered.
- **2D scene snapshot**: `SceneSnapshotPanel` continues to surface
  the canonical scene-snapshot artifact metadata.

The 3D code lives under `apps/mission-control/src/3d/` and is
excluded from coverage thresholds (`vitest.config.ts`) because the
Canvas runtime is not exercised under happy-dom.

## Artifact structure

The 3D demo route consumes two artifact families:

1. **Rehearsal audit** — `mission-rehearsals/audits/<id>/rehearsal-audit.json`
   - `final_status`, `request`, `plan`, `runtime.events`,
     `decision`, `validation_diagnostics`, `analytics`, `replay`.
2. **Spatial replay** — `spatial-replay/runs/<id>/spatial-replay.json`
   - `samples` (pose stream), `segments`, `event_alignments`,
     `derivation_source`, `validation_status`, `bag_status`.

Both must be referenced from the canonical artifact registry at
`spatial-replay/registry/canonical-artifacts.json` for the loader to
trust them in the public build.

## Acceptance criteria for future 3D work

A new immersive visualization is acceptable for the public demo when:

- It mounts under a `force-static` route (no SSR/runtime data).
- It is dynamic-imported (`next/dynamic`, `ssr: false`) so static
  HTML never embeds three.js.
- It guards on WebGL support and provides a 2D fallback that still
  carries mission state and evidence links.
- Coordinates come from a committed artifact and the derivation
  source is displayed in the scene overlay.
- Animation is sequence-driven; the same artifact produces the same
  sequence of frames given the same elapsed time.
- The Canvas does not call `fetch`, `WebSocket`, `EventSource`, or
  `localStorage`.
- New components live under `src/3d/` (excluded from coverage) or
  under a route directory; new components in `src/components/` must
  carry a fixture file and an a11y test entry (enforced by
  `tests/honesty.test.ts`).

## Playwright visual regression gate

The `Playwright visual regression` job in
`.github/workflows/mission-control-ci.yml` **auto-skips when no
baselines are committed**. A first step (`Detect committed visual
baselines`) globs for any PNG under
`apps/mission-control/visual/__screenshots__/` and gates every
subsequent step on that result. With no baselines, the job emits a
GitHub notice and exits green — no browser download, no build, no
red X to ignore. As soon as an operator commits baseline PNGs, the
same workflow becomes a hard drift gate without any other change.

This replaces the previous `continue-on-error: true` posture, which
left a permanently-red check on every PR and trained the team to
ignore it.

### Bootstrapping baselines

To turn the gate on, an operator with `playwright.azureedge.net`
browser-download access runs:

```bash
cd apps/mission-control
npm ci
npx playwright install chromium
npm run build
npx playwright test --update-snapshots
```

Then commits the generated PNGs under
`apps/mission-control/visual/__screenshots__/`. The next CI run
will detect the baselines and start enforcing drift; no workflow
change required.

Scope the baselines tightly. The current `visual/routes.spec.ts`
covers `/`, `/workbench`, `/replay`, `/safety`, `/evidence`,
`/missions/warehouse_pickup_route_alpha`, and `/catalog`. Pages that
embed the animated 3D scene (`/start`, `/demo/warehouse-replay`)
are deliberately excluded — pixel-diffing a Three.js canvas during
active UI iteration produces churn without signal. Add them only
when the immersive UI has stabilized.

### What replaces the visual gate for now

The reviewer-experience test suites pin the behavior that matters for
recruiters and technical screeners:

- `tests/reviewer-experience.test.tsx` — navigation chrome, safety
  banner copy, Start Here landing, not-found fallback.
- `tests/warehouse-replay-demo.test.tsx` — demo route controls,
  reviewer copy, evidence links, descriptor invariants.
- `tests/a11y.test.tsx` — axe gate over every component in
  `src/components/`.
- `tests/honesty.test.ts` and `tests/phase20-honesty.test.ts` —
  static-analysis honesty rules.

Until baselines are committed, visual drift is caught by code review
rather than a CI gate.

### MermaidView layout stability

`MermaidView` renders a deterministic `<pre>` server-side and swaps
it for an async-rendered SVG after hydration. The swap previously
caused a few pixels of height jitter that prevented Playwright from
capturing two consecutive stable screenshots of the catalog. The
component now:

- Renders both states inside the same wrapper element so React
  hydration does not cross an element-type boundary.
- Carries a `data-mermaid-state` attribute (`pending` →
  `rendered` / `error`) so the Playwright specs can wait for the
  swap to complete before capture.
- Applies `contain: layout` to isolate the diagram's height changes
  from surrounding flow.

The `visual/*.spec.ts` files share a `waitForMermaid` helper that
blocks until every MermaidView on the page reports a non-pending
state. The helper short-circuits when no MermaidView is present.

## Planned improvements

- **Bag-backed canonical mission**. When a real bag-backed run is
  available, register it under `spatial-replay/registry/` and add a
  second canonical demo so the public flow can illustrate
  bag-backed vs fixture-derived replay side by side.
- **Rejected-mission demo**. Add a second public demo route that
  visualizes a rejected mission so the safety-supervisor authority
  story has a visual anchor.
- **Bootstrap visual baselines**. Once the visual language settles
  (post-portfolio launch), run the bootstrap procedure above and
  commit the PNGs. The CI gate switches on automatically — no
  workflow change required.
- **Add `/demo/warehouse-replay` to the visual suite**. After
  baseline bootstrap, add the demo route to `visual/routes.spec.ts`
  with a `waitForMermaid` + WebGL-canvas-ready wait so the 3D scene
  is captured deterministically.
- **Bundle budget**. Add `/demo/warehouse-replay` to
  `scripts/bundle-budgets.json` once the budget for dynamic-imported
  three.js is set.

## What is explicitly out of scope

- Real-time multi-robot fleet rendering.
- Streaming pose updates over a websocket.
- Photorealistic rover models or surveyed-warehouse environments.
- Anything that would imply live hardware control.

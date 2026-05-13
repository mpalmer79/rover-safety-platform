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

## Planned improvements

- **Bag-backed canonical mission**. When a real bag-backed run is
  available, register it under `spatial-replay/registry/` and add a
  second canonical demo so the public flow can illustrate
  bag-backed vs fixture-derived replay side by side.
- **Rejected-mission demo**. Add a second public demo route that
  visualizes a rejected mission so the safety-supervisor authority
  story has a visual anchor.
- **Visual regression**. Wire `/demo/warehouse-replay` into the
  Playwright visual suite under `apps/mission-control/visual/`.
- **Bundle budget**. Add `/demo/warehouse-replay` to
  `scripts/bundle-budgets.json` once the budget for dynamic-imported
  three.js is set.

## What is explicitly out of scope

- Real-time multi-robot fleet rendering.
- Streaming pose updates over a websocket.
- Photorealistic rover models or surveyed-warehouse environments.
- Anything that would imply live hardware control.

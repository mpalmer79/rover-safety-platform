# Spatial Replay Architecture (Phase 17B → 17C)

The platform is **not safety-certified.** This document records
the architectural shape of the spatial replay layer.

* Phase 17B (this document's original scope) wired a deterministic
  bounded-inputs mission map, scrubber, event projector, and
  per-mission detail page.
* Phase 17C extends the layer with a bag-backed / fixture-derived
  artefact path. See `docs/BAG_BACKED_SPATIAL_REPLAY.md` for the
  full evidence hierarchy and `docs/SPATIAL_REPLAY_HONESTY_RULES.md`
  for the rules that gatekeep the `bag_backed` label.

Phase 17C does not weaken any Phase 0..17B honesty rule; the
bounded-inputs derivation remains the default fallback.

## 1. The data flow

```
                 mission-rehearsals/audits/<id>/rehearsal-audit.json
                                |
                                v
        loadRehearsalAudit(...)  (src/adapters/loader.ts)
                                |
                                v
        buildMissionRoute(plan)  (src/adapters/spatial.ts)
                                |
                                v
        ┌─────────────────┬─────┴─────┬─────────────────┐
        v                 v           v                 v
   MissionMap     MissionRouteList   projectEvents   RouteProgressIndicator
        |                              |
        v                              v
        ┌──────────── MissionPlaybackPanel ────────────┐
                          |
                          v
                  /missions/[id]/page.tsx
                          |
                          v
                  prerendered HTML (Next.js static export)
                          |
                          v
                  Railway / static host
```

Every node in the data flow is a pure function. The build step
runs them once at compile time; the runtime UI re-runs them in
the browser only when the operator drags the scrubber.

## 1b. Phase 17C — bag-backed / fixture data flow

```
                  spatial-replay/runs/<run_id>/spatial-replay.json
                                  |
                                  v
                  loadSpatialReplay(runId)  (loader.ts)
                                  |
                                  v
                  selectMissionRoute(plan, artifact)  (spatial.ts)
                                  |
                                  +---- artifact present, samples > 0
                                  |          and derivation_source ∈
                                  |          {bag_backed, fixture}
                                  v
                  buildMissionRouteFromArtifact(artifact)
                                  |
                                  +---- otherwise
                                  v
                  buildMissionRoute(plan)  (Phase 17B path)
```

Both branches return a `MissionRoute` with the same shape. The
`derivation_source` field is the single source of truth for the
badge + caption text rendered by `MissionMap` and
`SpatialReplayBadge`. See
`docs/SPATIAL_REPLAY_HONESTY_RULES.md::R6` for the fallback rules.

## 2. Determinism guarantees

* `buildMissionRoute` is referentially transparent: identical
  inputs produce identical outputs.
* `projectEvent` consumes a frozen audit event and an immutable
  route; the projected marker carries the same
  `deterministic_hash` as the audit event.
* `fitViewBox` is a pure geometric transform; the same route fits
  the same view box across processes.
* The scrubber state is local to the page (`useState`); resetting
  the page restores the deterministic default.

## 3. Where state lives

| State                  | Location                            | Lifetime           |
|------------------------|-------------------------------------|--------------------|
| route geometry         | `buildMissionRoute` output          | per build          |
| event markers          | `projectEvents` output              | per build          |
| scrubber position      | `useState` in `MissionPlaybackPanel`| per page session   |
| active waypoint id     | `useMemo` on scrubber position      | per page session   |

There is no global store, no SWR, no Redux. The page renders
statically; client interactivity sits inside `MissionPlaybackPanel`
and `ReplayScrubber` only.

## 4. The dock-close-of-route convention

A waypoint with `stage_kind = "dock"` (after the first waypoint)
snaps the cursor back to the origin so the rendered route visually
closes. This is documented because a reviewer who looks at the
audit's waypoint list and the map side-by-side might otherwise
wonder where the dock segment "came from".

The convention applies only to visual rendering; the audit's
waypoint list is unchanged. The map's caption already states the
derivation source so an operator cannot mistake the closing
segment for real telemetry.

## 5. What is intentionally NOT in the architecture

* No real-time streams. No WebSocket, no Server-Sent Events.
* No external API calls. No fetch into a backend service.
* No 3D rendering. No game engine, no canvas WebGL, no Three.js.
* No SLAM, no occupancy grid, no point cloud. Phase 17B uses SVG
  + bounded inputs.
* No user-supplied JavaScript. Every panel is a typed React tree.
* No analytics SDK. No tracking pixel.

## 6. Extension points

A follow-up phase that wires the spatial layer to bag-backed runs
could:

1. add a new `evidence_status = "bag_backed"` branch to
   `buildMissionRoute`;
2. replace the deterministic dock-close convention with the bag's
   actual final pose;
3. update `EvidenceStatusChip` colouring to reflect the new
   origin;
4. extend the Mermaid timeline and the route progress indicator
   to handle a long-running bag's event density.

Each of those extensions requires updating
`docs/MISSION_SPATIAL_VISUALIZATION.md`, the Phase 17B requirements,
and the honesty tests before merging.

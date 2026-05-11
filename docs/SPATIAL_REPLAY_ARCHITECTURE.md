# Spatial Replay Architecture (Phase 17B)

The platform is **not safety-certified.** This document records
the architectural shape of Phase 17B's spatial replay layer: how
the deterministic mission map, the scrubber, the event projector,
and the per-mission detail page fit together without weakening any
Phase 0..17A honesty rule.

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

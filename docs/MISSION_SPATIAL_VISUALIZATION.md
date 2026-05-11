# Mission Spatial Visualization (Phase 17B)

The platform is **not safety-certified.** Phase 17B introduces a
deterministic 2D mission-space visualisation layer to the
mission-control UI. Maps are derived from the same bounded inputs
the deterministic backend already records; no real-world
coordinates exist.

## 1. Honesty contract

Phase 16 audit bundles record bounded motion **requests**:
``bounded_distance_m``, ``bounded_angle_deg``, ``bounded_speed_mps``.
They do NOT record where the rover went, because nothing in Phases
0..16 ran on real hardware.

The Phase 17B map honours that:

* coordinates are computed deterministically from the bounded
  inputs;
* the figure caption ALWAYS reports the derivation source
  (``derived from bounded inputs``, ``topology only``, or
  ``unavailable``);
* an unknown / missing plan renders an explicit placeholder, not an
  empty SVG.

The contract is enforced by tests:

* `apps/mission-control/tests/spatial.test.ts` covers the
  derivation logic;
* `apps/mission-control/tests/components.test.tsx` covers the
  rendered placeholder strings;
* `tests/honesty.test.ts` (extended in Phase 17B) covers the
  forbidden import surface.

## 2. The derivation algorithm

```
   cursor = (0, 0); heading = 0°
   for each waypoint w in plan.waypoints:
       if w.stage_kind in {rotate, turn, spin}:
           heading += w.bounded_angle_deg
       elif w.stage_kind in {move, patrol, inspect} and
            w.bounded_distance_m > 0:
           cursor += (cos(heading), sin(heading)) * w.bounded_distance_m
       elif w.stage_kind == dock:
           cursor = (0, 0)   # visual close-of-route
       emit waypoint at cursor with current heading
```

If every waypoint has zero distance and zero angle, the algorithm
falls back to a deterministic 1m-spaced line along the x-axis with
``derivation_source = "topology_only"``. This is the canonical
"we have topology but no spatial inputs" view.

## 3. Component layer

| Component                       | Role                                                             |
|---------------------------------|------------------------------------------------------------------|
| `MissionMap`                    | SVG renderer for the derived route + event markers              |
| `MissionRouteList`              | Tabular display of bounded inputs per waypoint                  |
| `MissionPlaybackPanel`          | Map + scrubber composite                                        |
| `ReplayScrubber`                | Sequence-based timeline scrubber                                |
| `RouteProgressIndicator`        | Horizontal waypoint progress strip                              |
| `WaypointOverlay`               | Right-rail card with the selected waypoint's bounded values     |
| `MissionEventMarker`            | Legend swatch for severity colours                              |
| `SupervisorInterventionOverlay` | Lists supervisor / safety events that fired during the rehearsal |
| `MissionSpatialTimeline`        | Horizontal coloured timeline of every event in the audit        |
| `SafetyZoneLayer`               | Topic + safety-constraint summary                                |
| `ZoneBoundaryOverlay`           | Boundary-related diagnostics from the audit                     |
| `WarehouseLaneMap`              | Static illustrative warehouse background (no real coordinates)  |

## 4. Adapter contract

The spatial adapter sits in
`apps/mission-control/src/adapters/spatial.ts`. Its public surface:

```ts
buildMissionRoute(plan: MissionPlan | null): MissionRoute
projectEvent(event: RehearsalEvent, route: MissionRoute): SpatialEventMarker
projectEvents(events: readonly RehearsalEvent[], route: MissionRoute): readonly SpatialEventMarker[]
fitViewBox(route: MissionRoute, width?: number, height?: number)
```

`MissionRoute` carries `derivation_source`, `note`, `has_motion`,
`bounds`, and the per-waypoint `SpatialWaypoint[]`. The note string
ALWAYS appears in the map's caption.

## 5. What this layer cannot do

* It cannot render real-time telemetry — there is none.
* It cannot show a real warehouse layout — the `WarehouseLaneMap` is
  decorative; its caption says so.
* It cannot infer position from sensor data — the adapter has no
  sensor input.
* It cannot mark an event as "physically observed" — the event hash
  is the only fidelity anchor.

## 6. Future direction

A follow-up phase that wires the rehearsal pipeline into a real
Gazebo run could replace the derivation with bag-backed positions.
That would require:

* a new `evidence_status` value (e.g. `bag_backed`);
* updated `EvidenceStatusChip` colouring;
* a new ADR explicitly documenting the bag-backed boundary;
* updates to `docs/SPATIAL_REPLAY_ARCHITECTURE.md`.

Until then, every map is simulation-only and labelled accordingly.

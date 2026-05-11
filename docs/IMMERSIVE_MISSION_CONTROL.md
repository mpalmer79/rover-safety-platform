# Immersive Mission Control (Phase 18)

The platform is **not safety-certified.** Phase 18 layers an
immersive 3D mission scene on top of the deterministic Phase
17B/17C mission map. The immersive layer is opt-in (WebGL-gated),
deterministic (no animation loops), and reads exclusively from
committed replay artefacts.

## 1. What's new

```
apps/mission-control/src/3d/
  types.ts                       # shared types + coordinate helpers
  MissionScene.tsx               # top-level R3F canvas
  ReplayTrajectory3D.tsx         # trajectory polyline
  WaypointNode3D.tsx             # waypoint markers
  EventBeacon3D.tsx              # event beacons
  SupervisorIntervention3D.tsx   # rejection-event markers
  SafetyBoundaryVolume.tsx       # illustrative authority volume
  WarehouseEnvironment.tsx       # floor + grid + dock pad
  RobotGhostModel.tsx            # stylised rover ghost
  ReplayCameraRig.tsx            # deterministic camera per mode
  MissionPlayback3D.tsx          # mode tabs + scrubber composite
  MissionTimelineBridge.tsx      # WebGL gate + 2D fallback
```

## 2. Stack

- **React Three Fiber 8.x** for the scene graph.
- **Drei 9.x** for `OrbitControls`, `Html`, and `Grid`.
- **three.js 0.169** as the renderer.
- **framer-motion** (already shipped in Phase 17A) for the few
  subtle 2D transitions outside the canvas.

The 3D module is dynamic-imported with `ssr: false`, so the static
export prerenders an HTML placeholder and the scene mounts on the
client. The build remains a pure static export.

## 3. Playback modes

| Mode                  | Camera distance | Look-at                | When to use            |
|-----------------------|-----------------|------------------------|------------------------|
| overview              | far              | scene centre           | first impression       |
| operator_review       | medium           | active waypoint        | review the active step |
| safety_intervention   | close            | midpoint focus↔centre  | investigate a rejection|
| trajectory_analysis   | top-down         | scene centre           | check the path shape   |

`ReplayCameraRig::chooseTarget` is a pure function; identical
inputs produce identical camera tuples. The rig snaps on mode
change — there is no tween.

## 4. Honesty rules

- The scene reads exclusively from the route returned by
  `selectMissionRoute(plan, artifact)` and the artefact's own
  `event_alignments` for marker positions.
- A bottom-left badge always names the verbatim derivation source
  (`describeDerivationSource`).
- The mode is rendered as a top-right badge so a reviewer can
  always tell which camera they are looking through.
- The scene never imports `rosbag2` / `mcap` / `socket.io` / `ws`
  / `EventSource` — enforced by `hydration-honesty.test.tsx`.
- The scene never calls `setInterval` — animation is driven by
  React state changes (mode + scrubber index).
- When WebGL is unavailable the bridge falls back to the Phase
  17C 2D playback panel; the data path is unchanged.

## 5. What this does NOT do

- It does not stream live telemetry.
- It does not open a network socket.
- It does not parse `.mcap` / `.db3` files.
- It does not animate a robot continuously — the ghost model
  re-positions when the scrubber index changes.
- It does not claim safety certification.
- It does not bypass the safety supervisor or motion arbitration.

## 6. Related docs

- `docs/CINEMATIC_REPLAY_ARCHITECTURE.md`
- `docs/3D_VISUALIZATION_BOUNDARY.md`
- `docs/OPERATOR_REVIEW_EXPERIENCE.md`
- `docs/SPATIAL_REPLAY_HONESTY_RULES.md`

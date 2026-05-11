# Cinematic Replay Architecture (Phase 18)

The platform is **not safety-certified.** This document records
the design of the deterministic cinematic playback layer.

## 1. Design goals

- The playback experience must feel like an autonomy operations
  console, not a game.
- Every camera position must be reproducible from
  `(mode, focus, sceneCenter, sceneRadius)`.
- The scene must read exclusively from committed replay artefacts.
- The scrubber must drive every visible state change — no implicit
  animation loop.

## 2. Camera rig

`apps/mission-control/src/3d/ReplayCameraRig.tsx` exports a
single function:

```ts
chooseTarget(mode, focus, sceneCenter, sceneRadius): CameraTarget
```

`CameraTarget` is `{ position: [x,y,z], lookAt: [x,y,z], label }`.
The rig snaps the perspective camera to that tuple via a single
`useEffect`; there is no tween, no animation loop.

| Mode                | Position formula                                   | LookAt           |
|---------------------|----------------------------------------------------|------------------|
| `overview`          | `center + (radius·1.4, radius·1.0, radius·1.4)`    | scene centre     |
| `operator_review`   | `focus + (1.6, 1.4, 1.6)`                          | focus            |
| `safety_intervention` | `focus + (0.8, 0.9, 0.8)`                        | midpoint(focus, centre) |
| `trajectory_analysis` | `(centre.x, centre.y + radius·1.2, centre.z + radius·0.4)` | scene centre |

## 3. Scene composition

`MissionScene.tsx` renders, in order:

1. `WarehouseEnvironment` — floor, grid, dock pad.
2. `SafetyBoundaryVolume` — illustrative authority outline.
3. `ReplayTrajectory3D` — full + highlighted polyline.
4. `WaypointNode3D` per waypoint, with the active one enlarged.
5. `EventBeacon3D` per projected marker.
6. `SupervisorIntervention3D` per `warning` / `rejection` marker.
7. `RobotGhostModel` at the active waypoint.
8. `OrbitControls` (Drei).

The `SceneOverlay` renders the verbatim derivation source caption
+ playback mode label as 2D HTML overlays.

## 4. Determinism

- `useMemo` is used for all derived geometry.
- `Vector3` instances are constructed inside `useMemo`, never
  inside render.
- The trajectory is split into "full" (dimmed) and "highlight"
  (up to scrubber index) lines; both rebuild only when the route
  or scrubber position changes.
- The camera rig uses `useEffect` with explicit dependencies on
  `(mode, focus, sceneCenter, sceneRadius)`.

## 5. The 2D fallback

`MissionTimelineBridge.tsx` probes for WebGL on mount. When no
WebGL context can be acquired, the bridge renders the Phase 17C
`MissionPlaybackPanel` instead. The fallback never fabricates
data — both paths consume the same artefact + bounded-input route.

## 6. What this does NOT do

- It does not stream live telemetry.
- It does not animate the rover continuously.
- It does not produce randomised camera transitions.
- It does not load external 3D assets (no `.glb`, no `.gltf`).
- It does not touch the network.

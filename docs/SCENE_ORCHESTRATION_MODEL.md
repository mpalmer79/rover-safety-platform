# Scene Orchestration Model

> Deterministic scene cues from workspace state.
> No randomness, no wall-clock timing, no uncontrolled animation loops.

## Why

Phase 20 left the 3D scene beside the workflow. Phase 20B introduces
a deterministic scene-cue model so the scene participates in the
review flow: a walkthrough step selects a cue, the cue maps to a
camera mode, and the scene focuses the corresponding artefact.

## Module layout

`apps/mission-control/src/3d/orchestration/`

```
sceneCueModel.ts            SceneCue + SceneCueKind types
buildSceneCues.ts           combine inputs into ordered cue list
cameraCuePlanner.ts         step → cue kind → camera mode map
eventFocusResolver.ts       focus a specific event by id
supervisorFocusResolver.ts  focus a supervisor decision
trajectoryFocusResolver.ts  follow a spatial-replay trajectory
```

## Scene cue kinds

| Kind                  | Camera mode  | When                                |
| --------------------- | ------------ | ----------------------------------- |
| `overview`            | orbit        | No mission selected                 |
| `operator_request`    | top-down     | Steps 1-2 of the walkthrough        |
| `mission_validation`  | top-down     | Steps 3-5 (sanitizer, compiler, validator) |
| `supervisor_decision` | top-down     | Step 6                              |
| `trajectory_follow`   | follow       | Step 7 + selected event focus       |
| `safety_intervention` | fixed        | Rejected supervisor decision        |
| `replay_evidence`     | follow       | Step 8                              |
| `limitation_focus`    | fixed        | Step 10                             |
| `completion_summary`  | orbit        | Step 9                              |

## Determinism

* `STEP_TO_CUE` is an exhaustive map — every walkthrough step has a
  fixed cue kind.
* `buildSceneCues` is a pure function. Repeated calls with the same
  input return JSON-identical output.
* No resolver uses `Math.random`, `Date.now`, or any wall-clock
  source.
* No continuous uncontrolled animation loop is introduced. Camera
  transitions are driven by parent-controlled state, not setInterval.

## Tests

`apps/mission-control/tests/scene-orchestration.test.ts` pins:

* `STEP_TO_CUE` covers every walkthrough step;
* `buildSceneCues` is deterministic under repeat calls;
* `resolveEventFocus` returns `null` for unknown event ids;
* `resolveSupervisorFocus` surfaces rejected decisions as
  `safety_intervention`;
* `resolveTrajectoryFocus` returns `null` for missing artefacts;
* `activeSceneCue` falls back to `overview` when no input applies.

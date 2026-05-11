# Mission rehearsals — Phase 16

This directory holds the canonical examples and audit bundles for
the Phase 16 governed mission-to-rehearsal pipeline.

The platform is **not safety-certified.** Every rehearsal here is
simulation-only. No real robot motion occurs; no bag artefacts
exist; no actuator authority is granted.

## Layout

```
mission-rehearsals/
  README.md                              this file
  examples/<example_id>.json             canonical request payloads
  audits/<example_id>/                   per-rehearsal audit bundles
    mission-request.json
    mission-plan.json
    validator-result.json
    supervisor-review.json
    rehearsal-events.json
    timeline.json
    timeline.mmd
    replay-review.json
    replay-review.md
    analytics.json
    rehearsal-audit.json
    rehearsal-report.md
```

## Canonical examples

### Accepted (5)

| Example id                       | Final status | Notes                                              |
|----------------------------------|--------------|----------------------------------------------------|
| `warehouse_pickup_route_alpha`   | `completed`  | bounded warehouse pickup + dock                    |
| `bounded_forward_patrol`         | `completed`  | bounded patrol leg + dock                          |
| `waypoint_delivery_alpha`        | `completed`  | named-waypoint delivery + dock                     |
| `inspection_lane_beta`           | `completed`  | sensor inspection + dock                           |
| `emergency_stop_rehearsal`       | `completed`  | bounded stop request                               |

### Rejected (5)

| Example id                       | Final status | Failure reason                                     |
|----------------------------------|--------------|----------------------------------------------------|
| `unsafe_speed_route`             | `rejected`   | `unsafe_speed`                                     |
| `restricted_zone_entry`          | `rejected`   | `restricted_zone`                                  |
| `direct_motor_override`          | `rejected`   | `direct_actuator_command`                          |
| `disable_supervisor_attempt`     | `rejected`   | `safety_override`                                  |
| `infinite_patrol_loop`           | `rejected`   | `missing_stop_condition`                           |

Even the accepted bundles are simulation-only. The runtime safety
supervisor and motion arbitration remain authoritative; nothing in
this directory authorises a real robot to move.

## How to regenerate

```
python3 rover_ws/tools/generate_rehearsal_examples.py
```

The generator is deterministic — repeated runs with the same
`--generated-at` produce byte-identical files.

## How to run one rehearsal manually

```
python3 rover_ws/tools/run_mission_rehearsal.py \
  --mission mission-rehearsals/examples/warehouse_pickup_route_alpha.json \
  --output mission-rehearsals/audits/warehouse_pickup_route_alpha \
  --generated-at 2026-05-13T00:00:00+00:00
```

## How to refresh replay artefacts only

```
python3 rover_ws/tools/generate_rehearsal_replay.py \
  --audit mission-rehearsals/audits/<id>/rehearsal-audit.json
```

## Where to read next

* `docs/GOVERNED_MISSION_REHEARSAL.md` — architectural contract.
* `docs/MISSION_REHEARSAL_STATE_MACHINE.md` — state transitions.
* `docs/SIMULATION_REHEARSAL_PIPELINE.md` — request/plan schema.
* `docs/REHEARSAL_REPLAY_INTEGRATION.md` — replay + analytics bridge.
* `docs/REHEARSAL_SAFETY_BOUNDARY.md` — what the pipeline cannot do.
* `docs/FUTURE_DIGITAL_TWIN_DIRECTION.md` — outlook for the next phase.

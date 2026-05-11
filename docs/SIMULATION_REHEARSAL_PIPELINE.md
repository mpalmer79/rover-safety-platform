# Simulation Rehearsal Pipeline

The platform is **not safety-certified.** This page documents the
deterministic shape of a Phase 16 mission rehearsal: the JSON
request, the resulting plan, and the bundle layout.

## 1. Mission request JSON

```jsonc
{
  "request_id": "warehouse_pickup_route_alpha",
  "mission_id": "warehouse_pickup_route_alpha",
  "description": "Warehouse pickup route alpha (simulation-only)",
  "proposal_source": "Drive to aisle A, inspect pickup zone alpha, return to dock.",
  "operator": "test-operator",
  "odd_profile_id": "default-warehouse",
  "seed": 42,
  "waypoints": [
    {"waypoint_id": "wp1", "label": "Aisle A", "stage_kind": "move",
     "bounded_distance_m": 2.5, "bounded_speed_mps": 0.25},
    {"waypoint_id": "wp2", "label": "Pickup zone alpha", "stage_kind": "inspect",
     "bounded_distance_m": 0.5, "bounded_speed_mps": 0.15},
    {"waypoint_id": "wp3", "label": "Dock", "stage_kind": "dock"}
  ],
  "safety_constraints": ["bounded speed", "final dock"],
  "requested_topics": ["/cmd_vel_requested"],
  "forbidden_topics": ["/cmd_vel"]
}
```

Fields:

| Field                  | Required? | Notes                                                       |
|------------------------|-----------|-------------------------------------------------------------|
| `request_id`           | yes       | non-empty                                                   |
| `mission_id`           | yes       | non-empty                                                   |
| `description`          | no        | free text                                                   |
| `proposal_source`      | yes       | text fed into the safety scan                               |
| `operator`             | no        | recorded in the supervisor rationale                        |
| `odd_profile_id`       | no        | defaults to `default-warehouse`                             |
| `seed`                 | no        | defaults to 42; determinism anchor                          |
| `waypoints`            | yes       | non-empty; motion waypoints require a stop / dock follow-up |
| `safety_constraints`   | no        | recorded in the plan + audit                                |
| `requested_topics`     | no        | defaults to `["/cmd_vel_requested"]`                        |
| `forbidden_topics`     | no        | defaults to `["/cmd_vel"]`                                  |

## 2. Waypoint stages

| `stage_kind` | Allowed?  | Notes                                                  |
|--------------|-----------|--------------------------------------------------------|
| `move`       | yes       | bounded distance + speed enforced                      |
| `patrol`     | yes       | bounded distance + speed enforced                      |
| `inspect`    | yes       | bounded distance + speed enforced                      |
| `wait`       | yes       | no motion                                              |
| `stop`       | yes       | terminal stop                                          |
| `dock`       | yes       | recommended terminal for motion-bearing plans          |

Any other value is rejected by the validator.

## 3. Bounded-motion limits

```
max_distance_meters     = 25.0
max_angle_degrees       = 720.0
max_linear_speed_mps    = 0.5
max_angular_speed_rad_s = 1.0
```

Set in `app.mission_rehearsal.rehearsal_safety.SAFETY_LIMITS`.

## 4. Bundle layout

```
mission-rehearsals/audits/<mission_id>/
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

Every JSON file is written with sorted keys; the Markdown files
depend only on the bundle data, so two runs against the same
`--generated-at` produce byte-identical bundles.

## 5. Pipeline stages

```
build_plan
   ↓
validate_plan
   ↓
review_plan
   ↓
run_rehearsal      (state machine + event stream)
   ↓
build_replay_bundle
   ↓
build_analytics_result
   ↓
build_audit_bundle
   ↓
write_audit_files
```

Each stage is a pure function. `run_rehearsal` is the only stage
that drives state; every transition becomes an event.

## 6. Failure modes

| Stage         | Failure                                                   | Result                                  |
|---------------|-----------------------------------------------------------|-----------------------------------------|
| `validate_plan` | distance > 25 m, speed > 0.5 m/s, missing stop, etc.      | rejection diagnostics                   |
| `validate_plan` | direct `/cmd_vel` reference, safety / e-stop override    | rejection diagnostics                   |
| `review_plan` | risk band `blocked` or `validation rejected`              | supervisor `rejected`                   |
| `review_plan` | risk band `restricted`                                    | supervisor `needs_review`               |
| `run_rehearsal` | supervisor not `approved`                                 | state goes straight to `rejected`       |

A rejection at any stage produces an honest audit bundle that
records the cause.

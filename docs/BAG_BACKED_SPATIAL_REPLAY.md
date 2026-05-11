# Bag-backed spatial replay (Phase 17C)

The platform is **not safety-certified.** Phase 17C upgrades the
mission map so that, when a real bag-backed run produces pose
samples, the operator can replay the trajectory alongside the
event stream. Everything else — bounded-inputs derivation,
topology-only fallback, simulation-only banner — is unchanged.

## 1. Evidence hierarchy

The frontend chooses the most-honest derivation source the inputs
support:

```
bag-backed spatial replay
↓ fallback
fixture-derived spatial replay
↓ fallback
bounded-inputs derived spatial replay  (Phase 17B)
↓ fallback
topology-only replay                   (Phase 17B)
↓ fallback
spatial data unavailable
```

The chosen source is rendered verbatim in the map caption (see
`describeDerivationSource` in `apps/mission-control/src/adapters/spatial.ts`).
The reviewer can therefore tell at a glance whether the map is
real telemetry, a fixture, a bounded-input derivation, or unavailable.

## 2. What a real bag-backed run produces

A run qualifies as `derivation_source = bag_backed` only when **all**
of the following hold:

1. `evidence/runtime/<run_id>/bag-manifest.json` exists and parses.
2. The manifest's `bag_status` is `bag_backed`.
3. Every path in `bag_paths` exists on disk under the run directory.
4. `metadata_yaml_path` exists on disk.
5. The manifest's `validation_status` is `passed` or `partial`.
6. The run directory contains
   `evidence/runtime/<run_id>/pose-samples.jsonl` (operator-produced
   from the real bag).

If any condition fails the run is demoted to `fixture` (if a
committed fixture exists) or `unavailable`. The gatekeeper is
`backend/app/spatial_replay/manifest_loader.py::evaluate_bag_eligibility`.

## 3. Producing `pose-samples.jsonl`

Phase 17C does **not** bundle a rosbag2 parser. The expectation is
that a qualified self-hosted runner produces the JSONL file in
post-processing, then commits it alongside the run's
`bag-manifest.json`.

One JSON object per line, sorted by `time_ns`:

```jsonl
{"sample_id": "s0", "time_ns": 0, "x_m": 0.0, "y_m": 0.0, "theta_rad": 0.0, "source_topic": "/odom", "confidence": "high", "event_refs": []}
{"sample_id": "s1", "time_ns": 1000000000, "x_m": 0.5, "y_m": 0.0, "theta_rad": 0.0, "source_topic": "/odom", "confidence": "high", "event_refs": []}
```

The fields mirror the
`backend/app/spatial_replay/models.py::PoseSample` dataclass.
`source_topic` should be one of the preferred topics
(`/odom`, `/tf`, `/tf_static`).

## 4. Why the fixture path exists

`spatial-replay/fixtures/canonical-fixture/pose-samples.jsonl`
contains hand-authored samples that follow the
`warehouse_pickup_route_alpha` bounded route. The fixture exists to:

* regression-test the trajectory + alignment code paths;
* let the Mission Control build prerender a real-looking playback
  panel without requiring a self-hosted runner;
* keep the frontend's bag-backed code path covered by tests.

The fixture is **never** labelled `bag_backed`. The CI workflow,
the backend validator, and the frontend adapter all enforce this.

## 5. CLI

```
python tools/generate_spatial_replay.py \
    --run-id canonical-fixture \
    --scenario-id warehouse_pickup_route_alpha \
    --mission-id warehouse_pickup_route_alpha \
    --rehearsal mission-rehearsals/audits/warehouse_pickup_route_alpha \
    --fixtures-root spatial-replay/fixtures \
    --output-root spatial-replay/runs
```

The CLI is read-only: it never invents pose samples and never
fabricates a bag manifest.

## 6. What this phase does NOT do

* run real hardware;
* parse real `.mcap` or `.db3` files (the operator does this);
* publish to ROS topics;
* call cloud APIs;
* execute generated robot code;
* mark simulated artefacts as bag-backed;
* imply real-world deployment or safety certification.

See `docs/SPATIAL_REPLAY_HONESTY_RULES.md` for the complete rule set.

# Spatial replay artefact format (Phase 17C)

The platform is **not safety-certified.** This document defines the
on-disk schema that the backend builder emits and the frontend
adapter consumes.

## 1. Directory layout

```
spatial-replay/
  fixtures/<run_id>/pose-samples.jsonl
  runs/<run_id>/
    spatial-replay.json
    trajectory.jsonl
    event-alignment.json
    spatial-validation.json
    spatial-replay-report.md
```

The `runs/` subtree is the one the frontend reads. The `fixtures/`
subtree holds operator-supplied input data; it is never read by the
frontend.

## 2. `spatial-replay.json`

```jsonc
{
  "run_id": "canonical-fixture",
  "scenario_id": "warehouse_pickup_route_alpha",
  "mission_id": "warehouse_pickup_route_alpha",
  "evidence_origin": "fixture",
  "bag_status": "missing_manifest",
  "derivation_source": "fixture",
  "trajectory_status": "complete",
  "validation_status": "passed",
  "sample_count": 10,
  "segment_count": 9,
  "topic_sources": ["/odom"],
  "missing_topics": [],
  "known_limitations": [
    "fixture-derived spatial samples; not bag-backed evidence"
  ],
  "generated_at_utc": "2026-05-11T18:00:00+00:00",
  "note": "...",
  "samples": [ { "sample_id": "s00000", "time_ns": 0, "x_m": 0, ... } ],
  "segments": [ { "from_sample_id": "s00000", "to_sample_id": "s00001", ... } ],
  "event_alignments": [ { "event_id": "...", "matched_sample_id": "...", "spatial_position": [x, y] } ]
}
```

### `derivation_source` (required)

One of:

| Value             | Meaning                                                  |
|-------------------|----------------------------------------------------------|
| `bag_backed`      | Pose samples extracted from real bag-backed evidence.    |
| `fixture`         | Pose samples from a committed fixture; not bag-backed.   |
| `bounded_inputs`  | (Frontend only) bounded distance/angle from plan.        |
| `topology_only`   | (Frontend only) topology layout when no motion bounded.  |
| `unavailable`     | No spatial data.                                          |

### `bag_status` (required)

Mirrors the verbatim `bag_status` from
`evidence/runtime/<run_id>/bag-manifest.json`. When no manifest
exists the field is `missing_manifest`.

### `validation_status` (required)

One of `passed`, `partial`, `failed`, `not_executed`. The
validator in
`backend/app/spatial_replay/validator.py::validate_spatial_replay`
sets this field; the builder never upgrades it.

## 3. `trajectory.jsonl`

One JSON object per line, sorted by `(time_ns, sample_id)`. Fields:

* `sample_id` — stable id (string).
* `time_ns` — int.
* `x_m`, `y_m`, `theta_rad` — float, metres / radians.
* `source_topic` — one of the preferred pose topics
  (`/odom`, `/tf`, `/tf_static`) or empty.
* `confidence` — string supplied by the producer; never upgraded by
  the platform.
* `event_refs` — string array of rehearsal event ids that the
  producer associates with this sample.

## 4. `event-alignment.json`

```jsonc
{
  "run_id": "...",
  "alignments": [
    {
      "event_id": "...",
      "deterministic_hash": "...",
      "matched_sample_id": "s00003",
      "spatial_position": [1.5, 0.0],
      "delta_time_ns": 25000000,
      "confidence": "high"
    }
  ]
}
```

When an event falls outside the alignment tolerance the
`matched_sample_id` is empty and `spatial_position` is `null`.

## 5. `spatial-validation.json`

```jsonc
{
  "status": "passed",
  "warnings": [],
  "missing_topics": [],
  "topic_sources": ["/odom"],
  "sample_count": 10,
  "bag_validation_warnings": []
}
```

## 6. `spatial-replay-report.md`

A human-readable report. The report's "Next step" section is
hard-wired to the derivation source — a `fixture` artefact always
recommends producing a real bag-backed run.

## 7. Honesty invariants

The validator rejects any artefact that violates:

* `derivation_source=bag_backed` ⇒ `bag_status=bag_backed` AND
  `sample_count > 0`.
* `derivation_source=fixture` ⇒ `bag_status != bag_backed`.
* `derivation_source=unavailable` ⇒ `sample_count == 0` AND
  `segment_count == 0`.
* `derivation_source ∈ {bounded_inputs, topology_only}` ⇒ no samples.

See `docs/SPATIAL_REPLAY_HONESTY_RULES.md` for the complete list.

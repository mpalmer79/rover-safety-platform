# Spatial replay artefacts (Phase 17C)

The platform is **not safety-certified.** This directory contains
two parallel trees of deterministic spatial-replay artefacts:

```
spatial-replay/
  fixtures/<run_id>/pose-samples.jsonl   # committed, hand-authored
  runs/<run_id>/                         # generated artefacts
```

## Honesty contract

| Tree         | `derivation_source` | Bag-backed? |
|--------------|---------------------|-------------|
| `fixtures/`  | `fixture`           | Never       |
| `runs/`      | `bag_backed`, `fixture`, or `unavailable` | Only when `bag_backed` is enforced by the validator |

`fixture` samples are explicit fixtures: they are not extracted from
a real bag and are not labelled `bag_backed`. They exist to
regression-test the trajectory + alignment code paths.

`bag_backed` is only set when:

* `evidence/runtime/<run_id>/bag-manifest.json` validates with
  `bag_status=bag_backed`;
* every bag path on the manifest exists on disk;
* the metadata yaml exists on disk;
* runtime pose samples are present at
  `evidence/runtime/<run_id>/pose-samples.jsonl` (operator-produced
  from the real bag).

If any condition fails the run is demoted to `fixture` (if a
fixture exists) or `unavailable`. See
`docs/SPATIAL_REPLAY_HONESTY_RULES.md` for the full rule set.

## Generating a run

```
python tools/generate_spatial_replay.py \
    --run-id canonical-fixture \
    --scenario-id warehouse_pickup_route_alpha \
    --mission-id warehouse_pickup_route_alpha \
    --rehearsal mission-rehearsals/audits/warehouse_pickup_route_alpha \
    --fixtures-root spatial-replay/fixtures \
    --output-root spatial-replay/runs
```

The CLI is read-only and never invents pose samples; it only
consumes files committed to this repository.

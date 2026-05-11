# Canonical fixture — `canonical-fixture`

The platform is **not safety-certified.** This is a hand-authored
fixture used to regression-test the Phase 17C spatial-replay
pipeline. It is **not** bag-backed evidence.

| Field              | Value                                       |
|--------------------|---------------------------------------------|
| `run_id`           | `canonical-fixture`                         |
| `scenario_id`      | `warehouse_pickup_route_alpha`              |
| `mission_id`       | `warehouse_pickup_route_alpha`              |
| `evidence_origin`  | `fixture`                                   |
| `derivation_source`| `fixture` (never `bag_backed`)              |
| `bag_status`       | `missing_manifest` (no bag manifest exists) |
| `source_topic`     | `/odom` (claimed; not extracted from a bag) |

The pose samples track the bounded-input route declared in
`mission-rehearsals/audits/warehouse_pickup_route_alpha/mission-plan.json`:

* `wp1`: forward 2.5 m on heading 0° → (2.5, 0)
* `wp2`: inspect 0.5 m → (3.0, 0)
* `wp3`: dock back to origin → (0, 0)

The 10 samples are equispaced along this path. They are NOT real
telemetry; producing real bag-backed evidence requires a qualified
self-hosted Jazzy + Gazebo runner. Until that runs, the spatial
layer renders this fixture's trajectory marked as
`Fixture-derived spatial replay. Not bag-backed evidence.`

# Spatial-replay honesty rules (Phase 17C)

The platform is **not safety-certified.** This document is the
single source of truth for the rules that gatekeep the
`bag_backed` label across the backend, the frontend, the CI
workflow, and the prerendered HTML.

## R1 — `bag_backed` requires the full evidence stack

A spatial-replay artifact may set `derivation_source = bag_backed`
only when **all** of these hold:

1. `evidence/runtime/<run_id>/bag-manifest.json` exists and parses.
2. The manifest's `bag_status` is `bag_backed`.
3. Every path in the manifest's `bag_paths` exists on disk.
4. The manifest's `metadata_yaml_path` exists on disk.
5. The manifest's `validation_status` is `passed` or `partial`.
6. The run directory contains
   `evidence/runtime/<run_id>/pose-samples.jsonl` and at least one
   sample parses successfully.

Enforced by:

* `backend/app/spatial_replay/manifest_loader.py::evaluate_bag_eligibility`
* `backend/tests/test_spatial_replay.py::test_missing_manifest_blocks_bag_backed`
* `backend/tests/test_spatial_replay.py::test_partial_manifest_blocks_bag_backed`
* `backend/tests/test_spatial_replay.py::test_missing_pose_samples_blocks_bag_backed`
* `backend/tests/test_spatial_replay.py::test_bag_backed_demoted_when_bag_path_missing`

## R2 — Fixtures are never bag-backed

Pose samples loaded from
`spatial-replay/fixtures/<run_id>/pose-samples.jsonl` always
produce `derivation_source = fixture`. The artifact's
`bag_status` is `missing_manifest` (or whatever the manifest
honestly reports). The validator additionally surfaces a known
limitation:

```
fixture-derived spatial samples; not bag-backed evidence
```

Enforced by:

* `backend/app/spatial_replay/builder.py::build_spatial_replay`
* `backend/tests/test_spatial_replay.py::test_fixture_samples_are_not_bag_backed`
* `backend/tests/test_spatial_replay.py::test_canonical_fixture_emits_fixture_derivation`
* `apps/mission-control/tests/spatial-replay.test.ts::loadSpatialReplay > returns the canonical fixture artifact`

## R3 — Derivation source is preserved through every artifact

The string emitted by the backend builder appears verbatim in:

* `spatial-replay.json` (`derivation_source` field);
* `spatial-replay-report.md`;
* the frontend's `MissionMap` caption
  (`describeDerivationSource`);
* the frontend's `SpatialReplayBadge` `data-source` attribute.

No layer is allowed to upgrade the string. The frontend may *fall
back* (e.g. from a malformed `bag_backed` artifact to
`bounded_inputs`) but never upgrades.

## R4 — Missing topics surface as warnings, never as fabricated samples

When the expected topics include `/tf` but the bag's topic
inventory does not, the trajectory is downgraded to `partial` and
`/tf` appears in `missing_topics`. No `/tf` sample is invented.

Enforced by:

* `backend/app/spatial_replay/validator.py::compute_missing_topics`
* `backend/tests/test_spatial_replay.py::test_missing_topic_produces_warning_not_fabrication`

## R5 — Internal consistency is validated

The validator rejects artifacts whose `derivation_source` and
`bag_status` are inconsistent. Examples:

| `derivation_source` | `bag_status`        | Outcome             |
|---------------------|---------------------|---------------------|
| `bag_backed`        | `bag_backed`        | passes              |
| `bag_backed`        | anything else       | failed              |
| `fixture`           | `bag_backed`        | failed              |
| `unavailable`       | any sample > 0      | failed              |

Enforced by:

* `backend/app/spatial_replay/validator.py::validate_spatial_replay`
* `backend/tests/test_spatial_replay.py::test_validator_rejects_bag_backed_without_samples`

## R6 — Frontend fallback hierarchy

The frontend never silently upgrades a derivation source. The
fallback hierarchy in
`apps/mission-control/src/adapters/spatial.ts::selectMissionRoute`
is:

1. Prefer the artifact when `derivation_source ∈ {bag_backed,
   fixture}` AND `samples.length > 0`.
2. Otherwise call `buildMissionRoute(plan)` — the Phase 17B
   bounded-inputs adapter.

If the artifact's `derivation_source` is `unavailable`, the
frontend takes the bounded-inputs path; the unavailable artifact is
treated as a no-op signal that the operator hasn't produced one yet.

Enforced by:

* `apps/mission-control/tests/spatial-replay.test.ts::selectMissionRoute > falls back to bounded_inputs when artifact is null`
* `apps/mission-control/tests/spatial-replay.test.ts::selectMissionRoute > falls back to bounded_inputs when artifact has zero samples`

## R7 — UI surfaces the derivation source

Every mission map renders one of the verbatim captions:

* `Spatial source: bag-backed runtime evidence.`
* `Spatial source: fixture-derived spatial replay. Not bag-backed evidence.`
* `Spatial source: bounded simulation inputs.`
* `Spatial source: topology only.`
* `Spatial source: unavailable.`

The captions come from
`apps/mission-control/src/adapters/spatial.ts::describeDerivationSource`
and are never overridden by individual components.

Enforced by:

* `apps/mission-control/tests/spatial-honesty.test.tsx::MissionMap > caption names the derivation source`
* `apps/mission-control/tests/spatial-honesty.test.tsx::SpatialReplayBadge > visible per-source colouring`

## R8 — CI grep verifies the prerendered HTML

`.github/workflows/mission-control-ci.yml` runs three honesty greps:

1. Every prerendered page contains "Simulation-only".
2. No prerendered page contains "bag-backed: yes" (Phase 13 rule).
3. If any prerendered page mentions "bag-backed runtime evidence",
   at least one committed `spatial-replay.json` artifact must
   declare `derivation_source=bag_backed` with non-zero samples.

Today the canonical fixture is the only committed artifact, so
rule (3) ensures the prerendered HTML never carries a bag-backed
caption.

## R9 — `is_honestly_bag_backed` is the single gatekeeper

`backend/app/spatial_replay/validator.py::is_honestly_bag_backed`
is the only function any caller (CLI, frontend, downstream report)
should call before rendering a bag-backed badge. The frontend mirror
is `apps/mission-control/src/adapters/spatial.ts::artifactIsBagBacked`.

Both functions return `false` when:

* the artifact is null;
* `derivation_source != bag_backed`;
* `bag_status != bag_backed`;
* `samples.length == 0`.

## R10 — No simulated runtime claim

The platform makes no claim of live robot telemetry, live robot
control, or safety certification. Every committed artifact carries
a `disclaimer` reminding the reviewer of this; every page renders
the `SafetyBoundaryBanner` from Phase 17A.

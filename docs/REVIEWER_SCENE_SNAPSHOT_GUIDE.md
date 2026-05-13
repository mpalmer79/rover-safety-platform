# Reviewer Scene Snapshot Guide (Phase 19)

The platform is **not safety-certified.** Reviewer scene snapshots
are *deterministic metadata*, not screenshots. This document is
the contract.

## 1. What is a scene snapshot?

A scene snapshot is a JSON+Markdown bundle describing a moment in
the immersive Mission Control scene that a reviewer could capture:

```jsonc
{
  "run_id": "...",
  "status": "bag_backed | fixture | not_executed | unavailable",
  "scene_source": "apps/mission-control/src/3d/MissionScene",
  "derivation_source": "bag_backed",
  "bag_status": "bag_backed",
  "integrity": "passed",
  "reviewer_export_ready": true,
  "artifact_registry_entry": "spatial-replay/registry/canonical-artifacts.json",
  "spatial_replay_path": "spatial-replay/runs/<id>/spatial-replay.json",
  "artifact_hash_chain": [{ "relative_path": "...", "sha256_prefix": "...", "size_bytes": "..." }],
  "missing_inputs": [],
  "notes": ["..."],
  "disclaimer": "This project is not safety-certified ..."
}
```

The snapshot is metadata only. The platform does not render or
attach a PNG to a PR — that step is operator-driven and depends
on a real browser/render harness.

## 2. Eligibility

A run is eligible for a bag-backed snapshot when **all** of:

- `spatial-replay/runs/<run_id>/spatial-replay.json` exists,
- its `derivation_source = "bag_backed"`,
- its `bag_status = "bag_backed"`,
- the artifact registry record exists,
- `verify_artifact(record, artefact_root=repo_root)` recomputes
  `integrity = "passed"` against the bytes on disk.

If any condition fails, the snapshot's `status` is `fixture` /
`not_executed` / `unavailable` and `reviewer_export_ready = false`.

## 3. CLI

```bash
python tools/generate_reviewer_scene_snapshot.py --run-id <run_id>
```

The CLI writes the snapshot JSON + Markdown to
`spatial-replay/snapshots/<run_id>.scene-snapshot.{json,md}`.

The CLI never:

- generates a screenshot,
- opens a browser,
- runs the immersive scene headlessly,
- claims a snapshot exists.

## 4. Frontend behaviour

`apps/mission-control/src/components/SceneSnapshotPanel.tsx`
surfaces the snapshot metadata in the per-mission detail page:

- a status chip (one of `bag_backed`, `fixture`, `not_executed`,
  `unavailable`),
- a `reviewer_export_ready` flag,
- the missing-inputs list (when status != `bag_backed`),
- the artifact hash chain (from the registry record).

The panel never invents data. The frontend mirror of the backend
pipeline is `apps/mission-control/src/adapters/sceneSnapshot.ts`.

## 5. Honesty rules

- A fixture-derived run can never become a bag-backed snapshot.
- A bag-backed artifact with `integrity != passed` cannot become a
  bag-backed snapshot.
- The disclaimer is included in every JSON / MD output.
- The CLI exit code is informational only; CI never auto-promotes
  a snapshot to `bag_backed`.

## 6. Next steps for a real bag-backed snapshot

See `docs/FIRST_BAG_BACKED_RUN_PLAYBOOK.md`. Producing a real
snapshot requires:

1. A real bag-backed spatial-replay artifact.
2. A browser-render harness (out of scope for Phase 19).
3. The harness must record a deterministic camera snapshot for a
   specific `playback_mode` + scrubber index.

The Phase 19 metadata layer is the on-ramp; the rendering harness
is a Phase 20+ activity.

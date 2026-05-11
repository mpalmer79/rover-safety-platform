# Artifact Governance Model (Phase 18)

The platform is **not safety-certified.** This document describes
the governance layer that owns the canonical lifecycle of every
committed replay artefact.

## 1. Why this exists

Phase 17C CI failed when the runner expected committed replay
artefacts that the workspace had not yet hydrated. The frontend
read files by convention, the CI built without a hydration gate,
and the failure surfaced as a generic pytest crash. Phase 18 fixes
that by introducing an explicit governance layer with three
responsibilities:

1. **Discovery.** A canonical registry lists every committed
   artefact the platform is allowed to render.
2. **Verification.** Every registered file records a deterministic
   sha256 prefix; bytes on disk must match.
3. **Hydration.** A dedicated CLI rebuilds canonical fixtures from
   their source inputs and fails honestly when hashes drift.

## 2. The registry

The registry lives at
`spatial-replay/registry/canonical-artifacts.json`.

Schema (see `backend/app/artifact_registry/models.py`):

```jsonc
{
  "generated_at_utc": "2026-05-11T18:00:00+00:00",
  "schema_version": "phase18-1",
  "artefact_root": "spatial-replay",
  "notes": ["..."],
  "records": [
    {
      "run_id": "canonical-fixture",
      "kind": "spatial_replay",
      "derivation_source": "fixture",
      "bag_status": "missing_manifest",
      "lifecycle": "canonical",
      "integrity": "passed",
      "related_mission_id": "warehouse_pickup_route_alpha",
      "related_scenario_id": "warehouse_pickup_route_alpha",
      "files": [
        {
          "relative_path": "spatial-replay/runs/canonical-fixture/spatial-replay.json",
          "expected_hash": "<64-char sha256>",
          "size_bytes": 8956,
          "description": "frontend-consumable spatial-replay artefact"
        }
      ],
      "notes": ["..."]
    }
  ]
}
```

## 3. Lifecycle ladder

| Rung         | Meaning                                                   |
|--------------|-----------------------------------------------------------|
| `generated`  | Built by a CLI; not committed yet.                        |
| `hydrated`   | Rebuilt from sources, hash verified locally.              |
| `committed`  | Lives on `main`; the UI may render it.                    |
| `verified`   | A reviewer has signed off on the artefact's evidence.     |
| `canonical`  | Phase-level milestone; the artefact will not be deleted.  |
| `deprecated` | Hidden from the UI; available for archive lookups only.   |

Phase 18 ships every canonical fixture at lifecycle = `canonical`.

## 4. Integrity states

| State         | Meaning                                              |
|---------------|------------------------------------------------------|
| `passed`      | Every registered file matches its expected sha256.   |
| `partial`     | Some files match; some are missing on disk.          |
| `failed`      | At least one file's sha256 drifts from the registry. |
| `missing`     | Every registered file is absent on disk.             |
| `unverified`  | The registry has not been verified in this run.      |

A drop below `passed` clamps the lifecycle claim to `committed`
via `lifecycle_for_integrity`.

## 5. Honesty invariants

- The frontend reads the registry first; if the registry exists,
  filesystem guessing is forbidden.
- A failing hydration NEVER rewrites the canonical registry.
- A `derivation_source = bag_backed` record must point at an
  artefact with `bag_status = bag_backed` and `sample_count > 0`.
- A `deprecated` record is never rendered.
- A `partial` / `failed` integrity demotes the artefact's
  rendering confidence in the UI.

## 6. Where it lives

```
backend/app/artifact_registry/
  __init__.py
  models.py
  deterministic_hash.py
  lifecycle.py
  manifest.py
  registry.py
  validation.py
  hydration.py
  reporter.py

tools/hydrate_replay_artifacts.py    # CLI

spatial-replay/registry/
  canonical-artifacts.json            # registry payload
  canonical-artifacts.md              # auto-generated summary
  hydration-report.json               # auto-generated report
  hydration-report.md                 # human-readable report
```

The frontend reads the registry via
`apps/mission-control/src/adapters/loader.ts::loadArtifactRegistry`.

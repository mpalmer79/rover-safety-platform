# Replay Evidence Lineage (Phase 18)

The platform is **not safety-certified.** This document describes
how the operator can read the lineage of every spatial-replay
artefact that the UI renders.

## 1. The lineage chain

Every immersive scene resolves a chain of inputs:

```
rehearsal audit
   ↓
bag manifest (only when bag-backed)
   ↓
pose-samples.jsonl (operator post-processed for bag-backed; fixture for fixture)
   ↓
spatial-replay.json
   ↓
canonical artefact registry
   ↓
render: caption + badge + 3D scene
```

The Phase 18 UI surfaces this chain as a single panel:
`EvidenceLineageGraph`.

## 2. Confidence band

`ReplayConfidencePanel` rolls three inputs into a single band:

| Inputs                                                                                | Band         |
|---------------------------------------------------------------------------------------|--------------|
| `bag_backed` + validation `passed` + integrity `passed`                               | `high`       |
| `fixture` + validation `passed` + integrity `passed`                                  | `medium`     |
| any of validation / integrity `partial`                                               | `low`        |
| any of validation / integrity `failed`                                                | `low`        |
| `unavailable`                                                                         | `unavailable`|

The band is rendered with per-tier colour (green / yellow / red /
gray); the panel never upgrades a fixture to `high`, and never
ignores a `failed` integrity.

## 3. Lifecycle ladder

`ReplayLifecyclePanel` renders the lifecycle as a ladder:

```
generated → hydrated → committed → verified → canonical
                                                  +
                                            (deprecated, side-state)
```

Reached rungs are highlighted in accent colour; un-reached rungs
are muted. A `deprecated` record renders an extra red rung.

## 4. Deterministic hash chain

`DeterministicHashChain` lists every registered file with its 16-
character sha256 prefix and its byte count. Operators can
manually verify reproducibility with:

```
python tools/hydrate_replay_artifacts.py --check-only
```

A drift between the registry and the bytes on disk fails the
hydration CLI honestly.

## 5. Honesty rules

- The lineage chain never invents an upstream source. A fixture
  artefact's chain explicitly says `committed fixture`; a bag-
  backed artefact's chain explicitly says
  `evidence/runtime/<id>/bag-manifest.json`.
- The confidence band never upgrades the underlying derivation.
- The lifecycle ladder reflects the registry verbatim; the helper
  `lifecycle_for_integrity` clamps the claim when integrity drops.

## 6. Related docs

- `docs/ARTIFACT_GOVERNANCE_MODEL.md`
- `docs/IMMERSIVE_MISSION_CONTROL.md`
- `docs/SPATIAL_REPLAY_HONESTY_RULES.md`

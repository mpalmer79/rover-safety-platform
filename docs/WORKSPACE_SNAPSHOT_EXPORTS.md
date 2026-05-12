# Workspace Snapshot Exports

> Deterministic JSON capture of operator review state.
> No server, no database, no network.

## Why

A reviewer needs to say: *"Open this exact view"* — same preset,
same mission, same camera mode, same evidence focus — without
screen-sharing.

Phase 20B ships a workspace snapshot module that captures that state
deterministically and exposes it as copyable JSON.

## Shape

`apps/mission-control/src/workspaces/snapshot/models.ts` declares
the v1 shape:

| Field               | Notes                                             |
| ------------------- | ------------------------------------------------- |
| `schemaVersion`     | `workspace-snapshot/1`                            |
| `presetId`          | Active workspace preset id                        |
| `missionId`         | Mission id or null                                |
| `replayRunId`       | Registry record id (canonical-fixture, …) or null |
| `selectedEventId`   | Event id from rehearsal_runtime or null           |
| `selectedPanelIds`  | Sorted set of focused panel ids                   |
| `walkthroughStep`   | 1..10 or null                                     |
| `cameraMode`        | follow / orbit / top-down / fixed                 |
| `evidenceFocus`     | `{ kind, ref }` reference into the artefact set   |
| `theme`             | light / dark                                      |
| `density`           | comfortable / standard / dense                    |
| `capturedAtUtc`     | Caller-supplied; tests pass `null`                |
| `snapshotHash`      | Deterministic FNV-1a fingerprint of canonical form|
| `disclaimer`        | Verbatim simulation-only disclaimer               |

## Determinism rules

1. The hash is computed over the canonical JSON form with sorted keys
   at every depth, EXCLUDING `snapshotHash` and `capturedAtUtc`.
2. `selectedPanelIds` is sorted before hashing — panel order does
   NOT affect the fingerprint.
3. The hash is FNV-1a 32-bit, rendered as `ws-<8-hex>`. It is a
   deterministic fingerprint, not a cryptographic guarantee.
4. No wall-clock timestamp is captured unless the caller explicitly
   passes `capturedAtUtc`.

## Components

| Component                          | Role                                  |
| ---------------------------------- | ------------------------------------- |
| `WorkspaceSnapshotPanel`           | Renders the JSON block + integrity    |
| `WorkspaceSnapshotSummary`         | Compact field list                    |
| `WorkspaceSnapshotExportButton`    | Copy JSON to clipboard (no server)    |
| `WorkspaceSnapshotImportCard`      | Paste + validate JSON                 |
| `SnapshotIntegrityBadge`           | Hash + ok/drifted indicator           |

## Route

`/workspaces/snapshot` — static-only. Renders the canonical
fixtures plus an import card. No server write, no network call.

## Honesty rules

* Snapshots NEVER claim live runtime authority.
* The hash detects post-hoc tampering — tampered snapshots fail
  import with an explicit `snapshotHash` issue.
* Workspace presets remain deterministic; snapshots are read-only
  references into the existing preset registry.
* Adding fields requires bumping `schemaVersion` AND updating
  `validateWorkspaceSnapshot` + `snapshotHash`.

## Tests

`apps/mission-control/tests/workspace-snapshot.test.ts` pins:

* deterministic serialization
* hash sensitivity to meaningful field changes
* `capturedAtUtc` neutrality
* canonical fixtures validate
* hash-drift detection after tampering
* round-trip parsing
* malformed JSON honest handling

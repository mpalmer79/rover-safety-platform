/**
 * Phase 20B workspace snapshot models.
 *
 * A workspace snapshot is a deterministic JSON capture of operator
 * review state. The shape is the single source of truth for what
 * "open this exact view" means.
 *
 * Honesty rules:
 *   * snapshots never include wall-clock timestamps unless an
 *     explicit ``capturedAtUtc`` is supplied by the caller;
 *   * snapshots never imply a live runtime; they reference
 *     committed artefact identifiers only;
 *   * snapshots never persist drag/drop layout state — the
 *     workspace preset id is the authoritative layout reference.
 */

import type {
  CameraMode,
  WorkspacePanelId,
  WorkspacePresetId,
} from "@/workspaces/types";

export type EvidenceFocusKind =
  | "mission-plan"
  | "supervisor-decision"
  | "replay-bundle"
  | "spatial-replay"
  | "artifact-registry"
  | "validation-diagnostics"
  | "rehearsal-events"
  | "fleet-readiness"
  | "none";

export interface EvidenceFocus {
  kind: EvidenceFocusKind;
  /** Optional artefact path or registry record id. */
  ref: string | null;
}

export type SnapshotTheme = "light" | "dark";
export type SnapshotDensity = "comfortable" | "standard" | "dense";

/**
 * Workspace snapshot v1 shape. Adding fields requires bumping
 * ``schemaVersion`` AND updating ``validateWorkspaceSnapshot`` +
 * ``snapshotHash``.
 */
export interface WorkspaceSnapshotV1 {
  schemaVersion: "workspace-snapshot/1";
  /** Active workspace preset id. */
  presetId: WorkspacePresetId;
  /** Mission id the operator is reviewing (or null at fleet level). */
  missionId: string | null;
  /** Replay run id (registry-record key) or null. */
  replayRunId: string | null;
  /** Selected event id (event_id from rehearsal_runtime). */
  selectedEventId: string | null;
  /** Panels currently visible / focused. */
  selectedPanelIds: readonly WorkspacePanelId[];
  /** Walkthrough step index (1-based) or null when not in
   *  walkthrough mode. */
  walkthroughStep: number | null;
  /** Active 3D scene camera mode. */
  cameraMode: CameraMode;
  /** Selected evidence focus reference. */
  evidenceFocus: EvidenceFocus;
  /** Theme at capture time. */
  theme: SnapshotTheme;
  /** Operator-density mode. */
  density: SnapshotDensity;
  /** Optional caller-supplied capture timestamp. Tests pass null. */
  capturedAtUtc: string | null;
  /** Deterministic hash of the canonical JSON form (set after
   *  serialization). */
  snapshotHash: string;
  /** Verbatim disclaimer rendered alongside every snapshot. */
  disclaimer: string;
}

export const SNAPSHOT_DISCLAIMER: string =
  "Simulation-only · not safety-certified · artefacts referenced are committed JSON only";

export const SNAPSHOT_SCHEMA_VERSION: WorkspaceSnapshotV1["schemaVersion"] =
  "workspace-snapshot/1";

/**
 * Phase 20B snapshot validator.
 *
 * Strict, deterministic validation. Returns a list of issues; an
 * empty list means the input parses cleanly into a v1 snapshot.
 * The validator never coerces values silently — bad input becomes a
 * documented issue.
 */

import { isWorkspacePresetId } from "@/workspaces/presets";
import type { CameraMode, WorkspacePanelId } from "@/workspaces/types";

import {
  SNAPSHOT_SCHEMA_VERSION,
  type EvidenceFocus,
  type EvidenceFocusKind,
  type SnapshotDensity,
  type SnapshotTheme,
  type WorkspaceSnapshotV1,
} from "./models";
import { computeSnapshotHash } from "./snapshotHash";

export interface ValidationIssue {
  field: string;
  message: string;
}

const VALID_CAMERA_MODES: readonly CameraMode[] = [
  "follow",
  "orbit",
  "top-down",
  "fixed",
];
const VALID_THEMES: readonly SnapshotTheme[] = ["light", "dark"];
const VALID_DENSITIES: readonly SnapshotDensity[] = [
  "comfortable",
  "standard",
  "dense",
];
const VALID_EVIDENCE_KINDS: readonly EvidenceFocusKind[] = [
  "mission-plan",
  "supervisor-decision",
  "replay-bundle",
  "spatial-replay",
  "artifact-registry",
  "validation-diagnostics",
  "rehearsal-events",
  "fleet-readiness",
  "none",
];

function isStringOrNull(v: unknown): v is string | null {
  return v === null || typeof v === "string";
}

export function validateWorkspaceSnapshot(value: unknown): {
  ok: boolean;
  issues: ValidationIssue[];
  snapshot: WorkspaceSnapshotV1 | null;
} {
  const issues: ValidationIssue[] = [];
  const push = (field: string, message: string) =>
    issues.push({ field, message });

  if (!value || typeof value !== "object") {
    return {
      ok: false,
      issues: [{ field: "$", message: "not an object" }],
      snapshot: null,
    };
  }
  const v = value as Record<string, unknown>;

  if (v.schemaVersion !== SNAPSHOT_SCHEMA_VERSION) {
    push("schemaVersion", `expected ${SNAPSHOT_SCHEMA_VERSION}`);
  }
  if (typeof v.presetId !== "string" || !isWorkspacePresetId(v.presetId)) {
    push("presetId", "unknown preset id");
  }
  if (!isStringOrNull(v.missionId)) push("missionId", "must be string or null");
  if (!isStringOrNull(v.replayRunId)) push("replayRunId", "must be string or null");
  if (!isStringOrNull(v.selectedEventId))
    push("selectedEventId", "must be string or null");
  if (!Array.isArray(v.selectedPanelIds))
    push("selectedPanelIds", "must be an array");
  if (
    v.walkthroughStep !== null &&
    (typeof v.walkthroughStep !== "number" ||
      v.walkthroughStep < 1 ||
      v.walkthroughStep > 10)
  ) {
    push("walkthroughStep", "must be null or 1..10");
  }
  if (
    typeof v.cameraMode !== "string" ||
    !VALID_CAMERA_MODES.includes(v.cameraMode as CameraMode)
  ) {
    push("cameraMode", "unknown camera mode");
  }
  const ef = v.evidenceFocus as EvidenceFocus | undefined;
  if (!ef || typeof ef !== "object") {
    push("evidenceFocus", "missing");
  } else {
    if (!VALID_EVIDENCE_KINDS.includes(ef.kind)) {
      push("evidenceFocus.kind", "unknown evidence focus kind");
    }
    if (!isStringOrNull(ef.ref)) {
      push("evidenceFocus.ref", "must be string or null");
    }
  }
  if (
    typeof v.theme !== "string" ||
    !VALID_THEMES.includes(v.theme as SnapshotTheme)
  ) {
    push("theme", "unknown theme");
  }
  if (
    typeof v.density !== "string" ||
    !VALID_DENSITIES.includes(v.density as SnapshotDensity)
  ) {
    push("density", "unknown density");
  }
  if (!isStringOrNull(v.capturedAtUtc))
    push("capturedAtUtc", "must be string or null");
  if (typeof v.disclaimer !== "string") push("disclaimer", "missing");
  if (typeof v.snapshotHash !== "string") push("snapshotHash", "missing");

  if (issues.length > 0) return { ok: false, issues, snapshot: null };

  const snapshot = value as unknown as WorkspaceSnapshotV1;

  // Verify the supplied hash matches the canonical hash. A mismatch
  // means the snapshot was edited after serialization.
  const expected = computeSnapshotHash(snapshot);
  if (snapshot.snapshotHash !== expected) {
    issues.push({
      field: "snapshotHash",
      message: `hash mismatch — expected ${expected}`,
    });
    return { ok: false, issues, snapshot: null };
  }

  return { ok: true, issues: [], snapshot };
}

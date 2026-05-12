/**
 * Phase 20B snapshot serializer.
 *
 * Produces a complete snapshot from explicit inputs. The caller is
 * responsible for supplying every value — no values are inferred
 * from runtime state, and no wall-clock timestamp is captured unless
 * explicitly passed in.
 */

import type { CameraMode, WorkspacePanelId, WorkspacePresetId } from "@/workspaces/types";

import {
  SNAPSHOT_DISCLAIMER,
  SNAPSHOT_SCHEMA_VERSION,
  type EvidenceFocus,
  type SnapshotDensity,
  type SnapshotTheme,
  type WorkspaceSnapshotV1,
} from "./models";
import { computeSnapshotHash } from "./snapshotHash";

export interface SnapshotInput {
  presetId: WorkspacePresetId;
  missionId: string | null;
  replayRunId: string | null;
  selectedEventId: string | null;
  selectedPanelIds: readonly WorkspacePanelId[];
  walkthroughStep: number | null;
  cameraMode: CameraMode;
  evidenceFocus: EvidenceFocus;
  theme: SnapshotTheme;
  density: SnapshotDensity;
  /** Optional caller-supplied timestamp (rare; tests pass null). */
  capturedAtUtc?: string | null;
}

export function serializeWorkspaceSnapshot(
  input: SnapshotInput,
): WorkspaceSnapshotV1 {
  const draft: WorkspaceSnapshotV1 = {
    schemaVersion: SNAPSHOT_SCHEMA_VERSION,
    presetId: input.presetId,
    missionId: input.missionId,
    replayRunId: input.replayRunId,
    selectedEventId: input.selectedEventId,
    selectedPanelIds: [...input.selectedPanelIds].sort(),
    walkthroughStep: input.walkthroughStep,
    cameraMode: input.cameraMode,
    evidenceFocus: input.evidenceFocus,
    theme: input.theme,
    density: input.density,
    capturedAtUtc: input.capturedAtUtc ?? null,
    snapshotHash: "",
    disclaimer: SNAPSHOT_DISCLAIMER,
  };
  return { ...draft, snapshotHash: computeSnapshotHash(draft) };
}

/** Render the snapshot as canonical JSON (sorted keys, 2-space indent). */
export function snapshotToJsonString(snapshot: WorkspaceSnapshotV1): string {
  // Use JSON.stringify with sorted-key replacer for human readability.
  const sortedKeys = (obj: Record<string, unknown>): string[] =>
    Object.keys(obj).sort();
  return JSON.stringify(
    snapshot,
    (_, value) => {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const out: Record<string, unknown> = {};
        for (const k of sortedKeys(value as Record<string, unknown>)) {
          out[k] = (value as Record<string, unknown>)[k];
        }
        return out;
      }
      return value;
    },
    2,
  );
}

/**
 * Phase 19 scene-snapshot adapter.
 *
 * The adapter mirrors the deterministic eligibility check from
 * ``backend/app/scene_snapshot/pipeline.py``. It NEVER claims a
 * snapshot exists unless the artifact registry + spatial-replay
 * artifact together prove it could. The frontend uses this to
 * render the SceneSnapshotPanel without touching the network.
 */

import type {
  ArtifactRegistryRecord,
  SpatialReplayArtifact,
} from "./types";

export type SceneSnapshotStatus =
  | "bag_backed"
  | "fixture"
  | "not_executed"
  | "unavailable";

export interface SceneSnapshotState {
  run_id: string;
  status: SceneSnapshotStatus;
  eligible_for_bag_backed_snapshot: boolean;
  derivation_source: string;
  bag_status: string;
  integrity: string;
  reviewer_export_ready: boolean;
  artifact_registry_entry: string;
  spatial_replay_path: string;
  artifact_hash_chain: ReadonlyArray<{
    relative_path: string;
    sha256_prefix: string;
    size_bytes: number;
  }>;
  missing_inputs: readonly string[];
  notes: readonly string[];
}

function shortHash(hex: string): string {
  return (hex || "").slice(0, 16);
}

/**
 * Compute the snapshot state for one run, mirroring the backend
 * pipeline's eligibility rules.
 */
export function computeSceneSnapshot(
  runId: string,
  artifact: SpatialReplayArtifact | null,
  record: ArtifactRegistryRecord | null,
): SceneSnapshotState {
  const missing: string[] = [];
  if (!artifact) {
    missing.push(`spatial-replay/runs/${runId}/spatial-replay.json`);
  }
  if (!record) {
    missing.push(
      `spatial-replay/registry/canonical-artifacts.json record for ${runId}`,
    );
  }

  const derivation = artifact?.derivation_source ?? "";
  const bag_status = (artifact?.bag_status as string) ?? "";
  const integrity = record?.integrity ?? "missing";

  const eligible =
    artifact !== null &&
    record !== null &&
    derivation === "bag_backed" &&
    bag_status === "bag_backed" &&
    integrity === "passed";

  let status: SceneSnapshotStatus;
  if (eligible) {
    status = "bag_backed";
  } else if (derivation === "fixture" && integrity === "passed") {
    status = "fixture";
  } else if (!artifact && !record) {
    status = "unavailable";
  } else {
    status = "not_executed";
  }

  if (status === "not_executed") {
    if (derivation !== "bag_backed") {
      missing.push(
        `derivation_source = bag_backed (currently '${derivation}')`,
      );
    }
    if (bag_status !== "bag_backed") {
      missing.push(`bag_status = bag_backed (currently '${bag_status}')`);
    }
    if (integrity !== "passed") {
      missing.push(`registry integrity = passed (currently '${integrity}')`);
    }
  }

  const hashChain =
    record?.files.map((f) => ({
      relative_path: f.relative_path,
      sha256_prefix: shortHash(f.expected_hash),
      size_bytes: f.size_bytes,
    })) ?? [];

  const notes: string[] = [];
  if (status === "fixture") {
    notes.push("Fixture-derived run; not eligible for a bag-backed snapshot.");
  } else if (status === "unavailable") {
    notes.push("No spatial-replay or registry record for this run id.");
  } else if (status === "bag_backed") {
    notes.push(
      "Eligible for a bag-backed reviewer snapshot. A browser-render harness is required to produce the image.",
    );
  }

  return {
    run_id: runId,
    status,
    eligible_for_bag_backed_snapshot: eligible,
    derivation_source: derivation,
    bag_status,
    integrity,
    reviewer_export_ready: eligible,
    artifact_registry_entry:
      record !== null
        ? "spatial-replay/registry/canonical-artifacts.json"
        : "",
    spatial_replay_path:
      artifact !== null
        ? `spatial-replay/runs/${runId}/spatial-replay.json`
        : "",
    artifact_hash_chain: hashChain,
    missing_inputs: missing,
    notes,
  };
}

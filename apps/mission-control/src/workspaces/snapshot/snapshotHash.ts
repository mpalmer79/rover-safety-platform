/**
 * Phase 20B deterministic snapshot hash.
 *
 * The hash is computed over the canonical JSON form (keys sorted)
 * EXCLUDING ``snapshotHash`` and ``capturedAtUtc``. This makes the
 * hash sensitive to meaningful review-state changes only.
 *
 * Honesty rule: the hash is not cryptographically authoritative; it
 * is a deterministic fingerprint suitable for handoff. The verbatim
 * disclaimer remains in every snapshot.
 */

import type { WorkspaceSnapshotV1 } from "./models";

type Hashable = Omit<WorkspaceSnapshotV1, "snapshotHash" | "capturedAtUtc">;

/**
 * FNV-1a 32-bit hash, rendered as an 8-char hex prefix. Deterministic
 * in pure JS, no Node-only crypto required.
 */
function fnv1a(input: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  // Convert to unsigned 32-bit and zero-pad.
  return (hash >>> 0).toString(16).padStart(8, "0");
}

/** Canonical JSON serializer: sorted keys at every depth. */
export function canonicalize(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (Array.isArray(value)) {
    return `[${value.map(canonicalize).join(",")}]`;
  }
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj).sort();
    return `{${keys
      .map((k) => `${JSON.stringify(k)}:${canonicalize(obj[k])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

/** Compute the deterministic snapshot hash. */
export function computeSnapshotHash(snapshot: WorkspaceSnapshotV1): string {
  const hashable: Hashable = {
    schemaVersion: snapshot.schemaVersion,
    presetId: snapshot.presetId,
    missionId: snapshot.missionId,
    replayRunId: snapshot.replayRunId,
    selectedEventId: snapshot.selectedEventId,
    selectedPanelIds: [...snapshot.selectedPanelIds].sort(),
    walkthroughStep: snapshot.walkthroughStep,
    cameraMode: snapshot.cameraMode,
    evidenceFocus: snapshot.evidenceFocus,
    theme: snapshot.theme,
    density: snapshot.density,
    disclaimer: snapshot.disclaimer,
  };
  return `ws-${fnv1a(canonicalize(hashable))}`;
}

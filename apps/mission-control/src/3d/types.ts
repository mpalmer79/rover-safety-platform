/**
 * Shared 3D scene types.
 *
 * Phase 18 honesty rules baked in:
 *   - the scene NEVER opens a network socket;
 *   - playback is sequence-driven, not wall-clock-driven;
 *   - the camera rig and waypoint geometry are deterministic;
 *   - the scene reads from the spatial-replay artifact verbatim.
 */

import type {
  RehearsalEvent,
  SpatialDerivationSource,
  SpatialReplayArtifact,
} from "@/adapters/types";
import type { MissionRoute, SpatialPoint } from "@/adapters/spatial";

export type PlaybackMode =
  | "overview"
  | "operator_review"
  | "safety_intervention"
  | "trajectory_analysis";

export interface CameraTarget {
  position: readonly [number, number, number];
  lookAt: readonly [number, number, number];
  /** A short label rendered in the cinematic mode badge. */
  label: string;
}

export interface SceneEventMarker {
  event_id: string;
  position: readonly [number, number, number];
  severity: RehearsalEvent["severity"];
  event_subtype: string;
  description: string;
  deterministic_hash: string;
}

export interface SceneInputs {
  route: MissionRoute;
  events: readonly RehearsalEvent[];
  artifact: SpatialReplayArtifact | null;
  /** Index into the ordered event stream that the scrubber selected. */
  activeIndex: number;
  /** Current playback mode (drives the camera rig). */
  playbackMode: PlaybackMode;
  /** Verbatim string the scene displays in its lower-left badge. */
  derivationSource: SpatialDerivationSource;
}

export function pointTo3D(
  point: SpatialPoint,
  height = 0,
): readonly [number, number, number] {
  return [point.x, height, -point.y];
}

export function spatialMidpoint(
  a: readonly [number, number, number],
  b: readonly [number, number, number],
): readonly [number, number, number] {
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
}

export function spatialDistance(
  a: readonly [number, number, number],
  b: readonly [number, number, number],
): number {
  const dx = a[0] - b[0];
  const dy = a[1] - b[1];
  const dz = a[2] - b[2];
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

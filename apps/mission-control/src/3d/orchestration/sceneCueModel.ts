/**
 * Phase 20B scene cue model.
 *
 * Scene cues are deterministic descriptions of "what the 3D scene
 * should show next". They are produced by pure functions from
 * workspace state — no wall-clock timing, no randomness, no
 * continuous animation loops.
 *
 * The cues are consumed by the immersive scene to drive camera
 * mode, focus target, and rationale captions. The scene itself
 * never invents a cue.
 */

import type { CameraMode } from "@/workspaces/types";

export type SceneCueKind =
  | "overview"
  | "operator_request"
  | "mission_validation"
  | "supervisor_decision"
  | "trajectory_follow"
  | "safety_intervention"
  | "replay_evidence"
  | "limitation_focus"
  | "completion_summary";

export interface SceneCue {
  kind: SceneCueKind;
  cameraMode: CameraMode;
  /** Human-readable focus target label. */
  focusTarget: string | null;
  /** Optional artifact path or registry record id. */
  focusRef: string | null;
  /** Rationale rendered in the scene caption. */
  rationale: string;
  /** Optional ordering hint within a cue sequence. */
  order: number;
}

export const DEFAULT_OVERVIEW_CUE: SceneCue = {
  kind: "overview",
  cameraMode: "orbit",
  focusTarget: null,
  focusRef: null,
  rationale: "No mission selected. Camera orbits the default site overview.",
  order: 0,
};

import type { WalkthroughStepId } from "@/reviewer/steps";

import type { SceneCue, SceneCueKind } from "./sceneCueModel";

/**
 * Map a walkthrough step id to a scene cue kind. The mapping is
 * deterministic and intentional — there is no fallback inference.
 */
export const STEP_TO_CUE: Readonly<Record<WalkthroughStepId, SceneCueKind>> = {
  "operator-request": "operator_request",
  "proposal-generation": "operator_request",
  "sanitizer-decision": "mission_validation",
  "compiler-result": "mission_validation",
  "validator-result": "mission_validation",
  "supervisor-decision": "supervisor_decision",
  "rehearsal-execution": "trajectory_follow",
  "replay-evidence": "replay_evidence",
  "analytics-outcome": "completion_summary",
  "unresolved-limitations": "limitation_focus",
};

const KIND_TO_CAMERA: Readonly<Record<SceneCueKind, SceneCue["cameraMode"]>> = {
  overview: "orbit",
  operator_request: "top-down",
  mission_validation: "top-down",
  supervisor_decision: "top-down",
  trajectory_follow: "follow",
  safety_intervention: "fixed",
  replay_evidence: "follow",
  limitation_focus: "fixed",
  completion_summary: "orbit",
};

export function planCameraCue(step: WalkthroughStepId): SceneCue {
  const kind = STEP_TO_CUE[step];
  return {
    kind,
    cameraMode: KIND_TO_CAMERA[kind],
    focusTarget: step,
    focusRef: null,
    rationale: `Walkthrough step ${step} maps to scene cue ${kind}.`,
    order: 0,
  };
}

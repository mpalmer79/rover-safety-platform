import type { SpatialReplayArtifact } from "@/adapters/types";

import type { SceneCue } from "./sceneCueModel";

export function resolveTrajectoryFocus(
  spatial: SpatialReplayArtifact | null,
): SceneCue | null {
  if (!spatial) return null;
  if (spatial.sample_count === 0) {
    return {
      kind: "limitation_focus",
      cameraMode: "fixed",
      focusTarget: "trajectory.empty",
      focusRef: spatial.run_id,
      rationale:
        "Spatial-replay artefact has zero samples — trajectory cannot be followed.",
      order: 0,
    };
  }
  return {
    kind: "trajectory_follow",
    cameraMode: "follow",
    focusTarget: spatial.scenario_id,
    focusRef: spatial.run_id,
    rationale: `Follow ${spatial.sample_count} samples derived from ${spatial.derivation_source}.`,
    order: 0,
  };
}

import type { SupervisorDecision } from "@/adapters/types";

import type { SceneCue } from "./sceneCueModel";

export function resolveSupervisorFocus(
  decision: SupervisorDecision | null,
): SceneCue | null {
  if (!decision) return null;
  if (decision.decision_status === "approved") {
    return {
      kind: "supervisor_decision",
      cameraMode: "top-down",
      focusTarget: "supervisor.approved",
      focusRef: decision.decision_id,
      rationale: `Supervisor approved: ${decision.safety_status}.`,
      order: 0,
    };
  }
  return {
    kind: "safety_intervention",
    cameraMode: "fixed",
    focusTarget: "supervisor.intervention",
    focusRef: decision.decision_id,
    rationale:
      decision.rejected_reasons.length > 0
        ? `Supervisor rejected: ${decision.rejected_reasons.join(", ")}.`
        : "Supervisor flagged this run for human review.",
    order: 0,
  };
}

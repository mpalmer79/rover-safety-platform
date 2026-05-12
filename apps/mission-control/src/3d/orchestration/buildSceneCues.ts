/**
 * Phase 20B scene cue builder.
 *
 * Combines workspace state into a deterministic ordered cue list.
 * The caller is the immersive scene; the scene NEVER invents a cue.
 */

import type {
  RehearsalAudit,
  SpatialReplayArtifact,
} from "@/adapters/types";
import type { WalkthroughStepId } from "@/reviewer/steps";

import { resolveEventFocus } from "./eventFocusResolver";
import { resolveSupervisorFocus } from "./supervisorFocusResolver";
import { resolveTrajectoryFocus } from "./trajectoryFocusResolver";
import { planCameraCue } from "./cameraCuePlanner";
import { DEFAULT_OVERVIEW_CUE, type SceneCue } from "./sceneCueModel";

export interface SceneCueInput {
  audit: RehearsalAudit | null;
  spatial: SpatialReplayArtifact | null;
  walkthroughStep: WalkthroughStepId | null;
  /** Selected event id from the event-stream panel. */
  selectedEventId: string | null;
}

/**
 * Build a deterministic ordered list of scene cues. The first cue
 * is the "active" cue; subsequent entries provide context.
 */
export function buildSceneCues(input: SceneCueInput): readonly SceneCue[] {
  const cues: SceneCue[] = [];
  let order = 0;
  const push = (cue: SceneCue | null) => {
    if (cue) cues.push({ ...cue, order: order++ });
  };

  if (!input.audit) {
    push(DEFAULT_OVERVIEW_CUE);
    return cues;
  }
  if (input.walkthroughStep) {
    push(planCameraCue(input.walkthroughStep));
  }
  if (input.selectedEventId) {
    push(resolveEventFocus(input.audit.runtime?.events ?? [], input.selectedEventId));
  }
  push(resolveSupervisorFocus(input.audit.decision));
  push(resolveTrajectoryFocus(input.spatial));
  if (cues.length === 0) push(DEFAULT_OVERVIEW_CUE);
  return cues;
}

export function activeSceneCue(input: SceneCueInput): SceneCue {
  const cues = buildSceneCues(input);
  return cues[0] ?? DEFAULT_OVERVIEW_CUE;
}

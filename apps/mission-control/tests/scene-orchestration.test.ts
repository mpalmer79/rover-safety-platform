/**
 * Phase 20B scene orchestration tests.
 *
 * Pins:
 *   * scene cues are deterministic — same input, same output;
 *   * cues never use randomness or wall-clock time;
 *   * a missing audit yields the overview cue, never a fake cue;
 *   * walkthrough step → cue mapping is exhaustive.
 */

import { describe, it, expect } from "vitest";

import {
  activeSceneCue,
  buildSceneCues,
  DEFAULT_OVERVIEW_CUE,
  planCameraCue,
  resolveEventFocus,
  resolveSupervisorFocus,
  resolveTrajectoryFocus,
  STEP_TO_CUE,
} from "@/3d/orchestration";
import { WALKTHROUGH_STEPS } from "@/reviewer/steps";

import {
  FIX_AUDIT,
  FIX_EVENT_INFO,
  FIX_SPATIAL_ARTIFACT,
  FIX_SUPERVISOR_DECISION,
} from "@/components/__fixtures__/_shared";

describe("scene cues", () => {
  it("default overview when no audit is supplied", () => {
    const cues = buildSceneCues({
      audit: null,
      spatial: null,
      walkthroughStep: null,
      selectedEventId: null,
    });
    expect(cues).toHaveLength(1);
    expect(cues[0].kind).toBe("overview");
  });

  it("walkthrough step produces a deterministic cue", () => {
    const cue = planCameraCue("supervisor-decision");
    expect(cue.kind).toBe("supervisor_decision");
    expect(cue.cameraMode).toBe("top-down");
  });

  it("STEP_TO_CUE covers every walkthrough step", () => {
    for (const step of WALKTHROUGH_STEPS) {
      expect(STEP_TO_CUE[step.id]).toBeDefined();
    }
  });

  it("event focus resolver returns null for unknown event id", () => {
    const cue = resolveEventFocus([FIX_EVENT_INFO], "not-a-real-event");
    expect(cue).toBeNull();
  });

  it("event focus resolver picks the matching event", () => {
    const cue = resolveEventFocus([FIX_EVENT_INFO], FIX_EVENT_INFO.event_id);
    expect(cue?.focusRef).toBe(FIX_EVENT_INFO.event_id);
    expect(cue?.cameraMode).toBe("follow");
  });

  it("supervisor focus surfaces rejected decisions as safety_intervention", () => {
    const cue = resolveSupervisorFocus(FIX_SUPERVISOR_DECISION);
    expect(cue?.kind).toBe("safety_intervention");
  });

  it("trajectory focus follows non-empty samples", () => {
    const cue = resolveTrajectoryFocus(FIX_SPATIAL_ARTIFACT);
    expect(cue?.kind).toBe("trajectory_follow");
    expect(cue?.cameraMode).toBe("follow");
  });

  it("trajectory focus is null when artefact is null", () => {
    expect(resolveTrajectoryFocus(null)).toBeNull();
  });

  it("buildSceneCues is deterministic under repeat calls", () => {
    const inputs = {
      audit: FIX_AUDIT,
      spatial: FIX_SPATIAL_ARTIFACT,
      walkthroughStep: "supervisor-decision" as const,
      selectedEventId: null,
    };
    const a = buildSceneCues(inputs);
    const b = buildSceneCues(inputs);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  it("activeSceneCue falls back to overview when no input applies", () => {
    expect(activeSceneCue({
      audit: null,
      spatial: null,
      walkthroughStep: null,
      selectedEventId: null,
    })).toEqual(DEFAULT_OVERVIEW_CUE);
  });
});

import { describe, it, expect } from "vitest";

import { chooseTarget } from "@/3d/ReplayCameraRig";
import type { PlaybackMode } from "@/3d/types";

const FOCUS: readonly [number, number, number] = [2, 0, 1];
const CENTER: readonly [number, number, number] = [0, 0, 0];

describe("ReplayCameraRig", () => {
  it("is deterministic for identical inputs", () => {
    const modes: PlaybackMode[] = [
      "overview",
      "operator_review",
      "safety_intervention",
      "trajectory_analysis",
    ];
    for (const mode of modes) {
      const a = chooseTarget(mode, FOCUS, CENTER, 4);
      const b = chooseTarget(mode, FOCUS, CENTER, 4);
      expect(a.position).toEqual(b.position);
      expect(a.lookAt).toEqual(b.lookAt);
      expect(a.label).toBe(b.label);
    }
  });

  it("renders a finite-distance camera in every mode", () => {
    const modes: PlaybackMode[] = [
      "overview",
      "operator_review",
      "safety_intervention",
      "trajectory_analysis",
    ];
    for (const mode of modes) {
      const target = chooseTarget(mode, FOCUS, CENTER, 4);
      for (const v of [...target.position, ...target.lookAt]) {
        expect(Number.isFinite(v)).toBe(true);
      }
    }
  });

  it("overview camera is farther from the focus than operator review", () => {
    const overview = chooseTarget("overview", FOCUS, CENTER, 4);
    const operator = chooseTarget("operator_review", FOCUS, CENTER, 4);
    const dist = (a: readonly number[], b: readonly number[]) =>
      Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    expect(dist(overview.position, FOCUS)).toBeGreaterThan(
      dist(operator.position, FOCUS),
    );
  });

  it("safety intervention is the closest mode to the focus", () => {
    const intervention = chooseTarget("safety_intervention", FOCUS, CENTER, 4);
    const operator = chooseTarget("operator_review", FOCUS, CENTER, 4);
    const dist = (a: readonly number[], b: readonly number[]) =>
      Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    expect(dist(intervention.position, FOCUS)).toBeLessThan(
      dist(operator.position, FOCUS),
    );
  });

  it("trajectory analysis looks at the scene center", () => {
    const target = chooseTarget("trajectory_analysis", FOCUS, CENTER, 4);
    expect(target.lookAt).toEqual(CENTER);
  });

  it("returns the verbatim mode label", () => {
    const target = chooseTarget("safety_intervention", FOCUS, CENTER, 4);
    expect(target.label).toBe("safety intervention");
  });
});

"use client";

import { useThree } from "@react-three/fiber";
import { useEffect } from "react";

import type { CameraTarget, PlaybackMode } from "./types";
import { spatialMidpoint } from "./types";

interface ReplayCameraRigProps {
  mode: PlaybackMode;
  /** World-space target the camera should look at (e.g. active waypoint). */
  focus: readonly [number, number, number];
  /** Centre of the entire mission area, used by the overview camera. */
  sceneCenter: readonly [number, number, number];
  /** Tunable bounding-radius — drives the overview camera distance. */
  sceneRadius: number;
}

/**
 * Deterministic camera rig.
 *
 * The rig snaps the perspective camera's POSITION to the chosen
 * mode's target. Orientation is delegated to OrbitControls so the
 * rover (its target) stays centered as it moves; otherwise the
 * rig's per-frame lookAt fights OrbitControls and the rover drifts
 * off-screen.
 */
export function ReplayCameraRig({
  mode,
  focus,
  sceneCenter,
  sceneRadius,
}: ReplayCameraRigProps) {
  const { camera } = useThree();

  useEffect(() => {
    const target = chooseTarget(mode, focus, sceneCenter, sceneRadius);
    camera.position.set(target.position[0], target.position[1], target.position[2]);
    camera.updateProjectionMatrix();
  }, [camera, mode, focus, sceneCenter, sceneRadius]);

  return null;
}

export function chooseTarget(
  mode: PlaybackMode,
  focus: readonly [number, number, number],
  sceneCenter: readonly [number, number, number],
  sceneRadius: number,
): CameraTarget {
  switch (mode) {
    case "operator_review":
      return {
        position: [focus[0] + 1.6, focus[1] + 1.4, focus[2] + 1.6],
        lookAt: focus,
        label: "operator review",
      };
    case "safety_intervention":
      return {
        position: [focus[0] + 0.8, focus[1] + 0.9, focus[2] + 0.8],
        lookAt: spatialMidpoint(focus, sceneCenter),
        label: "safety intervention",
      };
    case "trajectory_analysis":
      return {
        position: [
          sceneCenter[0],
          sceneCenter[1] + sceneRadius * 1.2,
          sceneCenter[2] + sceneRadius * 0.4,
        ],
        lookAt: sceneCenter,
        label: "trajectory analysis",
      };
    case "overview":
    default:
      return {
        position: [
          sceneCenter[0] + sceneRadius * 1.4,
          sceneCenter[1] + sceneRadius * 1.0,
          sceneCenter[2] + sceneRadius * 1.4,
        ],
        lookAt: sceneCenter,
        label: "overview",
      };
  }
}

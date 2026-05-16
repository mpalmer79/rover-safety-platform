"use client";

import { useMemo } from "react";
import { Vector3 } from "three";

import type { MissionRoute } from "@/adapters/spatial";
import { pointTo3D } from "./types";

interface ReplayTrajectory3DProps {
  route: MissionRoute;
  /** Number of segments to highlight (sequence-driven by the scrubber). */
  highlightUpTo: number;
}

/**
 * Trajectory polyline.
 *
 * Two passes:
 *   - dimmed line for the entire derived path;
 *   - highlighted line up to ``highlightUpTo`` for the active
 *     scrubber position.
 *
 * No per-frame mutation; the line is rebuilt only when route /
 * highlight changes.
 */
export function ReplayTrajectory3D({
  route,
  highlightUpTo,
}: ReplayTrajectory3DProps) {
  const fullPoints = useMemo<Vector3[]>(() => {
    if (route.segments.length === 0) {
      return route.waypoints.map((w) =>
        new Vector3(...pointTo3D(w.position, 0.05)),
      );
    }
    const pts: Vector3[] = [];
    pts.push(new Vector3(...pointTo3D(route.segments[0].from, 0.05)));
    for (const s of route.segments) {
      pts.push(new Vector3(...pointTo3D(s.to, 0.05)));
    }
    return pts;
  }, [route]);

  const highlightPoints = useMemo<Vector3[]>(() => {
    const stop = Math.max(0, Math.min(highlightUpTo + 1, fullPoints.length));
    return fullPoints.slice(0, stop);
  }, [fullPoints, highlightUpTo]);

  if (fullPoints.length < 2) {
    return null;
  }

  const fullColour =
    route.derivation_source === "bag_backed"
      ? "#4ade80"
      : route.derivation_source === "fixture"
        ? "#facc15"
        : "#3cb4a8";

  return (
    <group>
      <Polyline points={fullPoints} color={fullColour} opacity={0.25} />
      <Polyline points={highlightPoints} color={fullColour} opacity={0.95} />
    </group>
  );
}

interface PolylineProps {
  points: Vector3[];
  color: string;
  opacity: number;
}

function Polyline({ points, color, opacity }: PolylineProps) {
  const positions = useMemo(() => {
    const arr = new Float32Array(points.length * 3);
    points.forEach((p, i) => {
      arr[i * 3 + 0] = p.x;
      arr[i * 3 + 1] = p.y;
      arr[i * 3 + 2] = p.z;
    });
    return arr;
  }, [points]);

  if (points.length < 2) return null;
  return (
    <line>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} transparent opacity={opacity} linewidth={2} />
    </line>
  );
}

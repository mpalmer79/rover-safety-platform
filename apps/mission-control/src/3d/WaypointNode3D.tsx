"use client";

import { Html } from "@react-three/drei";

import type { SpatialWaypoint } from "@/adapters/spatial";
import { pointTo3D } from "./types";

const STAGE_COLOR: Record<string, string> = {
  move: "#3cb4a8",
  patrol: "#7c8499",
  inspect: "#facc15",
  wait: "#525c75",
  stop: "#f87171",
  dock: "#4ade80",
  rotate: "#a78bfa",
};

interface WaypointNode3DProps {
  waypoint: SpatialWaypoint;
  active?: boolean;
  showLabel?: boolean;
}

/**
 * Single waypoint marker.
 *
 * Geometry: a vertical pillar capped with a coloured sphere. Active
 * waypoint glows softly. Position is read from the waypoint's
 * deterministic position (already projected into 3D).
 */
export function WaypointNode3D({
  waypoint,
  active = false,
  showLabel = true,
}: WaypointNode3DProps) {
  const position = pointTo3D(waypoint.position);
  const colour = STAGE_COLOR[waypoint.stage_kind] ?? "#3cb4a8";
  const scale = active ? 1.4 : 1;
  return (
    <group position={position}>
      {/* pillar */}
      <mesh position={[0, 0.25, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.04, 0.5, 12]} />
        <meshStandardMaterial color={colour} emissive={colour} emissiveIntensity={active ? 0.6 : 0.15} />
      </mesh>
      {/* head */}
      <mesh position={[0, 0.55, 0]} castShadow scale={scale}>
        <sphereGeometry args={[0.09, 24, 16]} />
        <meshStandardMaterial color={colour} emissive={colour} emissiveIntensity={active ? 0.9 : 0.3} />
      </mesh>
      {/* base ring */}
      <mesh position={[0, 0.005, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.12, 0.18, 24]} />
        <meshBasicMaterial color={colour} transparent opacity={active ? 0.8 : 0.45} />
      </mesh>
      {showLabel ? (
        <Html
          position={[0, 0.85, 0]}
          center
          style={{ pointerEvents: "none" }}
        >
          <span
            data-testid={`waypoint-label-${waypoint.waypoint_id}`}
            className="rounded bg-base-50/90 px-1.5 py-0.5 font-mono text-[10px] text-base-800"
          >
            {waypoint.waypoint_id}
          </span>
        </Html>
      ) : null}
    </group>
  );
}

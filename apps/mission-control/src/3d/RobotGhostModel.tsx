"use client";

import { Html } from "@react-three/drei";

import type { SpatialPoint } from "@/adapters/spatial";
import { pointTo3D } from "./types";

interface RobotGhostModelProps {
  position: SpatialPoint;
  headingDeg?: number;
  active?: boolean;
}

/**
 * Stylised rover ghost model.
 *
 * The model is intentionally minimal — a chassis box, two wheels,
 * a heading arrow — so a reviewer never mistakes it for a real
 * robot model or live telemetry. Position is read deterministically
 * from the active waypoint or the active pose sample.
 */
export function RobotGhostModel({
  position,
  headingDeg = 0,
  active = true,
}: RobotGhostModelProps) {
  const pos = pointTo3D(position, 0.12);
  const yaw = (-headingDeg * Math.PI) / 180; // y-up coordinate flip
  const opacity = active ? 0.95 : 0.6;
  return (
    <group position={pos} rotation={[0, yaw, 0]}>
      {/* chassis */}
      <mesh position={[0, 0.05, 0]} castShadow>
        <boxGeometry args={[0.3, 0.08, 0.45]} />
        <meshStandardMaterial color="#3cb4a8" roughness={0.55} metalness={0.3} transparent opacity={opacity} />
      </mesh>
      {/* sensor stack */}
      <mesh position={[0, 0.13, -0.05]}>
        <cylinderGeometry args={[0.04, 0.04, 0.08, 12]} />
        <meshStandardMaterial color="#1b3d3a" roughness={0.7} />
      </mesh>
      {/* wheels */}
      <mesh position={[-0.18, 0.04, 0.18]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.06, 0.06, 0.04, 16]} />
        <meshStandardMaterial color="#0e1117" roughness={1} />
      </mesh>
      <mesh position={[0.18, 0.04, 0.18]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.06, 0.06, 0.04, 16]} />
        <meshStandardMaterial color="#0e1117" roughness={1} />
      </mesh>
      <mesh position={[-0.18, 0.04, -0.18]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.06, 0.06, 0.04, 16]} />
        <meshStandardMaterial color="#0e1117" roughness={1} />
      </mesh>
      <mesh position={[0.18, 0.04, -0.18]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.06, 0.06, 0.04, 16]} />
        <meshStandardMaterial color="#0e1117" roughness={1} />
      </mesh>
      {/* heading indicator */}
      <mesh position={[0, 0.1, -0.28]} rotation={[Math.PI / 2, 0, 0]}>
        <coneGeometry args={[0.04, 0.12, 12]} />
        <meshStandardMaterial color="#facc15" emissive="#facc15" emissiveIntensity={0.5} />
      </mesh>
      <Html
        position={[0, 0.4, 0]}
        center
        distanceFactor={5}
        style={{ pointerEvents: "none" }}
      >
        <span
          data-testid="robot-ghost-label"
          className="rounded bg-base-50/80 px-1.5 py-0.5 font-mono text-[10px] text-base-800"
        >
          ghost · derived
        </span>
      </Html>
    </group>
  );
}

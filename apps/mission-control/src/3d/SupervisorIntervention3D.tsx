"use client";

import { Html } from "@react-three/drei";

import type { SpatialEventMarker } from "@/adapters/spatial";
import { pointTo3D } from "./types";

interface SupervisorIntervention3DProps {
  marker: SpatialEventMarker;
  active?: boolean;
}

/**
 * Visual marker for a supervisor intervention.
 *
 * Distinct from the generic event beacon: the intervention marker
 * is a halo + downward-pointing chevron, communicating "supervisor
 * authority intervened here." Only renders for ``rejection`` /
 * ``warning`` events that carry a position.
 */
export function SupervisorIntervention3D({
  marker,
  active = false,
}: SupervisorIntervention3DProps) {
  if (!marker.position) return null;
  if (marker.severity === "info") return null;
  const pos = pointTo3D(marker.position, 0.6);
  return (
    <group position={pos}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.32, 0.4, 32]} />
        <meshBasicMaterial color="#f87171" transparent opacity={active ? 0.85 : 0.45} />
      </mesh>
      <mesh position={[0, -0.18, 0]} rotation={[Math.PI, 0, 0]}>
        <coneGeometry args={[0.1, 0.22, 12]} />
        <meshStandardMaterial color="#f87171" emissive="#f87171" emissiveIntensity={active ? 0.9 : 0.3} />
      </mesh>
      <Html
        position={[0, 0.4, 0]}
        center
        distanceFactor={6}
        style={{ pointerEvents: "none" }}
      >
        <span
          data-testid={`intervention-${marker.event_id}`}
          className="rounded bg-status-rejected/90 px-1.5 py-0.5 font-mono text-[10px] text-base-50"
        >
          supervisor
        </span>
      </Html>
    </group>
  );
}

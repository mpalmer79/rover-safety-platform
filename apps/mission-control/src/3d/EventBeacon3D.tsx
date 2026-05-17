"use client";

import { Html } from "@react-three/drei";

import { pointTo3D } from "./types";
import type { SpatialEventMarker } from "@/adapters/spatial";

const SEVERITY_COLOR: Record<SpatialEventMarker["severity"], string> = {
  info: "#aab1c1",
  warning: "#facc15",
  rejection: "#f87171",
};

interface EventBeacon3DProps {
  marker: SpatialEventMarker;
  active?: boolean;
}

/**
 * Vertical beacon at an event location.
 *
 * Beacons render only when the underlying marker has a position
 * (i.e. the event aligned to a pose sample or a waypoint payload).
 * Off-map events are skipped — the timeline panel is the only
 * surface that shows them.
 */
export function EventBeacon3D({ marker, active = false }: EventBeacon3DProps) {
  if (!marker.position) return null;
  const pos = pointTo3D(marker.position, 0);
  const colour = SEVERITY_COLOR[marker.severity];
  const heightTo = active ? 1.4 : 0.85;
  return (
    <group position={pos}>
      <mesh position={[0, heightTo / 2, 0]}>
        <cylinderGeometry args={[0.025, 0.025, heightTo, 8]} />
        <meshBasicMaterial color={colour} transparent opacity={active ? 0.9 : 0.5} />
      </mesh>
      <mesh position={[0, heightTo + 0.03, 0]}>
        <sphereGeometry args={[0.06, 16, 12]} />
        <meshStandardMaterial
          color={colour}
          emissive={colour}
          emissiveIntensity={active ? 0.9 : 0.3}
        />
      </mesh>
      {active ? (
        <Html
          position={[0, heightTo + 0.25, 0]}
          center
          style={{ pointerEvents: "none" }}
        >
          <span
            data-testid={`event-beacon-${marker.event_id}`}
            className="rounded bg-base-50/90 px-1.5 py-0.5 font-mono text-[10px] text-base-800"
          >
            {marker.event_subtype}
          </span>
        </Html>
      ) : null}
    </group>
  );
}

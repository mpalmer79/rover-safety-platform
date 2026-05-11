"use client";

/**
 * Warehouse environment: floor, lane lines, and outline.
 *
 * Geometry is deterministic and rendered from constants — no
 * randomness, no per-frame mutation. The model is illustrative; it
 * is NOT a digital twin of any physical site.
 */

import { Grid } from "@react-three/drei";

interface WarehouseEnvironmentProps {
  /** Half-extent of the floor along x and z (meters). */
  size?: number;
}

export function WarehouseEnvironment({ size = 8 }: WarehouseEnvironmentProps) {
  return (
    <group>
      {/* floor slab */}
      <mesh position={[0, -0.02, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[size * 2, size * 2]} />
        <meshStandardMaterial color="#0e1117" roughness={1} metalness={0} />
      </mesh>

      {/* metric grid */}
      <Grid
        args={[size * 2, size * 2]}
        cellSize={1}
        cellThickness={0.6}
        cellColor="#1d2230"
        sectionSize={5}
        sectionThickness={1.2}
        sectionColor="#3cb4a8"
        fadeDistance={size * 2.5}
        fadeStrength={1}
        infiniteGrid={false}
      />

      {/* warehouse outline */}
      <mesh position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[size - 0.02, size, 64]} />
        <meshBasicMaterial color="#3cb4a8" transparent opacity={0.18} />
      </mesh>

      {/* dock pad */}
      <mesh position={[-size * 0.65, 0.03, -size * 0.55]}>
        <boxGeometry args={[1.4, 0.05, 0.9]} />
        <meshStandardMaterial color="#1b3d3a" roughness={0.9} />
      </mesh>
    </group>
  );
}

"use client";

import { Html } from "@react-three/drei";
import { useEffect, useRef } from "react";
import { Group, MathUtils, Mesh } from "three";
import { useFrame } from "@react-three/fiber";

import type { SpatialPoint } from "@/adapters/spatial";
import { pointTo3D } from "./types";

interface AnimatedRoverProps {
  /** Target position the rover should be moving toward. */
  targetPosition: SpatialPoint;
  /** Target heading in degrees (0° = +y in scene coordinates). */
  targetHeadingDeg: number;
  /** Whether the rover is "moving" (label badge state). */
  moving?: boolean;
  /** Emissive label shown above the rover. */
  label?: string;
}

/**
 * Smoothly-interpolated rover marker.
 *
 * Snaps to the first target on mount, then eases toward subsequent
 * targets at a fixed rate so the rover glides between scrub
 * positions instead of teleporting. Animation is purely visual; the
 * authoritative position is always the deterministic ``targetPosition``.
 */
export function AnimatedRover({
  targetPosition,
  targetHeadingDeg,
  moving = true,
  label = "rover · derived",
}: AnimatedRoverProps) {
  const groupRef = useRef<Group>(null);
  const initialised = useRef(false);

  useEffect(() => {
    if (!groupRef.current || initialised.current) return;
    const [tx, ty, tz] = pointTo3D(targetPosition, 0.12);
    groupRef.current.position.set(tx, ty, tz);
    groupRef.current.rotation.y = (-targetHeadingDeg * Math.PI) / 180;
    initialised.current = true;
  }, [targetPosition, targetHeadingDeg]);

  useFrame((_state, delta) => {
    const group = groupRef.current;
    if (!group) return;
    const [tx, ty, tz] = pointTo3D(targetPosition, 0.12);
    const lerpAlpha = Math.min(1, delta * 6);
    group.position.x = MathUtils.lerp(group.position.x, tx, lerpAlpha);
    group.position.y = MathUtils.lerp(group.position.y, ty, lerpAlpha);
    group.position.z = MathUtils.lerp(group.position.z, tz, lerpAlpha);
    const targetYaw = (-targetHeadingDeg * Math.PI) / 180;
    let delta_yaw = targetYaw - group.rotation.y;
    delta_yaw = Math.atan2(Math.sin(delta_yaw), Math.cos(delta_yaw));
    group.rotation.y += delta_yaw * lerpAlpha;
  });

  return (
    <group ref={groupRef} userData={{ testid: "animated-rover" }}>
      {/* chassis */}
      <mesh position={[0, 0.05, 0]} castShadow>
        <boxGeometry args={[0.32, 0.09, 0.5]} />
        <meshStandardMaterial color="#3cb4a8" roughness={0.55} metalness={0.3} />
      </mesh>
      {/* sensor stack */}
      <mesh position={[0, 0.16, -0.06]}>
        <cylinderGeometry args={[0.05, 0.05, 0.1, 12]} />
        <meshStandardMaterial color="#1b3d3a" roughness={0.7} />
      </mesh>
      <PulseRing visible={moving} />
      {/* wheels */}
      {[
        [-0.19, 0.04, 0.2],
        [0.19, 0.04, 0.2],
        [-0.19, 0.04, -0.2],
        [0.19, 0.04, -0.2],
      ].map(([x, y, z], i) => (
        <mesh
          key={i}
          position={[x, y, z]}
          rotation={[0, 0, Math.PI / 2]}
        >
          <cylinderGeometry args={[0.07, 0.07, 0.05, 16]} />
          <meshStandardMaterial color="#0e1117" roughness={1} />
        </mesh>
      ))}
      {/* heading indicator */}
      <mesh position={[0, 0.11, -0.32]} rotation={[Math.PI / 2, 0, 0]}>
        <coneGeometry args={[0.05, 0.16, 12]} />
        <meshStandardMaterial color="#facc15" emissive="#facc15" emissiveIntensity={0.6} />
      </mesh>
      <Html
        position={[0, 0.5, 0]}
        center
        style={{ pointerEvents: "none" }}
      >
        <span
          data-testid="animated-rover-label"
          className="rounded bg-[color:var(--mc-surface-overlay)] px-1.5 py-0.5 font-mono text-[10px] text-[color:var(--mc-text)] shadow-panel backdrop-blur-sm"
        >
          {label}
        </span>
      </Html>
    </group>
  );
}

function PulseRing({ visible }: { visible: boolean }) {
  const meshRef = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    const m = meshRef.current;
    if (!m) return;
    const t = clock.getElapsedTime();
    const scale = visible ? 1 + 0.18 * Math.sin(t * 3) : 0.6;
    m.scale.set(scale, scale, scale);
    const mat = m.material as { opacity?: number };
    if (visible) {
      mat.opacity = 0.45 + 0.2 * Math.sin(t * 3);
    } else {
      mat.opacity = 0.15;
    }
  });
  return (
    <mesh ref={meshRef} position={[0, 0.005, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[0.32, 0.42, 32]} />
      <meshBasicMaterial color="#3cb4a8" transparent opacity={0.4} />
    </mesh>
  );
}

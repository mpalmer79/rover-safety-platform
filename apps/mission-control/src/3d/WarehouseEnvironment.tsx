"use client";

/**
 * Warehouse environment: floor, grid, periphery, and optional
 * detail props (shelving racks, mezzanine slab, charging dock,
 * companion rover, crate stacks).
 *
 * Geometry is deterministic and rendered from constants — no
 * randomness, no per-frame mutation. The model is illustrative; it
 * is NOT a digital twin of any physical site.
 */

import { Grid } from "@react-three/drei";

interface WarehouseEnvironmentProps {
  size?: number;
  /**
   * When true, render warehouse context (shelves, mezzanine,
   * crates, second dock, companion rover). The default scene keeps
   * the floor + grid only so existing tests / fixtures are
   * unaffected.
   */
  detailed?: boolean;
}

export function WarehouseEnvironment({
  size = 8,
  detailed = false,
}: WarehouseEnvironmentProps) {
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

      {detailed ? <WarehouseDetail size={size} /> : null}
    </group>
  );
}

function WarehouseDetail({ size }: { size: number }) {
  const halfX = size * 0.92;
  const halfZ = size * 0.92;
  return (
    <group>
      {/* periphery shelving — line both long walls with bays */}
      <ShelfRow z={-halfZ + 0.5} count={6} spanX={size * 1.4} />
      <ShelfRow z={halfZ - 0.5} count={6} spanX={size * 1.4} flip />

      {/* end caps — a couple of bays on the short walls */}
      <ShelfRow
        z={0}
        count={3}
        spanX={size * 0.7}
        offsetX={-halfX + 0.3}
        rotateY={Math.PI / 2}
      />

      {/* mezzanine slab above the restricted area */}
      <Mezzanine size={size} />

      {/* second dock pad + companion (parked) rover */}
      <DockPad x={-halfX * 0.55} z={halfZ * 0.55} />
      <ParkedRover x={-halfX * 0.55} z={halfZ * 0.55} />

      {/* charging station */}
      <ChargingStation x={halfX * 0.78} z={halfZ * 0.78} />

      {/* crate stacks near the pickup zone */}
      <CrateStack x={halfX * 0.35} z={-halfZ * 0.05} h={3} />
      <CrateStack x={halfX * 0.45} z={halfZ * 0.12} h={2} />
    </group>
  );
}

interface ShelfRowProps {
  z: number;
  count: number;
  spanX: number;
  offsetX?: number;
  flip?: boolean;
  rotateY?: number;
}

function ShelfRow({
  z,
  count,
  spanX,
  offsetX = 0,
  flip = false,
  rotateY = 0,
}: ShelfRowProps) {
  const step = spanX / count;
  const start = -spanX / 2 + step / 2;
  const bays: number[] = [];
  for (let i = 0; i < count; i++) bays.push(start + i * step);
  return (
    <group position={[offsetX, 0, z]} rotation={[0, rotateY, 0]}>
      {bays.map((x, i) => (
        <ShelfBay key={i} x={x} flip={flip} />
      ))}
    </group>
  );
}

function ShelfBay({ x, flip }: { x: number; flip: boolean }) {
  const sign = flip ? -1 : 1;
  return (
    <group position={[x, 0, 0]}>
      {/* uprights */}
      {[-0.45, 0.45].map((dx, i) => (
        <mesh key={i} position={[dx, 0.55, 0]} castShadow>
          <boxGeometry args={[0.05, 1.1, 0.45]} />
          <meshStandardMaterial color="#2a3142" roughness={0.85} />
        </mesh>
      ))}
      {/* three shelves */}
      {[0.15, 0.55, 0.95].map((y, i) => (
        <mesh key={i} position={[0, y, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.0, 0.04, 0.45]} />
          <meshStandardMaterial color="#3a4358" roughness={0.7} />
        </mesh>
      ))}
      {/* deterministic crate placeholders on the middle shelf */}
      <mesh position={[-0.25 * sign, 0.62, 0]} castShadow>
        <boxGeometry args={[0.35, 0.18, 0.32]} />
        <meshStandardMaterial color="#5b6b85" roughness={0.95} />
      </mesh>
      <mesh position={[0.28 * sign, 0.62, 0]} castShadow>
        <boxGeometry args={[0.28, 0.14, 0.32]} />
        <meshStandardMaterial color="#42506b" roughness={0.95} />
      </mesh>
      {/* one crate on the top shelf */}
      <mesh position={[0, 1.02, 0]} castShadow>
        <boxGeometry args={[0.5, 0.16, 0.32]} />
        <meshStandardMaterial color="#3b475e" roughness={0.95} />
      </mesh>
    </group>
  );
}

function Mezzanine({ size }: { size: number }) {
  const w = size * 0.55;
  const d = 0.55;
  return (
    <group position={[size * 0.18, 1.4, -size * 0.18]}>
      {/* deck */}
      <mesh receiveShadow castShadow>
        <boxGeometry args={[w, 0.06, d]} />
        <meshStandardMaterial color="#1b2030" roughness={0.9} />
      </mesh>
      {/* edge rail */}
      <mesh position={[0, 0.12, d / 2 - 0.02]}>
        <boxGeometry args={[w, 0.18, 0.03]} />
        <meshBasicMaterial color="#ef4444" transparent opacity={0.55} />
      </mesh>
      {/* support columns */}
      {[-w / 2 + 0.1, w / 2 - 0.1].map((dx, i) => (
        <mesh key={i} position={[dx, -0.7, 0]} castShadow>
          <boxGeometry args={[0.08, 1.4, 0.08]} />
          <meshStandardMaterial color="#2a3142" roughness={0.85} />
        </mesh>
      ))}
    </group>
  );
}

function DockPad({ x, z }: { x: number; z: number }) {
  return (
    <mesh position={[x, 0.03, z]}>
      <boxGeometry args={[1.4, 0.05, 0.9]} />
      <meshStandardMaterial color="#1b3d3a" roughness={0.9} />
    </mesh>
  );
}

function ParkedRover({ x, z }: { x: number; z: number }) {
  return (
    <group position={[x, 0.05, z]}>
      <mesh position={[0, 0.05, 0]} castShadow>
        <boxGeometry args={[0.32, 0.09, 0.5]} />
        <meshStandardMaterial color="#2c5d57" roughness={0.7} metalness={0.2} />
      </mesh>
      <mesh position={[0, 0.16, -0.06]}>
        <cylinderGeometry args={[0.05, 0.05, 0.1, 12]} />
        <meshStandardMaterial color="#1b3d3a" roughness={0.7} />
      </mesh>
      {/* idle status pip */}
      <mesh position={[0, 0.23, -0.06]}>
        <sphereGeometry args={[0.018, 8, 8]} />
        <meshBasicMaterial color="#3cb4a8" />
      </mesh>
    </group>
  );
}

function ChargingStation({ x, z }: { x: number; z: number }) {
  return (
    <group position={[x, 0, z]}>
      <mesh position={[0, 0.3, 0]} castShadow>
        <boxGeometry args={[0.4, 0.6, 0.3]} />
        <meshStandardMaterial color="#23304a" roughness={0.85} />
      </mesh>
      <mesh position={[0, 0.6, 0.16]}>
        <boxGeometry args={[0.22, 0.06, 0.02]} />
        <meshBasicMaterial color="#5fb0ff" transparent opacity={0.85} />
      </mesh>
      <mesh position={[0, 0.5, 0.16]}>
        <boxGeometry args={[0.22, 0.06, 0.02]} />
        <meshBasicMaterial color="#5fb0ff" transparent opacity={0.45} />
      </mesh>
    </group>
  );
}

function CrateStack({ x, z, h }: { x: number; z: number; h: number }) {
  const crates: number[] = [];
  for (let i = 0; i < h; i++) crates.push(i);
  return (
    <group position={[x, 0, z]}>
      {crates.map((i) => (
        <mesh
          key={i}
          position={[0, 0.13 + i * 0.22, 0]}
          rotation={[0, (i % 2 === 0 ? 0 : Math.PI / 14), 0]}
          castShadow
        >
          <boxGeometry args={[0.4, 0.22, 0.4]} />
          <meshStandardMaterial color={i % 2 === 0 ? "#475569" : "#3f4a5f"} roughness={0.95} />
        </mesh>
      ))}
    </group>
  );
}

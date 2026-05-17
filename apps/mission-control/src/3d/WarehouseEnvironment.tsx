"use client";

/**
 * Warehouse environment rendered as a mission-control AR overlay.
 *
 * The floor stays solid; the building structure (shelving racks,
 * mezzanine, ceiling trusses, dock roll-up door) renders as cyan
 * wireframe edges so the scene reads as an operator's AR scan of
 * the bay, not as a photoreal digital twin. The rover, route line,
 * and event beacons remain solid — they are the "real" agents in
 * the supervised scene; everything else is annotation.
 *
 * All geometry is deterministic — no randomness, no per-frame
 * mutation. The model is illustrative; it is NOT a digital twin of
 * any physical site.
 */

import { Grid } from "@react-three/drei";
import { useMemo } from "react";
import { BoxGeometry, EdgesGeometry } from "three";

interface WarehouseEnvironmentProps {
  size?: number;
  /**
   * When true, render warehouse context (shelving wireframes,
   * mezzanine, ceiling trusses, loading dock, aisle floor
   * markings, parked companion rover). Default false keeps the
   * lighter floor + grid only so existing tests / fixtures are
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
      {/* concrete floor slab */}
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
      {/* AR aisle stripes — the bay's drivable corridor, drawn flat */}
      <AisleStripes size={size} />

      {/* periphery wireframe shelving — two long-wall rows + an end cap */}
      <ShelfRow z={-halfZ + 0.6} count={5} spanX={size * 1.5} />
      <ShelfRow z={halfZ - 0.6} count={5} spanX={size * 1.5} />
      <ShelfRow
        x={-halfX + 0.6}
        z={0}
        count={3}
        spanX={size * 0.85}
        rotateY={Math.PI / 2}
      />

      {/* mezzanine wireframe + safety rail above the restricted zone */}
      <Mezzanine size={size} />

      {/* overhead truss structure */}
      <CeilingTrusses size={size} />

      {/* roll-up loading dock door behind the original dock pad */}
      <LoadingDockDoor
        x={-size * 0.65}
        z={-halfZ + 0.05}
        height={2.0}
        width={1.7}
      />

      {/* second dock pad with a parked companion rover */}
      <DockPad x={-halfX * 0.55} z={halfZ * 0.55} />
      <ParkedRover x={-halfX * 0.55} z={halfZ * 0.55} />

      {/* charging station near the second dock */}
      <ChargingStation x={halfX * 0.78} z={halfZ * 0.78} />

      {/* a couple of holographic pallet outlines near the pickup zone */}
      <PalletOutline x={halfX * 0.35} z={-halfZ * 0.05} />
      <PalletOutline x={halfX * 0.45} z={halfZ * 0.12} />
    </group>
  );
}

function AisleStripes({ size }: { size: number }) {
  const span = size * 1.6;
  const inset = size * 0.42;
  const dashes: number[] = [];
  for (let i = -span / 2; i <= span / 2; i += 0.6) dashes.push(i);
  return (
    <group position={[0, 0.011, 0]}>
      {[-inset, inset].map((z, row) => (
        <group key={row}>
          {dashes.map((x, i) => (
            <mesh key={i} position={[x, 0, z]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[0.35, 0.1]} />
              <meshBasicMaterial color="#facc15" transparent opacity={0.55} />
            </mesh>
          ))}
        </group>
      ))}
    </group>
  );
}

interface ShelfRowProps {
  x?: number;
  z?: number;
  count: number;
  spanX: number;
  rotateY?: number;
}

function ShelfRow({ x = 0, z = 0, count, spanX, rotateY = 0 }: ShelfRowProps) {
  const step = spanX / count;
  const start = -spanX / 2 + step / 2;
  const bays = useMemo(() => {
    const out: number[] = [];
    for (let i = 0; i < count; i++) out.push(start + i * step);
    return out;
  }, [count, start, step]);
  return (
    <group position={[x, 0, z]} rotation={[0, rotateY, 0]}>
      {bays.map((bx, i) => (
        <ShelfBay key={i} x={bx} />
      ))}
    </group>
  );
}

function ShelfBay({ x }: { x: number }) {
  // Industrial pallet-rack dimensions: 2.2m bay, 1.6m tall, 0.6m deep
  const w = 2.2;
  const h = 1.6;
  const d = 0.6;
  const edges = useMemo(() => new EdgesGeometry(new BoxGeometry(w, h, d)), []);
  return (
    <group position={[x, h / 2, 0]}>
      {/* outer wireframe shell */}
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#3cb4a8" transparent opacity={0.55} />
      </lineSegments>
      {/* three horizontal shelf decks rendered as thin glowing lines */}
      {[h * 0.18, h * 0.5, h * 0.82].map((y, i) => (
        <ShelfDeck key={i} y={y - h / 2} w={w} d={d} />
      ))}
      {/* subtle base shadow puck so it grounds visually */}
      <mesh position={[0, -h / 2 + 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[w * 0.95, d * 0.95]} />
        <meshBasicMaterial color="#0e1117" transparent opacity={0.85} />
      </mesh>
    </group>
  );
}

function ShelfDeck({ y, w, d }: { y: number; w: number; d: number }) {
  const edges = useMemo(
    () => new EdgesGeometry(new BoxGeometry(w * 0.98, 0.01, d * 0.95)),
    [w, d],
  );
  return (
    <group position={[0, y, 0]}>
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#5fe5d6" transparent opacity={0.45} />
      </lineSegments>
    </group>
  );
}

function Mezzanine({ size }: { size: number }) {
  const w = size * 0.55;
  const d = 0.55;
  const h = 1.6;
  const deck = useMemo(
    () => new EdgesGeometry(new BoxGeometry(w, 0.06, d)),
    [w, d],
  );
  return (
    <group position={[size * 0.18, h, -size * 0.18]}>
      <lineSegments geometry={deck}>
        <lineBasicMaterial color="#ef4444" transparent opacity={0.7} />
      </lineSegments>
      {/* edge rail */}
      <mesh position={[0, 0.12, d / 2 - 0.02]}>
        <boxGeometry args={[w, 0.04, 0.02]} />
        <meshBasicMaterial color="#ef4444" transparent opacity={0.55} />
      </mesh>
      {/* support columns rendered as thin glowing lines */}
      {[-w / 2 + 0.1, w / 2 - 0.1].map((dx, i) => (
        <Column key={i} x={dx} h={h} />
      ))}
    </group>
  );
}

function Column({ x, h }: { x: number; h: number }) {
  return (
    <mesh position={[x, -h / 2, 0]}>
      <boxGeometry args={[0.04, h, 0.04]} />
      <meshBasicMaterial color="#3cb4a8" transparent opacity={0.6} />
    </mesh>
  );
}

function CeilingTrusses({ size }: { size: number }) {
  const span = size * 1.7;
  const yTop = 2.8;
  const beams: number[] = [];
  for (let z = -span / 2 + 1.0; z <= span / 2 - 1.0; z += 1.6) beams.push(z);
  return (
    <group position={[0, yTop, 0]}>
      {/* perimeter cyan rim */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[size - 0.08, size, 64]} />
        <meshBasicMaterial color="#3cb4a8" transparent opacity={0.14} />
      </mesh>
      {/* horizontal trusses */}
      {beams.map((z, i) => (
        <Truss key={i} z={z} span={span} />
      ))}
    </group>
  );
}

function Truss({ z, span }: { z: number; span: number }) {
  return (
    <mesh position={[0, 0, z]}>
      <boxGeometry args={[span, 0.04, 0.06]} />
      <meshBasicMaterial color="#3cb4a8" transparent opacity={0.32} />
    </mesh>
  );
}

function LoadingDockDoor({
  x,
  z,
  height,
  width,
}: {
  x: number;
  z: number;
  height: number;
  width: number;
}) {
  // Wireframe roll-up door drawn as horizontal segments + a frame.
  const frameEdges = useMemo(
    () => new EdgesGeometry(new BoxGeometry(width, height, 0.06)),
    [width, height],
  );
  const slats: number[] = [];
  for (let y = 0.15; y < height - 0.05; y += 0.22) slats.push(y);
  return (
    <group position={[x, height / 2, z]}>
      <lineSegments geometry={frameEdges}>
        <lineBasicMaterial color="#5fe5d6" transparent opacity={0.55} />
      </lineSegments>
      {/* slats */}
      {slats.map((y, i) => (
        <mesh key={i} position={[0, y - height / 2, 0.04]}>
          <boxGeometry args={[width * 0.92, 0.04, 0.01]} />
          <meshBasicMaterial color="#3cb4a8" transparent opacity={0.35} />
        </mesh>
      ))}
      {/* hazard chevrons along the bottom */}
      <mesh position={[0, -height / 2 + 0.05, 0.05]}>
        <boxGeometry args={[width * 0.92, 0.08, 0.005]} />
        <meshBasicMaterial color="#facc15" transparent opacity={0.75} />
      </mesh>
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
      <mesh position={[0, 0.23, -0.06]}>
        <sphereGeometry args={[0.018, 8, 8]} />
        <meshBasicMaterial color="#3cb4a8" />
      </mesh>
    </group>
  );
}

function ChargingStation({ x, z }: { x: number; z: number }) {
  const edges = useMemo(
    () => new EdgesGeometry(new BoxGeometry(0.4, 0.6, 0.3)),
    [],
  );
  return (
    <group position={[x, 0.3, z]}>
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#5fe5d6" transparent opacity={0.55} />
      </lineSegments>
      <mesh position={[0, 0.16, 0.16]}>
        <boxGeometry args={[0.22, 0.06, 0.02]} />
        <meshBasicMaterial color="#5fb0ff" transparent opacity={0.85} />
      </mesh>
      <mesh position={[0, 0.06, 0.16]}>
        <boxGeometry args={[0.22, 0.06, 0.02]} />
        <meshBasicMaterial color="#5fb0ff" transparent opacity={0.45} />
      </mesh>
    </group>
  );
}

function PalletOutline({ x, z }: { x: number; z: number }) {
  // Euro pallet footprint: 0.8m × 1.2m. Rendered as a hovering
  // wireframe so it reads as an AR scan ghost.
  const edges = useMemo(
    () => new EdgesGeometry(new BoxGeometry(0.8, 0.14, 1.2)),
    [],
  );
  return (
    <group position={[x, 0.07, z]}>
      <lineSegments geometry={edges}>
        <lineBasicMaterial color="#facc15" transparent opacity={0.5} />
      </lineSegments>
    </group>
  );
}

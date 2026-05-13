"use client";

import { OrbitControls, Text } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";

import type { MissionRoute, SpatialEventMarker } from "@/adapters/spatial";

import { AnimatedRover } from "./AnimatedRover";
import { EventBeacon3D } from "./EventBeacon3D";
import { ReplayCameraRig } from "./ReplayCameraRig";
import { ReplayTrajectory3D } from "./ReplayTrajectory3D";
import { SafetyBoundaryVolume } from "./SafetyBoundaryVolume";
import { SupervisorIntervention3D } from "./SupervisorIntervention3D";
import { WarehouseEnvironment } from "./WarehouseEnvironment";
import { WaypointNode3D } from "./WaypointNode3D";
import type { PlaybackMode } from "./types";

interface ZoneOverlay {
  id: string;
  label: string;
  /** Centre, in route coordinates. */
  center: { x: number; y: number };
  /** Half-extent. */
  half: { x: number; y: number };
  tone: "dock" | "aisle" | "exclusion" | "pickup";
}

interface WarehouseDemoSceneProps {
  route: MissionRoute;
  markers: readonly SpatialEventMarker[];
  /** Smooth-interpolated current rover position. */
  roverPosition: { x: number; y: number };
  /** Current rover heading, deg. */
  roverHeadingDeg: number;
  /** Index into the event stream (drives marker emphasis). */
  activeIndex: number;
  /** Index into the waypoint list (drives trajectory highlight). */
  highlightWaypointIdx: number;
  /** Camera mode. */
  playbackMode?: PlaybackMode;
  /** Whether the rover should pulse. */
  moving: boolean;
  /** Zone overlays drawn under the trajectory. */
  zones: readonly ZoneOverlay[];
  height?: number;
}

const ZONE_TONE: Record<ZoneOverlay["tone"], { color: string; label: string }> = {
  dock: { color: "#3cb4a8", label: "Dock" },
  aisle: { color: "#5e7bff", label: "Aisle" },
  pickup: { color: "#facc15", label: "Pickup" },
  exclusion: { color: "#ef4444", label: "Restricted" },
};

/**
 * Polished, demo-grade 3D mission scene.
 *
 * Differs from ``MissionScene`` in three ways:
 *   1. Renders zone overlays so reviewers can see warehouse context
 *      (dock, aisle, pickup, restricted).
 *   2. Uses ``AnimatedRover`` so the robot glides between samples.
 *   3. Always renders waypoint and event markers, even at the
 *      starting frame, so the scene never looks empty.
 *
 * Geometry is illustrative — coordinates come from the canonical
 * fixture pose samples; zone overlays are layout hints, not surveyed
 * coordinates.
 */
export function WarehouseDemoScene({
  route,
  markers,
  roverPosition,
  roverHeadingDeg,
  activeIndex,
  highlightWaypointIdx,
  playbackMode = "overview",
  moving,
  zones,
  height = 520,
}: WarehouseDemoSceneProps) {
  const sceneCenter = useMemo<readonly [number, number, number]>(() => {
    const xs = route.waypoints.map((w) => w.position.x);
    const ys = route.waypoints.map((w) => w.position.y);
    if (!xs.length) return [0, 0, 0];
    const cx = xs.reduce((a, b) => a + b, 0) / xs.length;
    const cy = ys.reduce((a, b) => a + b, 0) / ys.length;
    return [cx, 0, -cy];
  }, [route.waypoints]);

  const sceneRadius = useMemo(() => {
    if (!route.waypoints.length) return 5;
    const xSpan = route.bounds.max.x - route.bounds.min.x;
    const ySpan = route.bounds.max.y - route.bounds.min.y;
    return Math.max(3, Math.max(xSpan, ySpan));
  }, [route.bounds, route.waypoints.length]);

  const focus = useMemo<readonly [number, number, number]>(
    () => [roverPosition.x, 0.1, -roverPosition.y],
    [roverPosition],
  );

  return (
    <div
      role="region"
      aria-label="Warehouse mission replay"
      data-testid="warehouse-demo-scene"
      className="relative overflow-hidden rounded-lg border border-[color:var(--mc-border)]"
      style={{ height, background: "linear-gradient(180deg,#0a0e16 0%,#10141c 100%)" }}
    >
      <Canvas
        shadows
        dpr={[1, 1.6]}
        camera={{ fov: 38, near: 0.1, far: 200, position: [6, 6, 6] }}
        gl={{ antialias: true, preserveDrawingBuffer: false }}
      >
        <ReplayCameraRig
          mode={playbackMode}
          focus={focus}
          sceneCenter={sceneCenter}
          sceneRadius={sceneRadius}
        />
        <ambientLight intensity={0.55} />
        <directionalLight
          intensity={0.85}
          position={[6, 10, 6]}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <hemisphereLight intensity={0.22} color="#3cb4a8" groundColor="#0a0e16" />
        <fog attach="fog" args={["#0a0e16", sceneRadius * 1.6, sceneRadius * 4]} />

        <WarehouseEnvironment size={Math.max(5, sceneRadius * 1.3)} />
        <SafetyBoundaryVolume size={Math.max(3, sceneRadius * 1.05)} />

        {zones.map((zone) => (
          <ZonePad key={zone.id} zone={zone} />
        ))}

        <ReplayTrajectory3D route={route} highlightUpTo={highlightWaypointIdx} />

        <group>
          {route.waypoints.map((wp, idx) => (
            <WaypointNode3D
              key={wp.waypoint_id}
              waypoint={wp}
              active={idx === highlightWaypointIdx}
            />
          ))}
        </group>

        <group>
          {markers.map((marker, idx) => (
            <group key={marker.event_id}>
              <EventBeacon3D marker={marker} active={idx === activeIndex} />
              <SupervisorIntervention3D marker={marker} active={idx === activeIndex} />
            </group>
          ))}
        </group>

        <AnimatedRover
          targetPosition={roverPosition}
          targetHeadingDeg={roverHeadingDeg}
          moving={moving}
          label={moving ? "rover · simulating" : "rover · paused"}
        />

        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          enablePan={false}
          minDistance={2}
          maxDistance={28}
          target={focus as [number, number, number]}
          makeDefault
        />
      </Canvas>

      <div className="pointer-events-none absolute inset-x-0 top-0 flex justify-between px-3 pt-2 text-[11px]">
        <span className="rounded bg-[color:var(--mc-surface-overlay)] px-2 py-0.5 font-mono text-[color:var(--mc-text)] shadow-panel backdrop-blur-sm">
          warehouse · simulation only
        </span>
        <span
          data-testid="demo-scene-mode"
          className="rounded bg-[color:var(--mc-surface-overlay)] px-2 py-0.5 font-mono uppercase tracking-wide text-[color:var(--mc-text)] shadow-panel backdrop-blur-sm"
        >
          {playbackMode.replace(/_/g, " ")}
        </span>
      </div>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-wrap justify-between gap-2 px-3 pb-2 text-[10px]">
        <span className="rounded bg-[color:var(--mc-surface-overlay)] px-2 py-0.5 font-mono text-[color:var(--mc-text-muted)] shadow-panel backdrop-blur-sm">
          coordinates · {route.derivation_source}
        </span>
        <span className="rounded bg-[color:var(--mc-surface-overlay)] px-2 py-0.5 font-mono text-[color:var(--mc-text-muted)] shadow-panel backdrop-blur-sm">
          drag to orbit · scroll to zoom
        </span>
      </div>
    </div>
  );
}

function ZonePad({ zone }: { zone: ZoneOverlay }) {
  const tone = ZONE_TONE[zone.tone];
  const w = Math.max(0.4, zone.half.x * 2);
  const d = Math.max(0.4, zone.half.y * 2);
  return (
    <group position={[zone.center.x, 0.005, -zone.center.y]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[w, d]} />
        <meshStandardMaterial
          color={tone.color}
          transparent
          opacity={zone.tone === "exclusion" ? 0.22 : 0.14}
          roughness={1}
        />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.001, 0]}>
        <ringGeometry args={[Math.min(w, d) / 2.4, Math.min(w, d) / 2.2, 48]} />
        <meshBasicMaterial color={tone.color} transparent opacity={0.55} />
      </mesh>
      <Text
        position={[0, 0.02, -d / 2 - 0.12]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.18}
        color={tone.color}
        anchorX="center"
        anchorY="middle"
      >
        {zone.label}
      </Text>
    </group>
  );
}

"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";

import {
  describeDerivationSource,
  projectArtifactEvent,
} from "@/adapters/spatial";
import type { MissionRoute, SpatialEventMarker } from "@/adapters/spatial";

import { EventBeacon3D } from "./EventBeacon3D";
import { ReplayCameraRig } from "./ReplayCameraRig";
import { ReplayTrajectory3D } from "./ReplayTrajectory3D";
import { RobotGhostModel } from "./RobotGhostModel";
import { SafetyBoundaryVolume } from "./SafetyBoundaryVolume";
import { SupervisorIntervention3D } from "./SupervisorIntervention3D";
import { WarehouseEnvironment } from "./WarehouseEnvironment";
import { WaypointNode3D } from "./WaypointNode3D";
import { pointTo3D, type SceneInputs } from "./types";

interface MissionSceneProps extends SceneInputs {
  /** Optional max height for the canvas. Defaults to 480px. */
  height?: number;
}

/**
 * Top-level immersive mission scene.
 *
 * The scene is a deterministic, sequence-driven view: the active
 * waypoint and event markers move in lock-step with the scrubber's
 * ``activeIndex``. There is NO render loop side-effect — Drei's
 * OrbitControls remains the only interactive surface, and the
 * camera rig snaps deterministically when ``playbackMode`` changes.
 */
export function MissionScene({
  route,
  events,
  artifact,
  activeIndex,
  playbackMode,
  derivationSource,
  height = 480,
}: MissionSceneProps) {
  const markers: readonly SpatialEventMarker[] = useMemo(
    () => events.map((e) => projectArtifactEvent(e, route)),
    [events, route],
  );

  const activeWaypoint = useMemo(() => {
    if (!artifact) {
      // Fall back to the most-recent payload-tagged waypoint.
      for (let i = activeIndex; i >= 0; i -= 1) {
        const wid = (events[i]?.payload as Record<string, unknown> | undefined)
          ?.waypoint_id;
        if (typeof wid === "string" && wid) {
          return route.waypoints.find((w) => w.waypoint_id === wid) ?? null;
        }
      }
      return route.waypoints[0] ?? null;
    }
    // Artifact-backed: walk the alignment list.
    for (let i = activeIndex; i >= 0; i -= 1) {
      const ev = events[i];
      if (!ev) continue;
      const aligned = artifact.event_alignments.find(
        (a) =>
          a.event_id === ev.event_id ||
          a.deterministic_hash === ev.deterministic_hash,
      );
      if (aligned && aligned.matched_sample_id) {
        const sample = route.waypoints.find(
          (w) => w.waypoint_id === aligned.matched_sample_id,
        );
        if (sample) return sample;
      }
    }
    return route.waypoints[0] ?? null;
  }, [activeIndex, artifact, events, route.waypoints]);

  const sceneCenter = useMemo<readonly [number, number, number]>(() => {
    const xs = route.waypoints.map((w) => w.position.x);
    const ys = route.waypoints.map((w) => w.position.y);
    if (!xs.length) return [0, 0, 0];
    const cx = xs.reduce((a, b) => a + b, 0) / xs.length;
    const cy = ys.reduce((a, b) => a + b, 0) / ys.length;
    return [cx, 0, -cy];
  }, [route.waypoints]);

  const sceneRadius = useMemo(() => {
    if (!route.waypoints.length) return 4;
    const xSpan = route.bounds.max.x - route.bounds.min.x;
    const ySpan = route.bounds.max.y - route.bounds.min.y;
    return Math.max(2, Math.max(xSpan, ySpan));
  }, [route.bounds, route.waypoints.length]);

  const focus = useMemo<readonly [number, number, number]>(
    () => (activeWaypoint ? pointTo3D(activeWaypoint.position) : sceneCenter),
    [activeWaypoint, sceneCenter],
  );

  const heading = activeWaypoint?.heading_deg ?? 0;

  return (
    <div
      role="region"
      aria-label="Immersive mission scene"
      data-testid="mission-scene"
      className="relative overflow-hidden rounded-md border border-base-200 bg-base-100"
      style={{ height }}
    >
      <Canvas
        shadows
        dpr={[1, 1.5]}
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
          intensity={0.7}
          position={[5, 8, 5]}
          castShadow
          shadow-mapSize-width={1024}
          shadow-mapSize-height={1024}
        />
        <hemisphereLight intensity={0.18} color="#3cb4a8" groundColor="#0e1117" />

        <WarehouseEnvironment size={Math.max(4, sceneRadius * 1.5)} />
        <SafetyBoundaryVolume size={Math.max(3, sceneRadius * 1.1)} />
        <SceneSegments route={route} highlightUpTo={activeIndex} />
        <SceneWaypoints route={route} activeId={activeWaypoint?.waypoint_id ?? null} />
        <SceneMarkers markers={markers} activeIndex={activeIndex} />

        {activeWaypoint ? (
          <RobotGhostModel
            position={activeWaypoint.position}
            headingDeg={heading}
            active={playbackMode !== "trajectory_analysis"}
          />
        ) : null}

        <OrbitControls
          enableDamping
          dampingFactor={0.08}
          enablePan={false}
          minDistance={2}
          maxDistance={20}
          target={focus as [number, number, number]}
          makeDefault
        />
      </Canvas>

      <SceneOverlay
        derivationSource={derivationSource}
        playbackMode={playbackMode}
      />
    </div>
  );
}

function SceneSegments({
  route,
  highlightUpTo,
}: {
  route: MissionRoute;
  highlightUpTo: number;
}) {
  return <ReplayTrajectory3D route={route} highlightUpTo={highlightUpTo} />;
}

function SceneWaypoints({
  route,
  activeId,
}: {
  route: MissionRoute;
  activeId: string | null;
}) {
  return (
    <group>
      {route.waypoints.map((wp) => (
        <WaypointNode3D
          key={wp.waypoint_id}
          waypoint={wp}
          active={wp.waypoint_id === activeId}
        />
      ))}
    </group>
  );
}

function SceneMarkers({
  markers,
  activeIndex,
}: {
  markers: readonly SpatialEventMarker[];
  activeIndex: number;
}) {
  return (
    <group>
      {markers.map((m, idx) => (
        <group key={m.event_id}>
          <EventBeacon3D marker={m} active={idx === activeIndex} />
          <SupervisorIntervention3D marker={m} active={idx === activeIndex} />
        </group>
      ))}
    </group>
  );
}

function SceneOverlay({
  derivationSource,
  playbackMode,
}: {
  derivationSource: SceneInputs["derivationSource"];
  playbackMode: SceneInputs["playbackMode"];
}) {
  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-0 flex justify-between gap-3 px-3 pb-2 text-[11px] text-base-700">
      <span
        data-testid="scene-derivation"
        className="rounded bg-base-50/80 px-2 py-0.5 font-mono text-base-800 shadow-panel"
      >
        {describeDerivationSource(derivationSource)}
      </span>
      <span
        data-testid="scene-mode"
        className="rounded bg-base-50/80 px-2 py-0.5 font-mono uppercase tracking-wide text-base-700 shadow-panel"
      >
        {playbackMode.replace(/_/g, " ")}
      </span>
    </div>
  );
}

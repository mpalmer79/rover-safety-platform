"use client";

import { useState } from "react";

import {
  buildMissionRoute,
  buildMissionRouteFromArtifact,
  selectMissionRoute,
} from "@/adapters/spatial";
import type { MissionPlan, RehearsalEvent, SpatialReplayArtifact } from "@/adapters/types";
import { Panel } from "@/components/Panel";
import { ReplayScrubber } from "@/components/ReplayScrubber";
import { SpatialReplayBadge } from "@/components/SpatialReplayBadge";

import { MissionScene } from "./MissionScene";
import type { PlaybackMode } from "./types";

interface MissionPlayback3DProps {
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
  spatialReplay: SpatialReplayArtifact | null;
}

const MODES: ReadonlyArray<{ value: PlaybackMode; label: string }> = [
  { value: "overview", label: "Overview" },
  { value: "operator_review", label: "Operator review" },
  { value: "safety_intervention", label: "Safety intervention" },
  { value: "trajectory_analysis", label: "Trajectory analysis" },
];

/**
 * Composite immersive playback panel.
 *
 * Combines a mode selector, the deterministic mission scene, and
 * the existing sequence-based scrubber. Camera transitions are
 * deterministic (the rig snaps), and the scrubber drives the
 * scene's ``activeIndex`` directly.
 */
export function MissionPlayback3D({
  plan,
  events,
  spatialReplay,
}: MissionPlayback3DProps) {
  const route = selectMissionRoute(plan, spatialReplay);
  const [activeIndex, setActiveIndex] = useState(
    Math.max(0, events.length - 1),
  );
  const [playbackMode, setPlaybackMode] = useState<PlaybackMode>("overview");

  return (
    <Panel
      eyebrow="Immersive playback"
      title="3D mission scene"
      trailing={
        <div className="flex items-center gap-2">
          <SpatialReplayBadge source={route.derivation_source} />
        </div>
      }
    >
      <div className="space-y-3">
        <ModeSelector value={playbackMode} onChange={setPlaybackMode} />
        <MissionScene
          route={route}
          events={events}
          artifact={spatialReplay}
          activeIndex={activeIndex}
          playbackMode={playbackMode}
          derivationSource={route.derivation_source}
        />
        <ReplayScrubber events={events} onIndexChange={setActiveIndex} />
        <p className="text-[11px] text-base-500">
          Scene geometry is deterministic; the camera rig snaps when
          a mode changes. Coordinates come from{" "}
          <span data-testid="playback-derivation" className="font-mono text-base-700">
            {route.derivation_source}
          </span>{" "}
          — the scene never invents pose data.
        </p>
      </div>
    </Panel>
  );
}

function ModeSelector({
  value,
  onChange,
}: {
  value: PlaybackMode;
  onChange: (next: PlaybackMode) => void;
}) {
  return (
    <div
      role="tablist"
      aria-label="Playback mode"
      className="flex flex-wrap gap-1.5 text-[11px]"
      data-testid="playback-mode-selector"
    >
      {MODES.map((mode) => {
        const active = mode.value === value;
        return (
          <button
            key={mode.value}
            type="button"
            role="tab"
            aria-selected={active}
            data-testid={`playback-mode-${mode.value}`}
            onClick={() => onChange(mode.value)}
            className={
              "rounded border px-2 py-1 font-mono uppercase tracking-wide transition-colors " +
              (active
                ? "border-accent bg-accent-soft/40 text-accent"
                : "border-base-300 bg-base-100 text-base-600 hover:border-base-500")
            }
          >
            {mode.label}
          </button>
        );
      })}
    </div>
  );
}

// Re-export the bounded-inputs / artifact-derived helpers in case
// callers want to pre-resolve the route. Avoids a deep import.
export { buildMissionRoute, buildMissionRouteFromArtifact };

"use client";

import { useMemo, useState } from "react";

import {
  buildMissionRoute,
  buildMissionRouteFromArtifact,
  projectArtifactEvent,
  projectEvents,
} from "@/adapters/spatial";
import type {
  MissionPlan,
  RehearsalEvent,
  SpatialReplayArtifact,
} from "@/adapters/types";
import { MissionMap } from "./MissionMap";
import { Panel } from "./Panel";
import { ReplayScrubber } from "./ReplayScrubber";
import { RouteProgressIndicator } from "./RouteProgressIndicator";
import { SpatialReplayBadge } from "./SpatialReplayBadge";

interface MissionPlaybackPanelProps {
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
  spatialReplay?: SpatialReplayArtifact | null;
}

/**
 * Tactical playback panel. Combines the deterministic mission map
 * with the event scrubber so an operator can advance through the
 * ordered event stream and watch the active waypoint highlight.
 *
 * Phase 17C: when a spatial-replay artifact is provided AND it
 * declares a ``bag_backed`` or ``fixture`` derivation source AND
 * carries pose samples, the panel renders the artifact's
 * trajectory. Otherwise the panel falls back to the bounded-inputs
 * derivation from Phase 17B. The map caption always names the
 * derivation source verbatim.
 *
 * Honesty notes:
 *   * the derivation source is the single source of truth for the
 *     "bag-backed" vs "fixture" vs "bounded inputs" badge;
 *   * the scrubber's position is sequence-based, not wall-clock;
 *   * advancing the scrubber never publishes anything — it merely
 *     re-highlights an already-rendered waypoint.
 */
export function MissionPlaybackPanel({
  plan,
  events,
  spatialReplay,
}: MissionPlaybackPanelProps) {
  const route = useMemo(() => {
    if (
      spatialReplay &&
      (spatialReplay.derivation_source === "bag_backed" ||
        spatialReplay.derivation_source === "fixture") &&
      spatialReplay.samples.length > 0
    ) {
      return buildMissionRouteFromArtifact(spatialReplay);
    }
    return buildMissionRoute(plan);
  }, [plan, spatialReplay]);

  const markers = useMemo(
    () => events.map((e) => projectArtifactEvent(e, route)),
    [events, route],
  );

  // Used by the bounded-inputs adapter when no artifact is present.
  // Avoid ever rendering markers that fail the artifact alignment.
  void projectEvents; // type retained for adapter symmetry

  const [activeIndex, setActiveIndex] = useState(
    Math.max(0, events.length - 1),
  );

  const activeWaypointId = useMemo(() => {
    for (let i = activeIndex; i >= 0; i -= 1) {
      const ev = events[i];
      // Prefer the artifact alignment when available.
      if (route.artifact) {
        const aligned = route.artifact.event_alignments.find(
          (a) =>
            a.event_id === ev?.event_id ||
            a.deterministic_hash === ev?.deterministic_hash,
        );
        if (aligned && aligned.matched_sample_id) {
          return aligned.matched_sample_id;
        }
      }
      const wid = (ev?.payload as Record<string, unknown> | undefined)
        ?.waypoint_id;
      if (typeof wid === "string" && wid) return wid;
    }
    return null;
  }, [events, activeIndex, route]);

  return (
    <Panel
      eyebrow="Mission playback"
      title="Tactical map + scrubber"
      trailing={
        <div className="flex items-center gap-2">
          <SpatialReplayBadge source={route.derivation_source} />
          <span className="text-[11px] text-base-500">
            {route.has_motion
              ? `${route.segments.length} segments`
              : "topology only"}
          </span>
        </div>
      }
    >
      <div className="space-y-3">
        <MissionMap
          route={route}
          events={markers.slice(0, activeIndex + 1)}
          activeWaypointId={activeWaypointId}
        />
        <RouteProgressIndicator
          route={route}
          activeWaypointId={activeWaypointId}
        />
        <ReplayScrubber events={events} onIndexChange={setActiveIndex} />
        {route.artifact && route.artifact.missing_topics.length > 0 ? (
          <p className="text-[11px] text-status-pending">
            Missing pose topics: {route.artifact.missing_topics.join(", ")} —
            trajectory is partial.
          </p>
        ) : null}
      </div>
    </Panel>
  );
}

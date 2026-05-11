"use client";

import { useMemo, useState } from "react";

import { buildMissionRoute, projectEvents } from "@/adapters/spatial";
import type { MissionPlan, RehearsalEvent } from "@/adapters/types";
import { MissionMap } from "./MissionMap";
import { Panel } from "./Panel";
import { ReplayScrubber } from "./ReplayScrubber";
import { RouteProgressIndicator } from "./RouteProgressIndicator";

interface MissionPlaybackPanelProps {
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
}

/**
 * Tactical playback panel. Combines the deterministic mission map
 * with the event scrubber so an operator can advance through the
 * ordered event stream and watch the active waypoint highlight.
 *
 * Honesty notes:
 *   * the map labels its derivation source ("derived from bounded
 *     distance/angle inputs", "topology only", or "unavailable");
 *   * the scrubber's position is sequence-based, not wall-clock;
 *   * advancing the scrubber never publishes anything — it merely
 *     re-highlights an already-rendered waypoint.
 */
export function MissionPlaybackPanel({
  plan,
  events,
}: MissionPlaybackPanelProps) {
  const route = useMemo(() => buildMissionRoute(plan), [plan]);
  const markers = useMemo(() => projectEvents(events, route), [events, route]);
  const [activeIndex, setActiveIndex] = useState(
    Math.max(0, events.length - 1),
  );

  // Resolve the active waypoint id: the most recent event whose
  // payload references a known waypoint up to the active index.
  const activeWaypointId = useMemo(() => {
    for (let i = activeIndex; i >= 0; i -= 1) {
      const ev = events[i];
      const wid = (ev?.payload as Record<string, unknown> | undefined)
        ?.waypoint_id;
      if (typeof wid === "string" && wid) return wid;
    }
    return null;
  }, [events, activeIndex]);

  return (
    <Panel
      eyebrow="Mission playback"
      title="Tactical map + scrubber"
      trailing={
        <span className="text-[11px] text-base-500">
          {route.has_motion
            ? `${route.segments.length} segments`
            : "topology only"}
        </span>
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
      </div>
    </Panel>
  );
}

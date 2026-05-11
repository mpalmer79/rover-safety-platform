/**
 * Deterministic spatial layout derived from rehearsal plan inputs.
 *
 * The mission rehearsal artefacts produced by Phase 16 record bounded
 * motion *requests* (distance, angle, speed) but never x/y coordinates.
 * A coordinate would imply the platform knew where the rover actually
 * went; it never does, because nothing in Phases 0..16 ran on real
 * hardware.
 *
 * The mission map below honours that boundary. It synthesises a
 * deterministic 2D path from the same bounded inputs:
 *
 *   * each waypoint advances forward by ``bounded_distance_m`` along
 *     a heading that starts at 0°;
 *   * rotation waypoints rotate the heading by ``bounded_angle_deg``;
 *   * stop / wait / dock waypoints add no displacement.
 *
 * Two simultaneous identical plans produce byte-identical paths. The
 * UI labels every map as a "derived layout (no real coordinates)" so
 * an operator cannot mistake the visualisation for real telemetry.
 */

import type {
  MissionPlan,
  MissionWaypoint,
  RehearsalEvent,
} from "./types";

export interface SpatialPoint {
  x: number;
  y: number;
}

export interface SpatialWaypoint {
  waypoint_id: string;
  label: string;
  stage_kind: string;
  position: SpatialPoint;
  heading_deg: number;
  // The deterministic derivation source. Always populated; never
  // omitted, so an audit reading the UI's output can confirm the
  // map's provenance.
  source: "bounded_distance_angle" | "topology_only";
  bounded_distance_m: number;
  bounded_angle_deg: number;
  bounded_speed_mps: number;
}

export interface MissionRoute {
  waypoints: readonly SpatialWaypoint[];
  segments: ReadonlyArray<{
    from: SpatialPoint;
    to: SpatialPoint;
    waypoint_id: string;
    stage_kind: string;
  }>;
  bounds: {
    min: SpatialPoint;
    max: SpatialPoint;
  };
  has_motion: boolean;
  derivation_source: "bounded_inputs" | "topology_only" | "unavailable";
  note: string;
}

export interface SpatialEventMarker {
  event_id: string;
  position: SpatialPoint | null;
  severity: RehearsalEvent["severity"];
  event_subtype: string;
  description: string;
  deterministic_hash: string;
}

const MOTION_STAGES = new Set(["move", "patrol", "inspect"]);
const ROTATION_HINTS = new Set(["rotate", "turn", "spin"]);

function normaliseHeading(headingDeg: number): number {
  let h = headingDeg % 360;
  if (h < 0) h += 360;
  return h;
}

function isMotionStage(stage: string): boolean {
  return MOTION_STAGES.has(stage);
}

function isRotationStage(stage: string): boolean {
  return ROTATION_HINTS.has(stage);
}

function expandBounds(
  bounds: { min: SpatialPoint; max: SpatialPoint },
  point: SpatialPoint,
): void {
  bounds.min.x = Math.min(bounds.min.x, point.x);
  bounds.min.y = Math.min(bounds.min.y, point.y);
  bounds.max.x = Math.max(bounds.max.x, point.x);
  bounds.max.y = Math.max(bounds.max.y, point.y);
}

/**
 * Build a deterministic spatial route from a mission plan.
 *
 * Returns ``derivation_source = "unavailable"`` when there are no
 * waypoints at all. Returns ``"topology_only"`` when every waypoint
 * has zero bounded distance and zero bounded angle (the UI then
 * arranges the waypoints in a deterministic line).
 */
export function buildMissionRoute(
  plan: MissionPlan | null,
): MissionRoute {
  const note =
    "Derived deterministically from bounded distance/angle inputs. " +
    "No real-world coordinates exist; the map is a tactical layout, " +
    "not telemetry.";
  if (!plan || plan.waypoints.length === 0) {
    return {
      waypoints: [],
      segments: [],
      bounds: { min: { x: 0, y: 0 }, max: { x: 0, y: 0 } },
      has_motion: false,
      derivation_source: "unavailable",
      note: "No mission plan attached; spatial data unavailable.",
    };
  }

  const start: SpatialPoint = { x: 0, y: 0 };
  let cursor: SpatialPoint = { ...start };
  let heading = 0;

  const spatialWaypoints: SpatialWaypoint[] = [];
  const segments: MissionRoute["segments"] = [] as MissionRoute["segments"];
  const bounds = {
    min: { x: 0, y: 0 },
    max: { x: 0, y: 0 },
  };

  let hasMotion = false;
  let hasDistance = false;

  for (let i = 0; i < plan.waypoints.length; i += 1) {
    const w: MissionWaypoint = plan.waypoints[i];
    const distance = Math.max(0, w.bounded_distance_m);
    const angle = w.bounded_angle_deg;
    const previous: SpatialPoint = { ...cursor };

    if (isRotationStage(w.stage_kind) || w.stage_kind === "rotate") {
      // Rotation-only waypoint: change heading, no displacement.
      heading = normaliseHeading(heading + angle);
    } else if (isMotionStage(w.stage_kind) && distance > 0) {
      // Forward motion along current heading; record displacement.
      const rad = (heading * Math.PI) / 180;
      cursor = {
        x: previous.x + distance * Math.cos(rad),
        y: previous.y + distance * Math.sin(rad),
      };
      hasMotion = true;
      hasDistance = true;
      expandBounds(bounds, cursor);
      (segments as Array<MissionRoute["segments"][number]>).push({
        from: previous,
        to: { ...cursor },
        waypoint_id: w.waypoint_id,
        stage_kind: w.stage_kind,
      });
    } else if (w.stage_kind === "dock" && i > 0) {
      // Dock waypoint: nudge back to the start so the route closes
      // visually. This is documented in MISSION_SPATIAL_VISUALIZATION.md.
      cursor = { x: 0, y: 0 };
      (segments as Array<MissionRoute["segments"][number]>).push({
        from: previous,
        to: { ...cursor },
        waypoint_id: w.waypoint_id,
        stage_kind: w.stage_kind,
      });
      expandBounds(bounds, cursor);
    }

    spatialWaypoints.push({
      waypoint_id: w.waypoint_id,
      label: w.label,
      stage_kind: w.stage_kind,
      position: { ...cursor },
      heading_deg: heading,
      source: hasDistance
        ? "bounded_distance_angle"
        : "topology_only",
      bounded_distance_m: w.bounded_distance_m,
      bounded_angle_deg: w.bounded_angle_deg,
      bounded_speed_mps: w.bounded_speed_mps,
    });
  }

  if (!hasMotion) {
    // Topology-only fallback: arrange waypoints along x-axis at a
    // deterministic 1m spacing so the topology is visible.
    let xCursor = 0;
    const fallbackWaypoints = spatialWaypoints.map((sw) => {
      const point = { x: xCursor, y: 0 };
      xCursor += 1;
      return { ...sw, position: point, source: "topology_only" as const };
    });
    const fallbackSegments: Array<MissionRoute["segments"][number]> = [];
    for (let i = 1; i < fallbackWaypoints.length; i += 1) {
      fallbackSegments.push({
        from: fallbackWaypoints[i - 1].position,
        to: fallbackWaypoints[i].position,
        waypoint_id: fallbackWaypoints[i].waypoint_id,
        stage_kind: fallbackWaypoints[i].stage_kind,
      });
    }
    const lastX = Math.max(0, fallbackWaypoints.length - 1);
    return {
      waypoints: fallbackWaypoints,
      segments: fallbackSegments,
      bounds: {
        min: { x: -0.5, y: -0.5 },
        max: { x: lastX + 0.5, y: 0.5 },
      },
      has_motion: false,
      derivation_source: "topology_only",
      note,
    };
  }

  return {
    waypoints: spatialWaypoints,
    segments,
    bounds: {
      min: { x: bounds.min.x - 0.5, y: bounds.min.y - 0.5 },
      max: { x: bounds.max.x + 0.5, y: bounds.max.y + 0.5 },
    },
    has_motion: true,
    derivation_source: "bounded_inputs",
    note,
  };
}

/**
 * Project a rehearsal event onto a position on the derived route.
 *
 * Events that name a waypoint in their payload (motion +
 * safety-check events) map to that waypoint's spatial position.
 * Events with no spatial anchor return ``position = null``; the UI
 * draws them in the timeline only, not on the map.
 */
export function projectEvent(
  event: RehearsalEvent,
  route: MissionRoute,
): SpatialEventMarker {
  const payload = event.payload as Record<string, unknown>;
  const waypointId = typeof payload?.waypoint_id === "string"
    ? payload.waypoint_id
    : null;
  let position: SpatialPoint | null = null;
  if (waypointId) {
    const sw = route.waypoints.find((w) => w.waypoint_id === waypointId);
    if (sw) {
      position = sw.position;
    }
  }
  return {
    event_id: event.event_id,
    position,
    severity: event.severity,
    event_subtype: event.event_subtype,
    description: event.description,
    deterministic_hash: event.deterministic_hash,
  };
}

export function projectEvents(
  events: readonly RehearsalEvent[],
  route: MissionRoute,
): readonly SpatialEventMarker[] {
  return events.map((e) => projectEvent(e, route));
}

/**
 * Compute a fitted SVG viewBox for a route. Used by ``MissionMap`` so
 * every map renders at the same on-screen aspect regardless of how
 * far the simulated rover travelled.
 */
export function fitViewBox(
  route: MissionRoute,
  width = 480,
  height = 280,
): { viewBox: string; transform: (point: SpatialPoint) => SpatialPoint } {
  const span = {
    x: Math.max(0.01, route.bounds.max.x - route.bounds.min.x),
    y: Math.max(0.01, route.bounds.max.y - route.bounds.min.y),
  };
  const scale = Math.min(width / span.x, height / span.y);
  const offsetX = -route.bounds.min.x * scale + (width - span.x * scale) / 2;
  const offsetY = -route.bounds.min.y * scale + (height - span.y * scale) / 2;
  const transform = (point: SpatialPoint): SpatialPoint => ({
    x: point.x * scale + offsetX,
    y: height - (point.y * scale + offsetY),
  });
  return { viewBox: `0 0 ${width} ${height}`, transform };
}

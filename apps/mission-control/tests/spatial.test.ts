import { describe, it, expect } from "vitest";

import {
  buildMissionRoute,
  fitViewBox,
  projectEvent,
  projectEvents,
} from "../src/adapters/spatial";
import { loadRehearsalAudit } from "../src/adapters/loader";
import type { MissionPlan, RehearsalEvent } from "../src/adapters/types";

function makePlan(
  waypoints: Array<Partial<MissionPlan["waypoints"][number]>>,
): MissionPlan {
  return {
    mission_id: "m",
    request_id: "r",
    proposal_source: "",
    waypoints: waypoints.map((w, idx) => ({
      waypoint_id: `wp${idx}`,
      label: `Waypoint ${idx}`,
      stage_kind: "move",
      bounded_distance_m: 0,
      bounded_angle_deg: 0,
      bounded_speed_mps: 0,
      ...w,
    })),
    safety_constraints: [],
    requested_topics: ["/cmd_vel_requested"],
    forbidden_topics: ["/cmd_vel"],
    odd_profile_id: "default",
    deterministic_hash: "test-hash",
    risk_band: "guarded",
    notes: [],
  };
}

describe("buildMissionRoute", () => {
  it("returns unavailable when there is no plan", () => {
    const route = buildMissionRoute(null);
    expect(route.derivation_source).toBe("unavailable");
    expect(route.waypoints).toEqual([]);
    expect(route.segments).toEqual([]);
  });

  it("returns unavailable when the plan has no waypoints", () => {
    const route = buildMissionRoute(makePlan([]));
    expect(route.derivation_source).toBe("unavailable");
  });

  it("forward motion advances along heading deterministically", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 2.0 },
      { waypoint_id: "wp2", stage_kind: "move", bounded_distance_m: 1.0 },
      { waypoint_id: "wp3", stage_kind: "dock" },
    ]);
    const route = buildMissionRoute(plan);
    expect(route.derivation_source).toBe("bounded_inputs");
    expect(route.has_motion).toBe(true);
    expect(route.waypoints[0].position.x).toBeCloseTo(2.0, 4);
    expect(route.waypoints[1].position.x).toBeCloseTo(3.0, 4);
    expect(route.waypoints[2].position.x).toBeCloseTo(0.0, 4);
  });

  it("rotation waypoints rotate the heading without displacement", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "rotate", bounded_angle_deg: 90 },
      { waypoint_id: "wp2", stage_kind: "move", bounded_distance_m: 1.0 },
      { waypoint_id: "wp3", stage_kind: "stop" },
    ]);
    const route = buildMissionRoute(plan);
    // After rotating 90° at origin then moving 1m, we should be near (0, 1).
    const wp2 = route.waypoints.find((w) => w.waypoint_id === "wp2")!;
    expect(wp2.position.x).toBeCloseTo(0, 3);
    expect(wp2.position.y).toBeCloseTo(1, 3);
  });

  it("topology-only fallback when no distance is bounded", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "wait" },
      { waypoint_id: "wp2", stage_kind: "wait" },
    ]);
    const route = buildMissionRoute(plan);
    expect(route.derivation_source).toBe("topology_only");
    expect(route.waypoints.length).toBe(2);
  });

  it("stops and docks add no displacement", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 1.0 },
      { waypoint_id: "wp2", stage_kind: "stop" },
    ]);
    const route = buildMissionRoute(plan);
    expect(route.waypoints[1].position).toEqual(route.waypoints[0].position);
  });

  it("is deterministic across repeated calls", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 2.5, bounded_speed_mps: 0.25 },
      { waypoint_id: "wp2", stage_kind: "dock" },
    ]);
    const a = buildMissionRoute(plan);
    const b = buildMissionRoute(plan);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });
});

describe("event projection", () => {
  const makeEvent = (
    overrides: Partial<RehearsalEvent> = {},
  ): RehearsalEvent => ({
    event_id: "e1",
    mission_id: "m",
    event_type: "motion",
    event_subtype: "waypoint_reached",
    event_time_ns: 1_000_000_000,
    source_phase: "rehearsal_runtime",
    severity: "info",
    description: "test",
    deterministic_hash: "ev-hash-001",
    payload: { waypoint_id: "wp1" },
    ...overrides,
  });

  it("carries through deterministic hashes", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 1 },
      { waypoint_id: "wp2", stage_kind: "stop" },
    ]);
    const route = buildMissionRoute(plan);
    const event = makeEvent({ deterministic_hash: "deadbeef" });
    const marker = projectEvent(event, route);
    expect(marker.deterministic_hash).toBe("deadbeef");
    expect(marker.position).not.toBeNull();
  });

  it("marks events without waypoint payloads as off-map", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 1 },
    ]);
    const route = buildMissionRoute(plan);
    const event = makeEvent({ payload: {} });
    const marker = projectEvent(event, route);
    expect(marker.position).toBeNull();
  });

  it("projectEvents returns one marker per event", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 1 },
    ]);
    const route = buildMissionRoute(plan);
    const events = [
      makeEvent({ event_id: "e1" }),
      makeEvent({ event_id: "e2", payload: {} }),
    ];
    const markers = projectEvents(events, route);
    expect(markers.length).toBe(2);
  });
});

describe("fitViewBox", () => {
  it("returns a valid SVG viewBox string", () => {
    const plan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 1 },
      { waypoint_id: "wp2", stage_kind: "stop" },
    ]);
    const route = buildMissionRoute(plan);
    const view = fitViewBox(route, 480, 280);
    expect(view.viewBox).toBe("0 0 480 280");
    const screen = view.transform({ x: 0, y: 0 });
    expect(Number.isFinite(screen.x)).toBe(true);
    expect(Number.isFinite(screen.y)).toBe(true);
  });
});

describe("MissionMap derivation", () => {
  it("labels the derivation source on every route", () => {
    const motionPlan = makePlan([
      { waypoint_id: "wp1", stage_kind: "move", bounded_distance_m: 2 },
      { waypoint_id: "wp2", stage_kind: "stop" },
    ]);
    expect(buildMissionRoute(motionPlan).derivation_source).toBe("bounded_inputs");

    const topologyPlan = makePlan([
      { waypoint_id: "wp1", stage_kind: "wait" },
    ]);
    expect(buildMissionRoute(topologyPlan).derivation_source).toBe("topology_only");

    expect(buildMissionRoute(null).derivation_source).toBe("unavailable");
  });

  it("unavailable plan renders an honest placeholder", () => {
    const route = buildMissionRoute(null);
    expect(route.derivation_source).toBe("unavailable");
    expect(route.note).toContain("unavailable");
  });

  it("derives a route from a real committed audit", async () => {
    const audit = await loadRehearsalAudit("warehouse_pickup_route_alpha");
    expect(audit).not.toBeNull();
    const route = buildMissionRoute(audit!.plan);
    expect(route.derivation_source).toBe("bounded_inputs");
    // The audit declares a multi-segment route ending at the dock.
    expect(route.segments.length).toBeGreaterThan(0);
    const last = route.waypoints[route.waypoints.length - 1];
    expect(last.stage_kind).toBe("dock");
  });
});

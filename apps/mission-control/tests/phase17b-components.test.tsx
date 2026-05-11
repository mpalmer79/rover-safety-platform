import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { buildMissionRoute } from "@/adapters/spatial";
import type {
  RehearsalAudit,
  RehearsalEvent,
  SupervisorDecision,
} from "@/adapters/types";
import { MissionEventMarker } from "@/components/MissionEventMarker";
import { MissionMap } from "@/components/MissionMap";
import { MissionRouteList } from "@/components/MissionRoute";
import { MissionSpatialTimeline } from "@/components/MissionSpatialTimeline";
import { ReplayScrubber } from "@/components/ReplayScrubber";
import { RouteProgressIndicator } from "@/components/RouteProgressIndicator";
import { SafetyZoneLayer } from "@/components/SafetyZoneLayer";
import { SupervisorInterventionOverlay } from "@/components/SupervisorInterventionOverlay";
import { WarehouseLaneMap } from "@/components/WarehouseLaneMap";
import { WaypointOverlay } from "@/components/WaypointOverlay";
import { WhyRejectedDrilldown } from "@/components/WhyRejectedDrilldown";
import { ZoneBoundaryOverlay } from "@/components/ZoneBoundaryOverlay";

const baseDecision: SupervisorDecision = {
  decision_id: "d-1",
  decision_status: "rejected",
  safety_status: "unsafe_rejected",
  rationale: ["test"],
  rejected_reasons: ["unsafe_speed"],
  allowed_topics: ["/cmd_vel_requested"],
  forbidden_topics: ["/cmd_vel"],
  requires_human_review: true,
  decided_at_utc: "2026-05-13T00:00:00+00:00",
};

const baseAudit: RehearsalAudit = {
  request: {
    request_id: "r",
    description: "desc",
    mission_id: "m",
    proposal_source: "go forward",
    requested_at_utc: "2026-05-13T00:00:00+00:00",
    seed: 42,
    operator: "",
    odd_profile_id: "default",
    notes: [],
  },
  plan: null,
  validation_diagnostics: [
    { code: "unsafe_speed", severity: "rejection", message: "too fast" },
  ],
  decision: baseDecision,
  runtime: null,
  replay: null,
  analytics: null,
  final_status: "rejected",
  final_failure_reason: "unsafe_speed",
  safety_status: "unsafe_rejected",
  generated_at_utc: "2026-05-13T00:00:00+00:00",
  disclaimer: "test",
  mission_rehearsal_version: "phase16-1",
};

describe("WhyRejectedDrilldown", () => {
  it("shows the verbatim rejection reason", () => {
    render(<WhyRejectedDrilldown audit={baseAudit} />);
    // 'unsafe_speed' appears multiple times (title + diagnostics list +
    // rejected reasons). The test only needs to confirm the value is
    // rendered at least once.
    expect(screen.getAllByText(/unsafe_speed/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/too fast/i)).toBeInTheDocument();
  });

  it("renders nothing on accepted missions", () => {
    const completed = { ...baseAudit, final_status: "completed" as const };
    const { container } = render(<WhyRejectedDrilldown audit={completed} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("ZoneBoundaryOverlay", () => {
  it("lists boundary-related rejections", () => {
    render(<ZoneBoundaryOverlay audit={baseAudit} />);
    // The audit's only diagnostic is unsafe_speed, which is not a
    // boundary code; the overlay reports the empty case honestly.
    expect(screen.getByText(/No boundary violations recorded/i)).toBeInTheDocument();
  });
});

describe("SafetyZoneLayer", () => {
  it("renders an honest placeholder for missing plans", () => {
    render(<SafetyZoneLayer plan={null} />);
    expect(
      screen.getByText(/No mission plan; safety zones unavailable/i),
    ).toBeInTheDocument();
  });
});

describe("SupervisorInterventionOverlay", () => {
  it("lists rejection events", () => {
    const events: RehearsalEvent[] = [
      {
        event_id: "e1",
        mission_id: "m",
        event_type: "supervisor",
        event_subtype: "rejected",
        event_time_ns: 0,
        source_phase: "supervisor",
        severity: "rejection",
        description: "supervisor rejection",
        deterministic_hash: "h1",
        payload: {},
      },
    ];
    render(<SupervisorInterventionOverlay events={events} />);
    expect(screen.getByText(/supervisor rejection/i)).toBeInTheDocument();
  });

  it("renders honest placeholder for empty input", () => {
    render(<SupervisorInterventionOverlay events={[]} />);
    expect(
      screen.getByText(/No supervisor interventions recorded/i),
    ).toBeInTheDocument();
  });
});

describe("RouteProgressIndicator", () => {
  it("shows placeholder for empty waypoints", () => {
    const empty = buildMissionRoute(null);
    render(<RouteProgressIndicator route={empty} />);
    expect(screen.getByText(/No waypoints recorded/i)).toBeInTheDocument();
  });
});

describe("MissionMap", () => {
  it("unavailable route renders an explicit placeholder", () => {
    const route = buildMissionRoute(null);
    render(<MissionMap route={route} />);
    expect(
      screen.getByText(/Spatial data unavailable/i),
    ).toBeInTheDocument();
  });
});

describe("WaypointOverlay", () => {
  it("prompts when no waypoint is selected", () => {
    render(<WaypointOverlay waypoint={null} />);
    expect(
      screen.getByText(/Select a waypoint on the map/i),
    ).toBeInTheDocument();
  });
});

describe("ReplayScrubber", () => {
  const ev = (id: string): RehearsalEvent => ({
    event_id: id,
    mission_id: "m",
    event_type: "motion",
    event_subtype: "waypoint_requested",
    event_time_ns: 0,
    source_phase: "rehearsal_runtime",
    severity: "info",
    description: `event ${id}`,
    deterministic_hash: `h-${id}`,
    payload: {},
  });

  it("renders one slider per event", () => {
    render(<ReplayScrubber events={[ev("e1"), ev("e2"), ev("e3")]} />);
    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("max", "2");
  });

  it("handles empty event lists honestly", () => {
    render(<ReplayScrubber events={[]} />);
    expect(
      screen.getByText(/No rehearsal events recorded/i),
    ).toBeInTheDocument();
  });
});

describe("MissionSpatialTimeline", () => {
  it("renders a coloured stripe with at least one event-type swatch", () => {
    const events: RehearsalEvent[] = [
      {
        event_id: "e1",
        mission_id: "m",
        event_type: "mission",
        event_subtype: "created",
        event_time_ns: 0,
        source_phase: "rehearsal_runtime",
        severity: "info",
        description: "created",
        deterministic_hash: "h1",
        payload: {},
      },
    ];
    render(<MissionSpatialTimeline events={events} />);
    expect(screen.getByLabelText(/Mission timeline/i)).toBeInTheDocument();
    expect(screen.getByText("mission")).toBeInTheDocument();
  });
});

describe("MissionEventMarker", () => {
  it("renders the legend label", () => {
    render(<MissionEventMarker severity="warning" label="warning" />);
    expect(screen.getByText("warning")).toBeInTheDocument();
  });
});

describe("MissionRouteList", () => {
  it("renders bounded inputs and the derivation note", () => {
    const route = buildMissionRoute({
      mission_id: "m",
      request_id: "r",
      proposal_source: "",
      waypoints: [
        {
          waypoint_id: "wp1",
          label: "Forward",
          stage_kind: "move",
          bounded_distance_m: 2.5,
          bounded_angle_deg: 0,
          bounded_speed_mps: 0.25,
        },
        {
          waypoint_id: "wp2",
          label: "Dock",
          stage_kind: "dock",
          bounded_distance_m: 0,
          bounded_angle_deg: 0,
          bounded_speed_mps: 0,
        },
      ],
      safety_constraints: [],
      requested_topics: ["/cmd_vel_requested"],
      forbidden_topics: ["/cmd_vel"],
      odd_profile_id: "default",
      deterministic_hash: "x",
      risk_band: "guarded",
      notes: [],
    });
    render(<MissionRouteList route={route} />);
    expect(screen.getByText("wp1")).toBeInTheDocument();
    expect(screen.getByText("wp2")).toBeInTheDocument();
    expect(screen.getByText(/bounded_inputs/i)).toBeInTheDocument();
  });
});

describe("WarehouseLaneMap", () => {
  it("labels itself as illustrative", () => {
    render(<WarehouseLaneMap />);
    expect(screen.getByText(/Illustrative warehouse layout/i)).toBeInTheDocument();
  });
});

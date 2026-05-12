/**
 * Phase 20 deterministic site definition.
 *
 * One simulated site, one robot. The values are static review
 * fixtures — they map to ``mission-library`` examples and the
 * canonical ODD profile but never encode live state.
 */

import type {
  MissionQueue,
  RobotReadiness,
  Site,
  ZoneStatus,
} from "./models";

export const CANONICAL_SITE: Site = {
  site_id: "rsp-warehouse-1",
  label: "Reference Warehouse",
  description:
    "Single-site reference layout used to rehearse warehouse pickup missions.",
  disclaimer: "Simulation-only · not surveyed coordinates · not safety-certified",
  zones: [
    {
      zone_id: "zone-receiving",
      label: "Receiving",
      description: "Loading-bay apron where missions begin.",
      zone_type: "dock_apron",
      docks: [{ dock_id: "dock-1", label: "Dock A", zone_id: "zone-receiving" }],
      lanes: [
        {
          lane_id: "lane-1",
          label: "Receiving → Aisle",
          zone_id: "zone-receiving",
          direction: "north",
        },
      ],
    },
    {
      zone_id: "zone-aisle-a",
      label: "Aisle A",
      description: "Pickup aisle where bounded missions traverse.",
      zone_type: "operations",
      docks: [],
      lanes: [
        {
          lane_id: "lane-2",
          label: "Aisle A · forward",
          zone_id: "zone-aisle-a",
          direction: "north",
        },
        {
          lane_id: "lane-3",
          label: "Aisle A · return",
          zone_id: "zone-aisle-a",
          direction: "south",
        },
      ],
    },
    {
      zone_id: "zone-exclusion",
      label: "Exclusion · Mezzanine",
      description: "Forbidden zone. No bounded mission may enter.",
      zone_type: "exclusion",
      docks: [],
      lanes: [],
    },
  ],
  robots: [
    {
      robot_id: "rover-001",
      label: "Rover-001 (reference)",
      platform: "warehouse-rover-v1",
      odd_profile_id: "default-warehouse",
      approved_mission_ids: [
        "warehouse_pickup_route_alpha",
        "warehouse_pickup_route_beta",
      ],
      limits: {
        bounded_speed_mps: 0.5,
        bounded_distance_m: 8.0,
      },
      notes: [
        "Bag-backed evidence not yet established for this robot.",
        "Simulation profile only — no hardware control authority.",
      ],
    },
  ],
};

export const REFERENCE_ZONE_STATUS: readonly ZoneStatus[] = [
  {
    zone_id: "zone-receiving",
    status: "nominal",
    active_missions: 0,
    forbidden_topics: ["/cmd_vel"],
    notes: ["Dock A is the canonical mission origin."],
  },
  {
    zone_id: "zone-aisle-a",
    status: "needs_review",
    active_missions: 0,
    forbidden_topics: ["/cmd_vel"],
    notes: ["Speed bound 0.25 m/s in this aisle for canonical rehearsals."],
  },
  {
    zone_id: "zone-exclusion",
    status: "blocked",
    active_missions: 0,
    forbidden_topics: ["/cmd_vel", "/cmd_vel_requested"],
    notes: ["Hard-rejected for every mission with a path through here."],
  },
];

/**
 * Build a readiness record from the canonical rehearsal-audit shape.
 * Inputs are honest: ``hasAudit`` + ``finalStatus`` come straight
 * from the artifact, no recoding.
 */
export function deriveRobotReadiness(input: {
  robotId: string;
  hasAudit: boolean;
  finalStatus: string | null;
  lastRehearsalId: string | null;
  openIssues: readonly string[];
}): RobotReadiness {
  if (!input.hasAudit) {
    return {
      robot_id: input.robotId,
      state: "evidence_missing",
      reason: "No rehearsal audit on disk for this robot's mission profile.",
      last_rehearsal_id: null,
      last_rehearsal_status: null,
      open_issues: input.openIssues,
    };
  }
  const status = input.finalStatus ?? "not_evaluated";
  if (status === "rejected" || status === "aborted") {
    return {
      robot_id: input.robotId,
      state: "blocked",
      reason: `Most recent rehearsal terminated with status: ${status}.`,
      last_rehearsal_id: input.lastRehearsalId,
      last_rehearsal_status: status,
      open_issues: input.openIssues,
    };
  }
  if (status === "completed") {
    return {
      robot_id: input.robotId,
      state: "ready_to_rehearse",
      reason: "Latest rehearsal completed against the canonical ODD profile.",
      last_rehearsal_id: input.lastRehearsalId,
      last_rehearsal_status: status,
      open_issues: input.openIssues,
    };
  }
  return {
    robot_id: input.robotId,
    state: "needs_review",
    reason: `Latest rehearsal status: ${status}. Manual review required.`,
    last_rehearsal_id: input.lastRehearsalId,
    last_rehearsal_status: status,
    open_issues: input.openIssues,
  };
}

export function buildMissionQueue(input: {
  siteId: string;
  generatedAtUtc: string;
  entries: readonly {
    missionId: string;
    description: string;
    auditRequestId: string | null;
    readinessState:
      | "ready_to_rehearse"
      | "needs_review"
      | "blocked"
      | "evidence_missing"
      | "not_evaluated";
    readinessReason: string;
  }[];
}): MissionQueue {
  return {
    site_id: input.siteId,
    generated_at_utc: input.generatedAtUtc,
    entries: input.entries.map((entry) => ({
      mission_id: entry.missionId,
      description: entry.description,
      queued_for: input.siteId,
      readiness: entry.readinessState,
      readiness_reason: entry.readinessReason,
      audit_request_id: entry.auditRequestId,
    })),
  };
}

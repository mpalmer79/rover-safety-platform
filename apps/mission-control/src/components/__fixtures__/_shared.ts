/**
 * Shared fixture data for the component catalog.
 *
 * These shapes mirror the production audit / event / plan models so
 * the catalog renders each component with a realistic prop set. The
 * test suite (tests/a11y-fixtures.ts) consumes parallel values for
 * the a11y gate.
 */

import type {
  ArtifactRegistryRecord,
  MissionPlan,
  RehearsalAudit,
  RehearsalEvent,
  SpatialReplayArtifact,
  SupervisorDecision,
} from "@/adapters/types";
import { buildMissionRoute } from "@/adapters/spatial";

export const FIX_SUPERVISOR_DECISION: SupervisorDecision = {
  decision_id: "d-1",
  decision_status: "rejected",
  safety_status: "unsafe_rejected",
  rationale: ["bounded speed exceeded; supervisor refused"],
  rejected_reasons: ["unsafe_speed"],
  allowed_topics: ["/cmd_vel_requested"],
  forbidden_topics: ["/cmd_vel"],
  requires_human_review: true,
  decided_at_utc: "2026-05-13T00:00:00+00:00",
};

export const FIX_EVENT_INFO: RehearsalEvent = {
  event_id: "e-info-1",
  mission_id: "warehouse_pickup_route_alpha",
  event_type: "motion",
  event_subtype: "waypoint_requested",
  event_time_ns: 0,
  source_phase: "rehearsal_runtime",
  severity: "info",
  description: "waypoint requested",
  deterministic_hash: "h-info-1",
  payload: {},
};

export const FIX_EVENT_REJECTION: RehearsalEvent = {
  event_id: "e-rej-1",
  mission_id: "warehouse_pickup_route_alpha",
  event_type: "supervisor",
  event_subtype: "rejected",
  event_time_ns: 1_000_000_000,
  source_phase: "supervisor",
  severity: "rejection",
  description: "supervisor rejection: unsafe_speed",
  deterministic_hash: "h-rej-1",
  payload: {},
};

export const FIX_AUDIT: RehearsalAudit = {
  request: {
    request_id: "warehouse_pickup_route_alpha",
    description: "Drive to aisle A, inspect pickup zone alpha, return to dock.",
    mission_id: "warehouse_pickup_route_alpha",
    proposal_source: "operator",
    requested_at_utc: "2026-05-13T00:00:00+00:00",
    seed: 42,
    operator: "operator",
    odd_profile_id: "default-warehouse",
    notes: [],
  },
  plan: null,
  validation_diagnostics: [
    { code: "unsafe_speed", severity: "rejection", message: "too fast" },
  ],
  decision: FIX_SUPERVISOR_DECISION,
  runtime: null,
  replay: null,
  analytics: null,
  final_status: "rejected",
  final_failure_reason: "unsafe_speed",
  safety_status: "unsafe_rejected",
  generated_at_utc: "2026-05-13T00:00:00+00:00",
  disclaimer: "Not safety-certified.",
  mission_rehearsal_version: "phase16-1",
};

export const FIX_PLAN: MissionPlan = {
  mission_id: "warehouse_pickup_route_alpha",
  request_id: "warehouse_pickup_route_alpha",
  proposal_source: "operator",
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
  safety_constraints: ["bounded speed", "final dock"],
  requested_topics: ["/cmd_vel_requested"],
  forbidden_topics: ["/cmd_vel"],
  odd_profile_id: "default-warehouse",
  deterministic_hash: "x".repeat(16),
  risk_band: "guarded",
  notes: [],
};

export const FIX_ROUTE = buildMissionRoute(FIX_PLAN);

export const FIX_SPATIAL_ARTIFACT: SpatialReplayArtifact = {
  run_id: "canonical-fixture",
  scenario_id: "warehouse_pickup_route_alpha",
  mission_id: "warehouse_pickup_route_alpha",
  evidence_origin: "fixture",
  bag_status: "missing_manifest",
  derivation_source: "fixture",
  trajectory_status: "complete",
  validation_status: "passed",
  sample_count: 2,
  segment_count: 1,
  topic_sources: ["/odom"],
  missing_topics: [],
  known_limitations: [],
  generated_at_utc: "2026-05-11T18:00:00+00:00",
  note: "fixture-derived; not bag-backed",
  samples: [
    {
      sample_id: "s0",
      time_ns: 0,
      x_m: 0,
      y_m: 0,
      theta_rad: 0,
      source_topic: "/odom",
      confidence: "high",
      event_refs: [],
    },
  ],
  segments: [],
  event_alignments: [],
};

export const FIX_REGISTRY_RECORD: ArtifactRegistryRecord = {
  run_id: "canonical-fixture",
  kind: "spatial_replay",
  derivation_source: "fixture",
  bag_status: "missing_manifest",
  lifecycle: "canonical",
  integrity: "passed",
  related_mission_id: "warehouse_pickup_route_alpha",
  related_scenario_id: "warehouse_pickup_route_alpha",
  notes: [],
  generated_at_utc: "2026-05-11T18:00:00+00:00",
  files: [
    {
      relative_path:
        "spatial-replay/runs/canonical-fixture/spatial-replay.json",
      expected_hash: "0".repeat(64),
      size_bytes: 8956,
      description: "frontend-consumable spatial-replay artefact",
    },
  ],
};

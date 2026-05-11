/**
 * Minimal valid props for every component under src/components/.
 *
 * Shapes are derived from the component's TypeScript signature +
 * the existing test files (components.test.tsx,
 * phase17b-components.test.tsx, artifact-lineage.test.tsx, etc.) so
 * the a11y test exercises the same render paths the unit tests do.
 *
 * Do not invent fields. If a component grows a new required prop,
 * add it here AFTER updating the component's own test file.
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

export const SUPERVISOR_DECISION: SupervisorDecision = {
  decision_id: "d-1",
  decision_status: "rejected",
  safety_status: "unsafe_rejected",
  rationale: ["rationale"],
  rejected_reasons: ["unsafe_speed"],
  allowed_topics: ["/cmd_vel_requested"],
  forbidden_topics: ["/cmd_vel"],
  requires_human_review: true,
  decided_at_utc: "2026-05-13T00:00:00+00:00",
};

export const REHEARSAL_EVENT_INFO: RehearsalEvent = {
  event_id: "e-info-1",
  mission_id: "m",
  event_type: "motion",
  event_subtype: "waypoint_requested",
  event_time_ns: 0,
  source_phase: "rehearsal_runtime",
  severity: "info",
  description: "event info",
  deterministic_hash: "h-info-1",
  payload: {},
};

export const REHEARSAL_EVENT_REJECTION: RehearsalEvent = {
  event_id: "e-rej-1",
  mission_id: "m",
  event_type: "supervisor",
  event_subtype: "rejected",
  event_time_ns: 0,
  source_phase: "supervisor",
  severity: "rejection",
  description: "supervisor rejection",
  deterministic_hash: "h-rej-1",
  payload: {},
};

export const BASE_AUDIT: RehearsalAudit = {
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
  decision: SUPERVISOR_DECISION,
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

export const SAMPLE_PLAN: MissionPlan = {
  mission_id: "m",
  request_id: "r",
  proposal_source: "go forward",
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
};

export const SAMPLE_ROUTE = buildMissionRoute(SAMPLE_PLAN);

export const SPATIAL_ARTIFACT: SpatialReplayArtifact = {
  run_id: "r",
  scenario_id: "s",
  mission_id: "m",
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
  generated_at_utc: "",
  note: "",
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

export const REGISTRY_RECORD: ArtifactRegistryRecord = {
  run_id: "r",
  kind: "spatial_replay",
  derivation_source: "fixture",
  bag_status: "missing_manifest",
  lifecycle: "canonical",
  integrity: "passed",
  related_mission_id: "m",
  related_scenario_id: "s",
  notes: [],
  generated_at_utc: "",
  files: [
    {
      relative_path: "spatial-replay/runs/r/spatial-replay.json",
      expected_hash: "0".repeat(64),
      size_bytes: 128,
      description: "",
    },
  ],
};

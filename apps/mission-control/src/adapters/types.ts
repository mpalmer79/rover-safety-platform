/**
 * Shared TypeScript types for backend artefacts the mission-control UI consumes.
 *
 * Every field name mirrors the JSON shape emitted by the deterministic
 * backend pipelines (Phase 13..16). The UI never invents fields — if a
 * field is absent on disk, the adapter returns ``null`` or an empty
 * array and the UI renders an honest placeholder.
 *
 * Honesty rules enforced at the adapter layer:
 *   * ``bag_backed`` is preserved verbatim from the source JSON;
 *   * rejection / aborted / not-executed statuses are never recoded;
 *   * deterministic hashes are passed through unchanged;
 *   * a missing artefact returns a sentinel — never a synthesised
 *     "happy path" value.
 */

export type RehearsalStatus =
  | "created"
  | "validated"
  | "approved"
  | "rehearsing"
  | "paused"
  | "rejected"
  | "aborted"
  | "completed";

export type RehearsalSafetyStatus =
  | "safe"
  | "guarded"
  | "unsafe_rejected"
  | "requires_review"
  | "not_evaluated";

export type RiskBand = "low" | "guarded" | "restricted" | "blocked";

export type EvidenceStatus = "simulated" | "static_only" | "not_evaluated";

export interface MissionRequest {
  request_id: string;
  description: string;
  mission_id: string;
  proposal_source: string;
  requested_at_utc: string;
  seed: number;
  operator: string;
  odd_profile_id: string;
  notes: readonly string[];
}

export interface MissionWaypoint {
  waypoint_id: string;
  label: string;
  stage_kind: string;
  bounded_distance_m: number;
  bounded_angle_deg: number;
  bounded_speed_mps: number;
}

export interface MissionPlan {
  mission_id: string;
  request_id: string;
  proposal_source: string;
  waypoints: readonly MissionWaypoint[];
  safety_constraints: readonly string[];
  requested_topics: readonly string[];
  forbidden_topics: readonly string[];
  odd_profile_id: string;
  deterministic_hash: string;
  risk_band: RiskBand | string;
  notes: readonly string[];
}

export interface ValidationDiagnostic {
  code: string;
  severity: "info" | "warning" | "rejection";
  message: string;
  parameter?: string;
}

export interface SupervisorDecision {
  decision_id: string;
  decision_status: "approved" | "rejected" | "needs_review";
  safety_status: RehearsalSafetyStatus;
  rationale: readonly string[];
  rejected_reasons: readonly string[];
  allowed_topics: readonly string[];
  forbidden_topics: readonly string[];
  requires_human_review: boolean;
  decided_at_utc: string;
}

export interface RehearsalEvent {
  event_id: string;
  mission_id: string;
  event_type: string;
  event_subtype: string;
  event_time_ns: number;
  source_phase: string;
  severity: "info" | "warning" | "rejection";
  description: string;
  deterministic_hash: string;
  payload: Record<string, unknown>;
}

export interface RehearsalTimeline {
  transitions: ReadonlyArray<readonly [string, string, string]>;
  rendered_markdown: string;
  rendered_mermaid: string;
}

export interface RehearsalRuntime {
  mission_id: string;
  final_status: RehearsalStatus;
  final_failure_reason: string;
  safety_status: RehearsalSafetyStatus;
  events: readonly RehearsalEvent[];
  deterministic_hash: string;
  started_at_utc: string;
  finished_at_utc: string;
  timeline: RehearsalTimeline;
}

export interface ReplayMarker {
  marker_id: string;
  type: string;
  subtype: string;
  time_ns: number;
  deterministic_hash: string;
  description: string;
}

export interface ReplayBundle {
  mission_id: string;
  evidence_status: EvidenceStatus;
  bag_backed: boolean;
  replay_markers: readonly ReplayMarker[];
  review_status: "passed" | "partial" | "rejected" | "not_evaluated";
  rendered_markdown: string;
  deterministic_hash: string;
  notes: readonly string[];
}

export interface RehearsalAnalytics {
  mission_id: string;
  rehearsal_count: number;
  approved_count: number;
  rejected_count: number;
  aborted_count: number;
  completed_count: number;
  supervisor_rejection_count: number;
  validator_rejection_count: number;
  deterministic_replay_stable: boolean;
  notes: readonly string[];
}

export interface RehearsalAudit {
  request: MissionRequest;
  plan: MissionPlan | null;
  validation_diagnostics: readonly ValidationDiagnostic[];
  decision: SupervisorDecision;
  runtime: RehearsalRuntime | null;
  replay: ReplayBundle | null;
  analytics: RehearsalAnalytics | null;
  final_status: RehearsalStatus | string;
  final_failure_reason: string;
  safety_status: RehearsalSafetyStatus | string;
  generated_at_utc: string;
  disclaimer: string;
  mission_rehearsal_version: string;
}

export type MissionLibraryKind = "accepted" | "rejected";

export interface MissionLibraryEntry {
  example_id: string;
  kind: MissionLibraryKind;
  description: string;
  mission_id: string;
  request_id: string;
  proposal_source: string;
  waypoints: readonly MissionWaypoint[];
  safety_constraints: readonly string[];
}

export interface SkillCardSummary {
  skill_id: string;
  skill_type: string;
  language: string;
  title: string;
  subtitle: string;
  risk_band: string;
  safety_status: string;
  generated_at_utc: string;
  code: string;
  code_card: {
    safety_badges: readonly string[];
    animation_steps: readonly string[];
  };
}

export interface RequirementRow {
  req_id: string;
  kind: string;
  title: string;
  status: "passed" | "failed" | "partial" | "not_executed" | "skipped";
  status_detail: string;
  architecture_refs: readonly string[];
  implementation_refs: readonly string[];
  test_refs: readonly string[];
  scenario_refs: readonly string[];
  evidence_paths: readonly string[];
}

export interface TraceabilitySummary {
  generated_at_utc: string;
  overall_status: "passed" | "failed" | "partial" | "not_executed";
  row_count: number;
  rows: readonly RequirementRow[];
}

export interface LiveRuntimeMaturity {
  generated_at_utc: string;
  evidence_root: string;
  runs_total: number;
  latest_run_id: string | null;
  latest_run_status: string;
  runner_status: string;
  status_counts: Record<string, number>;
  bag_counters: Record<string, number>;
  downstream: Record<string, string>;
  known_limitations: readonly string[];
}

export interface NotFoundArtefact {
  kind: "not_found";
  path: string;
  reason: string;
}

/**
 * Phase 20 fleet / site models.
 *
 * The platform supports one robot today but is architected for
 * multi-site review. Every shape is rehearsal-derived; no field
 * encodes runtime telemetry.
 *
 * Honesty rules:
 *   * a robot's ``readiness`` is computed strictly from the most
 *     recent rehearsal audit on disk;
 *   * ``mission_queue`` is a list of catalog references, NOT a
 *     scheduling commitment;
 *   * site / zone / dock / lane shapes are illustrative, never
 *     surveyed coordinates.
 */

export type ReadinessState =
  | "ready_to_rehearse"
  | "needs_review"
  | "blocked"
  | "evidence_missing"
  | "not_evaluated";

export interface RobotProfile {
  robot_id: string;
  label: string;
  platform: string;
  /** ODD profile id this robot is approved for. */
  odd_profile_id: string;
  /** Mission ids this robot is allowed to rehearse. */
  approved_mission_ids: readonly string[];
  /** Hard limits — never derived from runtime, always from policy. */
  limits: {
    bounded_speed_mps: number;
    bounded_distance_m: number;
  };
  /** Notes shown verbatim in the readiness card. */
  notes: readonly string[];
}

export interface Dock {
  dock_id: string;
  label: string;
  zone_id: string;
}

export interface Lane {
  lane_id: string;
  label: string;
  zone_id: string;
  direction: "north" | "south" | "east" | "west" | "loop";
}

export interface Zone {
  zone_id: string;
  label: string;
  description: string;
  zone_type: "operations" | "transit" | "exclusion" | "dock_apron";
  docks: readonly Dock[];
  lanes: readonly Lane[];
}

export interface Site {
  site_id: string;
  label: string;
  description: string;
  zones: readonly Zone[];
  /** Robots associated with the site. */
  robots: readonly RobotProfile[];
  /** Verbatim disclaimer rendered on every fleet view. */
  disclaimer: string;
}

export interface MissionQueueEntry {
  mission_id: string;
  description: string;
  queued_for: string;
  readiness: ReadinessState;
  readiness_reason: string;
  /** Pointer to the rehearsal audit that justifies the readiness. */
  audit_request_id: string | null;
}

export interface MissionQueue {
  site_id: string;
  generated_at_utc: string;
  entries: readonly MissionQueueEntry[];
}

export interface RobotReadiness {
  robot_id: string;
  state: ReadinessState;
  reason: string;
  last_rehearsal_id: string | null;
  last_rehearsal_status: string | null;
  open_issues: readonly string[];
}

export interface ZoneStatus {
  zone_id: string;
  status: "nominal" | "needs_review" | "blocked";
  active_missions: number;
  forbidden_topics: readonly string[];
  notes: readonly string[];
}

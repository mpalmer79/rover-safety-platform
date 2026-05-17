import type {
  SpatialReplayArtifact,
  SpatialReplayEventAlignment,
  SpatialReplayPoseSample,
  SpatialReplaySegment,
} from "./types";

/**
 * Pure coercion helpers for spatial-replay JSON.
 *
 * Split out from `loader.ts` so client bundles (e.g. the /start hero
 * preview) can import them without pulling in `node:fs` / `node:path`.
 * `loader.ts` re-exports these so existing call sites keep working.
 */

export interface SpatialReplayRaw {
  run_id?: string;
  scenario_id?: string;
  mission_id?: string;
  evidence_origin?: string;
  bag_status?: string;
  derivation_source?: string;
  trajectory_status?: string;
  validation_status?: string;
  sample_count?: number;
  segment_count?: number;
  topic_sources?: string[];
  missing_topics?: string[];
  known_limitations?: string[];
  generated_at_utc?: string;
  note?: string;
  samples?: Array<Record<string, unknown>>;
  segments?: Array<Record<string, unknown>>;
  event_alignments?: Array<Record<string, unknown>>;
}

function coerceSample(raw: Record<string, unknown>): SpatialReplayPoseSample {
  const refsRaw = raw.event_refs;
  const refs = Array.isArray(refsRaw) ? refsRaw.map(String) : [];
  return {
    sample_id: String(raw.sample_id ?? ""),
    time_ns: Number(raw.time_ns ?? 0),
    x_m: Number(raw.x_m ?? 0),
    y_m: Number(raw.y_m ?? 0),
    theta_rad: Number(raw.theta_rad ?? 0),
    source_topic: String(raw.source_topic ?? ""),
    confidence: String(raw.confidence ?? "unknown"),
    event_refs: refs,
  };
}

function coerceSegment(raw: Record<string, unknown>): SpatialReplaySegment {
  return {
    from_sample_id: String(raw.from_sample_id ?? ""),
    to_sample_id: String(raw.to_sample_id ?? ""),
    distance_m: Number(raw.distance_m ?? 0),
    duration_ns: Number(raw.duration_ns ?? 0),
  };
}

function coerceAlignment(
  raw: Record<string, unknown>,
): SpatialReplayEventAlignment {
  const pos = raw.spatial_position;
  let spatial: readonly [number, number] | null = null;
  if (Array.isArray(pos) && pos.length === 2) {
    spatial = [Number(pos[0]), Number(pos[1])];
  }
  return {
    event_id: String(raw.event_id ?? ""),
    deterministic_hash: String(raw.deterministic_hash ?? ""),
    matched_sample_id: String(raw.matched_sample_id ?? ""),
    spatial_position: spatial,
    delta_time_ns: Number(raw.delta_time_ns ?? 0),
    confidence: String(raw.confidence ?? "unknown"),
  };
}

export function coerceSpatialReplayArtifact(
  raw: SpatialReplayRaw,
): SpatialReplayArtifact | null {
  if (!raw.run_id || !raw.derivation_source) return null;
  const allowed = new Set([
    "bag_backed",
    "fixture",
    "bounded_inputs",
    "topology_only",
    "unavailable",
  ]);
  if (!allowed.has(raw.derivation_source)) return null;
  const samples = (raw.samples ?? []).map(coerceSample);
  const segments = (raw.segments ?? []).map(coerceSegment);
  const alignments = (raw.event_alignments ?? []).map(coerceAlignment);
  return {
    run_id: String(raw.run_id),
    scenario_id: String(raw.scenario_id ?? ""),
    mission_id: String(raw.mission_id ?? ""),
    evidence_origin: String(raw.evidence_origin ?? ""),
    bag_status: String(raw.bag_status ?? "missing_manifest"),
    derivation_source: raw.derivation_source as SpatialReplayArtifact[
      "derivation_source"
    ],
    trajectory_status: String(raw.trajectory_status ?? "missing"),
    validation_status: String(raw.validation_status ?? "not_executed"),
    sample_count: Number(raw.sample_count ?? samples.length),
    segment_count: Number(raw.segment_count ?? segments.length),
    topic_sources: raw.topic_sources ?? [],
    missing_topics: raw.missing_topics ?? [],
    known_limitations: raw.known_limitations ?? [],
    generated_at_utc: String(raw.generated_at_utc ?? ""),
    note: String(raw.note ?? ""),
    samples,
    segments,
    event_alignments: alignments,
  };
}

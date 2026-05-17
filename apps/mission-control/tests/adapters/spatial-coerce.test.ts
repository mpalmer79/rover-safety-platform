/**
 * Pure-coercion tests for spatial-coerce.
 *
 * The canonical bundled fixture exercises only the happy path, so
 * the ?? default branches in coerceSpatialReplayArtifact and friends
 * are otherwise uncovered. These tests feed deliberately-sparse and
 * deliberately-malformed JSON to exercise every fallback branch.
 */

import { describe, expect, it } from "vitest";

import {
  coerceSpatialReplayArtifact,
  type SpatialReplayRaw,
} from "@/adapters/spatial-coerce";

describe("coerceSpatialReplayArtifact", () => {
  it("returns null when run_id is missing", () => {
    expect(
      coerceSpatialReplayArtifact({ derivation_source: "fixture" } as SpatialReplayRaw),
    ).toBeNull();
  });

  it("returns null when derivation_source is missing", () => {
    expect(
      coerceSpatialReplayArtifact({ run_id: "x" } as SpatialReplayRaw),
    ).toBeNull();
  });

  it("returns null when derivation_source is not in the allowed set", () => {
    expect(
      coerceSpatialReplayArtifact({
        run_id: "x",
        derivation_source: "made_up",
      }),
    ).toBeNull();
  });

  it("accepts every allowed derivation_source", () => {
    for (const ds of [
      "bag_backed",
      "fixture",
      "bounded_inputs",
      "topology_only",
      "unavailable",
    ] as const) {
      const art = coerceSpatialReplayArtifact({
        run_id: "r",
        derivation_source: ds,
      });
      expect(art).not.toBeNull();
      expect(art?.derivation_source).toBe(ds);
    }
  });

  it("fills every defaulted scalar when fields are missing", () => {
    const art = coerceSpatialReplayArtifact({
      run_id: "r",
      derivation_source: "fixture",
    });
    expect(art).not.toBeNull();
    expect(art?.scenario_id).toBe("");
    expect(art?.mission_id).toBe("");
    expect(art?.evidence_origin).toBe("");
    expect(art?.bag_status).toBe("missing_manifest");
    expect(art?.trajectory_status).toBe("missing");
    expect(art?.validation_status).toBe("not_executed");
    expect(art?.sample_count).toBe(0);
    expect(art?.segment_count).toBe(0);
    expect(art?.topic_sources).toEqual([]);
    expect(art?.missing_topics).toEqual([]);
    expect(art?.known_limitations).toEqual([]);
    expect(art?.generated_at_utc).toBe("");
    expect(art?.note).toBe("");
    expect(art?.samples).toEqual([]);
    expect(art?.segments).toEqual([]);
    expect(art?.event_alignments).toEqual([]);
  });

  it("derives sample_count and segment_count from the array lengths when missing", () => {
    const art = coerceSpatialReplayArtifact({
      run_id: "r",
      derivation_source: "fixture",
      samples: [{}, {}, {}],
      segments: [{}, {}],
    });
    expect(art?.sample_count).toBe(3);
    expect(art?.segment_count).toBe(2);
  });

  it("coerces sample fields and defaults event_refs to []", () => {
    const art = coerceSpatialReplayArtifact({
      run_id: "r",
      derivation_source: "fixture",
      samples: [
        {
          sample_id: "s1",
          time_ns: 1,
          x_m: 2,
          y_m: 3,
          theta_rad: 0.4,
          source_topic: "/odom",
          confidence: "high",
          event_refs: ["e1", "e2"],
        },
        { sample_id: "s2" },
      ],
    });
    expect(art?.samples.length).toBe(2);
    expect(art?.samples[0]).toMatchObject({
      sample_id: "s1",
      time_ns: 1,
      x_m: 2,
      y_m: 3,
      theta_rad: 0.4,
      source_topic: "/odom",
      confidence: "high",
      event_refs: ["e1", "e2"],
    });
    expect(art?.samples[1].event_refs).toEqual([]);
    expect(art?.samples[1].confidence).toBe("unknown");
  });

  it("coerces segments + event-alignment positions and tolerates non-array positions", () => {
    const art = coerceSpatialReplayArtifact({
      run_id: "r",
      derivation_source: "fixture",
      segments: [
        {
          from_sample_id: "a",
          to_sample_id: "b",
          distance_m: 1.5,
          duration_ns: 1000,
        },
        {},
      ],
      event_alignments: [
        {
          event_id: "e1",
          deterministic_hash: "h",
          matched_sample_id: "s1",
          spatial_position: [1, 2],
          delta_time_ns: 10,
          confidence: "high",
        },
        // Malformed: spatial_position should be a 2-tuple, here it's
        // a single value. The coerce path must default it to null.
        { event_id: "e2", spatial_position: 42 },
      ],
    });
    expect(art?.segments[0].distance_m).toBe(1.5);
    expect(art?.segments[1].from_sample_id).toBe("");
    expect(art?.event_alignments[0].spatial_position).toEqual([1, 2]);
    expect(art?.event_alignments[1].spatial_position).toBeNull();
    expect(art?.event_alignments[1].confidence).toBe("unknown");
  });
});

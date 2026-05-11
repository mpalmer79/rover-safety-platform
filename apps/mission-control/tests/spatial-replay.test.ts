import { describe, it, expect } from "vitest";

import {
  artifactIsBagBacked,
  buildMissionRoute,
  buildMissionRouteFromArtifact,
  describeDerivationSource,
  selectMissionRoute,
} from "@/adapters/spatial";
import {
  listSpatialReplayRunIds,
  loadSpatialReplay,
} from "@/adapters/loader";
import type {
  MissionPlan,
  SpatialReplayArtifact,
} from "@/adapters/types";

function makeArtifact(
  partial: Partial<SpatialReplayArtifact>,
): SpatialReplayArtifact {
  return {
    run_id: "r",
    scenario_id: "s",
    mission_id: "m",
    evidence_origin: "fixture",
    bag_status: "missing_manifest",
    derivation_source: "fixture",
    trajectory_status: "complete",
    validation_status: "passed",
    sample_count: 0,
    segment_count: 0,
    topic_sources: ["/odom"],
    missing_topics: [],
    known_limitations: [],
    generated_at_utc: "",
    note: "",
    samples: [],
    segments: [],
    event_alignments: [],
    ...partial,
  };
}

describe("loadSpatialReplay", () => {
  it("returns the canonical fixture artefact", async () => {
    const artifact = await loadSpatialReplay("canonical-fixture");
    expect(artifact).not.toBeNull();
    // The committed fixture must NEVER be labelled bag_backed.
    expect(artifact!.derivation_source).toBe("fixture");
    expect(artifact!.bag_status).toBe("missing_manifest");
    expect(artifact!.samples.length).toBeGreaterThan(0);
  });

  it("preserves derivation_source from artefact", async () => {
    const artifact = await loadSpatialReplay("canonical-fixture");
    expect(artifact!.derivation_source).toBe("fixture");
  });

  it("returns null for unknown runs", async () => {
    const artifact = await loadSpatialReplay("__definitely_missing__");
    expect(artifact).toBeNull();
  });

  it("lists available run ids", async () => {
    const ids = await listSpatialReplayRunIds();
    expect(ids).toContain("canonical-fixture");
  });
});

describe("buildMissionRouteFromArtifact", () => {
  it("preserves the artefact's derivation_source", () => {
    const route = buildMissionRouteFromArtifact(
      makeArtifact({
        derivation_source: "bag_backed",
        bag_status: "bag_backed",
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
          {
            sample_id: "s1",
            time_ns: 1_000_000_000,
            x_m: 1,
            y_m: 0,
            theta_rad: 0,
            source_topic: "/odom",
            confidence: "high",
            event_refs: [],
          },
        ],
      }),
    );
    expect(route.derivation_source).toBe("bag_backed");
    expect(route.has_motion).toBe(true);
    expect(route.segments.length).toBe(1);
  });

  it("falls back to unavailable when artefact has zero samples", () => {
    const route = buildMissionRouteFromArtifact(
      makeArtifact({ derivation_source: "fixture", samples: [] }),
    );
    expect(route.derivation_source).toBe("unavailable");
  });
});

describe("buildMissionRouteFromArtifact > prefers artefact over plan", () => {
  it("preserves the artefact's derivation_source", () => {
    const route = buildMissionRouteFromArtifact(
      makeArtifact({
        derivation_source: "fixture",
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
      }),
    );
    expect(route.derivation_source).toBe("fixture");
  });
});

describe("selectMissionRoute", () => {
  const plan: MissionPlan = {
    mission_id: "m",
    request_id: "r",
    proposal_source: "",
    waypoints: [
      {
        waypoint_id: "wp1",
        label: "Forward",
        stage_kind: "move",
        bounded_distance_m: 1.5,
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

  it("buildMissionRouteFromArtifact > prefers artefact over plan", () => {
    const artifact = makeArtifact({
      derivation_source: "fixture",
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
        {
          sample_id: "s1",
          time_ns: 1_000_000_000,
          x_m: 1,
          y_m: 0,
          theta_rad: 0,
          source_topic: "/odom",
          confidence: "high",
          event_refs: [],
        },
      ],
    });
    const route = selectMissionRoute(plan, artifact);
    expect(route.derivation_source).toBe("fixture");
    expect(route.artifact).not.toBeNull();
  });

  it("falls back to bounded_inputs when artefact is null", () => {
    const route = selectMissionRoute(plan, null);
    expect(route.derivation_source).toBe("bounded_inputs");
  });

  it("falls back to bounded_inputs when artefact has zero samples", () => {
    const artifact = makeArtifact({
      derivation_source: "fixture",
      samples: [],
    });
    const route = selectMissionRoute(plan, artifact);
    expect(route.derivation_source).toBe("bounded_inputs");
  });

  it("falls back to bounded_inputs when artefact is unavailable", () => {
    const artifact = makeArtifact({ derivation_source: "unavailable" });
    const route = selectMissionRoute(plan, artifact);
    expect(route.derivation_source).toBe("bounded_inputs");
  });

  it("plan-only when no artefact and no plan", () => {
    const route = selectMissionRoute(null, null);
    expect(route.derivation_source).toBe("unavailable");
  });
});

describe("artifactIsBagBacked", () => {
  it("requires derivation_source=bag_backed", () => {
    const artifact = makeArtifact({ derivation_source: "fixture" });
    expect(artifactIsBagBacked(artifact)).toBe(false);
  });

  it("requires at least one pose sample", () => {
    const artifact = makeArtifact({
      derivation_source: "bag_backed",
      bag_status: "bag_backed",
      samples: [],
    });
    expect(artifactIsBagBacked(artifact)).toBe(false);
  });

  it("requires bag_status=bag_backed", () => {
    const artifact = makeArtifact({
      derivation_source: "bag_backed",
      bag_status: "partial",
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
    });
    expect(artifactIsBagBacked(artifact)).toBe(false);
  });

  it("accepts a fully-valid bag-backed artefact", () => {
    const artifact = makeArtifact({
      derivation_source: "bag_backed",
      bag_status: "bag_backed",
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
    });
    expect(artifactIsBagBacked(artifact)).toBe(true);
  });

  it("rejects a null artefact", () => {
    expect(artifactIsBagBacked(null)).toBe(false);
  });
});

describe("describeDerivationSource", () => {
  it("returns the verbatim bag-backed caption", () => {
    expect(describeDerivationSource("bag_backed")).toMatch(
      /bag-backed runtime evidence/i,
    );
  });

  it("returns the verbatim fixture caption", () => {
    const caption = describeDerivationSource("fixture");
    expect(caption).toMatch(/fixture/i);
    expect(caption).toMatch(/not bag-backed evidence/i);
  });

  it("returns the bounded-inputs caption", () => {
    expect(describeDerivationSource("bounded_inputs")).toMatch(
      /bounded simulation inputs/i,
    );
  });

  it("returns the topology-only caption", () => {
    expect(describeDerivationSource("topology_only")).toMatch(/topology only/i);
  });

  it("returns the unavailable caption", () => {
    expect(describeDerivationSource("unavailable")).toMatch(/unavailable/i);
  });
});

describe("bounded-inputs fallback remains intact", () => {
  it("plan with bounded distance still derives bounded_inputs", () => {
    const route = buildMissionRoute({
      mission_id: "m",
      request_id: "r",
      proposal_source: "",
      waypoints: [
        {
          waypoint_id: "wp1",
          label: "Forward",
          stage_kind: "move",
          bounded_distance_m: 2,
          bounded_angle_deg: 0,
          bounded_speed_mps: 0.25,
        },
        {
          waypoint_id: "wp2",
          label: "Stop",
          stage_kind: "stop",
          bounded_distance_m: 0,
          bounded_angle_deg: 0,
          bounded_speed_mps: 0,
        },
      ],
      safety_constraints: [],
      requested_topics: [],
      forbidden_topics: [],
      odd_profile_id: "default",
      deterministic_hash: "x",
      risk_band: "guarded",
      notes: [],
    });
    expect(route.derivation_source).toBe("bounded_inputs");
  });
});

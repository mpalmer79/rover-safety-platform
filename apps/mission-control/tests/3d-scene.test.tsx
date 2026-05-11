import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";

import { MissionTimelineBridge } from "@/3d/MissionTimelineBridge";
import type { MissionPlan, SpatialReplayArtifact } from "@/adapters/types";

// Mock the heavy R3F module: testing the immersive scene mount in
// happy-dom would require a WebGL context. The bridge's WebGL guard
// is what we actually want to test; in the prefer2D path it must
// fall back to the existing 2D panel.
vi.mock("@/3d/MissionPlayback3D", () => ({
  MissionPlayback3D: () => <div data-testid="immersive-scene-mock" />,
}));

const PLAN: MissionPlan = {
  mission_id: "m",
  request_id: "r",
  proposal_source: "",
  waypoints: [
    {
      waypoint_id: "wp1",
      label: "Forward",
      stage_kind: "move",
      bounded_distance_m: 1,
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
};

const ARTIFACT: SpatialReplayArtifact = {
  run_id: "canonical-fixture",
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
  segments: [
    {
      from_sample_id: "s0",
      to_sample_id: "s1",
      distance_m: 1,
      duration_ns: 1_000_000_000,
    },
  ],
  event_alignments: [],
};

describe("MissionTimelineBridge", () => {
  it("falls back to the 2D panel when WebGL is unavailable", async () => {
    // happy-dom doesn't support WebGL; the bridge should detect that
    // and render the 2D MissionPlaybackPanel instead.
    const { findByTestId } = render(
      <MissionTimelineBridge
        plan={PLAN}
        events={[]}
        spatialReplay={ARTIFACT}
      />,
    );
    // The 2D fallback renders the SpatialReplayBadge from Phase 17C.
    const badge = await findByTestId("spatial-replay-badge");
    expect(badge).toBeInTheDocument();
  });

  it("renders the 2D fallback when prefer2D is explicit", async () => {
    const { findByTestId } = render(
      <MissionTimelineBridge
        plan={PLAN}
        events={[]}
        spatialReplay={null}
        prefer2D
      />,
    );
    const badge = await findByTestId("spatial-replay-badge");
    expect(badge).toBeInTheDocument();
  });
});

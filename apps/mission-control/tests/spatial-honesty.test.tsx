import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";
import { render, screen } from "@testing-library/react";

import {
  buildMissionRoute,
  buildMissionRouteFromArtifact,
} from "@/adapters/spatial";
import type { SpatialReplayArtifact } from "@/adapters/types";
import { MissionMap } from "@/components/MissionMap";
import { MissionPlaybackPanel } from "@/components/MissionPlaybackPanel";
import { SpatialReplayBadge } from "@/components/SpatialReplayBadge";

const REPO_ROOT = path.resolve(__dirname, "../../..");

function fixtureArtifact(): SpatialReplayArtifact {
  return {
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
    known_limitations: ["fixture-derived spatial samples; not bag-backed evidence"],
    generated_at_utc: "2026-05-11T18:00:00+00:00",
    note: "fixture",
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
}

function bagBackedArtifact(): SpatialReplayArtifact {
  return {
    ...fixtureArtifact(),
    derivation_source: "bag_backed",
    bag_status: "bag_backed",
    evidence_origin: "runtime",
  };
}

describe("MissionMap > caption names the derivation source", () => {
  it("renders the bag-backed caption verbatim", () => {
    const route = buildMissionRouteFromArtifact(bagBackedArtifact());
    render(<MissionMap route={route} />);
    expect(
      screen.getByTestId("mission-map-derivation").textContent,
    ).toMatch(/bag-backed runtime evidence/i);
  });

  it("renders the fixture caption + warning", () => {
    const route = buildMissionRouteFromArtifact(fixtureArtifact());
    render(<MissionMap route={route} />);
    expect(
      screen.getByTestId("mission-map-derivation").textContent,
    ).toMatch(/fixture-derived spatial replay/i);
    // The phrase appears in both the caption and the warning span.
    expect(
      screen.getAllByText(/not bag-backed evidence/i).length,
    ).toBeGreaterThan(0);
  });

  it("renders the bounded-inputs caption", () => {
    const route = buildMissionRoute({
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
    });
    render(<MissionMap route={route} />);
    expect(
      screen.getByTestId("mission-map-derivation").textContent,
    ).toMatch(/bounded simulation inputs/i);
  });

  it("renders the unavailable caption when route is empty", () => {
    const route = buildMissionRoute(null);
    render(<MissionMap route={route} />);
    expect(screen.getByText(/Spatial data unavailable/i)).toBeInTheDocument();
  });
});

describe("SpatialReplayBadge > visible per-source colouring", () => {
  it("exposes data-source for every derivation source", () => {
    const sources = [
      "bag_backed",
      "fixture",
      "bounded_inputs",
      "topology_only",
      "unavailable",
    ] as const;
    for (const source of sources) {
      const { unmount } = render(<SpatialReplayBadge source={source} />);
      const badge = screen.getByTestId("spatial-replay-badge");
      expect(badge.getAttribute("data-source")).toBe(source);
      unmount();
    }
  });
});

describe("MissionPlaybackPanel > badge surfaces bag-backed vs fixture", () => {
  it("renders the fixture badge when artefact is fixture-derived", () => {
    render(
      <MissionPlaybackPanel
        plan={null}
        events={[]}
        spatialReplay={fixtureArtifact()}
      />,
    );
    const badge = screen.getByTestId("spatial-replay-badge");
    expect(badge.getAttribute("data-source")).toBe("fixture");
  });

  it("renders the bag-backed badge when artefact is bag-backed", () => {
    render(
      <MissionPlaybackPanel
        plan={null}
        events={[]}
        spatialReplay={bagBackedArtifact()}
      />,
    );
    const badge = screen.getByTestId("spatial-replay-badge");
    expect(badge.getAttribute("data-source")).toBe("bag_backed");
  });

  it("falls back to bounded-inputs badge when no artefact", () => {
    render(
      <MissionPlaybackPanel
        plan={{
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
        }}
        events={[]}
        spatialReplay={null}
      />,
    );
    const badge = screen.getByTestId("spatial-replay-badge");
    expect(badge.getAttribute("data-source")).toBe("bounded_inputs");
  });
});

describe("CI honesty grep > no fake bag-backed claim in prerendered HTML", () => {
  // The build hasn't run inside vitest; this test inspects the
  // committed canonical fixture instead, which the CI grep would
  // see in the prerendered HTML. Any prerendered page that renders
  // the canonical fixture must therefore inherit the fixture caption.
  it("canonical-fixture artefact is not labelled bag_backed", async () => {
    const text = await fs.readFile(
      path.join(REPO_ROOT, "spatial-replay", "runs", "canonical-fixture", "spatial-replay.json"),
      "utf-8",
    );
    const data = JSON.parse(text);
    expect(data.derivation_source).toBe("fixture");
    expect(data.bag_status).toBe("missing_manifest");
  });
});

describe("simulated artefacts never claim bag-backed", () => {
  it("every committed spatial-replay run is honest about its source", async () => {
    const runsRoot = path.join(REPO_ROOT, "spatial-replay", "runs");
    let entries: string[] = [];
    try {
      entries = await fs.readdir(runsRoot);
    } catch {
      return;
    }
    for (const id of entries) {
      const replayPath = path.join(runsRoot, id, "spatial-replay.json");
      let text: string;
      try {
        text = await fs.readFile(replayPath, "utf-8");
      } catch {
        continue;
      }
      const data = JSON.parse(text);
      // The only way derivation_source=bag_backed is committed is if
      // a real bag manifest validated. The canonical fixture must
      // therefore declare 'fixture'. If a future bag-backed run is
      // committed, validation_status must be passed/partial.
      if (data.derivation_source === "bag_backed") {
        expect(data.bag_status).toBe("bag_backed");
        expect(data.validation_status).toMatch(/passed|partial/);
        expect(data.sample_count).toBeGreaterThan(0);
      } else {
        expect(["fixture", "bounded_inputs", "topology_only", "unavailable"]).toContain(
          data.derivation_source,
        );
        expect(data.bag_status).not.toBe("bag_backed");
      }
    }
  });
});

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { computeSceneSnapshot } from "@/adapters/sceneSnapshot";
import { SceneSnapshotPanel } from "@/components/SceneSnapshotPanel";
import type {
  ArtifactRegistryRecord,
  SpatialReplayArtifact,
} from "@/adapters/types";

function makeArtifact(
  partial: Partial<SpatialReplayArtifact> = {},
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
    sample_count: 2,
    segment_count: 1,
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

function makeRecord(
  partial: Partial<ArtifactRegistryRecord> = {},
): ArtifactRegistryRecord {
  return {
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
    ...partial,
  };
}

describe("computeSceneSnapshot", () => {
  it("returns unavailable when nothing exists", () => {
    const state = computeSceneSnapshot("r", null, null);
    expect(state.status).toBe("unavailable");
    expect(state.eligible_for_bag_backed_snapshot).toBe(false);
    expect(state.missing_inputs.length).toBeGreaterThan(0);
  });

  it("returns fixture status for a fixture-derived artefact", () => {
    const state = computeSceneSnapshot("r", makeArtifact(), makeRecord());
    expect(state.status).toBe("fixture");
    expect(state.eligible_for_bag_backed_snapshot).toBe(false);
  });

  it("returns bag_backed status only when derivation + bag_status + integrity all align", () => {
    const state = computeSceneSnapshot(
      "r",
      makeArtifact({ derivation_source: "bag_backed", bag_status: "bag_backed" }),
      makeRecord({
        derivation_source: "bag_backed",
        bag_status: "bag_backed",
        integrity: "passed",
      }),
    );
    expect(state.status).toBe("bag_backed");
    expect(state.eligible_for_bag_backed_snapshot).toBe(true);
    expect(state.reviewer_export_ready).toBe(true);
  });

  it("does not become bag_backed if integrity is partial", () => {
    const state = computeSceneSnapshot(
      "r",
      makeArtifact({ derivation_source: "bag_backed", bag_status: "bag_backed" }),
      makeRecord({
        derivation_source: "bag_backed",
        bag_status: "bag_backed",
        integrity: "partial",
      }),
    );
    expect(state.status).not.toBe("bag_backed");
    expect(state.eligible_for_bag_backed_snapshot).toBe(false);
  });

  it("does not become bag_backed if the spatial replay claims fixture", () => {
    const state = computeSceneSnapshot(
      "r",
      makeArtifact({ derivation_source: "fixture" }),
      makeRecord({
        derivation_source: "bag_backed",
        bag_status: "bag_backed",
        integrity: "passed",
      }),
    );
    expect(state.status).not.toBe("bag_backed");
  });
});

describe("SceneSnapshotPanel", () => {
  it("renders the not_executed missing-inputs list when bag_status mismatches", () => {
    render(
      <SceneSnapshotPanel
        runId="r"
        artifact={makeArtifact({
          derivation_source: "bag_backed",
          bag_status: "missing_manifest",
        })}
        record={makeRecord({ derivation_source: "bag_backed" })}
      />,
    );
    const status = screen.getByTestId("scene-snapshot-status");
    expect(status.getAttribute("data-status")).toBe("not_executed");
    expect(status.getAttribute("data-export-ready")).toBe("false");
    expect(screen.getByTestId("scene-snapshot-missing")).toBeInTheDocument();
  });

  it("renders fixture status with the no-bag-backed note", () => {
    render(
      <SceneSnapshotPanel
        runId="canonical-fixture"
        artifact={makeArtifact()}
        record={makeRecord()}
      />,
    );
    const status = screen.getByTestId("scene-snapshot-status");
    expect(status.getAttribute("data-status")).toBe("fixture");
    expect(status.getAttribute("data-export-ready")).toBe("false");
  });

  it("renders bag_backed status only when ready", () => {
    render(
      <SceneSnapshotPanel
        runId="r"
        artifact={makeArtifact({
          derivation_source: "bag_backed",
          bag_status: "bag_backed",
        })}
        record={makeRecord({
          derivation_source: "bag_backed",
          bag_status: "bag_backed",
          integrity: "passed",
        })}
      />,
    );
    const status = screen.getByTestId("scene-snapshot-status");
    expect(status.getAttribute("data-status")).toBe("bag_backed");
    expect(status.getAttribute("data-export-ready")).toBe("true");
  });

  it("renders the hash chain when a registry record is present", () => {
    render(
      <SceneSnapshotPanel
        runId="r"
        artifact={makeArtifact()}
        record={makeRecord()}
      />,
    );
    expect(screen.getByTestId("scene-snapshot-hash-chain")).toBeInTheDocument();
  });

  it("renders unavailable when nothing is registered", () => {
    render(<SceneSnapshotPanel runId="nope" artifact={null} record={null} />);
    const status = screen.getByTestId("scene-snapshot-status");
    expect(status.getAttribute("data-status")).toBe("unavailable");
  });
});

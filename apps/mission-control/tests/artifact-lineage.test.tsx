import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { ArtifactIntegrityBadge } from "@/components/ArtifactIntegrityBadge";
import { DeterministicHashChain } from "@/components/DeterministicHashChain";
import { EvidenceLineageGraph } from "@/components/EvidenceLineageGraph";
import { ReplayConfidencePanel } from "@/components/ReplayConfidencePanel";
import { ReplayLifecyclePanel } from "@/components/ReplayLifecyclePanel";
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
    generated_at_utc: "2026-05-11T18:00:00+00:00",
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
    generated_at_utc: "2026-05-11T18:00:00+00:00",
    files: [
      {
        relative_path: "spatial-replay/runs/r/spatial-replay.json",
        expected_hash: "0".repeat(64),
        size_bytes: 128,
        description: "frontend-consumable artifact",
      },
    ],
    ...partial,
  };
}

describe("ArtifactIntegrityBadge", () => {
  it("renders the verbatim integrity string", () => {
    const sources = ["passed", "partial", "failed", "missing", "unverified"] as const;
    for (const s of sources) {
      const { unmount } = render(<ArtifactIntegrityBadge integrity={s} />);
      const badge = screen.getByTestId("artifact-integrity-badge");
      expect(badge.getAttribute("data-integrity")).toBe(s);
      unmount();
    }
  });

  it("surfaces the lifecycle when provided", () => {
    render(
      <ArtifactIntegrityBadge integrity="passed" lifecycle="canonical" />,
    );
    const badge = screen.getByTestId("artifact-integrity-badge");
    expect(badge.getAttribute("data-lifecycle")).toBe("canonical");
    expect(badge.textContent).toMatch(/canonical/);
  });
});

describe("DeterministicHashChain", () => {
  it("renders one row per file with sha256 prefix", () => {
    render(
      <DeterministicHashChain
        files={[
          {
            relative_path: "a.json",
            expected_hash: "abcdef0123456789".padEnd(64, "0"),
            size_bytes: 100,
            description: "first",
          },
          {
            relative_path: "b.json",
            expected_hash: "0".repeat(64),
            size_bytes: 200,
            description: "",
          },
        ]}
      />,
    );
    const table = screen.getByTestId("deterministic-hash-chain");
    expect(table).toBeInTheDocument();
    expect(screen.getByText("a.json")).toBeInTheDocument();
    expect(screen.getByText("b.json")).toBeInTheDocument();
    // 16-char prefix
    expect(screen.getByText(/abcdef0123456789/)).toBeInTheDocument();
  });

  it("renders an honest placeholder when there are no files", () => {
    render(<DeterministicHashChain files={[]} />);
    expect(screen.getByText(/No registered files/i)).toBeInTheDocument();
  });
});

describe("EvidenceLineageGraph", () => {
  it("renders the lineage chain for a fixture artifact", () => {
    render(
      <EvidenceLineageGraph
        artifact={makeArtifact()}
        record={makeRecord()}
      />,
    );
    expect(screen.getByTestId("evidence-lineage-graph")).toBeInTheDocument();
    // Rehearsal + fixture + spatial-replay + registry + render
    expect(screen.getAllByTestId(/evidence-lineage-node-/).length).toBeGreaterThanOrEqual(4);
    expect(screen.getByText(/fixture-derived spatial replay/i)).toBeInTheDocument();
  });

  it("renders the lineage chain for a bag-backed artifact", () => {
    render(
      <EvidenceLineageGraph
        artifact={makeArtifact({
          derivation_source: "bag_backed",
          bag_status: "bag_backed",
        })}
        record={makeRecord({ derivation_source: "bag_backed", bag_status: "bag_backed" })}
      />,
    );
    expect(screen.getByText(/bag-backed runtime evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/bag-manifest/i)).toBeInTheDocument();
  });

  it("renders an honest placeholder when no artifact", () => {
    render(<EvidenceLineageGraph artifact={null} record={null} />);
    expect(screen.getByText(/No spatial-replay artifact/i)).toBeInTheDocument();
  });
});

describe("ReplayConfidencePanel", () => {
  it("computes a fixture band as medium", () => {
    render(
      <ReplayConfidencePanel
        artifact={makeArtifact()}
        record={makeRecord()}
      />,
    );
    const band = screen.getByTestId("replay-confidence-band");
    expect(band.getAttribute("data-band")).toBe("medium");
  });

  it("computes a bag-backed band as high when integrity passes", () => {
    render(
      <ReplayConfidencePanel
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
    const band = screen.getByTestId("replay-confidence-band");
    expect(band.getAttribute("data-band")).toBe("high");
  });

  it("downgrades to low when integrity is partial", () => {
    render(
      <ReplayConfidencePanel
        artifact={makeArtifact({ validation_status: "partial" })}
        record={makeRecord({ integrity: "partial" })}
      />,
    );
    const band = screen.getByTestId("replay-confidence-band");
    expect(band.getAttribute("data-band")).toBe("low");
  });
});

describe("ReplayLifecyclePanel", () => {
  it("marks all rungs up to canonical as reached", () => {
    render(<ReplayLifecyclePanel record={makeRecord()} />);
    const canonicalRung = screen.getByTestId("lifecycle-rung-canonical");
    expect(canonicalRung.getAttribute("data-reached")).toBe("true");
    const generatedRung = screen.getByTestId("lifecycle-rung-generated");
    expect(generatedRung.getAttribute("data-reached")).toBe("true");
  });

  it("renders a placeholder for unregistered runs", () => {
    render(<ReplayLifecyclePanel record={null} />);
    expect(screen.getByText(/No artifact registered/i)).toBeInTheDocument();
  });

  it("renders the deprecated rung when lifecycle is deprecated", () => {
    render(
      <ReplayLifecyclePanel
        record={makeRecord({ lifecycle: "deprecated" })}
      />,
    );
    expect(screen.getByTestId("lifecycle-rung-deprecated")).toBeInTheDocument();
  });
});

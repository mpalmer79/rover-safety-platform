import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";

import {
  loadArtifactRegistry,
  loadArtifactRegistryRecord,
  loadSpatialReplay,
  listSpatialReplayRunIds,
} from "@/adapters/loader";

const REPO_ROOT = path.resolve(__dirname, "../../..");

describe("loadArtifactRegistry", () => {
  it("returns the committed canonical registry", async () => {
    const registry = await loadArtifactRegistry();
    expect(registry).not.toBeNull();
    expect(registry!.records.length).toBeGreaterThan(0);
    const canon = registry!.records.find(
      (r) => r.run_id === "canonical-fixture",
    );
    expect(canon).toBeDefined();
    expect(canon!.derivation_source).toBe("fixture");
    expect(canon!.bag_status).toBe("missing_manifest");
    expect(canon!.lifecycle).toBe("canonical");
  });

  it("registers every committed file with a non-empty hash", async () => {
    const registry = await loadArtifactRegistry();
    for (const record of registry!.records) {
      expect(record.files.length).toBeGreaterThan(0);
      for (const f of record.files) {
        expect(f.expected_hash).toMatch(/^[0-9a-f]{64}$/);
        expect(f.size_bytes).toBeGreaterThan(0);
      }
    }
  });

  it("does not list a record whose derivation_source is bag_backed unless it carries samples", async () => {
    const registry = await loadArtifactRegistry();
    for (const r of registry!.records) {
      if (r.derivation_source === "bag_backed") {
        // The artefact itself must declare samples > 0; the registry
        // mirrors that. We re-check via the artefact JSON below.
        const replayPath = path.join(
          REPO_ROOT,
          r.files.find((f) => f.relative_path.endsWith("spatial-replay.json"))!
            .relative_path,
        );
        const data = JSON.parse(await fs.readFile(replayPath, "utf-8"));
        expect(data.sample_count).toBeGreaterThan(0);
        expect(data.bag_status).toBe("bag_backed");
      }
    }
  });
});

describe("loadArtifactRegistryRecord", () => {
  it("returns null for unknown ids", async () => {
    const record = await loadArtifactRegistryRecord("__nope__");
    expect(record).toBeNull();
  });
  it("returns the canonical fixture record", async () => {
    const record = await loadArtifactRegistryRecord("canonical-fixture");
    expect(record).not.toBeNull();
    expect(record!.kind).toBe("spatial_replay");
  });
});

describe("loadSpatialReplay goes through the registry first", () => {
  it("returns the canonical fixture artefact for the registered run", async () => {
    const artifact = await loadSpatialReplay("canonical-fixture");
    expect(artifact).not.toBeNull();
    expect(artifact!.derivation_source).toBe("fixture");
  });

  it("returns null for an unregistered, missing run", async () => {
    const artifact = await loadSpatialReplay("__definitely_missing__");
    expect(artifact).toBeNull();
  });
});

describe("listSpatialReplayRunIds prefers the registry", () => {
  it("yields the canonical fixture", async () => {
    const ids = await listSpatialReplayRunIds();
    expect(ids).toContain("canonical-fixture");
  });
});

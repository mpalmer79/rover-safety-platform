import { describe, it, expect } from "vitest";

import { loadSpatialReplay } from "@/adapters/loader";

describe("loadSpatialReplay (registry-anchored resolution)", () => {
  it("returns the canonical fixture artifact with non-empty samples", async () => {
    const artifact = await loadSpatialReplay("canonical-fixture");
    expect(artifact).not.toBeNull();
    expect(artifact!.samples.length).toBeGreaterThan(0);
  });
});

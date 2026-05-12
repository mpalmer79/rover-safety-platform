import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";

const REPO_ROOT = path.resolve(__dirname, "../../..");
const WORKSPACE = path.resolve(__dirname, "..");

describe("vercel.json", () => {
  it("declares the Next.js framework", async () => {
    const data = JSON.parse(
      await fs.readFile(path.join(WORKSPACE, "vercel.json"), "utf-8"),
    );
    expect(data.framework).toBe("nextjs");
    expect(data.outputDirectory).toBe(".next");
  });

  it("uses the standard build pipeline", async () => {
    const data = JSON.parse(
      await fs.readFile(path.join(WORKSPACE, "vercel.json"), "utf-8"),
    );
    expect(data.buildCommand).toBe("next build");
    expect(data.installCommand).toContain("npm ci");
  });
});

describe("mission-control-ci.yml", () => {
  it("runs the full honesty gate", async () => {
    const yml = await fs.readFile(
      path.join(REPO_ROOT, ".github/workflows/mission-control-ci.yml"),
      "utf-8",
    );
    expect(yml).toContain("npm run typecheck");
    expect(yml).toContain("npm run test");
    expect(yml).toContain("npm run build");
    expect(yml).toContain("Simulation-only");
    expect(yml).toContain("bag-backed: yes");
  });

  it("targets PRs on apps/mission-control and traceability changes", async () => {
    const yml = await fs.readFile(
      path.join(REPO_ROOT, ".github/workflows/mission-control-ci.yml"),
      "utf-8",
    );
    expect(yml).toContain("apps/mission-control/**");
    expect(yml).toContain("verification/traceability.json");
  });
});

describe("README + docs", () => {
  it("workspace README mentions Vercel + honesty rules", async () => {
    const readme = await fs.readFile(path.join(WORKSPACE, "README.md"), "utf-8");
    expect(readme).toContain("vercel.json");
    expect(readme).toContain("SafetyBoundaryBanner");
    expect(readme).toContain("EvidenceStatusChip");
  });

  it("phase 17B docs are present and carry the disclaimer", async () => {
    const docs = [
      "MISSION_SPATIAL_VISUALIZATION.md",
      "MISSION_REPLAY_MAPS.md",
      "OPERATOR_EXPERIENCE_GUIDELINES.md",
      "SPATIAL_REPLAY_ARCHITECTURE.md",
    ];
    for (const file of docs) {
      const text = await fs.readFile(
        path.join(REPO_ROOT, "docs", file),
        "utf-8",
      );
      expect(text.toLowerCase()).toContain("not safety-certified");
    }
  });
});

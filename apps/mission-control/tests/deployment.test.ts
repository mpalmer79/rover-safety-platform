import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";

const REPO_ROOT = path.resolve(__dirname, "../../..");
const WORKSPACE = path.resolve(__dirname, "..");

// railway.json now lives at the repo root for monorepo deployment.
// The nixpacks plan invokes the build under apps/mission-control.
const RAILWAY_JSON_PATH = path.join(REPO_ROOT, "railway.json");

describe("railway.json", () => {
  it("declares the NIXPACKS builder", async () => {
    const data = JSON.parse(
      await fs.readFile(RAILWAY_JSON_PATH, "utf-8"),
    );
    expect(data.build.builder).toBe("NIXPACKS");
  });

  it("invokes npm run build under apps/mission-control", async () => {
    const data = JSON.parse(
      await fs.readFile(RAILWAY_JSON_PATH, "utf-8"),
    );
    const cmds = data.build.nixpacksPlan.phases.build.cmds.join("\n");
    expect(cmds).toContain("apps/mission-control");
    expect(cmds).toContain("npm run build");
  });

  it("sets a healthcheck path", async () => {
    const data = JSON.parse(
      await fs.readFile(RAILWAY_JSON_PATH, "utf-8"),
    );
    expect(data.deploy.healthcheckPath).toBe("/");
    expect(typeof data.deploy.healthcheckTimeout).toBe("number");
  });

  it("uses next start with a host + port", async () => {
    const data = JSON.parse(
      await fs.readFile(RAILWAY_JSON_PATH, "utf-8"),
    );
    expect(data.deploy.startCommand).toContain("npm run start");
    expect(data.deploy.startCommand).toContain("$PORT");
  });
});

describe(".env.example", () => {
  it("documents only port and telemetry vars", async () => {
    const env = await fs.readFile(path.join(WORKSPACE, ".env.example"), "utf-8");
    // Allowed:
    expect(env).toContain("PORT=");
    expect(env).toContain("HOSTNAME=");
    expect(env).toContain("NEXT_TELEMETRY_DISABLED=1");
    // Forbidden (must appear in the prohibited section only, not as
    // actual assignments).
    expect(env).not.toMatch(/^OPENAI_API_KEY\s*=/m);
    expect(env).not.toMatch(/^ANTHROPIC_API_KEY\s*=/m);
    expect(env).not.toMatch(/^COHERE_API_KEY\s*=/m);
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
  it("workspace README mentions Railway + honesty rules", async () => {
    const readme = await fs.readFile(path.join(WORKSPACE, "README.md"), "utf-8");
    expect(readme).toContain("railway.json");
    expect(readme).toContain("SafetyBoundaryBanner");
    expect(readme).toContain("EvidenceStatusChip");
  });

  it("phase 17B docs are present and carry the disclaimer", async () => {
    const docs = [
      "MISSION_SPATIAL_VISUALIZATION.md",
      "RAILWAY_DEPLOYMENT_GUIDE.md",
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

/**
 * Phase 20 honesty CI gates.
 *
 * These rules MUST hold for the operator-workspace surface:
 *
 *   * no websocket / EventSource / socket.io import — the frontend
 *     remains static-only;
 *   * no source file fabricates a "bag_backed: true" literal;
 *   * every page renders the SafetyBoundaryBanner via the root
 *     layout (re-asserts the Phase 19 invariant);
 *   * every workspace preset is paired with a deterministic JSON
 *     shape (no drag-drop persistence).
 */

import { describe, it, expect } from "vitest";
import { promises as fs } from "node:fs";
import * as path from "node:path";

const SRC_ROOT = path.resolve(__dirname, "../src");

async function* walk(dir: string): AsyncGenerator<string> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(full);
    } else if (
      entry.isFile() &&
      (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx"))
    ) {
      yield full;
    }
  }
}

describe("Phase 20 honesty rules", () => {
  it("no source file imports a websocket / EventSource / socket.io module", async () => {
    const forbidden = [
      "socket.io-client",
      "socket.io",
      "ws",
      "node:ws",
      "reconnecting-websocket",
      "eventsource",
    ];
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      for (const token of forbidden) {
        expect(
          text.includes(`from "${token}"`) ||
            text.includes(`from '${token}'`),
          `${file} must not import ${token}`,
        ).toBe(false);
      }
    }
  });

  it("no source file calls new WebSocket(", async () => {
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      expect(
        /\bnew\s+WebSocket\s*\(/.test(text),
        `${file} must not call new WebSocket(`,
      ).toBe(false);
    }
  });

  it("no source file calls new EventSource(", async () => {
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      expect(
        /\bnew\s+EventSource\s*\(/.test(text),
        `${file} must not call new EventSource(`,
      ).toBe(false);
    }
  });

  it("no source file hard-codes bag_backed: true", async () => {
    for await (const file of walk(SRC_ROOT)) {
      // Fixtures + tests carry test data; the bag_backed field is
      // honestly false in every committed fixture today. The rule
      // forbids fabricating a `bag_backed: true` literal inside
      // production source.
      if (file.includes("/__fixtures__/")) continue;
      const text = await fs.readFile(file, "utf-8");
      expect(
        /bag_backed\s*:\s*true\b/.test(text),
        `${file} must not hard-code bag_backed: true`,
      ).toBe(false);
    }
  });

  it("the SafetyBoundaryBanner remains mounted by the root layout", async () => {
    const layout = await fs.readFile(
      path.resolve(SRC_ROOT, "app/layout.tsx"),
      "utf-8",
    );
    expect(layout).toContain("SafetyBoundaryBanner");
  });

  it("workspace presets are deterministic JSON shapes (no setters)", async () => {
    const presets = await fs.readFile(
      path.resolve(SRC_ROOT, "workspaces/presets.ts"),
      "utf-8",
    );
    // The presets module exports `WorkspacePreset` constants; it
    // must never `setX(...)` mutate a preset at runtime.
    expect(presets).not.toMatch(/Object\.assign\(\s*WORKSPACE_PRESETS/);
    expect(presets).not.toMatch(/Object\.defineProperty/);
  });

  it("telemetry panels never imply live telemetry in their text", async () => {
    const telemetryDir = path.resolve(SRC_ROOT, "components/telemetry");
    const files = await fs.readdir(telemetryDir);
    for (const name of files) {
      if (!name.endsWith(".tsx")) continue;
      const text = await fs.readFile(path.join(telemetryDir, name), "utf-8");
      // Allowed: "rehearsal_runtime" appears as a derivation source
      // — we only forbid the marketing words.
      expect(/\blive\s+telemetry\b/i.test(text)).toBe(false);
      expect(/\bstreaming\b/i.test(text)).toBe(false);
      expect(/realtime/i.test(text)).toBe(false);
    }
  });

  it("velocity-command panel always names /cmd_vel as forbidden", async () => {
    const text = await fs.readFile(
      path.resolve(SRC_ROOT, "components/telemetry/VelocityCommandPanel.tsx"),
      "utf-8",
    );
    expect(text.includes("forbidden · /cmd_vel")).toBe(true);
  });

  it("the reviewer walkthrough exposes ten steps", async () => {
    const text = await fs.readFile(
      path.resolve(SRC_ROOT, "reviewer/steps.ts"),
      "utf-8",
    );
    const count = (text.match(/\bindex:\s*\d+/g) || []).length;
    expect(count).toBe(10);
  });
});

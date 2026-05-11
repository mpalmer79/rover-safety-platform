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

describe("Phase 18 honesty rules", () => {
  it("never imports a websocket / streaming / socket.io client", async () => {
    const forbidden = [
      "socket.io-client",
      "socket.io",
      "ws",
      "engine.io-client",
      "eventsource",
      "@stomp/stompjs",
      "mqtt",
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

  it("never uses raw WebSocket / EventSource constructors", async () => {
    const forbiddenPatterns = [
      /\bnew\s+WebSocket\s*\(/,
      /\bnew\s+EventSource\s*\(/,
    ];
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      for (const pat of forbiddenPatterns) {
        expect(pat.test(text), `${file} must not construct ${pat}`).toBe(false);
      }
    }
  });

  it("never polls with setInterval inside src/", async () => {
    // setInterval would imply a continuous animation / polling loop.
    // Phase 18 scenes are deterministic and re-render only when the
    // scrubber index or playback mode changes. Allow `setTimeout`
    // because Next.js + Vitest call it indirectly through their own
    // runtimes.
    for await (const file of walk(SRC_ROOT)) {
      const text = await fs.readFile(file, "utf-8");
      expect(
        /\bsetInterval\s*\(/.test(text),
        `${file} must not call setInterval`,
      ).toBe(false);
    }
  });

  it("3d scene components surface the derivation source", async () => {
    const sceneFile = path.join(SRC_ROOT, "3d", "MissionScene.tsx");
    const text = await fs.readFile(sceneFile, "utf-8");
    expect(text).toContain("describeDerivationSource");
    expect(text).toContain("scene-derivation");
  });

  it("3d module never parses bag files or imports rosbag2", async () => {
    const forbidden = [
      "rosbag2",
      "@mcap/core",
      "@mcap/nodejs",
      "mcap",
    ];
    for await (const file of walk(path.join(SRC_ROOT, "3d"))) {
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

  it("the canonical registry JSON never lists a bag_backed record without samples", async () => {
    const registryPath = path.resolve(
      __dirname,
      "../../..",
      "spatial-replay",
      "registry",
      "canonical-artifacts.json",
    );
    const data = JSON.parse(await fs.readFile(registryPath, "utf-8"));
    for (const record of data.records as Array<{
      derivation_source: string;
      bag_status: string;
      files: Array<{ relative_path: string }>;
    }>) {
      if (record.derivation_source === "bag_backed") {
        expect(record.bag_status).toBe("bag_backed");
        // Resolve the artefact's spatial-replay.json and confirm
        // sample_count > 0. This mirrors the CI honesty grep.
        const replayFile = record.files.find((f) =>
          f.relative_path.endsWith("spatial-replay.json"),
        );
        expect(replayFile).toBeDefined();
        const replayPath = path.resolve(
          __dirname,
          "../../..",
          replayFile!.relative_path,
        );
        const replay = JSON.parse(await fs.readFile(replayPath, "utf-8"));
        expect(replay.sample_count).toBeGreaterThan(0);
      } else {
        expect(record.bag_status).not.toBe("bag_backed");
      }
    }
  });

  it("the canonical registry JSON's expected_hash matches the bytes on disk", async () => {
    const crypto = await import("node:crypto");
    const registryPath = path.resolve(
      __dirname,
      "../../..",
      "spatial-replay",
      "registry",
      "canonical-artifacts.json",
    );
    const data = JSON.parse(await fs.readFile(registryPath, "utf-8"));
    for (const record of data.records as Array<{
      files: Array<{ relative_path: string; expected_hash: string }>;
    }>) {
      for (const f of record.files) {
        const abs = path.resolve(__dirname, "../../..", f.relative_path);
        const bytes = await fs.readFile(abs);
        const h = crypto.createHash("sha256").update(bytes).digest("hex");
        expect(h).toBe(f.expected_hash);
      }
    }
  });
});

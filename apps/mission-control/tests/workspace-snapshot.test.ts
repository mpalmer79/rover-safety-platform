/**
 * Phase 20B workspace snapshot tests.
 *
 * Pin:
 *   * deterministic serialization (hash is stable under repeat calls);
 *   * hash changes only when meaningful fields change;
 *   * parser rejects malformed JSON and reports hash drift;
 *   * canonical fixtures validate successfully.
 */

import { describe, it, expect } from "vitest";

import {
  CANONICAL_SNAPSHOT_FIXTURES,
  parseWorkspaceSnapshot,
  serializeWorkspaceSnapshot,
  snapshotToJsonString,
  validateWorkspaceSnapshot,
  computeSnapshotHash,
} from "@/workspaces/snapshot";

const BASE_INPUT = {
  presetId: "mission-review" as const,
  missionId: "warehouse_pickup_route_alpha",
  replayRunId: "canonical-fixture",
  selectedEventId: null,
  selectedPanelIds: ["mission-telemetry", "event-stream"] as const,
  walkthroughStep: null,
  cameraMode: "follow" as const,
  evidenceFocus: { kind: "spatial-replay" as const, ref: "x.json" },
  theme: "dark" as const,
  density: "standard" as const,
  capturedAtUtc: null,
};

describe("workspace snapshot", () => {
  it("serializes deterministically", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    const b = serializeWorkspaceSnapshot(BASE_INPUT);
    expect(a.snapshotHash).toBe(b.snapshotHash);
    expect(snapshotToJsonString(a)).toBe(snapshotToJsonString(b));
  });

  it("hash changes when a meaningful field changes", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    const b = serializeWorkspaceSnapshot({ ...BASE_INPUT, missionId: "x" });
    expect(a.snapshotHash).not.toBe(b.snapshotHash);
  });

  it("capturedAtUtc never affects the hash", () => {
    const a = serializeWorkspaceSnapshot({ ...BASE_INPUT, capturedAtUtc: null });
    const b = serializeWorkspaceSnapshot({
      ...BASE_INPUT,
      capturedAtUtc: "2026-05-12T00:00:00Z",
    });
    expect(a.snapshotHash).toBe(b.snapshotHash);
  });

  it("panel id order does not affect the hash", () => {
    const a = serializeWorkspaceSnapshot({
      ...BASE_INPUT,
      selectedPanelIds: ["mission-telemetry", "event-stream"],
    });
    const b = serializeWorkspaceSnapshot({
      ...BASE_INPUT,
      selectedPanelIds: ["event-stream", "mission-telemetry"],
    });
    expect(a.snapshotHash).toBe(b.snapshotHash);
  });

  it("carries the verbatim disclaimer", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    expect(a.disclaimer).toContain("Simulation-only");
    expect(a.disclaimer).toContain("not safety-certified");
  });

  it("validates a freshly serialized snapshot", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    const result = validateWorkspaceSnapshot(a);
    expect(result.ok).toBe(true);
    expect(result.snapshot).not.toBeNull();
  });

  it("detects hash drift after tampering", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    const tampered = { ...a, missionId: "tampered" };
    const result = validateWorkspaceSnapshot(tampered);
    expect(result.ok).toBe(false);
    expect(result.issues.some((i) => i.field === "snapshotHash")).toBe(true);
  });

  it("parses canonical JSON round-trip", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    const json = snapshotToJsonString(a);
    const parsed = parseWorkspaceSnapshot(json);
    expect(parsed.ok).toBe(true);
    expect(parsed.snapshot?.snapshotHash).toBe(a.snapshotHash);
  });

  it("reports malformed JSON honestly", () => {
    const result = parseWorkspaceSnapshot("{ not valid }");
    expect(result.ok).toBe(false);
    expect(result.issues[0].field).toBe("$");
  });

  it("rejects an unknown preset id", () => {
    const result = validateWorkspaceSnapshot({
      ...serializeWorkspaceSnapshot(BASE_INPUT),
      presetId: "not-a-real-preset",
    });
    expect(result.ok).toBe(false);
  });

  it("every canonical fixture validates", () => {
    for (const snapshot of Object.values(CANONICAL_SNAPSHOT_FIXTURES)) {
      const result = validateWorkspaceSnapshot(snapshot);
      expect(result.ok, result.issues.map((i) => i.message).join(", ")).toBe(true);
    }
  });

  it("computeSnapshotHash matches the serialized hash", () => {
    const a = serializeWorkspaceSnapshot(BASE_INPUT);
    expect(a.snapshotHash).toBe(computeSnapshotHash(a));
  });
});

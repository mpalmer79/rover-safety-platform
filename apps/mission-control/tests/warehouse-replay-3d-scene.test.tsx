/**
 * Regression guards for the /demo/warehouse-replay 3D scene.
 *
 * The route had a recurring failure where a render-time throw inside
 * @react-three/fiber would escape to DemoErrorBoundary and silently
 * replace the 3D scene with the static summary. These tests pin the
 * non-fallback render path, the input-validity invariants, and the
 * shape of the bufferAttribute usage that caused the most recent
 * regression (Three.js r163+ no longer accepts
 * `<bufferAttribute array={...} count={...} itemSize={...} />` —
 * the constructor must be invoked via `args={[arr, itemSize]}`).
 */

import * as fs from "node:fs";
import * as path from "node:path";

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/demo/warehouse-replay",
}));

import {
  coerceSpatialReplayArtifact,
  type SpatialReplayRaw,
} from "@/adapters/loader";
import type { RehearsalAudit } from "@/adapters/types";
import { buildMissionRouteFromArtifact } from "@/adapters/spatial";

import auditJson from "@/app/demo/warehouse-replay/data/rehearsal-audit.json";
import spatialJson from "@/app/demo/warehouse-replay/data/spatial-replay.json";
import { DemoErrorBoundary } from "@/app/demo/warehouse-replay/DemoErrorBoundary";
import { DEMO_MISSION } from "@/app/demo/warehouse-replay/sample-demo-mission";

const audit = auditJson as unknown as RehearsalAudit;
const spatialReplay = coerceSpatialReplayArtifact(
  spatialJson as unknown as SpatialReplayRaw,
);

const baseProps = {
  descriptor: DEMO_MISSION,
  plan: audit.plan,
  events: audit.runtime?.events ?? [],
  spatialReplay,
  evidenceLinks: [
    { label: "Open mission audit", href: "/missions/test" },
  ],
} as const;

describe("/demo/warehouse-replay 3D scene render path", () => {
  it("renders the interactive demo (not the static summary) when given valid inputs", () => {
    render(<DemoErrorBoundary {...baseProps} />);
    expect(screen.queryByTestId("demo-static-summary")).toBeNull();
    expect(screen.getByTestId("demo-play-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("demo-scrubber")).toBeInTheDocument();
    expect(screen.getByTestId("demo-restart")).toBeInTheDocument();
  });

  it("falls back to the static summary only when the rendered child throws", () => {
    function Boom(): JSX.Element {
      throw new Error("intentional 3D scene render error");
    }
    // Compose the error boundary class directly with a throwing child
    // to verify the boundary still captures real errors.
    class TestBoundary extends DemoErrorBoundary {
      render() {
        if (this.state.hasError) {
          return super.render();
        }
        return <Boom />;
      }
    }
    render(<TestBoundary {...baseProps} />);
    const summary = screen.getByTestId("demo-static-summary");
    expect(summary).toBeInTheDocument();
    expect(summary.getAttribute("data-fallback-reason")).toBe("render-error");
    expect(summary.getAttribute("data-fallback-error") ?? "").toMatch(
      /intentional 3D scene render error/,
    );
  });
});

describe("/demo/warehouse-replay scene inputs", () => {
  it("the canonical bundled fixture coerces into a non-null artifact", () => {
    expect(spatialReplay).not.toBeNull();
    expect(spatialReplay?.samples.length ?? 0).toBeGreaterThan(0);
  });

  it("the route built from the canonical fixture has finite waypoint coordinates", () => {
    expect(spatialReplay).not.toBeNull();
    const route = buildMissionRouteFromArtifact(spatialReplay!);
    expect(route.waypoints.length).toBeGreaterThan(0);
    for (const w of route.waypoints) {
      expect(Number.isFinite(w.position.x)).toBe(true);
      expect(Number.isFinite(w.position.y)).toBe(true);
      expect(Number.isFinite(w.heading_deg)).toBe(true);
    }
    expect(Number.isFinite(route.bounds.min.x)).toBe(true);
    expect(Number.isFinite(route.bounds.min.y)).toBe(true);
    expect(Number.isFinite(route.bounds.max.x)).toBe(true);
    expect(Number.isFinite(route.bounds.max.y)).toBe(true);
  });

  it("event-alignment marker positions are finite or null", () => {
    expect(spatialReplay).not.toBeNull();
    for (const a of spatialReplay!.event_alignments) {
      if (a.spatial_position) {
        expect(Number.isFinite(a.spatial_position[0])).toBe(true);
        expect(Number.isFinite(a.spatial_position[1])).toBe(true);
      }
    }
  });
});

describe("Three.js r163+ buffer-attribute compatibility", () => {
  // Three.js r163 changed BufferAttribute.array to a strict setter
  // that requires matching dimensions. Setting `array` and `itemSize`
  // as separate JSX props on `<bufferAttribute>` no longer reconciles
  // correctly under r163+ and throws at render time in production
  // builds — the exact failure mode that put /demo/warehouse-replay
  // into its DemoErrorBoundary on Vercel. The constructor MUST be
  // invoked via `args={[array, itemSize]}` instead.
  it("ReplayTrajectory3D constructs bufferAttribute via args={[positions, 3]}", () => {
    const src = fs.readFileSync(
      path.resolve(
        __dirname,
        "../src/3d/ReplayTrajectory3D.tsx",
      ),
      "utf-8",
    );
    expect(src).toMatch(/<bufferAttribute[\s\S]*?args=\{\[positions, 3\]\}/);
    expect(src).not.toMatch(
      /<bufferAttribute[\s\S]*?\barray=\{[\s\S]*?\bitemSize=\{/,
    );
  });

  it("no 3D component uses the legacy <bufferAttribute array=.. itemSize=..> form", () => {
    const dir = path.resolve(__dirname, "../src/3d");
    const files = fs
      .readdirSync(dir)
      .filter((f) => f.endsWith(".tsx") || f.endsWith(".ts"));
    for (const f of files) {
      const src = fs.readFileSync(path.join(dir, f), "utf-8");
      const legacy =
        /<bufferAttribute\b[\s\S]*?\barray=\{[\s\S]*?\bitemSize=\{/.exec(src);
      expect(
        legacy,
        `${f} uses the legacy <bufferAttribute array=.. itemSize=..> form; ` +
          "Three.js r163+ requires args={[array, itemSize]}",
      ).toBeNull();
    }
  });
});

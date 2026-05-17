"use client";

import dynamic from "next/dynamic";
import { ArrowRight, PlayCircle } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  coerceSpatialReplayArtifact,
  type SpatialReplayRaw,
} from "@/adapters/spatial-coerce";
import {
  buildMissionRouteFromArtifact,
  projectArtifactEvent,
  type SpatialEventMarker,
} from "@/adapters/spatial";
import type { RehearsalAudit } from "@/adapters/types";

import type { PlaybackMode } from "@/3d/types";

import auditJson from "@/app/demo/warehouse-replay/data/rehearsal-audit.json";
import spatialJson from "@/app/demo/warehouse-replay/data/spatial-replay.json";
import { DEMO_MISSION } from "@/app/demo/warehouse-replay/sample-demo-mission";

import { AnimatedMissionPreview } from "./AnimatedMissionPreview";

/**
 * The hero preview that runs on /start.
 *
 * - On WebGL-capable browsers it embeds the real WarehouseDemoScene
 *   in a compact frame so the homepage shows the actual 3D mission
 *   replay, not just an illustration.
 * - On browsers without WebGL it falls back to the SVG mission
 *   preview so the page never shows an empty box.
 */

const audit = auditJson as unknown as RehearsalAudit;
const spatialReplay = coerceSpatialReplayArtifact(
  spatialJson as unknown as SpatialReplayRaw,
);
const route = spatialReplay
  ? buildMissionRouteFromArtifact(spatialReplay)
  : null;
const events = audit.runtime?.events ?? [];
const markers: readonly SpatialEventMarker[] = route
  ? events.map((e) => projectArtifactEvent(e, route))
  : [];
const zones = DEMO_MISSION.zones.map((z) => ({
  id: z.id,
  label: z.label,
  tone: z.tone,
  center: z.center,
  half: z.half,
}));

const WarehouseDemoScene = dynamic(
  () => import("@/3d/WarehouseDemoScene").then((m) => m.WarehouseDemoScene),
  { ssr: false, loading: () => <PreviewSkeleton /> },
);

const PREVIEW_SECONDS = 14;
const CAMERA_HOLD_SECONDS = 7;

const BEATS: ReadonlyArray<{ at: number; label: string; tone: "info" | "ok" | "warn" }> = [
  { at: 0.0, label: "Route loaded", tone: "info" },
  { at: 0.2, label: "Validator · bounded", tone: "info" },
  { at: 0.38, label: "Supervisor check", tone: "warn" },
  { at: 0.52, label: "Approved · /cmd_vel_requested", tone: "ok" },
  { at: 0.78, label: "Pickup waypoint reached", tone: "info" },
  { at: 0.95, label: "Replay artifact sealed", tone: "ok" },
];

const CAMERA_CYCLE: readonly PlaybackMode[] = [
  "overview",
  "trajectory_analysis",
  "operator_review",
];

const TONE_CLASS: Record<"info" | "ok" | "warn", string> = {
  info: "border-cyan-400/40 text-cyan-100 bg-cyan-400/10",
  ok: "border-emerald-400/50 text-emerald-100 bg-emerald-400/10",
  warn: "border-amber-300/50 text-amber-100 bg-amber-300/10",
};

export function HeroMissionPreview() {
  const [webglAvailable, setWebglAvailable] = useState<boolean | null>(null);
  const [phase, setPhase] = useState(0);
  const [cameraMode, setCameraMode] = useState<PlaybackMode>("overview");
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);
  const prefersReducedMotion = useRef(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("webgl2") || canvas.getContext("webgl");
      setWebglAvailable(Boolean(ctx));
    } catch {
      setWebglAvailable(false);
    }
    if (typeof window.matchMedia === "function") {
      prefersReducedMotion.current = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
    }
  }, []);

  const tick = useCallback((now: number) => {
    if (startRef.current === null) startRef.current = now;
    const elapsed = (now - startRef.current) / 1000;
    const p = (elapsed % PREVIEW_SECONDS) / PREVIEW_SECONDS;
    setPhase(p);
    const slot = Math.floor(elapsed / CAMERA_HOLD_SECONDS) % CAMERA_CYCLE.length;
    setCameraMode((current) =>
      current === CAMERA_CYCLE[slot] ? current : CAMERA_CYCLE[slot],
    );
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  useEffect(() => {
    if (webglAvailable !== true) return;
    if (prefersReducedMotion.current) {
      setPhase(0.45);
      setCameraMode("overview");
      return;
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      startRef.current = null;
    };
  }, [tick, webglAvailable]);

  if (webglAvailable === false || !route) {
    return <FallbackFrame />;
  }

  const interpolated = computeRoverPose(route, phase);
  const activeEventIdx =
    events.length === 0
      ? 0
      : Math.min(events.length - 1, Math.floor(phase * events.length));
  const reachedBeats = BEATS.filter((b) => phase >= b.at);
  const latestBeat = reachedBeats[reachedBeats.length - 1] ?? BEATS[0];
  const visibleBeats = reachedBeats.slice(-2);

  return (
    <div className="relative">
      <div
        data-testid="hero-mission-preview"
        className="relative overflow-hidden rounded-xl border border-cyan-400/15 shadow-[0_24px_60px_-24px_rgba(0,0,0,0.6)]"
      >
        <div
          className="relative"
          style={{ aspectRatio: "16 / 11" }}
        >
          <div className="absolute inset-0">
            <WarehouseDemoScene
              route={route}
              markers={markers}
              roverPosition={interpolated.position}
              roverHeadingDeg={interpolated.headingDeg}
              activeIndex={activeEventIdx}
              highlightWaypointIdx={interpolated.sampleIdx}
              moving
              zones={zones}
              height="100%"
              playbackMode={cameraMode}
            />
          </div>

          {/* Mobile / narrow: a single rotating chip in the top-left
              so labels never stack over the rover. The camera-mode
              chip already lives in the top-right (rendered by
              WarehouseDemoScene). */}
          <div className="pointer-events-none absolute left-3 top-3 sm:hidden">
            <span
              data-testid="hero-preview-beat"
              className={`inline-flex max-w-[180px] items-center gap-1.5 truncate rounded-md border px-2 py-0.5 font-mono text-[10px] backdrop-blur-sm ${TONE_CLASS[latestBeat.tone]}`}
            >
              <span aria-hidden className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
              <span className="truncate">{latestBeat.label}</span>
            </span>
          </div>

          {/* Desktop / wide: up to two stacked chips on the left edge.
              Capped width so they never crowd the right-side scene
              badges or the rover. */}
          <div className="pointer-events-none absolute left-3 top-3 hidden max-w-[60%] flex-col gap-1.5 sm:flex">
            {visibleBeats.map((beat) => (
              <span
                key={beat.label}
                data-testid="hero-preview-beat"
                className={`inline-flex max-w-full items-center gap-1.5 truncate rounded-md border px-2 py-0.5 font-mono text-[10px] backdrop-blur-sm ${TONE_CLASS[beat.tone]}`}
              >
                <span aria-hidden className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
                <span className="truncate">{beat.label}</span>
              </span>
            ))}
          </div>
        </div>
        <Link
          href="/demo/warehouse-replay"
          data-testid="hero-preview-cta"
          className="group absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-md border border-emerald-400/70 bg-gradient-to-b from-emerald-400/45 to-emerald-500/20 px-3 py-1.5 text-xs font-semibold text-emerald-50 shadow-[0_8px_24px_-12px_rgba(60,180,168,0.5)] backdrop-blur-sm transition-all hover:from-emerald-400/55 hover:to-emerald-500/30 hover:shadow-[0_12px_28px_-12px_rgba(60,180,168,0.6)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300"
        >
          <PlayCircle aria-hidden className="h-3.5 w-3.5" />
          Open full replay
          <ArrowRight
            aria-hidden
            className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5"
          />
        </Link>
      </div>
      <p className="mt-2 text-[10px] uppercase tracking-[0.18em] text-cyan-300/70">
        Live in-page preview · deterministic canonical-fixture artifact
      </p>
    </div>
  );
}

function FallbackFrame() {
  return (
    <div className="relative">
      <div data-testid="hero-mission-preview" data-mode="svg-fallback">
        <AnimatedMissionPreview />
      </div>
      <Link
        href="/demo/warehouse-replay"
        data-testid="hero-preview-cta"
        className="group absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-md border border-emerald-400/70 bg-gradient-to-b from-emerald-400/45 to-emerald-500/20 px-3 py-1.5 text-xs font-semibold text-emerald-50 shadow-[0_8px_24px_-12px_rgba(60,180,168,0.5)] backdrop-blur-sm transition-all hover:from-emerald-400/55 hover:to-emerald-500/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300"
      >
        <PlayCircle aria-hidden className="h-3.5 w-3.5" />
        Open full replay
        <ArrowRight
          aria-hidden
          className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5"
        />
      </Link>
      <p className="mt-2 text-[10px] uppercase tracking-[0.18em] text-cyan-300/70">
        Schematic preview · deterministic canonical-fixture artifact
      </p>
    </div>
  );
}

function PreviewSkeleton() {
  return (
    <div
      data-testid="hero-mission-preview-skeleton"
      className="relative overflow-hidden rounded-xl border border-cyan-400/15"
      style={{ aspectRatio: "16 / 11", background: "#070a12" }}
    >
      <div
        aria-hidden
        className="absolute inset-0 animate-pulse opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(95,229,214,0.18) 1px, transparent 1px), linear-gradient(90deg, rgba(95,229,214,0.18) 1px, transparent 1px)",
          backgroundSize: "40px 40px, 40px 40px",
        }}
      />
      <p className="absolute inset-0 flex items-center justify-center font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-200/80">
        Loading mission scene…
      </p>
    </div>
  );
}

function computeRoverPose(
  route: ReturnType<typeof buildMissionRouteFromArtifact>,
  phase: number,
): { position: { x: number; y: number }; headingDeg: number; sampleIdx: number } {
  if (route.waypoints.length === 0) {
    return { position: { x: 0, y: 0 }, headingDeg: 0, sampleIdx: 0 };
  }
  if (route.waypoints.length === 1) {
    const wp = route.waypoints[0];
    return { position: wp.position, headingDeg: wp.heading_deg, sampleIdx: 0 };
  }
  const totalSegments = route.waypoints.length - 1;
  const segmentPos = phase * totalSegments;
  const fromIdx = Math.min(totalSegments - 1, Math.floor(segmentPos));
  const t = segmentPos - fromIdx;
  const a = route.waypoints[fromIdx];
  const b = route.waypoints[fromIdx + 1];
  const x = a.position.x + (b.position.x - a.position.x) * t;
  const y = a.position.y + (b.position.y - a.position.y) * t;
  let dHeading = b.heading_deg - a.heading_deg;
  while (dHeading > 180) dHeading -= 360;
  while (dHeading < -180) dHeading += 360;
  const headingDeg = a.heading_deg + dHeading * t;
  return {
    position: { x, y },
    headingDeg,
    sampleIdx: t < 0.5 ? fromIdx : fromIdx + 1,
  };
}

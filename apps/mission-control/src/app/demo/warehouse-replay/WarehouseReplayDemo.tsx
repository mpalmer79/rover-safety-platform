"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  buildMissionRouteFromArtifact,
  projectArtifactEvent,
  selectMissionRoute,
} from "@/adapters/spatial";
import type { SpatialEventMarker } from "@/adapters/spatial";
import type {
  MissionPlan,
  RehearsalEvent,
  SpatialReplayArtifact,
} from "@/adapters/types";
import { Panel } from "@/components/Panel";
import { GradientPanel } from "@/components/GradientPanel";

import type { DemoMissionDescriptor } from "./sample-demo-mission";

const WarehouseDemoScene = dynamic(
  () => import("@/3d/WarehouseDemoScene").then((m) => m.WarehouseDemoScene),
  { ssr: false, loading: () => <ScenePlaceholder /> },
);

interface WarehouseReplayDemoProps {
  descriptor: DemoMissionDescriptor;
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
  spatialReplay: SpatialReplayArtifact | null;
  evidenceLinks: ReadonlyArray<{ label: string; href: string }>;
}

const PLAYBACK_SECONDS = 12; // wall-clock duration of one play loop

const TONE_COLOR: Record<DemoMissionDescriptor["beats"][number]["tone"], string> = {
  info: "border-[color:var(--mc-accent)] text-[color:var(--mc-accent)]",
  validate: "border-status-completed text-status-completed",
  supervise: "border-status-pending text-status-pending",
  complete: "border-status-completed text-status-completed",
};

export function WarehouseReplayDemo({
  descriptor,
  plan,
  events,
  spatialReplay,
  evidenceLinks,
}: WarehouseReplayDemoProps) {
  const route = useMemo(() => {
    if (
      spatialReplay &&
      spatialReplay.samples &&
      spatialReplay.samples.length > 0
    ) {
      return buildMissionRouteFromArtifact(spatialReplay);
    }
    return selectMissionRoute(plan, spatialReplay);
  }, [plan, spatialReplay]);

  const markers = useMemo<readonly SpatialEventMarker[]>(
    () => events.map((e) => projectArtifactEvent(e, route)),
    [events, route],
  );

  const [phase, setPhase] = useState(0); // 0..1
  const [playing, setPlaying] = useState(true);
  const [webglAvailable, setWebglAvailable] = useState<boolean | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTickRef = useRef<number | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const canvas = document.createElement("canvas");
      const ctx =
        canvas.getContext("webgl2") || canvas.getContext("webgl");
      setWebglAvailable(Boolean(ctx));
    } catch {
      setWebglAvailable(false);
    }
  }, []);

  const tick = useCallback((now: number) => {
    if (lastTickRef.current === null) lastTickRef.current = now;
    const dt = (now - lastTickRef.current) / 1000;
    lastTickRef.current = now;
    setPhase((p) => {
      const next = p + dt / PLAYBACK_SECONDS;
      return next >= 1 ? 0 : next;
    });
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  useEffect(() => {
    if (!playing) {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastTickRef.current = null;
      return;
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastTickRef.current = null;
    };
  }, [playing, tick]);

  const samples = spatialReplay?.samples ?? [];
  const sampleCount = samples.length;

  const interpolated = useMemo(() => {
    if (route.waypoints.length === 0) {
      return {
        position: { x: 0, y: 0 },
        headingDeg: 0,
        sampleIdx: 0,
      };
    }
    if (route.waypoints.length === 1 || sampleCount <= 1) {
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
  }, [phase, route.waypoints, sampleCount]);

  const activeEventIndex = useMemo(() => {
    if (events.length === 0) return 0;
    return Math.min(events.length - 1, Math.floor(phase * events.length));
  }, [events.length, phase]);

  const activeBeat = useMemo(() => {
    if (descriptor.beats.length === 0) return null;
    let chosen = descriptor.beats[0];
    for (const beat of descriptor.beats) {
      if (phase >= beat.at) chosen = beat;
    }
    return chosen;
  }, [descriptor.beats, phase]);

  const sceneZones = useMemo(
    () =>
      descriptor.zones.map((z) => ({
        id: z.id,
        label: z.label,
        tone: z.tone,
        center: z.center,
        half: z.half,
      })),
    [descriptor.zones],
  );

  const onScrub = useCallback((value: number) => {
    setPhase(value);
    setPlaying(false);
  }, []);

  return (
    <div className="space-y-6">
      <GradientPanel
        tone="accent"
        elevated
        className="px-5 py-5 sm:px-6 sm:py-6"
      >
        <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1">
            <p className="label">Mission Replay Demo</p>
            <h1 className="display-1">{descriptor.title}</h1>
            <p className="text-base text-[color:var(--mc-text)]">
              {descriptor.subtitle}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-1.5 text-xs font-mono text-[color:var(--mc-text)]">
              <ShieldCheck aria-hidden className="h-3.5 w-3.5 text-[color:var(--mc-accent)]" />
              simulation only · supervisor authority preserved
            </span>
          </div>
        </div>
      </GradientPanel>

      <div className="grid gap-5 lg:grid-cols-[1.45fr_1fr]">
        <div className="space-y-4">
          {webglAvailable === false ? (
            <FallbackScene route={route} />
          ) : (
            <div
              className="relative w-full"
              style={{ aspectRatio: "16 / 9", minHeight: 420 }}
            >
              <div className="absolute inset-0">
                <WarehouseDemoScene
                  route={route}
                  markers={markers}
                  roverPosition={interpolated.position}
                  roverHeadingDeg={interpolated.headingDeg}
                  activeIndex={activeEventIndex}
                  highlightWaypointIdx={interpolated.sampleIdx}
                  moving={playing}
                  zones={sceneZones}
                  height="100%"
                />
              </div>
            </div>
          )}

          <Panel
            eyebrow="Replay controls"
            title="Deterministic playback"
            trailing={
              <span
                data-testid="demo-progress-readout"
                className="font-mono text-xs text-[color:var(--mc-text-muted)]"
              >
                step {Math.min(events.length, activeEventIndex + 1)} /{" "}
                {events.length}
              </span>
            }
          >
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  data-testid="demo-play-toggle"
                  aria-pressed={playing}
                  onClick={() => setPlaying((p) => !p)}
                  className="inline-flex items-center gap-2 rounded-md border border-[color:var(--mc-accent)] bg-[color:var(--mc-accent-soft)] px-3 py-1.5 text-sm font-semibold text-[color:var(--mc-accent)] hover:bg-[color:var(--mc-accent)] hover:text-[color:var(--mc-text-inverse)]"
                >
                  {playing ? (
                    <>
                      <Pause aria-hidden className="h-4 w-4" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play aria-hidden className="h-4 w-4" />
                      Play
                    </>
                  )}
                </button>
                <button
                  type="button"
                  data-testid="demo-restart"
                  onClick={() => {
                    setPhase(0);
                    setPlaying(true);
                  }}
                  className="inline-flex items-center gap-2 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-1.5 text-sm text-[color:var(--mc-text)] hover:border-[color:var(--mc-accent)]"
                >
                  <RotateCcw aria-hidden className="h-4 w-4" />
                  Restart
                </button>
              </div>
              <label className="flex flex-col gap-1 text-xs text-[color:var(--mc-text-muted)]">
                <span>Timeline</span>
                <input
                  type="range"
                  min={0}
                  max={1000}
                  value={Math.round(phase * 1000)}
                  data-testid="demo-scrubber"
                  onChange={(e) => onScrub(Number(e.target.value) / 1000)}
                  className="h-2 w-full cursor-pointer appearance-none rounded-full bg-[color:var(--mc-surface-overlay)] accent-[color:var(--mc-accent)]"
                  aria-label="Replay timeline"
                />
                <span className="text-[10px] font-mono">
                  {(phase * 100).toFixed(1)}% · waypoint{" "}
                  {Math.min(route.waypoints.length, interpolated.sampleIdx + 1)}{" "}
                  / {route.waypoints.length}
                </span>
              </label>
            </div>
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel
            eyebrow="What this proves"
            title="Reviewer summary"
          >
            <ul className="space-y-1.5 text-sm text-[color:var(--mc-text)]">
              <li>• Mission progress is reconstructed from committed replay artifacts.</li>
              <li>• Unsafe proposals are blocked before motion authority.</li>
              <li>• Approved motion stays bounded by the safety supervisor.</li>
              <li>• Replay evidence supports audit and review.</li>
            </ul>
          </Panel>

          <Panel
            eyebrow="Mission narrative"
            title={activeBeat?.title ?? "Mission proposed"}
            trailing={
              activeBeat ? (
                <span
                  data-testid="demo-beat-tone"
                  data-tone={activeBeat.tone}
                  className={
                    "rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide " +
                    TONE_COLOR[activeBeat.tone]
                  }
                >
                  {activeBeat.tone}
                </span>
              ) : null
            }
          >
            <p className="text-sm text-[color:var(--mc-text)]">
              {activeBeat?.description ?? descriptor.summary}
            </p>
            <ol className="mt-3 space-y-1 text-xs text-[color:var(--mc-text-muted)]">
              {descriptor.beats.map((beat) => {
                const reached = phase >= beat.at;
                return (
                  <li
                    key={beat.title}
                    className={
                      "flex items-center gap-2 " +
                      (reached
                        ? "text-[color:var(--mc-text)]"
                        : "text-[color:var(--mc-text-muted)]")
                    }
                  >
                    <span
                      className={
                        "inline-block h-1.5 w-1.5 rounded-full " +
                        (reached
                          ? "bg-[color:var(--mc-accent)]"
                          : "bg-[color:var(--mc-border-strong)]")
                      }
                    />
                    <span className="font-mono">
                      {Math.round(beat.at * 100)
                        .toString()
                        .padStart(2, "0")}
                      %
                    </span>
                    <span>{beat.title}</span>
                  </li>
                );
              })}
            </ol>
          </Panel>

          <Panel
            eyebrow="Mission summary"
            title="Where the data comes from"
          >
            <p className="text-sm text-[color:var(--mc-text)]">
              {descriptor.summary}
            </p>
          </Panel>

          {evidenceLinks.length > 0 ? (
            <Panel
              eyebrow="Evidence & audit"
              title="Open the supporting artifacts"
            >
              <ul className="space-y-1.5 text-sm">
                {evidenceLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="inline-flex items-center gap-1.5 text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
                    >
                      <ChevronRight aria-hidden className="h-3.5 w-3.5" />
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ScenePlaceholder() {
  return (
    <div
      data-testid="warehouse-demo-placeholder"
      className="flex w-full items-center justify-center rounded-lg border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] text-sm text-[color:var(--mc-text-muted)]"
      style={{ aspectRatio: "16 / 9", minHeight: 420 }}
    >
      Loading immersive mission scene…
    </div>
  );
}

function FallbackScene({ route }: { route: ReturnType<typeof selectMissionRoute> }) {
  return (
    <div
      data-testid="warehouse-demo-fallback"
      className="flex w-full flex-col gap-3 rounded-lg border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-4 py-4 text-sm text-[color:var(--mc-text)]"
      style={{ aspectRatio: "16 / 9", minHeight: 420 }}
    >
      <p className="label">2D fallback</p>
      <h2 className="display-2">WebGL is unavailable in this browser</h2>
      <p>
        The 3D scene has been replaced with a deterministic 2D summary of
        the same canonical replay artifact. Mission state, decisions,
        and evidence remain fully available below.
      </p>
      <ul className="font-mono text-xs">
        <li>• Waypoints: {route.waypoints.length}</li>
        <li>• Segments: {route.segments.length}</li>
        <li>• Derivation source: {route.derivation_source}</li>
      </ul>
    </div>
  );
}

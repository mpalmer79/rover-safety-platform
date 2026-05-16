"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

/**
 * Animated SVG mission preview shown in the landing hero.
 *
 * Deliberately lightweight — pure SVG + CSS/framer-motion, no
 * Three.js. The full 3D scene is one click away on /demo/warehouse-replay.
 * This preview signals "robotics platform" within the first viewport
 * without paying the cost of a Canvas init on the public landing page.
 */

const PATH_POINTS: Array<readonly [number, number]> = [
  [60, 220], // dock
  [120, 220],
  [200, 220],
  [280, 220], // aisle
  [340, 220],
  [380, 180],
  [400, 140], // pickup
  [380, 100],
  [340, 80],
  [280, 80],
  [200, 80],
  [120, 80],
  [60, 80], // return upper
];

const ROUTE_D = PATH_POINTS.map(([x, y], i) =>
  i === 0 ? `M${x},${y}` : `L${x},${y}`,
).join(" ");

interface StatusBeat {
  id: string;
  label: string;
  tone: "info" | "ok" | "warn";
  at: number;
}

const BEATS: readonly StatusBeat[] = [
  { id: "load", label: "Route loaded", tone: "info", at: 0.05 },
  { id: "validate", label: "Validator: bounded distance/angle/speed", tone: "info", at: 0.18 },
  { id: "supervise", label: "Supervisor authority check", tone: "warn", at: 0.35 },
  { id: "approve", label: "Approved · /cmd_vel_requested", tone: "ok", at: 0.5 },
  { id: "pickup", label: "Pickup waypoint reached", tone: "info", at: 0.72 },
  { id: "replay", label: "Replay artifact sealed", tone: "ok", at: 0.92 },
];

const TONE_CLASS: Record<StatusBeat["tone"], string> = {
  info: "border-cyan-400/40 text-cyan-200 bg-cyan-400/10",
  ok: "border-emerald-400/50 text-emerald-200 bg-emerald-400/10",
  warn: "border-amber-300/50 text-amber-200 bg-amber-300/10",
};

const TELEMETRY: ReadonlyArray<{ k: string; v: string }> = [
  { k: "mission_id", v: "warehouse_pickup_route_alpha" },
  { k: "supervisor", v: "ACTIVE_NORMAL" },
  { k: "topic", v: "/cmd_vel_requested" },
  { k: "speed_max", v: "0.30 m/s" },
  { k: "deterministic_hash", v: "f81c659d…" },
  { k: "replay_status", v: "sealed" },
];

const DURATION_S = 9.5;

export function AnimatedMissionPreview() {
  const reduce = useReducedMotion();
  const [phase, setPhase] = useState(reduce ? 1 : 0);

  useEffect(() => {
    if (reduce) {
      setPhase(1);
      return;
    }
    let raf = 0;
    let start = 0;
    const tick = (t: number) => {
      if (!start) start = t;
      const elapsed = (t - start) / 1000;
      const p = (elapsed % DURATION_S) / DURATION_S;
      setPhase(p);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [reduce]);

  // Interpolate rover position along the polyline.
  const roverPos = (() => {
    const segs = PATH_POINTS.length - 1;
    const u = phase * segs;
    const i = Math.min(segs - 1, Math.floor(u));
    const t = u - i;
    const a = PATH_POINTS[i];
    const b = PATH_POINTS[i + 1];
    return { x: a[0] + (b[0] - a[0]) * t, y: a[1] + (b[1] - a[1]) * t };
  })();

  const visibleBeats = BEATS.filter((b) => phase >= b.at).slice(-3);
  const telemetryIdx = Math.floor(phase * TELEMETRY.length) % TELEMETRY.length;

  return (
    <div
      data-testid="mission-preview"
      className="relative overflow-hidden rounded-xl border border-cyan-400/15 bg-[#070a12] shadow-[0_24px_60px_-24px_rgba(0,0,0,0.6)]"
      style={{ aspectRatio: "16 / 11" }}
    >
      <svg
        viewBox="0 0 460 280"
        className="absolute inset-0 h-full w-full"
        role="img"
        aria-label="Simulated warehouse mission preview with rover route and safety supervisor status"
      >
        <defs>
          <pattern id="grid-fine" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(60,180,168,0.08)" strokeWidth="0.5" />
          </pattern>
          <pattern id="grid-bold" width="100" height="100" patternUnits="userSpaceOnUse">
            <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(60,180,168,0.18)" strokeWidth="0.8" />
          </pattern>
          <radialGradient id="sweep" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(60,180,168,0.35)" />
            <stop offset="60%" stopColor="rgba(60,180,168,0.06)" />
            <stop offset="100%" stopColor="rgba(60,180,168,0)" />
          </radialGradient>
          <linearGradient id="ribbon" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3cb4a8" />
            <stop offset="60%" stopColor="#5fb0ff" />
            <stop offset="100%" stopColor="#a78bfa" />
          </linearGradient>
        </defs>

        <rect width="460" height="280" fill="url(#grid-fine)" />
        <rect width="460" height="280" fill="url(#grid-bold)" />

        {/* warehouse outline */}
        <rect
          x="20"
          y="36"
          width="420"
          height="226"
          rx="10"
          fill="none"
          stroke="rgba(94,123,255,0.22)"
          strokeWidth="1"
          strokeDasharray="2 6"
        />

        {/* restricted mezzanine zone */}
        <g>
          <rect x="160" y="120" width="240" height="42" rx="6" fill="rgba(239,68,68,0.10)" stroke="rgba(239,68,68,0.55)" strokeDasharray="4 4" />
          <text x="170" y="135" fill="rgba(252,165,165,0.85)" fontFamily="ui-monospace, monospace" fontSize="9">
            RESTRICTED · MEZZANINE
          </text>
          {!reduce ? (
            <motion.rect
              x="160"
              y="120"
              width="240"
              height="42"
              rx="6"
              fill="rgba(239,68,68,0.10)"
              animate={{ opacity: [0.0, 0.45, 0.0] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            />
          ) : null}
        </g>

        {/* radar sweep around current rover position */}
        {!reduce ? (
          <motion.circle
            cx={roverPos.x}
            cy={roverPos.y}
            r="32"
            fill="url(#sweep)"
            animate={{ opacity: [0.0, 0.7, 0.0] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
          />
        ) : null}

        {/* faint full route */}
        <path d={ROUTE_D} fill="none" stroke="rgba(60,180,168,0.25)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

        {/* drawn portion of route */}
        <motion.path
          d={ROUTE_D}
          fill="none"
          stroke="url(#ribbon)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ pathLength: phase }}
          initial={false}
        />

        {/* dock pad */}
        <rect x="40" y="206" width="40" height="28" rx="3" fill="rgba(60,180,168,0.16)" stroke="rgba(60,180,168,0.55)" />
        <text x="42" y="252" fill="rgba(190,225,221,0.9)" fontFamily="ui-monospace, monospace" fontSize="8">DOCK A</text>

        {/* pickup pad */}
        <circle cx="400" cy="140" r="10" fill="rgba(250,204,21,0.18)" stroke="rgba(250,204,21,0.7)" />
        <text x="376" y="118" fill="rgba(254,240,138,0.9)" fontFamily="ui-monospace, monospace" fontSize="8">PICKUP</text>

        {/* waypoint nodes */}
        {PATH_POINTS.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="1.8" fill="rgba(159,191,224,0.85)" />
        ))}

        {/* rover */}
        <g transform={`translate(${roverPos.x},${roverPos.y})`}>
          <circle r="6.5" fill="rgba(60,180,168,0.95)" />
          <circle r="11" fill="none" stroke="rgba(60,180,168,0.55)" strokeWidth="1" />
          <circle r="2.4" fill="#04111a" />
        </g>

        {/* corner brand mark */}
        <g opacity="0.85">
          <circle cx="34" cy="22" r="3.5" fill="#3cb4a8" />
          <text x="44" y="26" fill="rgba(214,233,231,0.9)" fontFamily="ui-monospace, monospace" fontSize="9" letterSpacing="0.08em">
            PROJECTBOUNDARY · MISSION CONTROL
          </text>
        </g>
      </svg>

      {/* overlay: status chips */}
      <div className="pointer-events-none absolute inset-x-3 top-3 flex flex-col gap-1.5">
        {visibleBeats.map((beat) => (
          <motion.span
            key={`${beat.id}-${visibleBeats.indexOf(beat)}`}
            initial={reduce ? false : { opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.45, ease: "easeOut" }}
            className={`inline-flex w-fit items-center gap-1.5 rounded-md border px-2 py-0.5 font-mono text-[10px] backdrop-blur-sm ${TONE_CLASS[beat.tone]}`}
          >
            <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />
            {beat.label}
          </motion.span>
        ))}
      </div>

      {/* overlay: telemetry feed */}
      <div
        className="pointer-events-none absolute inset-x-3 bottom-3 rounded-md border border-cyan-400/15 px-3 py-2 font-mono text-[10px] text-cyan-100/90 backdrop-blur-sm"
        style={{ background: "rgba(7, 10, 18, 0.55)" }}
      >
        <div className="flex items-center justify-between text-cyan-300/80">
          <span>TELEMETRY · simulated</span>
          <span>{Math.round(phase * 100)}%</span>
        </div>
        <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5">
          {TELEMETRY.map((row, idx) => (
            <div
              key={row.k}
              className={`flex items-center gap-2 transition-opacity duration-300 ${idx === telemetryIdx ? "opacity-100" : "opacity-55"}`}
            >
              <span className="text-cyan-400/70">{row.k}</span>
              <span className="truncate">{row.v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

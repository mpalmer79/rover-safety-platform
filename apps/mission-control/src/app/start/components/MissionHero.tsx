"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, PlayCircle, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { AnimatedMissionPreview } from "./AnimatedMissionPreview";
import { MiniRoverAccent } from "./MiniRoverAccent";

const STATS: ReadonlyArray<{ k: string; v: string }> = [
  { k: "Mission states", v: "validated · supervised · replayed" },
  { k: "Authority", v: "supervisor over /cmd_vel" },
  { k: "Evidence", v: "deterministic · hash-chained" },
];

export function MissionHero() {
  const reduce = useReducedMotion();
  const fade = (delay = 0) =>
    reduce
      ? { initial: false, animate: { opacity: 1, y: 0 } }
      : {
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.55, delay, ease: "easeOut" as const },
        };

  return (
    <section
      data-testid="mission-hero"
      className="relative overflow-hidden rounded-2xl border border-[color:var(--mc-border)] bg-gradient-to-br from-[#0b1220] via-[#0a121e] to-[#0c1a26] px-4 py-7 sm:px-7 sm:py-9 lg:px-10 lg:py-12"
    >
      {/* ambient grid wash */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.18]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(95,229,214,0.18) 1px, transparent 1px), linear-gradient(90deg, rgba(95,229,214,0.18) 1px, transparent 1px)",
          backgroundSize: "40px 40px, 40px 40px",
          maskImage:
            "radial-gradient(ellipse at top right, rgba(0,0,0,1) 0%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0) 100%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 right-[-10%] h-72 w-72 rounded-full bg-cyan-400/15 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 left-[-10%] h-72 w-72 rounded-full bg-indigo-400/10 blur-3xl"
      />

      <div className="relative grid items-center gap-7 lg:grid-cols-[1.05fr_1fr] lg:gap-10">
        <div className="space-y-5">
          <motion.div {...fade(0)} className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-400/40 bg-cyan-400/10 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-200">
              <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-cyan-300" />
              Mission Control · live preview
            </span>
            <span
              data-testid="hero-sim-chip"
              className="inline-flex items-center gap-1.5 rounded-full border border-amber-300/40 bg-amber-300/10 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.18em] text-amber-200"
            >
              <ShieldCheck aria-hidden className="h-3 w-3" />
              Simulation only · Not safety certified
            </span>
          </motion.div>

          <motion.h1
            {...fade(0.05)}
            className="text-3xl font-semibold leading-tight tracking-tight text-slate-50 sm:text-4xl lg:text-[42px]"
          >
            Watch an autonomous rover mission get
            {" "}<span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-sky-300 bg-clip-text text-transparent">approved, rejected, and replayed</span>
            {" "}through a safety-supervised control stack.
          </motion.h1>

          <motion.p {...fade(0.12)} className="max-w-xl text-base text-slate-200/90 sm:text-lg">
            A simulation-only autonomous rover safety platform. Mission
            requests are validated, unsafe commands are refused before motion
            authority, and every decision produces deterministic replay evidence.
            It does not control real hardware and is not safety-certified.
          </motion.p>

          <motion.div {...fade(0.2)} className="flex flex-wrap items-center gap-2.5">
            <Link
              href="/demo/warehouse-replay"
              data-testid="start-cta-demo"
              className="group inline-flex items-center gap-2 rounded-md border border-emerald-400/70 bg-gradient-to-b from-emerald-400/40 to-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-50 shadow-[0_8px_24px_-12px_rgba(60,180,168,0.55)] ring-1 ring-emerald-300/20 transition-all hover:-translate-y-0.5 hover:from-emerald-400/55 hover:to-emerald-500/30 hover:shadow-[0_12px_28px_-12px_rgba(60,180,168,0.65)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300 sm:text-[15px]"
            >
              <PlayCircle aria-hidden className="h-4 w-4" />
              Run Mission Replay
              <ArrowRight
                aria-hidden
                className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              />
            </Link>
            <Link
              href="/safety"
              className="inline-flex items-center gap-2 rounded-md border border-cyan-400/40 bg-cyan-400/10 px-4 py-2.5 text-sm text-cyan-100 transition-colors hover:border-cyan-300 hover:bg-cyan-400/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
            >
              <ShieldCheck aria-hidden className="h-4 w-4" />
              Inspect Safety Authority
            </Link>
          </motion.div>

          <motion.dl
            {...fade(0.28)}
            className="grid gap-3 pt-1 text-[12px] sm:grid-cols-3"
          >
            {STATS.map((s) => (
              <div
                key={s.k}
                className="rounded-md border border-cyan-400/15 px-3 py-2 backdrop-blur-sm"
                style={{ background: "rgba(255,255,255,0.025)" }}
              >
                <dt className="font-mono text-[10px] uppercase tracking-[0.16em] text-cyan-300/80">
                  {s.k}
                </dt>
                <dd className="mt-0.5 font-medium text-slate-100">{s.v}</dd>
              </div>
            ))}
          </motion.dl>
        </div>

        <motion.div
          {...fade(0.18)}
          className="relative"
        >
          <AnimatedMissionPreview />
          <div className="pointer-events-none absolute -top-5 -right-3 hidden h-16 w-16 sm:block sm:h-20 sm:w-20">
            <MiniRoverAccent className="h-full w-full drop-shadow-[0_4px_12px_rgba(60,180,168,0.4)]" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

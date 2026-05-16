"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, FileSearch, OctagonX, Route } from "lucide-react";
import Link from "next/link";

interface Challenge {
  id: string;
  href: string;
  cta: string;
  badge: string;
  badgeTone: "ok" | "block" | "audit";
  title: string;
  copy: string;
  icon: typeof Route;
  detail: ReadonlyArray<string>;
}

const CHALLENGES: readonly Challenge[] = [
  {
    id: "approved",
    href: "/demo/warehouse-replay",
    cta: "View replay",
    badge: "Approved",
    badgeTone: "ok",
    title: "Approved path",
    copy: "A nominal warehouse pickup mission that stays inside the rover's bounded authority — distance, angle, speed, allowed topics. Replay is deterministic and traceable.",
    icon: Route,
    detail: [
      "Validator · bounded distance/angle/speed",
      "Supervisor · /cmd_vel_requested allowed",
      "Replay · canonical-fixture sealed",
    ],
  },
  {
    id: "boundary",
    href: "/safety",
    cta: "Inspect safety logic",
    badge: "Rejected",
    badgeTone: "block",
    title: "Boundary violation",
    copy: "A request attempts a path through a restricted mezzanine. The validator flags the violation and the supervisor refuses to authorise motion — every refusal is recorded.",
    icon: OctagonX,
    detail: [
      "Rejected · zone exclusion",
      "Supervisor · authority preserved",
      "Audit · refusal recorded with reason",
    ],
  },
  {
    id: "evidence",
    href: "/evidence",
    cta: "Open evidence",
    badge: "Audited",
    badgeTone: "audit",
    title: "Evidence review",
    copy: "Follow the decision trail from mission event to audit artifact: requirements, validator output, supervisor verdict, deterministic hashes, replay bundle.",
    icon: FileSearch,
    detail: [
      "Requirements · linked to tests",
      "Hash chain · tamper-evident events",
      "Replay bundle · hash-verifiable",
    ],
  },
];

const TONE_BADGE: Record<Challenge["badgeTone"], string> = {
  ok: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
  block: "border-rose-400/40 bg-rose-500/10 text-rose-200",
  audit: "border-sky-400/40 bg-sky-400/10 text-sky-200",
};

export function MissionChallengeCards() {
  const reduce = useReducedMotion();
  return (
    <section
      data-testid="mission-challenges"
      className="space-y-4"
    >
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="label">Mission challenges</p>
          <h2 className="display-2">Try the safety cases</h2>
        </div>
        <p className="text-xs text-[color:var(--mc-text-muted)]">
          Three scenarios that exercise validator, supervisor, and audit.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        {CHALLENGES.map((c, i) => {
          const Icon = c.icon;
          return (
            <motion.article
              key={c.id}
              initial={reduce ? false : { opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: "easeOut" }}
              className="group flex h-full flex-col gap-3 rounded-xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] p-5 transition-transform hover:-translate-y-0.5 hover:border-cyan-400/40 hover:shadow-[0_12px_28px_-16px_rgba(60,180,168,0.45)]"
            >
              <div className="flex items-center justify-between">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-cyan-400/30 bg-cyan-400/10 text-cyan-200">
                  <Icon aria-hidden className="h-4 w-4" />
                </span>
                <span
                  className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${TONE_BADGE[c.badgeTone]}`}
                >
                  {c.badge}
                </span>
              </div>
              <h3 className="text-base font-semibold text-[color:var(--mc-text)]">
                {c.title}
              </h3>
              <p className="text-sm leading-snug text-[color:var(--mc-text-muted)]">
                {c.copy}
              </p>
              <ul className="space-y-1 text-[11px] font-mono text-[color:var(--mc-text-muted)]">
                {c.detail.map((d) => (
                  <li key={d} className="flex items-center gap-2">
                    <span aria-hidden className="h-1 w-1 rounded-full bg-cyan-300/70" />
                    {d}
                  </li>
                ))}
              </ul>
              <div className="mt-auto pt-2">
                <Link
                  href={c.href}
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-cyan-200 underline-offset-2 group-hover:underline"
                >
                  {c.cta}
                  <ArrowRight aria-hidden className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </div>
            </motion.article>
          );
        })}
      </div>
    </section>
  );
}

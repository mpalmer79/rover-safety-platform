"use client";

import { motion, useReducedMotion } from "framer-motion";
import {
  ClipboardList,
  FileSearch,
  PlayCircle,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import Link from "next/link";

interface Step {
  n: string;
  href: string;
  title: string;
  copy: string;
  icon: typeof PlayCircle;
}

const STEPS: readonly Step[] = [
  {
    n: "01",
    href: "/demo/warehouse-replay",
    title: "Run the replay",
    copy: "Start a deterministic warehouse mission. Watch the rover glide along an approved route.",
    icon: PlayCircle,
  },
  {
    n: "02",
    href: "/safety",
    title: "Challenge the supervisor",
    copy: "See the authority boundary that blocks unsafe commands before motion is issued.",
    icon: ShieldCheck,
  },
  {
    n: "03",
    href: "/workbench",
    title: "Trace a decision",
    copy: "Walk an accepted intent and a rejected intent through the validator and supervisor.",
    icon: Workflow,
  },
  {
    n: "04",
    href: "/evidence",
    title: "Audit the evidence",
    copy: "Open the artifact trail behind every decision — hashes, requirements, replay bundles.",
    icon: FileSearch,
  },
  {
    n: "05",
    href: "/walkthrough",
    title: "Open the architecture",
    copy: "Reviewer walkthrough of the mission pipeline end to end.",
    icon: ClipboardList,
  },
];

export function MissionJourney() {
  const reduce = useReducedMotion();
  return (
    <section
      data-testid="mission-journey"
      className="rounded-2xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-5 py-6 sm:px-7 sm:py-7"
    >
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="label">Start the mission</p>
          <h2 className="display-2">A 5-step reviewer flow</h2>
        </div>
        <p className="text-xs text-[color:var(--mc-text-muted)]">
          About 3 minutes · every step links to a working route.
        </p>
      </header>

      <ol className="relative grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {/* connecting rail (desktop only, decorative) */}
        <span
          aria-hidden
          className="pointer-events-none absolute left-0 right-0 top-7 hidden h-px bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent xl:block"
        />
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.li
              key={s.href}
              initial={reduce ? false : { opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.06, ease: "easeOut" }}
              className="relative"
            >
              <Link
                href={s.href}
                data-testid={`journey-step-${i}`}
                className="group relative flex h-full flex-col gap-2 rounded-xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-4 py-4 transition-all hover:-translate-y-0.5 hover:border-cyan-400/50 hover:shadow-[0_8px_24px_-12px_rgba(60,180,168,0.4)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
              >
                <div className="flex items-center justify-between">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-cyan-400/30 bg-cyan-400/10 text-cyan-200">
                    <Icon aria-hidden className="h-4 w-4" />
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[color:var(--mc-text-muted)]">
                    {s.n}
                  </span>
                </div>
                <p className="text-sm font-semibold text-[color:var(--mc-text)] group-hover:text-cyan-200">
                  {s.title}
                </p>
                <p className="text-xs leading-snug text-[color:var(--mc-text-muted)]">
                  {s.copy}
                </p>
              </Link>
            </motion.li>
          );
        })}
      </ol>
    </section>
  );
}

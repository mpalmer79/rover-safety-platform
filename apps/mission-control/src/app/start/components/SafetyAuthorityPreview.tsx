"use client";

import { motion, useReducedMotion } from "framer-motion";
import {
  ChevronRight,
  Cpu,
  FileCheck2,
  Send,
  ShieldCheck,
  ShieldX,
} from "lucide-react";
import Link from "next/link";

interface Node {
  id: string;
  label: string;
  sub: string;
  tone: "neutral" | "ok" | "reject" | "evidence";
  icon: typeof Send;
}

const NODES: readonly Node[] = [
  {
    id: "proposed",
    label: "Proposed command",
    sub: "/cmd_vel_requested",
    tone: "neutral",
    icon: Send,
  },
  {
    id: "validator",
    label: "Validator",
    sub: "bounded · ODD profile",
    tone: "neutral",
    icon: Cpu,
  },
  {
    id: "supervisor",
    label: "Supervisor authority",
    sub: "ACTIVE_NORMAL",
    tone: "neutral",
    icon: ShieldCheck,
  },
  {
    id: "verdict",
    label: "Approved / rejected",
    sub: "deterministic verdict",
    tone: "ok",
    icon: ShieldCheck,
  },
  {
    id: "evidence",
    label: "Evidence",
    sub: "hash-chained audit",
    tone: "evidence",
    icon: FileCheck2,
  },
];

const TONE_NODE: Record<Node["tone"], string> = {
  neutral: "border-cyan-400/30 bg-cyan-400/10 text-cyan-100",
  ok: "border-emerald-400/45 bg-emerald-400/12 text-emerald-100",
  reject: "border-rose-400/45 bg-rose-500/12 text-rose-100",
  evidence: "border-sky-400/40 bg-sky-400/10 text-sky-100",
};

export function SafetyAuthorityPreview() {
  const reduce = useReducedMotion();
  return (
    <section
      data-testid="safety-authority-preview"
      className="rounded-2xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-5 py-6 sm:px-7 sm:py-7"
    >
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="label">Safety authority</p>
          <h2 className="display-2">How every command is gated</h2>
        </div>
        <Link
          href="/safety"
          className="inline-flex items-center gap-1.5 text-sm text-cyan-200 underline-offset-2 hover:underline"
        >
          Open the full safety surface
          <ChevronRight aria-hidden className="h-4 w-4" />
        </Link>
      </header>

      <ol className="flex flex-col gap-3 lg:flex-row lg:items-stretch lg:gap-2">
        {NODES.map((n, i) => {
          const Icon = n.icon;
          return (
            <motion.li
              key={n.id}
              initial={reduce ? false : { opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-30px" }}
              transition={{ duration: 0.4, delay: i * 0.08, ease: "easeOut" }}
              className="flex flex-1 items-stretch gap-2"
            >
              <div
                className={`flex flex-1 flex-col gap-1 rounded-lg border px-3 py-3 ${TONE_NODE[n.tone]}`}
              >
                <div className="flex items-center gap-2">
                  <Icon aria-hidden className="h-4 w-4" />
                  <span className="text-sm font-semibold">{n.label}</span>
                </div>
                <span className="font-mono text-[10px] uppercase tracking-[0.16em] opacity-80">
                  {n.sub}
                </span>
              </div>
              {i < NODES.length - 1 ? (
                <span
                  aria-hidden
                  className="hidden items-center text-[color:var(--mc-text-muted)] lg:flex"
                >
                  <ChevronRight className="h-5 w-5" />
                </span>
              ) : null}
            </motion.li>
          );
        })}
      </ol>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="flex items-start gap-2 rounded-md border border-emerald-400/30 bg-emerald-400/5 px-3 py-2 text-sm text-emerald-100">
          <ShieldCheck aria-hidden className="mt-0.5 h-4 w-4 text-emerald-300" />
          <p>
            <span className="font-semibold">Approved:</span> bounded request
            within ODD profile. Supervisor authorises{" "}
            <span className="font-mono">/cmd_vel_requested</span>. Replay sealed.
          </p>
        </div>
        <div className="flex items-start gap-2 rounded-md border border-rose-400/30 bg-rose-500/5 px-3 py-2 text-sm text-rose-100">
          <ShieldX aria-hidden className="mt-0.5 h-4 w-4 text-rose-300" />
          <p>
            <span className="font-semibold">Rejected:</span> unsafe speed, path
            through exclusion zone, or forbidden topic. No motion authority is
            issued. Refusal is logged with reason.
          </p>
        </div>
      </div>
    </section>
  );
}

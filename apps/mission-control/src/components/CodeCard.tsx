"use client";

import { motion } from "framer-motion";
import { Copy } from "lucide-react";

import type { SkillCardSummary } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface CodeCardProps {
  skill: SkillCardSummary;
  className?: string;
}

/** Renders verbatim source from the audit bundle - DO NOT reformat (audit hash depends on exact bytes). */
export function CodeCard({ skill, className }: CodeCardProps) {
  return (
    <article className={cn("panel overflow-hidden", className)}>
      <header className="flex items-start justify-between gap-3 border-b border-base-200 px-4 py-3">
        <div className="space-y-0.5">
          <p className="label">{skill.skill_type}</p>
          <h2 className="display-2">{skill.title}</h2>
          <p className="text-sm text-base-700">{skill.subtitle}</p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-1.5">
          {skill.code_card.safety_badges.map((badge) => (
            <span
              key={badge}
              className="rounded border border-base-300 bg-base-100 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-widest text-base-700"
            >
              {badge}
            </span>
          ))}
        </div>
      </header>
      <div className="grid gap-3 px-4 py-4 md:grid-cols-[1fr_auto]">
        <pre
          className="overflow-x-auto rounded bg-base-100 p-3 text-[12px] leading-relaxed font-mono text-base-800"
          aria-label={`Generated code for ${skill.skill_type}`}
        >
          {skill.code.split("\n").map((line, idx) => (
            <motion.span
              key={idx}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.6), duration: 0.18 }}
              className="block whitespace-pre"
            >
              {line || " "}
            </motion.span>
          ))}
        </pre>
        <aside className="md:w-44 space-y-2">
          <p className="label">Reading order</p>
          <ol className="space-y-1 text-xs text-base-700">
            {skill.code_card.animation_steps.map((step, idx) => (
              <li key={step} className="flex items-center gap-2">
                <span className="font-mono text-base-500">{idx + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </aside>
      </div>
      <footer className="flex items-center justify-between gap-2 border-t border-base-200 px-4 py-2 text-xs text-base-600">
        <span className="flex items-center gap-1.5">
          <Copy aria-hidden className="h-3 w-3" />
          {skill.code.split("\n").length} lines · {skill.language}
        </span>
        <span>Generated {skill.generated_at_utc}</span>
      </footer>
    </article>
  );
}

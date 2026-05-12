"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

export interface BreadcrumbEntry {
  label: string;
  href?: string;
}

interface WorkspaceBreadcrumbsProps {
  entries: readonly BreadcrumbEntry[];
  className?: string;
}

export function WorkspaceBreadcrumbs({
  entries,
  className,
}: WorkspaceBreadcrumbsProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      data-testid="workspace-breadcrumbs"
      className={cn(
        "flex flex-wrap items-center gap-1 text-xs text-[color:var(--mc-text-muted)]",
        className,
      )}
    >
      {entries.map((entry, idx) => {
        const isLast = idx === entries.length - 1;
        return (
          <span key={`${entry.label}-${idx}`} className="inline-flex items-center gap-1">
            {entry.href && !isLast ? (
              <Link
                href={entry.href}
                className="hover:text-[color:var(--mc-accent)]"
              >
                {entry.label}
              </Link>
            ) : (
              <span
                aria-current={isLast ? "page" : undefined}
                className={isLast ? "text-[color:var(--mc-text)]" : undefined}
              >
                {entry.label}
              </span>
            )}
            {!isLast ? (
              <ChevronRight aria-hidden className="h-3 w-3" />
            ) : null}
          </span>
        );
      })}
    </nav>
  );
}

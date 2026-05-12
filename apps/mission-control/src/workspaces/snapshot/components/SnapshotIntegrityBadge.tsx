"use client";

import { ShieldCheck, ShieldAlert } from "lucide-react";

import { cn } from "@/lib/utils";

interface SnapshotIntegrityBadgeProps {
  ok: boolean;
  /** Computed hash to show on the badge. */
  hash: string;
  className?: string;
}

export function SnapshotIntegrityBadge({
  ok,
  hash,
  className,
}: SnapshotIntegrityBadgeProps) {
  const Icon = ok ? ShieldCheck : ShieldAlert;
  return (
    <span
      data-testid="snapshot-integrity-badge"
      data-ok={ok}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px]",
        ok
          ? "border-[color:var(--mc-status-completed)] text-[color:var(--mc-status-completed)]"
          : "border-[color:var(--mc-status-rejected)] text-[color:var(--mc-status-rejected)]",
        className,
      )}
    >
      <Icon aria-hidden className="h-3.5 w-3.5" />
      <span className="font-mono">{hash}</span>
    </span>
  );
}

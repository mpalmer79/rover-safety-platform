"use client";

import { useState } from "react";

import type { RehearsalEvent } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface ReplayScrubberProps {
  events: readonly RehearsalEvent[];
  onIndexChange?: (index: number) => void;
  className?: string;
}

/**
 * A deterministic timeline scrubber. The slider advances through the
 * ordered event stream by index; ``event_time_ns`` is derived from
 * the same sequence in the backend, so the scrubber never invents
 * timestamps and the position is always reproducible.
 */
export function ReplayScrubber({
  events,
  onIndexChange,
  className,
}: ReplayScrubberProps) {
  const [index, setIndex] = useState(Math.max(0, events.length - 1));
  if (events.length === 0) {
    return (
      <p className={cn("body-mono text-base-500", className)}>
        No rehearsal events recorded.
      </p>
    );
  }
  const current = events[Math.min(index, events.length - 1)];
  const max = events.length - 1;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="label">scrubber</span>
        <span className="font-mono text-base-700">
          step {index + 1} / {events.length}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={max}
        value={Math.min(index, max)}
        step={1}
        aria-label="Rehearsal event scrubber"
        onChange={(e) => {
          const next = Number(e.target.value);
          setIndex(next);
          onIndexChange?.(next);
        }}
        className="w-full accent-accent"
      />
      <div className="flex items-baseline justify-between gap-2 text-xs text-base-600">
        <span className="font-mono">
          t+{(current.event_time_ns / 1_000_000_000).toFixed(1)}s
        </span>
        <span className="truncate text-base-700">{current.description}</span>
      </div>
    </div>
  );
}

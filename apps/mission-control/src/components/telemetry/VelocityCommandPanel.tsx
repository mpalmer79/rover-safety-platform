"use client";

import { typography } from "@/design-system/typography";
import type { MissionPlan } from "@/adapters/types";

import { TelemetryPanelFrame } from "./TelemetryPanelFrame";

interface VelocityCommandPanelProps {
  plan: MissionPlan | null;
}

/**
 * Renders the *requested* velocity bounds the deterministic
 * compiler produced. Honesty rule: the panel always lists
 * `/cmd_vel` as a forbidden topic and `/cmd_vel_requested` as the
 * sole allowed publisher — the platform never publishes to
 * `/cmd_vel` itself.
 */
export function VelocityCommandPanel({ plan }: VelocityCommandPanelProps) {
  return (
    <TelemetryPanelFrame
      kicker="Velocity command"
      title={plan ? "bounded · per waypoint" : "no plan"}
      derivation={plan ? "mission_plan.waypoints" : "—"}
      integrity={plan ? "passed" : "not_evaluated"}
    >
      {plan ? (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2 text-[11px] text-[color:var(--mc-text-muted)]">
            <span className="rounded-sm bg-[color:var(--mc-surface-overlay)] px-2 py-0.5">
              allowed · /cmd_vel_requested
            </span>
            <span className="rounded-sm bg-[color:var(--mc-surface-overlay)] px-2 py-0.5">
              forbidden · /cmd_vel
            </span>
          </div>
          <ul className="space-y-1.5 text-[12px]">
            {plan.waypoints.map((wp) => (
              <li
                key={wp.waypoint_id}
                className="flex flex-wrap items-baseline justify-between gap-2 rounded-sm border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-2 py-1"
              >
                <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
                  {wp.waypoint_id} · {wp.label}
                </span>
                <span className="font-mono text-[11px] text-[color:var(--mc-text)]">
                  v ≤ {wp.bounded_speed_mps} m/s · d ≤ {wp.bounded_distance_m} m
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className={typography("bodyDense")}>
          No mission plan available — rejected mission or audit not loaded.
        </p>
      )}
    </TelemetryPanelFrame>
  );
}

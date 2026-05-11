import type { MissionPlan } from "@/adapters/types";
import { cn } from "@/lib/utils";

interface SafetyZoneLayerProps {
  plan: MissionPlan | null;
  className?: string;
}

/**
 * Lists the safety zones the plan declares, plus the forbidden
 * topic list. This is a list-based overlay rather than a graphical
 * one — the audit doesn't record zone polygons, so we don't draw
 * any. Honesty over visual fidelity.
 */
export function SafetyZoneLayer({ plan, className }: SafetyZoneLayerProps) {
  if (!plan) {
    return (
      <p className={cn("text-xs text-base-500", className)}>
        No mission plan; safety zones unavailable.
      </p>
    );
  }
  return (
    <div className={cn("space-y-2", className)}>
      <div>
        <p className="label">Forbidden topics</p>
        <ul className="font-mono text-[11px] text-status-rejected">
          {plan.forbidden_topics.length === 0 ? (
            <li className="text-base-500">_(none)_</li>
          ) : (
            plan.forbidden_topics.map((t) => <li key={t}>{t}</li>)
          )}
        </ul>
      </div>
      <div>
        <p className="label">Allowed topics</p>
        <ul className="font-mono text-[11px] text-base-700">
          {plan.requested_topics.length === 0 ? (
            <li className="text-base-500">_(none)_</li>
          ) : (
            plan.requested_topics.map((t) => <li key={t}>{t}</li>)
          )}
        </ul>
      </div>
      <div>
        <p className="label">Safety constraints</p>
        {plan.safety_constraints.length === 0 ? (
          <p className="text-xs text-base-500">_(none declared)_</p>
        ) : (
          <ul className="text-[11px] text-base-700">
            {plan.safety_constraints.map((c) => (
              <li key={c}>• {c}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

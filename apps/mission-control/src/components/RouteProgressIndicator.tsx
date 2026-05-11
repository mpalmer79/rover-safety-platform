import type { MissionRoute } from "@/adapters/spatial";
import { cn } from "@/lib/utils";

interface RouteProgressIndicatorProps {
  route: MissionRoute;
  activeWaypointId?: string | null;
  className?: string;
}

const STAGE_COLOR: Record<string, string> = {
  move: "text-accent",
  patrol: "text-base-700",
  inspect: "text-status-pending",
  wait: "text-base-500",
  stop: "text-status-rejected",
  dock: "text-status-completed",
};

/** Horizontal pill stripe showing waypoint progress along the route. */
export function RouteProgressIndicator({
  route,
  activeWaypointId,
  className,
}: RouteProgressIndicatorProps) {
  if (route.waypoints.length === 0) {
    return (
      <p className={cn("text-xs text-base-500", className)}>
        No waypoints recorded for this rehearsal.
      </p>
    );
  }
  return (
    <ol
      className={cn(
        "flex flex-wrap items-center gap-1.5 text-[11px]",
        className,
      )}
      aria-label="Route progress"
    >
      {route.waypoints.map((wp, idx) => {
        const active = wp.waypoint_id === activeWaypointId;
        const stageColour = STAGE_COLOR[wp.stage_kind] ?? "text-accent";
        return (
          <li key={wp.waypoint_id} className="flex items-center gap-1.5">
            <span
              className={cn(
                "rounded border px-1.5 py-0.5 font-mono",
                active
                  ? "border-accent/60 bg-accent/10 text-accent"
                  : "border-base-300 text-base-700",
              )}
              title={`${wp.label} · ${wp.stage_kind}`}
            >
              <span className={stageColour}>{wp.stage_kind[0]}</span>
              <span className="px-0.5">·</span>
              <span>{wp.waypoint_id}</span>
            </span>
            {idx < route.waypoints.length - 1 ? (
              <span aria-hidden className="text-base-400">›</span>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

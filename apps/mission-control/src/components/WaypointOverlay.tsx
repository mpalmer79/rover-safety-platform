import type { SpatialWaypoint } from "@/adapters/spatial";
import { cn } from "@/lib/utils";

interface WaypointOverlayProps {
  waypoint: SpatialWaypoint | null;
  className?: string;
}

/**
 * Right-rail card that explains the currently-selected waypoint in
 * plain English. The card never invents fields; if the audit didn't
 * record a particular value, the row shows ``—``.
 */
export function WaypointOverlay({ waypoint, className }: WaypointOverlayProps) {
  if (!waypoint) {
    return (
      <div className={cn("panel-tight px-3 py-3 text-xs text-base-500", className)}>
        Select a waypoint on the map to see its bounded inputs.
      </div>
    );
  }
  return (
    <div className={cn("panel-tight px-3 py-3 text-xs", className)}>
      <p className="label mb-1">Waypoint</p>
      <p className="font-mono text-base-900">{waypoint.waypoint_id}</p>
      <p className="mb-2 text-base-700">{waypoint.label || "_(no label)_"}</p>
      <dl className="grid grid-cols-2 gap-1 font-mono text-[11px] text-base-700">
        <dt className="text-base-500">stage</dt>
        <dd>{waypoint.stage_kind}</dd>
        <dt className="text-base-500">x, y</dt>
        <dd>
          {waypoint.position.x.toFixed(2)}, {waypoint.position.y.toFixed(2)}
        </dd>
        <dt className="text-base-500">heading</dt>
        <dd>{waypoint.heading_deg.toFixed(0)}°</dd>
        <dt className="text-base-500">dist (m)</dt>
        <dd>{waypoint.bounded_distance_m.toFixed(2)}</dd>
        <dt className="text-base-500">angle (°)</dt>
        <dd>{waypoint.bounded_angle_deg.toFixed(2)}</dd>
        <dt className="text-base-500">speed (m/s)</dt>
        <dd>{waypoint.bounded_speed_mps.toFixed(2)}</dd>
        <dt className="text-base-500">source</dt>
        <dd>{waypoint.source}</dd>
      </dl>
    </div>
  );
}

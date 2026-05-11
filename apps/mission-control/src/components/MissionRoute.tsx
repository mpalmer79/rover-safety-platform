import type { MissionRoute as RouteData } from "@/adapters/spatial";
import { cn } from "@/lib/utils";

interface MissionRouteListProps {
  route: RouteData;
  className?: string;
}

/**
 * Tabular display of the derived mission route. Used as a companion
 * to ``MissionMap`` so a reviewer can see the underlying bounded
 * values (distance / angle / speed) per waypoint.
 */
export function MissionRouteList({ route, className }: MissionRouteListProps) {
  if (route.waypoints.length === 0) {
    return (
      <p className={cn("text-xs text-base-500", className)}>
        No waypoints recorded.
      </p>
    );
  }
  return (
    <div className={cn("space-y-1", className)}>
      <p className="label">Waypoints (bounded inputs)</p>
      <table className="w-full text-left font-mono text-[11px] text-base-700">
        <thead className="text-base-500">
          <tr>
            <th className="py-1">id</th>
            <th>stage</th>
            <th className="text-right">dist (m)</th>
            <th className="text-right">angle (°)</th>
            <th className="text-right">speed (m/s)</th>
          </tr>
        </thead>
        <tbody>
          {route.waypoints.map((wp) => (
            <tr key={wp.waypoint_id} className="border-t border-base-200">
              <td className="py-1 text-base-800">{wp.waypoint_id}</td>
              <td>{wp.stage_kind}</td>
              <td className="text-right">{wp.bounded_distance_m.toFixed(2)}</td>
              <td className="text-right">{wp.bounded_angle_deg.toFixed(2)}</td>
              <td className="text-right">{wp.bounded_speed_mps.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-[10px] text-base-500">
        Source: <code className="font-mono">{route.derivation_source}</code>.
        {" "}
        {route.note}
      </p>
    </div>
  );
}

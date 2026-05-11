import type {
  MissionRoute,
  SpatialEventMarker,
  SpatialWaypoint,
} from "@/adapters/spatial";
import { fitViewBox } from "@/adapters/spatial";
import { cn } from "@/lib/utils";

interface MissionMapProps {
  route: MissionRoute;
  events?: readonly SpatialEventMarker[];
  activeWaypointId?: string | null;
  className?: string;
  height?: number;
}

const STAGE_COLOR: Record<string, string> = {
  move: "#3cb4a8",
  patrol: "#7c8499",
  inspect: "#facc15",
  wait: "#525c75",
  stop: "#f87171",
  dock: "#4ade80",
};

const SEVERITY_COLOR: Record<SpatialEventMarker["severity"], string> = {
  info: "#525c75",
  warning: "#facc15",
  rejection: "#f87171",
};

/**
 * Deterministic 2D mission map.
 *
 * The map ALWAYS reports the derivation source ("derived from
 * bounded inputs", "topology only", or "unavailable") in its
 * caption so the reviewer cannot mistake the visualisation for
 * real telemetry. Coordinates are computed inside
 * ``buildMissionRoute`` from the same bounded distance/angle fields
 * the audit records; no coordinate is fabricated.
 */
export function MissionMap({
  route,
  events,
  activeWaypointId,
  className,
  height = 280,
}: MissionMapProps) {
  if (route.derivation_source === "unavailable") {
    return (
      <div
        role="img"
        aria-label="Mission map unavailable"
        className={cn(
          "panel-tight flex items-center justify-center px-4 py-6 text-sm text-base-500",
          className,
        )}
      >
        Spatial data unavailable for this mission.
      </div>
    );
  }
  const width = 480;
  const { viewBox, transform } = fitViewBox(route, width, height);

  return (
    <figure
      className={cn(
        "panel-tight overflow-hidden bg-base-100 text-base-700",
        className,
      )}
    >
      <svg
        role="img"
        aria-label="Mission spatial layout"
        viewBox={viewBox}
        width="100%"
        height={height}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <pattern
            id="mission-map-grid"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
          >
            <path d="M40 0L0 0 0 40" fill="none" stroke="#1d2230" strokeWidth="0.75" />
          </pattern>
          <marker
            id="mission-map-arrow"
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M0 0L10 5L0 10z" fill="#3cb4a8" />
          </marker>
        </defs>
        <rect width="100%" height="100%" fill="url(#mission-map-grid)" />

        {/* origin marker */}
        <g>
          {(() => {
            const origin = transform({ x: 0, y: 0 });
            return (
              <>
                <circle
                  cx={origin.x}
                  cy={origin.y}
                  r="6"
                  fill="#1b3d3a"
                  stroke="#3cb4a8"
                />
                <text
                  x={origin.x + 8}
                  y={origin.y - 6}
                  fontSize="10"
                  fill="#7c8499"
                  fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
                >
                  origin
                </text>
              </>
            );
          })()}
        </g>

        {/* route segments */}
        {route.segments.map((segment, idx) => {
          const a = transform(segment.from);
          const b = transform(segment.to);
          const colour = STAGE_COLOR[segment.stage_kind] ?? "#3cb4a8";
          return (
            <line
              key={`seg-${idx}-${segment.waypoint_id}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={colour}
              strokeWidth="2"
              strokeOpacity="0.85"
              markerEnd="url(#mission-map-arrow)"
            />
          );
        })}

        {/* event markers */}
        {events?.map((marker) =>
          marker.position ? (
            <g key={marker.event_id}>
              {(() => {
                const p = transform(marker.position);
                return (
                  <>
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r="3.5"
                      fill={SEVERITY_COLOR[marker.severity]}
                      opacity="0.85"
                    />
                  </>
                );
              })()}
            </g>
          ) : null,
        )}

        {/* waypoints */}
        {route.waypoints.map((wp: SpatialWaypoint) => {
          const p = transform(wp.position);
          const fill = STAGE_COLOR[wp.stage_kind] ?? "#3cb4a8";
          const isActive = wp.waypoint_id === activeWaypointId;
          return (
            <g key={wp.waypoint_id}>
              <circle
                cx={p.x}
                cy={p.y}
                r={isActive ? 9 : 6}
                fill={fill}
                fillOpacity={isActive ? 0.9 : 0.4}
                stroke={fill}
                strokeWidth={isActive ? 2 : 1.2}
              />
              <text
                x={p.x + 10}
                y={p.y + 4}
                fontSize="11"
                fill="#d2d6df"
                fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
              >
                {wp.waypoint_id}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="border-t border-base-200 px-3 py-2 text-[11px] text-base-500">
        <span className="label mr-2">map</span>
        {route.derivation_source === "bounded_inputs"
          ? "Derived layout from bounded distance/angle inputs. No real coordinates."
          : "Topology layout — no bounded distance available; waypoints arranged in order."}
      </figcaption>
    </figure>
  );
}

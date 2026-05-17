import type { RehearsalAudit, MissionWaypoint } from "@/adapters/types";

import { cn } from "@/lib/utils";

interface MissionRouteGlyphProps {
  audit: RehearsalAudit;
  className?: string;
}

type ToneKey = "approved" | "rejected" | "guarded" | "aborted" | "pending";

const TONE_STOPS: Record<ToneKey, { from: string; to: string; ring: string }> = {
  approved: {
    from: "var(--mc-accent)",
    to: "var(--mc-status-completed)",
    ring: "var(--mc-accent)",
  },
  guarded: {
    from: "var(--mc-status-pending)",
    to: "var(--mc-status-warning)",
    ring: "var(--mc-status-pending)",
  },
  rejected: {
    from: "var(--mc-status-rejected)",
    to: "var(--mc-status-aborted)",
    ring: "var(--mc-status-rejected)",
  },
  aborted: {
    from: "var(--mc-status-aborted)",
    to: "var(--mc-status-rejected)",
    ring: "var(--mc-status-aborted)",
  },
  pending: {
    from: "var(--mc-status-pending)",
    to: "var(--mc-accent)",
    ring: "var(--mc-status-pending)",
  },
};

function resolveTone(audit: RehearsalAudit): ToneKey {
  const status = String(audit.final_status);
  const safety = String(audit.safety_status ?? "");
  if (status === "rejected") return "rejected";
  if (status === "aborted") return "aborted";
  if (safety === "guarded") return "guarded";
  if (status === "completed") return "approved";
  return "pending";
}

interface GlyphNode {
  cx: number;
  kind: string;
  label: string;
}

/**
 * Computes node positions for the schematic. The dock origin is always
 * shown; subsequent waypoints are spaced along the x-axis with their
 * position proportional to cumulative bounded distance so a long-haul
 * mission visibly stretches further than a short patrol leg.
 */
function layoutNodes(
  waypoints: ReadonlyArray<MissionWaypoint>,
  width: number,
  padX: number,
): GlyphNode[] {
  const usable = width - padX * 2;
  if (!waypoints.length) {
    return [{ cx: padX, kind: "dock", label: "dock" }];
  }
  const distances = waypoints.map((w) => Math.max(0.25, w.bounded_distance_m));
  const totalDist = distances.reduce((a, b) => a + b, 0.5);
  // Origin dock (rover starts at a pad before the first waypoint).
  const nodes: GlyphNode[] = [{ cx: padX, kind: "dock", label: "start" }];
  let acc = 0.5; // reserve a small lead for the start dock.
  for (let i = 0; i < waypoints.length; i++) {
    acc += distances[i];
    nodes.push({
      cx: padX + (acc / totalDist) * usable,
      kind: waypoints[i].stage_kind || "move",
      label: waypoints[i].label,
    });
  }
  return nodes;
}

const RADIUS = 5.5;

function StageGlyph({
  node,
  color,
  rejected,
}: {
  node: GlyphNode;
  color: string;
  rejected: boolean;
}) {
  const cy = 30;
  const cx = node.cx;
  const kind = node.kind;
  if (kind === "dock") {
    return (
      <g>
        <rect
          x={cx - RADIUS}
          y={cy - RADIUS}
          width={RADIUS * 2}
          height={RADIUS * 2}
          rx={1.5}
          fill="none"
          stroke={color}
          strokeWidth={1.4}
        />
        <rect
          x={cx - 1.5}
          y={cy - 1.5}
          width={3}
          height={3}
          fill={color}
          opacity={0.75}
        />
      </g>
    );
  }
  if (kind === "inspect") {
    return (
      <g>
        <circle cx={cx} cy={cy} r={RADIUS} fill="none" stroke={color} strokeWidth={1.4} />
        <circle cx={cx} cy={cy} r={2.2} fill={color} opacity={0.85} />
        <circle cx={cx} cy={cy} r={RADIUS + 2.4} fill="none" stroke={color} strokeWidth={0.6} strokeDasharray="1 2" opacity={0.55} />
      </g>
    );
  }
  if (kind === "patrol") {
    return (
      <g>
        <path
          d={`M ${cx - RADIUS} ${cy} a ${RADIUS} ${RADIUS} 0 1 1 ${RADIUS * 2} 0 a ${RADIUS} ${RADIUS} 0 1 1 ${-RADIUS * 2} 0`}
          fill="none"
          stroke={color}
          strokeWidth={1.4}
          strokeLinecap="round"
        />
        <path
          d={`M ${cx + RADIUS - 2} ${cy - 2} L ${cx + RADIUS + 0.5} ${cy} L ${cx + RADIUS - 2} ${cy + 2}`}
          fill="none"
          stroke={color}
          strokeWidth={1.4}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    );
  }
  if (kind === "stop") {
    return (
      <g>
        <circle cx={cx} cy={cy} r={RADIUS} fill="none" stroke={color} strokeWidth={1.4} />
        <line x1={cx - 2.6} y1={cy - 2.6} x2={cx + 2.6} y2={cy + 2.6} stroke={color} strokeWidth={1.4} strokeLinecap="round" />
        <line x1={cx + 2.6} y1={cy - 2.6} x2={cx - 2.6} y2={cy + 2.6} stroke={color} strokeWidth={1.4} strokeLinecap="round" />
      </g>
    );
  }
  // default: "move" — arrow-tipped node
  return (
    <g>
      <circle cx={cx} cy={cy} r={RADIUS - 0.5} fill={color} opacity={rejected ? 0.55 : 0.85} />
      <path
        d={`M ${cx - 2} ${cy - 2} L ${cx + 2} ${cy} L ${cx - 2} ${cy + 2} Z`}
        fill="var(--mc-bg-1)"
      />
    </g>
  );
}

/**
 * Deterministic schematic glyph for a rehearsal audit's mission plan.
 *
 * Renders the sequence of waypoint stages (dock → move → inspect →
 * patrol → stop → dock) as small status-toned icons connected by a
 * gradient route. The glyph is derived from the committed plan
 * artifact and never synthesised at render time — distinct missions
 * look distinct, but the same audit always produces the same picture.
 *
 * Rejected and aborted missions show a dashed interrupt across the
 * route so reviewers can see at a glance which rows tripped a
 * supervisor.
 */
export function MissionRouteGlyph({ audit, className }: MissionRouteGlyphProps) {
  const width = 200;
  const height = 60;
  const padX = 14;
  const waypoints = audit.plan?.waypoints ?? [];
  const nodes = layoutNodes(waypoints, width, padX);
  const tone = resolveTone(audit);
  const stops = TONE_STOPS[tone];
  const gradientId = `route-grad-${audit.request.mission_id}`;
  const glowId = `route-glow-${audit.request.mission_id}`;
  const rejected = tone === "rejected" || tone === "aborted";
  const interruptAt = rejected
    ? nodes[Math.min(nodes.length - 1, Math.max(1, nodes.length - 2))]
    : null;

  const pathD = nodes
    .map((n, i) => (i === 0 ? `M ${n.cx} 30` : `L ${n.cx} 30`))
    .join(" ");
  const totalLabel = `${nodes.length} stage${nodes.length === 1 ? "" : "s"}`;
  const distance = waypoints.reduce((a, w) => a + (w.bounded_distance_m || 0), 0);

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md border border-base-200/60",
        className,
      )}
      style={{
        background:
          "linear-gradient(135deg, color-mix(in srgb, var(--mc-surface) 80%, transparent) 0%, color-mix(in srgb, var(--mc-bg-1) 80%, transparent) 100%)",
      }}
      data-testid="mission-route-glyph"
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="block h-full w-full"
        role="img"
        aria-labelledby={`${gradientId}-title`}
      >
        <title id={`${gradientId}-title`}>{`Route schematic: ${totalLabel}, ${distance.toFixed(1)} metres bounded, ${tone}`}</title>
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={stops.from} />
            <stop offset="100%" stopColor={stops.to} />
          </linearGradient>
          <radialGradient id={glowId} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={stops.ring} stopOpacity={0.35} />
            <stop offset="100%" stopColor={stops.ring} stopOpacity={0} />
          </radialGradient>
          <pattern id={`grid-${audit.request.mission_id}`} width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="color-mix(in srgb, var(--mc-text-muted) 18%, transparent)" strokeWidth="0.4" />
          </pattern>
        </defs>

        <rect width={width} height={height} fill={`url(#grid-${audit.request.mission_id})`} opacity={0.55} />
        <ellipse cx={width / 2} cy={30} rx={width / 2} ry={18} fill={`url(#${glowId})`} />

        {/* faint baseline */}
        <line
          x1={padX}
          y1={30}
          x2={width - padX}
          y2={30}
          stroke="color-mix(in srgb, var(--mc-text-muted) 22%, transparent)"
          strokeWidth={0.5}
          strokeDasharray="2 3"
        />

        {/* route stroke */}
        <path
          d={pathD}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={2.2}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={rejected ? "4 3" : undefined}
          opacity={rejected ? 0.7 : 0.95}
        />

        {/* nodes */}
        {nodes.map((node, i) => (
          <StageGlyph
            key={`${audit.request.mission_id}-${i}`}
            node={node}
            color={i === 0 ? stops.from : stops.to}
            rejected={rejected && i === nodes.length - 1}
          />
        ))}

        {/* rejection interrupt */}
        {interruptAt ? (
          <g>
            <line
              x1={interruptAt.cx - 4}
              y1={18}
              x2={interruptAt.cx + 4}
              y2={42}
              stroke="var(--mc-status-rejected)"
              strokeWidth={1.4}
              strokeLinecap="round"
            />
            <line
              x1={interruptAt.cx + 4}
              y1={18}
              x2={interruptAt.cx - 4}
              y2={42}
              stroke="var(--mc-status-rejected)"
              strokeWidth={1.4}
              strokeLinecap="round"
            />
          </g>
        ) : null}

        {/* caption */}
        <text
          x={padX}
          y={height - 6}
          fontFamily="ui-monospace, monospace"
          fontSize="7"
          fill="color-mix(in srgb, var(--mc-text-muted) 90%, transparent)"
          letterSpacing="0.12em"
        >
          {`${totalLabel.toUpperCase()} · ${distance.toFixed(1)}M`}
        </text>
        <text
          x={width - padX}
          y={height - 6}
          textAnchor="end"
          fontFamily="ui-monospace, monospace"
          fontSize="7"
          fill={stops.ring}
          letterSpacing="0.12em"
          opacity={0.85}
        >
          {tone.toUpperCase()}
        </text>
      </svg>
    </div>
  );
}
